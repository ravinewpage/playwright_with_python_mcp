# CLAUDE.md - Project Guidelines for Claude Code

## Project: Kohls.com Test Automation Suite
**Purpose:** Production-grade test automation framework using Playwright, Python, Page Object Model, and MCP servers.

**Branch:** `claude_with_skills` (main development branch)  
**Status:** ✅ Complete with Knowledge Skills, Agent Skills, and Smoke Testing

---

## 🚨 CRITICAL SAFETY RULES (Never Deviate)

### Rule 1: NEVER Click "Place Order" Button
- Tests stop at `checkout.click_review_order()`
- No `checkout.click_place_order()` anywhere in codebase
- Reason: Would create **real orders with real charges**
- Verification: Search codebase for `click_place_order` - should be ZERO results

### Rule 2: NEVER Automate Password Entry
- LoginPage pauses for human password input
- Use: `login.wait_for_manual_password_entry("Prompt message")`
- Never hardcode passwords in tests
- Reason: Security boundary - no credentials in code

### Rule 3: NEVER Automate CVV/Expiry Entry
- CheckoutPage pauses for human card entry
- Use: `checkout.wait_for_manual_card_entry("Prompt message")`
- Never automate payment secrets
- Reason: PCI compliance - card data not in automation

### Rule 4: All Config from Environment Only
- Use: `ScenarioData.from_env()` from config.py
- Never hardcode: emails, URLs, search queries, thresholds
- All overridable via `.env` or environment variables
- Reason: Enables test account separation, prevents accidental production use

### Rule 5: Test Accounts Only
- Never run against production/personal accounts
- Use dedicated test account for Kohls
- Document test account requirements in .env.example
- Reason: Prevents real charges and data exposure

---

## 📁 Project Structure

```
├── SKILL_*.md (5 files)            # Knowledge skills (< 50 lines each)
│   ├── SKILL_POM_BEST_PRACTICES.md
│   ├── SKILL_LOCATOR_STRATEGY.md
│   ├── SKILL_SAFETY_RULES.md       ⚠️ READ FIRST
│   ├── SKILL_TEST_WRITING.md
│   └── SKILL_KOHLS_PAGE_STRUCTURE.md
│
├── SKILL_AGENT_GENERATION.md       # Agent skills & parallel execution
├── README_SKILLS.md                # Comprehensive guide
├── CLAUDE.md                       # This file
│
├── run_tests.py                    # Test runner (scenario-based)
├── pytest.ini                      # Pytest config + smoke marker
├── requirements.txt                # Dependencies (includes pytest-xdist)
│
├── pages/                          # Page Object Model
│   ├── base_page.py                # Self-healing + retry logic
│   ├── login_page.py               # ⚠️ Manual password pause
│   ├── checkout_page.py            # ⚠️ Manual CVV pause, NO order button
│   └── ...
│
├── tests/
│   ├── test_scenarios.py           # NEW: Pytest classes (parameterized)
│   ├── test_kohls_flow.py          # LEGACY: Function-based E2E
│   ├── test_kohls_kids_clothing_browse.py  # LEGACY: Function-based Kids
│   ├── conftest.py                 # Fixtures (browser, db_logger, run_id)
│   └── utils.py                    # Logging helpers
│
└── db/
    └── schema.sql                  # Postgres schema (5 tables)
```

---

## 🎯 Test Suites

### Suite 1: `test_kohls_end_to_end` (@pytest.mark.smoke)
**Full shopping flow without order placement**
```
Login (fail) → Login (success) → Search → Product → Cart → Checkout → Review → STOP
```
- Assertions: Product price, cart subtotal, order total (with shipping)
- Manual pauses: Password entry, CVV/expiry entry
- Database logging: Login attempts, API calls, assertions
- **CRITICAL:** Stops at review_order, never clicks place_order

### Suite 2: `test_kids_clothing_browse_and_add_to_cart` (@pytest.mark.smoke)
**Category browsing without login (avoids Akamai bot-blocking)**
```
Homepage → Category menu → Kids & Toys → Carousel → Subcategory → Product → Add to cart
```
- Assertions: Category visible, cart popup text
- No login required (works around bot-blocking)
- Database logging: API calls, assertions

---

## 🚀 How to Run

### Installation
```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # Fill in credentials and DATABASE_URL
```

### Run Tests

**Option 1: Using run_tests.py (Recommended)**
```bash
python run_tests.py --scenario e2e              # E2E only
python run_tests.py --scenario kids             # Kids browse only
python run_tests.py --scenario smoke            # All critical paths
python run_tests.py --scenario all --parallel   # Everything in parallel
python run_tests.py --scenario smoke --parallel -n 4  # 4 workers
```

**Option 2: Direct pytest**
```bash
pytest -m smoke -v -s                  # Smoke tests
pytest -m smoke -n auto -v -s          # Smoke tests parallel
pytest tests/test_scenarios.py -v -s   # All tests in test_scenarios.py
```

---

## 🔍 Common Tasks

### Add a New Test
1. Read: SKILL_TEST_WRITING.md + SKILL_POM_BEST_PRACTICES.md
2. Add test method to appropriate class in `tests/test_scenarios.py`
3. Use fixtures: `browser_page`, `db_logger`, `run_id`
4. Add `@pytest.mark.smoke` if critical path
5. Ensure manual pauses for password/CVV

### Modify a Locator
1. Read: SKILL_LOCATOR_STRATEGY.md
2. Update page object in `pages/*.py`
3. Add 3+ candidates (data-testid first)
4. Run: `pytest tests/ -v -s` to verify
5. Check Postgres `locator_health` table for healing stats

