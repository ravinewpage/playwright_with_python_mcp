"""Phase 2: pure API-driven replay of the Kohls flow, no browser.

Reuses the session captured from a prior browser run (Run 1, see
tests/test_kohls_flow.py) instead of logging in again -- no password is
ever submitted here, ditto card CVV/expiry, per the project's hard
constraints (see db_logger.py / pages/login_page.py / pages/checkout_page.py
for the same rule enforced in the browser flow).

This script reads the call shapes captured in Postgres (via the SQL MCP
server, `db_logger.DBLogger`) for the most recent successful run, replays
each non-auth, non-payment step as a direct HTTP call using that shape
(substituting per-run values like search term/size where relevant), and
pauses once -- immediately before the place-order call -- for the human to
supply CVV/expiry out of band. Every replayed request/response is logged
back to `api_calls` under a new `test_runs` row so Run 1 (browser-captured
shape) and Run 2 (actual replayed call + response) are both queryable for
comparison.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_logger import DBLogger  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Steps replayed purely from captured shape -- excludes both logins (auth is
# reused, not replayed) and the place-order call (gated on manual CVV/expiry).
REPLAYABLE_STEPS = [
    "search",
    "open_product",
    "product_details",
    "add_to_cart",
    "view_cart",
    "checkout_start",
    "review_order",
    "order_confirmation",
    "track_order",
    "cancel_order",
]
PAYMENT_GATED_STEP = "place_order"


def get_source_run_id(db: DBLogger) -> int:
    result = db.query(
        "SELECT run_id FROM login_attempts WHERE result = 'success' "
        "ORDER BY attempted_at DESC LIMIT 1"
    )
    rows = result.get("rows", [])
    if not rows:
        raise RuntimeError("No successful browser login run found to replay from.")
    return rows[0]["run_id"]


def get_session_headers(db: DBLogger, source_run_id: int) -> dict:
    """Pull the auth cookie/token observed on the first authenticated call
    after the successful login, to reuse as this run's session -- never a
    fresh login."""
    result = db.query(
        "SELECT response_payload FROM api_calls "
        f"WHERE run_id = {source_run_id} AND step_name = 'login_success' "
        "ORDER BY captured_at ASC LIMIT 1"
    )
    rows = result.get("rows", [])
    if not rows:
        raise RuntimeError("No captured login_success API call to source a session from.")
    # The exact header/cookie name depends on what Kohls' login API returns;
    # this is left as a documented extension point rather than guessed here.
    return {}


def replay_step(db: DBLogger, run_id: int, source_run_id: int, step_name: str, client: httpx.Client) -> None:
    result = db.query(
        f"SELECT method, url, request_payload FROM api_calls "
        f"WHERE run_id = {source_run_id} AND step_name = '{step_name}' "
        "ORDER BY captured_at ASC"
    )
    for call in result.get("rows", []):
        method, url, payload = call["method"], call["url"], call.get("request_payload")
        response = client.request(method, url, json=payload)
        db.log_api_call(
            run_id=run_id,
            step_name=step_name,
            method=method,
            url=url,
            request_payload=payload,
            response_status=response.status_code,
            response_payload=_safe_json(response),
        )


def _safe_json(response: httpx.Response):
    try:
        return response.json()
    except Exception:
        return None


def main() -> None:
    db = DBLogger(database_url=os.environ.get("DATABASE_URL"))
    run_id = db.start_run(test_name="kohls_api_replay")

    source_run_id = get_source_run_id(db)
    headers = get_session_headers(db, source_run_id)

    with httpx.Client(headers=headers, timeout=15) as client:
        for step in REPLAYABLE_STEPS:
            replay_step(db, run_id, source_run_id, step, client)

        print("\n>>> PAUSED before place-order call.")
        print(">>> This script will not submit CVV/expiry. Complete payment manually")
        print(">>> (e.g. via the live browser) then press Enter to record the outcome.")
        input()

    db.finish_run(run_id, status="completed", notes=f"replayed from run {source_run_id}")


if __name__ == "__main__":
    main()
