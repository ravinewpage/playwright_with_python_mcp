# Kohls.com Test Automation - Skills & Best Practices

This project demonstrates professional test automation using **Page Object Model (POM)**, **Playwright**, **Python**, and **MCP servers** for Kohls.com shopping workflows.

## Quick Start

### Run All Tests
```bash
pytest -v -s
```

### Run Smoke Tests Only (Fast CI)
```bash
pytest -m smoke -v -s
```

### Run Specific Test
```bash
pytest tests/test_kohls_flow.py -v -s
```

## Project Skills (Best Practices)

### 1. **SKILL_POM_BEST_PRACTICES.md** 
   - One page = One class
   - No test logic in POM
   - Self-healing locators with 3+ candidates
   - Safety rules (never type passwords, never click order button)

### 2. **SKILL_LOCATOR_STRATEGY.md**
   - Locator selection order: data-testid → role+label → CSS
   - Kohls-specific element locators
   - Testing locator validity in Inspector

### 3. **SKILL_SAFETY_RULES.md** ⚠️ CRITICAL
   - **NEVER automate passwords** - Manual pause point
   - **NEVER click "Place Order"** - Test stops at review page
   - Test data from `.env` only (no hardcoding)
   - Test/sandbox accounts only (never production)
   - Full audit logging to Postgres

### 4. **SKILL_TEST_WRITING.md**
   - 3-part test structure: Setup → Action → Assert
   - Step-by-step comments explaining WHAT & WHY
   - Use `@pytest.mark.smoke` for critical paths
   - Assertions with business thresholds (price, subtotal, total)

### 5. **SKILL_KOHLS_PAGE_STRUCTURE.md**
   - Complete page map (HomePage, LoginPage, SearchPage, etc.)
   - Key locators for each page
   - API endpoints captured in network logs
   - Dynamic elements (cart count, prices, stock status)

## Test Suites

### Test Suite 1: `test_kohls_end_to_end` ✅ @pytest.mark.smoke
**Scenario:** Full authenticated shopping flow (minus order placement)

**Flow:**
1. Failed login attempt (negative test)
2. Successful login
3. Product search
4. Open product details
5. Add to cart
6. Review cart
7. Proceed to checkout
8. Fill contact email
9. Manual CVV/expiry entry (human pause)
10. Review order with shipping total
11. **STOPS** - Does NOT click "Place Order" ✓

**Assertions:**
- Login success/failure
- Product price ≤ threshold
- Cart subtotal ≤ threshold
- Order total (with shipping) ≤ threshold

### Test Suite 2: `test_kids_clothing_browse_and_add_to_cart` ✅ @pytest.mark.smoke
**Scenario:** Category browsing without login (avoids bot-blocking)

**Flow:**
1. Open homepage
2. Open "Shop by Category" hamburger menu
3. Verify "Kids & Toys" category visible
4. Click "Kids & Toys"
5. Select carousel item ("Little girls")
6. Drill into subcategory ("School Uniforms")
7. Open product
8. Select color
9. Select size
10. Add to cart
11. Verify cart popup confirmation text

**Assertions:**
- Category visible in menu
- Cart popup text confirms shipping

## Safety Guarantees

✅ **No passwords ever typed** - LoginPage pauses for human entry
✅ **No payment info ever entered** - CheckoutPage pauses for manual CVV/expiry
✅ **No orders ever placed** - Test stops at review page (never clicks "Place Order")
✅ **No hardcoded credentials** - All data from `.env` + `config.py`
✅ **Test accounts only** - Never touches production accounts
✅ **Full audit trail** - Every step logged to Postgres

## Architecture

```
pages/
  ├── base_page.py              # Self-healing + retry logic
  ├── login_page.py             # Manual password pause
  ├── search_page.py            # Product search
  ├── product_page.py           # Product details + add to cart
  ├── cart_page.py              # Cart review
  ├── checkout_page.py          # Manual CVV/expiry pause (NEVER clicks order button)
  └── ...

tests/
  ├── conftest.py               # Fixtures + MCP setup
  ├── test_kohls_flow.py        # @pytest.mark.smoke - full flow
  ├── test_kohls_kids_clothing_browse.py  # @pytest.mark.smoke - browse only
  └── utils.py                  # Logging + assertion helpers

.mcp.json                         # MCP servers: GitHub, Postgres, Playwright
pytest.ini                        # Marker definitions (smoke, etc.)
SKILL_*.md                        # 5 skill files (~40 lines each)
```

## Running Smoke Tests in CI

```yaml
# Example GitHub Actions
- name: Run smoke tests
  run: |
    source .venv/bin/activate
    pytest -m smoke -v -s --tb=short
```

## Known Limitations

- **Kohls.com bot-blocking:** Akamai WAF blocks automated sign-in (see README.md §3.1)
  - Workaround: Use `test_kohls_kids_clothing_browse.py` (no login needed)
  - Alternative: Target a site without bot-blocking (saucedemo.com, etc.)

## File Size Limits

All SKILL_*.md files are < 50 lines each, following best practices:
- Concise, actionable guidance
- Code examples over prose
- Links to related skills
- Never duplicative

## Next Steps

1. Read all 5 SKILL_*.md files (takes ~10 minutes)
2. Review `pages/base_page.py` for self-healing mechanics
3. Trace one test against its page objects
4. Run: `pytest -m smoke -v -s`
5. Check Postgres for logged data (api_calls, locator_health, test_assertions)
