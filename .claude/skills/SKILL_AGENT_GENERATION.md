---
name: agent-generation
description: Parameterized test execution, pytest class-based scenarios, parallel processing with pytest-xdist, and fixture-driven test generation. Use when running tests or adding new test scenarios.
user-invocable: true
---

# Agent Skills - Test Generation & Parameterized Execution

## Overview
Tests are organized as **parameterized scenarios** using fixtures and pytest classes, enabling:
- **Scenario-based execution** (E2E, Kids, Smoke, All)
- **Parallel processing** with pytest-xdist
- **Dynamic test generation** via fixtures
- **Command-line control** via `run_tests.py`

## Scenarios

### 1. E2E Scenario (`kohls_end_to_end`)
**Test:** `tests/test_scenarios.py::TestKohlsEndToEnd::test_kohls_end_to_end`

**Flow:**
1. Failed login (negative test)
2. Successful login
3. Product search
4. Product details + price assertion
5. Add to cart
6. Review cart + subtotal assertion
7. Checkout flow (no order placement)

**Command:**
```bash
python run_tests.py --scenario e2e
```

### 2. Kids Clothing Scenario (`kids_clothing`)
**Test:** `tests/test_scenarios.py::TestKidsClothingBrowse::test_kids_clothing_browse_and_add_to_cart`

**Flow:**
1. Open homepage
2. Browse category menu
3. Navigate to Kids & Toys
4. Select carousel item
5. Drill into subcategory
6. Add product to cart
7. Verify cart popup

**Command:**
```bash
python run_tests.py --scenario kids
```

### 3. Smoke Tests (All Critical Paths)
**Tests:** Both E2E and Kids tests marked with `@pytest.mark.smoke`

**Command:**
```bash
python run_tests.py --scenario smoke
pytest -m smoke -v -s  # Direct pytest
```

### 4. All Tests
**Tests:** Every test in `tests/`

**Command:**
```bash
python run_tests.py --scenario all
```

## Parallel Processing

### Enable Parallel Execution
```bash
# Auto-detect CPU count
python run_tests.py --scenario smoke --parallel

# Specify worker count
python run_tests.py --scenario all --parallel -n 4

# Direct pytest
pytest -m smoke -n auto -v -s
```

### How It Works
- `pytest-xdist` distributes tests across multiple workers
- Each worker gets a fresh browser instance (fixtures per worker)
- Database logging is serialized (Postgres handles concurrency)
- Results are aggregated and reported

### When to Use Parallel
- ✅ Large test suites (10+ tests)
- ✅ Multiple scenarios that don't interfere
- ✅ CI/CD pipelines (nightly runs)
- ❌ When tests share state (not our case)
- ❌ Quick smoke runs (overhead may slow down)

## Fixture-Based Parameterization

### Built-in Fixtures
```python
# From conftest.py - automatically injected
browser_page       # (page, network_log) tuple
db_logger          # MCP Postgres client
run_id             # Unique test run ID
kohls_urls         # Site URLs
scenario_data      # E2E test data (from .env)
kids_clothing_scenario_data  # Kids test data
view_delay_ms      # Viewing pause duration
```

### Using Fixtures in Tests
```python
@pytest.mark.smoke
class TestKohlsEndToEnd:
    def test_kohls_end_to_end(
        self,
        browser_page,           # Injected by conftest
        db_logger,
        run_id,
        scenario_data,
        view_delay_ms,
    ):
        page, network_log = browser_page
        # Test code uses fixtures
```

### Custom Fixture Override
```bash
# Override scenario data via environment variables
KOHLS_REAL_EMAIL="test@example.com" \
KOHLS_SEARCH_QUERY="shoes" \
pytest tests/test_scenarios.py -v -s
```

## Test Class Organization

### Pattern: One Class Per Scenario
```python
@pytest.mark.smoke
class TestKohlsEndToEnd:
    """Critical path E2E scenario."""
    
    def test_kohls_end_to_end(self, fixtures...):
        """Full flow."""

@pytest.mark.smoke
class TestKidsClothingBrowse:
    """Category browse scenario."""
    
    def test_kids_clothing_browse_and_add_to_cart(self, fixtures...):
        """Browse and add flow."""
```

**Benefits:**
- Logical grouping by scenario
- Easy to run one scenario at a time
- Clear test organization
- Supports pytest discovery

## Run Examples

### Quick Smoke Tests (CI Pipeline)
```bash
python run_tests.py --scenario smoke
# or
pytest -m smoke -v -s
```

### Full E2E (Nightly)
```bash
python run_tests.py --scenario e2e
```

### Parallel Kids Tests (Multiple workers)
```bash
python run_tests.py --scenario kids --parallel -n 2
```

### All Tests in Parallel (Full Regression)
```bash
python run_tests.py --scenario all --parallel
```

### Quiet Mode (CI Summary)
```bash
python run_tests.py --scenario smoke --quiet
```

## Database Logging Integration

Each test fixture gets:
- Unique `run_id` (session-scoped, shared per run)
- `db_logger` MCP client (handles Postgres serialization)
- Network capture (`network_log` list)

**Logged Data:**
- `test_runs` - Overall run status
- `login_attempts` - Auth steps
- `api_calls` - Network requests/responses per step
- `test_assertions` - Price/subtotal/total checks
- `locator_health` - Which selectors resolved

### Query Results
```bash
psql playwright_mcp
SELECT * FROM test_runs ORDER BY created_at DESC LIMIT 5;
SELECT * FROM api_calls WHERE run_id = <run_id> ORDER BY created_at;
SELECT * FROM test_assertions WHERE run_id = <run_id>;
```

## Next Steps

1. **Install pytest-xdist:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a test:**
   ```bash
   python run_tests.py --scenario smoke
   ```

3. **Run in parallel:**
   ```bash
   python run_tests.py --scenario smoke --parallel
   ```

4. **Query results:**
   ```bash
   psql playwright_mcp -c "SELECT * FROM test_assertions ORDER BY created_at DESC LIMIT 10;"
   ```