### Run Specific Test
```bash
pytest tests/test_scenarios.py::TestKohlsEndToEnd::test_kohls_end_to_end -v -s
pytest tests/test_scenarios.py::TestKidsClothingBrowse -v -s -k kids_clothing
```

### Debug a Failure
```bash
# Run with output, capture screenshots
pytest tests/test_scenarios.py -v -s --tb=short

# Check Postgres logs
psql playwright_mcp
SELECT * FROM test_assertions WHERE run_id = <run_id> ORDER BY created_at;
SELECT * FROM api_calls WHERE run_id = <run_id>;
SELECT * FROM locator_health WHERE run_id = <run_id>;
```

### Query Test Results
```bash
psql playwright_mcp

# All runs
SELECT id, status, created_at FROM test_runs ORDER BY created_at DESC LIMIT 10;

# Assertions for a specific run
SELECT step_name, assertion_name, actual_value, threshold_value, passed 
FROM test_assertions WHERE run_id = <run_id>;

# API calls captured
SELECT step_name, method, url, response_status FROM api_calls WHERE run_id = <run_id>;
```

---

## ✅ Verification Checklist Before Modifying

- [ ] Read SKILL_SAFETY_RULES.md (Rule 1-5 above)
- [ ] Search codebase for `click_place_order` → must be 0 results
- [ ] Search for hardcoded emails/passwords → must be 0 results
- [ ] All test data from `ScenarioData.from_env()` → no hardcoding
- [ ] Pytest fixtures injected (browser_page, db_logger, run_id)
- [ ] Manual pauses for password and CVV
- [ ] Tests marked with `@pytest.mark.smoke` if critical
- [ ] Database logging present (capture_step_apis, assert_and_log)

---

## 📚 Documentation Files (Read in Order)

1. **SKILL_SAFETY_RULES.md** ⚠️ START HERE
   - Critical safety boundaries
   - Never automate passwords, CVV, or order placement

2. **SKILL_POM_BEST_PRACTICES.md**
   - Page Object Model structure
   - One page = one class rule
   - Self-healing with 3+ candidates

3. **SKILL_LOCATOR_STRATEGY.md**
   - Locator selection order (data-testid → role → CSS)
   - Kohls-specific locators

4. **SKILL_TEST_WRITING.md**
   - 3-part test structure (Setup→Action→Assert)
   - Smoke marker usage

5. **SKILL_KOHLS_PAGE_STRUCTURE.md**
   - Complete page map
   - API endpoints logged

6. **SKILL_AGENT_GENERATION.md**
   - Parameterized test execution
   - Parallel processing with pytest-xdist

7. **README_SKILLS.md**
   - Comprehensive overview
   - Full architecture guide

---

## 🔗 Important Files (Never Delete or Break)

| File | Reason | If Broken |
|------|--------|----------|
| `pages/checkout_page.py` | Manual CVV pause & never order button | Orders could be placed |
| `pages/login_page.py` | Manual password pause | Passwords hardcoded in code |
| `pytest.ini` | Smoke marker definition | CI/CD smoke tests won't work |
| `conftest.py` | Database logging fixtures | No test data captured |
| `.env.example` | Configuration template | New devs don't know what to set |

---

## 🚫 What NOT to Do

- ❌ Never add hardcoded emails, passwords, or test data
- ❌ Never automate payment entry (CVV, expiry)
- ❌ Never click "Place Order" or "Finish" buttons
- ❌ Never run tests against production Kohls account
- ❌ Never skip manual pause points
- ❌ Never remove `@pytest.mark.smoke` from critical tests
- ❌ Never commit `.env` file (credentials exposed)
- ❌ Never merge to main without running `pytest -m smoke`

---

## ✨ Best Practices

- ✅ Use `ScenarioData.from_env()` for all test data
- ✅ Add 3+ locator candidates per element (most stable first)
- ✅ Use explicit Playwright waits (never hardcoded `sleep()`)
- ✅ Log every meaningful step (`capture_step_apis`, `assert_and_log`)
- ✅ Assert business thresholds (prices, subtotals, totals)
- ✅ Mark critical paths with `@pytest.mark.smoke`
- ✅ Run smoke tests before committing (`pytest -m smoke`)
- ✅ Query Postgres to verify test data captured

---

## 🔄 Git Workflow

**Branch:** `claude_with_skills`

```bash
# Before working
git pull origin claude_with_skills

# After changes
git add -A
git commit -m "Description (follow conventional commits)"
git push origin claude_with_skills

# Before merging to main
pytest -m smoke -v -s  # All smoke tests must pass
```

---

## 📞 Questions?

1. **How do I add a test?** → Read SKILL_TEST_WRITING.md
2. **How do I fix a locator?** → Read SKILL_LOCATOR_STRATEGY.md
3. **Is password automation allowed?** → NO, read SKILL_SAFETY_RULES.md
4. **Can I click the order button?** → NO, never, read SKILL_SAFETY_RULES.md
5. **How do I run tests in parallel?** → Read SKILL_AGENT_GENERATION.md + run `python run_tests.py --scenario all --parallel`

---

## 🎯 Project Status

✅ Knowledge Skills: 5 files, all < 50 lines  
✅ Agent Skills: Parameterized tests, pytest classes, parallel support  
✅ Safety Rules: Enforced in code (no passwords, CVV, order placement)  
✅ Smoke Testing: @pytest.mark.smoke on both test suites  
✅ Documentation: Comprehensive guides for all aspects  
✅ Ready for: CI/CD, team onboarding, production use  

**Last Updated:** 2026-08-29  
**Branch:** claude_with_skills  
**Status:** ✅ Production Ready
