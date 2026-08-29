---
name: test-writing
description: Test structure patterns, pytest fixtures, smoke markers, assertions with business thresholds, and common mistakes to avoid. Use when writing new tests or reviewing test code.
user-invocable: true
---

# Test Writing Guidelines for Kohls.com

## Test Structure (3-Part Pattern)
```python
def test_scenario_name(browser_page, db_logger, run_id, scenario_data):
    page, network_log = browser_page
    
    # PART 1: Setup - Create page objects, navigate
    login = LoginPage(page, db_logger=db_logger, run_id=run_id)
    login.open(kohls_urls.base)
    
    # PART 2: Action - Perform user workflow
    login.fill_email(scenario_data.real_email)
    login.wait_for_manual_password_entry("Type password and submit")
    
    # PART 3: Assert - Verify outcomes, log results
    assert login.assert_login_succeeded()
    capture_step_apis(network_log, db_logger, run_id, "login_success")
    db_logger.finish_run(run_id, status="passed")
```

## Step-by-Step Naming
```python
# Each major flow = 1 numbered comment explaining WHAT & WHY
# Step 1: Login with failing credentials (negative test for error handling)
# Step 2: Real login (needed for account-specific features)
# Step 3: Search product (verify catalog works)
```

## Assertions & Logging
```python
# Use assert_and_log() for business thresholds
assert_and_log(
    db_logger, run_id, "product_details", "product_price",
    actual_value=price, threshold=scenario_data.max_product_price,
)

# Use db_logger.log_*() for non-assertion events
db_logger.log_login_attempt(run_id, email, "success")

# Capture every API call per step
capture_step_apis(network_log, db_logger, run_id, "step_name")
```

## Smoke Testing Mark
```python
import pytest

@pytest.mark.smoke  # Run this in quick CI checks
def test_kohls_end_to_end(browser_page, db_logger, run_id, ...):
    """Critical path: login → search → product → cart → checkout."""
    # test code...
```

## Run Smoke Tests Only
```bash
pytest -m smoke -v -s  # Fast CI pipeline
pytest -v -s           # Full suite for nightly
```

## Pause Points (Manual Intervention)
```python
# Use when automation hits hard security boundary
page.wait_for_timeout(view_delay_ms)  # Human can see what happened
login.wait_for_manual_password_entry("Prompt message to user")
```

## Common Mistakes to Avoid
1. ❌ Testing UI details (colors, fonts) → ✅ Test workflows (login → cart)
2. ❌ Hard sleep(5) waits → ✅ Explicit `wait_for_load_state()`
3. ❌ Assertions in page objects → ✅ Assertions in tests only
4. ❌ One test does everything → ✅ Small focused tests
