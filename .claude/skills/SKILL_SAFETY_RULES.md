---
name: safety-rules
description: Critical safety rules for Kohls.com test automation - never automate passwords, CVV, order placement, or hardcode config. Must follow these rules.
user-invocable: true
---

# Safety Rules - Critical for Kohls.com Tests

## Rule 1: NEVER Automate Passwords/CVV/Expiry
```python
# ❌ WRONG
page.fill("#cvv", "123")  # NEVER

# ✅ CORRECT
checkout.wait_for_manual_card_entry(
    "Checkout ready → Enter CVV & Expiry in browser, then press Submit"
)
```
**Why:** Credentials in code = security breach. Hard pause ensures human approval.

## Rule 2: NEVER Click "Place Order" or "Finish"
```python
# ❌ WRONG
checkout.click_place_order()  # Creates REAL order on account

# ✅ CORRECT
order_total = checkout.get_order_total()
assert_and_log(db_logger, run_id, "review_order", "order_total", order_total, threshold)
# TEST STOPS HERE - no order placed
```
**Why:** Real orders = real charges. This is a test account safety boundary.

## Rule 3: Test Data from Environment Only
```python
# ❌ WRONG
email = "test@example.com"  # Hardcoded

# ✅ CORRECT
from config import ScenarioData
data = ScenarioData.from_env()
email = data.real_email  # From .env
```
**Why:** Prevent accidental use of real accounts in shared repos.

## Rule 4: Use Test/Sandbox Accounts
- Always use a dedicated test account for Kohls
- Never use production/personal accounts
- Account should be created for testing only
- Verify account exists before running suite

## Rule 5: Log Everything
```python
db_logger.log_login_attempt(run_id, email, "success")
db_logger.log_order(run_id, subtotal=subtotal, status="pending")
capture_step_apis(network_log, db_logger, run_id, "step_name")
```
**Why:** Full audit trail for debugging and compliance.

## Pre-Run Checklist
- [ ] Playwright in headless=False (you can see what's happening)
- [ ] Test account credentials in .env (never hardcoded)
- [ ] `-s` flag in pytest (shows manual pause prompts)
- [ ] No real payment card on file
- [ ] Review `test_kohls_flow.py` line 147 - stops before place_order
