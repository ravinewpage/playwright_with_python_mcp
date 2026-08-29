---
name: locator-strategy
description: Locator selection priority order (data-testid → role+label → CSS) for Kohls.com and best practices for resilient element selection. Use when writing or debugging page object locators.
user-invocable: true
---

# Locator Strategy for Kohls.com

## Candidate Selection Order (Most Stable First)

### 1st Choice: Data Attributes (Most Stable)
```python
# Best: data-testid, data-qa, data-id
p.get_by_test_id("email-input")
p.locator("[data-qa='add-to-cart']")
```
**Why:** Developers maintain these; rarely change during UI refactor.

### 2nd Choice: Semantic Accessibility Roles
```python
# Good: aria-label, role + name
p.get_by_role("button", name="Add to Cart")
p.get_by_label("Email Address")
```
**Why:** Accessible; tied to user-facing text, survives minor markup changes.

### 3rd Choice: CSS Selectors (Least Stable)
```python
# Last resort: id, class, or specificity
p.locator("#email-input")
p.locator("button.add-to-cart:first-of-type")
```
**Why:** Brittle; changes with every CSS refactor. Use only if no alternatives.

## Kohls.com Specific Locators

| Page | Element | Best Locator | Backup |
|------|---------|--------------|--------|
| Login | Email | `data-testid="email"` | `role="textbox", name="Email"` |
| Login | Password | Manual pause (NEVER automate) | N/A |
| Search | Search box | `[data-testid="search-input"]` | `placeholder="Search"` |
| Product | Add to Cart | `data-testid="add-to-cart"` | `role="button", name="Add"` |
| Checkout | Review Order | `data-testid="review-button"` | CSS button |
| Checkout | Place Order | **NEVER USE** | N/A |

## Testing Locators
```bash
# Open DevTools in Playwright Inspector
# Right-click element → Inspect → copy selector
# Verify with: element.locator("selector").count() > 0
```
