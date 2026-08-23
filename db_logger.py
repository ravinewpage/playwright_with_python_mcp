"""MCP-only Postgres logging client.

All test data (runs, login attempts, captured API calls, orders, locator
health) is written through the Postgres MCP server's tools over stdio --
never through a raw psycopg2/DB-API connection -- per the project's
MCP-only requirement.

Note: the official @modelcontextprotocol/server-postgres wraps every query
in a read-only transaction and rejects INSERT/UPDATE, so this project uses
the `mcp-postgres` npm package instead, which exposes insert_data/
query_data/execute_raw_query tools with real write support. See .mcp.json.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

_CALL_TIMEOUT_S = 20


class DBLogger:
    """Synchronous-looking wrapper around an MCP Postgres client session.

    Each call opens a short-lived MCP stdio session, issues one tool call,
    and closes it -- simple and robust for a page-object-driven test run
    where writes are infrequent relative to browser actions.
    """

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.environ.get(
            "DATABASE_URL", "postgresql://localhost/playwright_mcp"
        )

    def _run(self, coro):
        """Run an MCP coroutine to completion from synchronous callers.

        Always executes on a fresh thread with its own new event loop,
        rather than calling asyncio.run() directly on the caller's thread.
        This matters because Playwright's sync API (used throughout
        pages/ and tests/conftest.py) keeps its own event loop active on
        the calling thread -- e.g. every BasePage.resolve() call logs to
        locator_health mid-page-interaction -- and asyncio.run() raises
        "cannot be called from a running event loop" if one is already
        active there. A dedicated thread sidesteps the question of
        whether that's the case entirely.
        """
        result: dict[str, Any] = {}

        def runner() -> None:
            try:
                result["value"] = asyncio.run(asyncio.wait_for(coro, timeout=_CALL_TIMEOUT_S))
            except BaseException as exc:  # re-raised on the calling thread below
                result["error"] = exc

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        thread.join()
        if "error" in result:
            raise result["error"]
        return result["value"]

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        params = StdioServerParameters(
            command="npx",
            args=["-y", "mcp-postgres"],
            env={"DATABASE_URL": self.database_url},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                text_chunks = [c.text for c in result.content if isinstance(c, TextContent)]
                raw = "\n".join(text_chunks)
                if result.is_error:
                    raise RuntimeError(f"MCP tool '{tool_name}' failed: {raw}")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"raw": raw}

    def insert(self, table_name: str, data: dict[str, Any]) -> dict:
        """Returns mcp-postgres's insert_data shape:
        {"inserted_rows": int, "returning": [{...row}], "execution_time_ms": int}
        -- note the row lives under "returning", not "rows" (that key is
        query_data's shape -- see `query()` below). Callers that need the
        inserted row use `result["returning"][0]`.
        """
        return self._run(self._call_tool("insert_data", {"table_name": table_name, "data": data}))

    def query(self, sql: str) -> dict:
        """Returns mcp-postgres's query_data shape:
        {"rows": [{...}], "rowCount": int, "execution_time_ms": int}
        """
        return self._run(self._call_tool("query_data", {"query": sql}))

    # -- Convenience wrappers for this project's schema --------------------

    def start_run(self, test_name: str) -> int:
        result = self.insert("test_runs", {"test_name": test_name, "status": "running"})
        return result["returning"][0]["id"]

    def finish_run(self, run_id: int, status: str, notes: str | None = None) -> None:
        self._run(
            self._call_tool(
                "execute_raw_query",
                {
                    "query": (
                        "UPDATE test_runs SET status = $1, finished_at = $2, notes = $3 "
                        "WHERE id = $4"
                    ),
                    "params": [status, datetime.now(timezone.utc).isoformat(), notes, run_id],
                },
            )
        )

    def log_login_attempt(self, run_id: int, email: str, result: str) -> None:
        self.insert("login_attempts", {"run_id": run_id, "email": email, "result": result})

    def log_api_call(
        self,
        run_id: int,
        step_name: str,
        method: str,
        url: str,
        *,
        api_name: str | None = None,
        request_payload: dict | None = None,
        response_status: int | None = None,
        response_payload: dict | None = None,
    ) -> None:
        self.insert(
            "api_calls",
            {
                "run_id": run_id,
                "step_name": step_name,
                "api_name": api_name,
                "method": method,
                "url": url,
                "request_payload": json.dumps(request_payload) if request_payload is not None else None,
                "response_status": response_status,
                "response_payload": json.dumps(response_payload) if response_payload is not None else None,
            },
        )

    def log_order(
        self,
        run_id: int,
        *,
        order_id: str | None = None,
        subtotal: float | None = None,
        status: str = "pending",
        placed_at: str | None = None,
        cancelled_at: str | None = None,
    ) -> int:
        result = self.insert(
            "orders",
            {
                "run_id": run_id,
                "order_id": order_id,
                "subtotal": subtotal,
                "status": status,
                "placed_at": placed_at,
                "cancelled_at": cancelled_at,
            },
        )
        return result["returning"][0]["id"]

    def update_order(self, order_row_id: int, **fields: Any) -> None:
        if not fields:
            return
        set_clauses = ", ".join(f"{col} = ${i + 1}" for i, col in enumerate(fields))
        params = list(fields.values()) + [order_row_id]
        self._run(
            self._call_tool(
                "execute_raw_query",
                {
                    "query": f"UPDATE orders SET {set_clauses} WHERE id = ${len(params)}",
                    "params": params,
                },
            )
        )

    def insert_locator_health(
        self, run_id: int | None, element_name: str, candidate_index: int, candidate_strategy: str
    ) -> None:
        self.insert(
            "locator_health",
            {
                "run_id": run_id,
                "element_name": element_name,
                "candidate_index": candidate_index,
                "candidate_strategy": candidate_strategy,
            },
        )

    def log_assertion(
        self,
        run_id: int,
        step_name: str,
        assertion_name: str,
        expected_condition: str,
        actual_value: float | None,
        passed: bool,
    ) -> None:
        """Persist one business-rule check (e.g. "product price < $40") so
        the threshold and the observed value are auditable after the run,
        not just asserted in Python and thrown away. Call this alongside
        every ``assert`` in a test that checks a business rule sourced from
        ScenarioData (see config.py) -- price/subtotal/total thresholds and
        similar. Raises nothing on ``passed=False``; the caller's ``assert``
        is what fails the test -- this just records what was checked.
        """
        self.insert(
            "test_assertions",
            {
                "run_id": run_id,
                "step_name": step_name,
                "assertion_name": assertion_name,
                "expected_condition": expected_condition,
                "actual_value": actual_value,
                "passed": passed,
            },
        )
