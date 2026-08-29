---
name: page-object-generator
type: agent
description: Generates new Page Object Model classes for Kohls.com pages with self-healing locators
capabilities: [read, write, bash]
model: claude-opus-5
---

# Page Object Generator Agent

## Purpose
Automatically generate new Page Object Model classes for Kohls.com pages with proper structure, self-healing locators, and error handling.

## Instructions

### When Invoked
Create a new page object following this structure:

1. **Identify Page**
   - Understand which Kohls page this is (HomePage, ProductPage, etc.)
   - Review existing page objects in `pages/` for patterns
   - Check SKILL_KOHLS_PAGE_STRUCTURE.md for known elements

2. **Create Class Structure**
   ```python
   from __future__ import annotations
   from pages.base_page import BasePage, LocatorCandidate
   
   class PageNamePage(BasePage):
       """User-friendly description of page purpose."""
       
       # Private candidates (most stable first)
       ELEMENT_CANDIDATES = [
           LocatorCandidate("data-testid", lambda p: p.get_by_test_id("id")),
           LocatorCandidate("role+label", lambda p: p.get_by_role("button", name="Label")),
           LocatorCandidate("css", lambda p: p.locator("#css-id")),
       ]
   ```

3. **Add Public Methods**
   - Only expose high-level actions (no raw selectors)
   - Use `self.resolve()` for self-healing
   - Add logging where appropriate
   - Return meaningful values

4. **Follow POM Rules**
   - ✅ One page = one class
   - ✅ No test logic in page objects
   - ✅ Locators as private with 3+ candidates
   - ✅ Public methods only expose actions
   - ✅ Use `self.retry()` for transient failures

5. **Use Self-Healing**
   ```python
   def click_button(self) -> None:
       """Click the action button."""
       element = self.resolve("button", self.BUTTON_CANDIDATES)
       self.retry(lambda: element.click())
   ```

6. **Add to pages/__init__.py**
   - Import the new class
   - Make it discoverable

### Example Page Object
```python
class ProductPage(BasePage):
    """Product details page - price, size, color, add to cart."""
    
    PRICE_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("price")),
        LocatorCandidate("role", lambda p: p.get_by_role("heading", name=re.compile(r"\$"))),
        LocatorCandidate("css", lambda p: p.locator(".product-price")),
    ]
    
    SIZE_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("size-select")),
        LocatorCandidate("role+name", lambda p: p.get_by_role("listbox", name="Size")),
        LocatorCandidate("css", lambda p: p.locator("select[name='size']")),
    ]
    
    def get_price(self) -> float:
        """Extract product price."""
        element = self.resolve("price", self.PRICE_CANDIDATES)
        price_text = element.text_content().strip()
        return float(price_text.replace("$", ""))
    
    def select_size(self, size: str) -> None:
        """Select product size."""
        element = self.resolve("size", self.SIZE_CANDIDATES)
        self.retry(lambda: element.select_option(size))
    
    def add_to_cart(self) -> None:
        """Click add to cart button."""
        button = self.resolve("add_to_cart", self.ADD_TO_CART_CANDIDATES)
        self.retry(lambda: button.click())
```

## Key References
- `SKILL_POM_BEST_PRACTICES.md` - POM architecture rules
- `SKILL_LOCATOR_STRATEGY.md` - Locator candidate ordering
- `pages/base_page.py` - Self-healing mechanics
- `SKILL_KOHLS_PAGE_STRUCTURE.md` - Page map & known locators

## Do NOT
- ❌ Put test logic in page objects
- ❌ Expose raw CSS selectors
- ❌ Use single locator (need 3+ candidates)
- ❌ Use hardcoded waits or sleeps
- ❌ Duplicate code across pages
- ❌ Make methods too granular (actions, not clicks)
