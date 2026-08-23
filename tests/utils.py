"""Test-level helper utilities. Kept separate from conftest.py, which owns
fixture *infrastructure* (browser/DB/config wiring) -- these are plain
functions the test body calls directly, not fixtures.
"""

from __future__ import annotations

from db_logger import DBLogger


def capture_step_apis(network_log: list[dict], db_logger: DBLogger, run_id: int, step_name: str) -> None:
    """Persist every network request/response captured since the last call,
    tagged with the step they belong to, then clear the buffer.

    The `browser_page` fixture (see conftest.py) accumulates raw
    request/response pairs into `network_log` as the test drives the page;
    calling this after each step attributes that traffic to the step that
    caused it, so `api_calls` in Postgres reads as a timeline rather than
    one undifferentiated blob per run.
    """
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


def assert_and_log(
    db_logger: DBLogger,
    run_id: int,
    step_name: str,
    assertion_name: str,
    *,
    actual_value: float,
    threshold: float,
    comparison: str = "<",
) -> None:
    """Check a business-rule threshold (e.g. "price < $40"), persist the
    check (expected condition, actual value, pass/fail) to `test_assertions`
    for audit, and raise via a plain `assert` so pytest reports it normally.

    This exists so every threshold sourced from ScenarioData (config.py) is
    both enforced *and* recorded -- previously these were asserted in the
    test body and the pass/fail criteria lived only in that one Python
    line, invisible outside the test run's console output.
    """
    passed = actual_value < threshold if comparison == "<" else actual_value <= threshold
    db_logger.log_assertion(
        run_id=run_id,
        step_name=step_name,
        assertion_name=assertion_name,
        expected_condition=f"{comparison} {threshold:.2f}",
        actual_value=actual_value,
        passed=passed,
    )
    assert passed, f"{assertion_name}: expected {comparison} ${threshold:.2f}, got ${actual_value:.2f}"


def assert_visible_and_log(
    db_logger: DBLogger,
    run_id: int,
    step_name: str,
    assertion_name: str,
    *,
    condition: bool,
    description: str,
) -> None:
    """Same purpose as `assert_and_log`, for boolean checks (an element/text
    is visible, a menu item exists) rather than numeric thresholds --
    `test_assertions.actual_value` stays NULL for these rows since there's
    no number to record, only `expected_condition` (the description) and
    `passed`.
    """
    db_logger.log_assertion(
        run_id=run_id,
        step_name=step_name,
        assertion_name=assertion_name,
        expected_condition=description,
        actual_value=None,
        passed=condition,
    )
    assert condition, f"{assertion_name}: {description}"
