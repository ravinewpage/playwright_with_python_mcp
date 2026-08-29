# Page Object Model (POM) Best Practices

## Core Rules
1. **One page = One class** - Each Kohls page gets a dedicated class in `pages/`
2. **No test logic in POM** - Page objects only expose high-level actions (`add_to_cart()`, `fill_email()`)
3. **Locators as private** - Store CSS/XPath selectors privately, never expose raw selectors to tests
4. **Self-healing candidates** - Define 3+ locator alternatives, most stable first (data-testid → role+label → CSS)
5. **Explicit waits only** - Use `wait_for_load_state()`, `expect()` visibility, never `sleep()`

## Structure
```python
class PageName(BasePage):
    # Private candidates (most stable first)
    ELEMENT_NAME_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("id")),
        LocatorCandidate("role+label", lambda p: p.get_by_role("button", name="Label")),
        LocatorCandidate("css", lambda p: p.locator("#id, .class")),
    ]
    
    # Public high-level actions only
    def action_name(self) -> ReturnType:
        """User-friendly description of what this does."""
        element = self.resolve("element_name", self.ELEMENT_NAME_CANDIDATES)
        return element.click()
```

## Logging & Assertions
- Use `db_logger.log_*()` for every meaningful step
- Use `assert_and_log()` for price/subtotal/order-total checks
- Capture API calls via `capture_step_apis()`

## Safety & Security
- **NEVER type passwords, CVV, expiry** - Pause and wait for human input
- **NEVER click "Place Order" or "Finish"** - Stop at review/confirmation page
- **No hardcoded test data** - All config from `.env` via `config.py`
- **No production accounts** - Use test/sandbox accounts only
