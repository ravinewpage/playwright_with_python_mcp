from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import KohlsUrls, ScenarioData  # noqa: E402
from db_logger import DBLogger  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@pytest.fixture(scope="session")
def db_logger() -> DBLogger:
    return DBLogger(database_url=os.environ.get("DATABASE_URL"))


@pytest.fixture(scope="session")
def run_id(db_logger: DBLogger) -> int:
    return db_logger.start_run(test_name="kohls_end_to_end_flow")


@pytest.fixture(scope="session")
def kohls_urls() -> KohlsUrls:
    """Site URLs, overridable via KOHLS_BASE_URL / KOHLS_LOGIN_URL in .env."""
    return KohlsUrls.from_env()


@pytest.fixture(scope="session")
def scenario_data() -> ScenarioData:
    """Scenario inputs (emails, search term, product, size, thresholds,
    viewing delay), overridable via env vars -- see config.py / .env.example.
    Never hardcode these in a page object or test body."""
    return ScenarioData.from_env()


@pytest.fixture()
def browser_page(run_id, db_logger):
    """A page with network request/response capture wired up for API logging.

    Yields (page, network_log) where network_log is a list of dicts
    accumulating every request/response pair seen during the test, so the
    test can attribute each captured call to the step it occurred in and
    persist it via db_logger.log_api_call.
    """
    Path("test-results").mkdir(exist_ok=True)
    network_log: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        pending: dict[str, dict] = {}

        def on_request(request):
            pending[request.url + request.method] = {
                "method": request.method,
                "url": request.url,
                "request_payload": _safe_json(request.post_data),
            }

        def on_response(response):
            key = response.url + response.request.method
            entry = pending.pop(key, {
                "method": response.request.method,
                "url": response.url,
                "request_payload": None,
            })
            try:
                response_payload = response.json()
            except Exception:
                response_payload = None
            entry.update(response_status=response.status, response_payload=response_payload)
            network_log.append(entry)

        page.on("request", on_request)
        page.on("response", on_response)

        yield page, network_log

        context.close()
        browser.close()


def _safe_json(raw: str | None):
    if not raw:
        return None
    import json

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"raw": raw[:2000]}


def capture_step_apis(network_log: list[dict], db_logger: DBLogger, run_id: int, step_name: str) -> None:
    """Persist and clear whatever network calls have accumulated for a step."""
    for entry in network_log:
        db_logger.log_api_call(
            run_id=run_id,
            step_name=step_name,
            method=entry["method"],
            url=entry["url"],
            request_payload=entry.get("request_payload"),
            response_status=entry.get("response_status"),
            response_payload=entry.get("response_payload"),
        )
    network_log.clear()
