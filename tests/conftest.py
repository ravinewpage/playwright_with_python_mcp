from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # import config.py, db_logger.py

from config import KidsClothingScenarioData, KohlsUrls, ScenarioData  # noqa: E402
from db_logger import DBLogger  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Env vars every fixture below depends on, directly or via config.py.
# Checked once, up front, so a missing DATABASE_URL fails immediately with
# a clear message instead of surfacing as an opaque MCP connection error
# partway through the first test.
_REQUIRED_ENV_VARS = {
    "DATABASE_URL": "Postgres connection string for the SQL MCP server, e.g. "
    "postgresql://localhost/playwright_mcp",
}


@pytest.fixture(scope="session", autouse=True)
def validate_environment() -> None:
    missing = {name: hint for name, hint in _REQUIRED_ENV_VARS.items() if not os.environ.get(name)}
    if missing:
        details = "\n".join(f"  {name}: {hint}" for name, hint in missing.items())
        raise RuntimeError(
            f"Missing required environment variable(s):\n{details}\n"
            "Copy .env.example to .env and fill these in."
        )


@pytest.fixture(scope="session")
def db_logger() -> DBLogger:
    return DBLogger(database_url=os.environ.get("DATABASE_URL"))


@pytest.fixture(scope="session")
def run_id(db_logger: DBLogger):
    """One test_runs row per pytest session, marked finished on teardown
    even if a test raises -- so a crashed run never sits at status='running'
    in Postgres. test_kohls_end_to_end still calls db_logger.finish_run()
    itself on the success path to record the order ID in `notes`; this
    teardown is the safety net for the failure path."""
    run_id = db_logger.start_run(test_name="kohls_end_to_end_flow")
    yield run_id
    result = db_logger.query(f"SELECT status FROM test_runs WHERE id = {run_id}")
    if result.get("rows", [{}])[0].get("status") == "running":
        db_logger.finish_run(run_id, status="incomplete", notes="Session ended without an explicit finish_run call")


@pytest.fixture(scope="session")
def kohls_urls() -> KohlsUrls:
    """Site URLs, overridable via KOHLS_BASE_URL / KOHLS_LOGIN_URL in .env."""
    return KohlsUrls.from_env()


@pytest.fixture(scope="session")
def scenario_data() -> ScenarioData:
    """Checkout-scenario inputs (emails, search term, product, size,
    thresholds), overridable via env vars -- see config.py / .env.example.
    Never hardcode these in a page object or test body."""
    return ScenarioData.from_env()


@pytest.fixture(scope="session")
def kids_clothing_scenario_data() -> KidsClothingScenarioData:
    """Category-browse-scenario inputs (menu labels, product, color/size,
    expected cart-popup text), overridable via env vars -- see config.py /
    .env.example. Never hardcode these in a page object or test body."""
    return KidsClothingScenarioData.from_env()


@pytest.fixture(scope="session")
def view_delay_ms() -> int:
    """Shared viewing-pace delay (STEP_VIEW_DELAY_MS, default 5000) used by
    every test file's `_pause_for_viewing()` helper -- not scenario-specific
    data, so it lives in its own fixture rather than inside ScenarioData/
    KidsClothingScenarioData."""
    return int(os.environ.get("STEP_VIEW_DELAY_MS", "5000"))


@pytest.fixture()
def browser_page(run_id, db_logger, request):
    """A page with network request/response capture wired up for API logging.

    Yields (page, network_log) where network_log is a list of dicts
    accumulating every request/response pair seen during the test, so the
    test can attribute each captured call to the step it occurred in and
    persist it via db_logger.log_api_call (see tests/utils.py:capture_step_apis).

    On teardown: if the test failed (via the pytest_runtest_makereport hook
    below, which stashes the outcome on the test node), a screenshot is
    captured before the browser closes -- automatic, so a failure is never
    left without visual evidence just because a page object didn't call
    BasePage.capture_failure_evidence() itself.
    """
    Path("test-results").mkdir(exist_ok=True)
    network_log: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        pending: dict[str, dict] = {}

        def on_request(req):
            # req.post_data itself can raise (Playwright tries to utf-8-decode
            # the raw body, which fails for binary/gzip-encoded request
            # bodies -- seen in practice on ordinary sub-resource requests,
            # not just uploads). A network-capture bug must never take down
            # page.goto()/clicks, so this is caught broadly and the payload
            # just recorded as unavailable rather than crashing the test.
            try:
                post_data = req.post_data
            except Exception:
                post_data = None
            pending[req.url + req.method] = {
                "method": req.method,
                "url": req.url,
                "request_payload": _safe_json(post_data),
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

        failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
        if failed:
            page.screenshot(path=f"test-results/failure_{request.node.name}.png", full_page=True)

        context.close()
        browser.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Stash each phase's outcome on the test item (as rep_<phase>) so the
    browser_page fixture's teardown can check whether the test body failed
    and screenshot accordingly -- pytest doesn't expose pass/fail to
    fixtures any other way."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def _safe_json(raw: str | None):
    if not raw:
        return None
    import json

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Not JSON -- e.g. an HTML error page or form-encoded body. Keep a
        # truncated raw snippet rather than dropping the request entirely,
        # so api_calls still shows *something* happened at this step.
        return {"raw": raw[:2000]}
