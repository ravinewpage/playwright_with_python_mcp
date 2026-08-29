---
name: locator-finder
type: agent
description: Finds and updates locators for broken page object selectors using Playwright Inspector
capabilities: [read, write, bash]
model: claude-opus-5
---

# Locator Finder Agent

## Purpose
Automatically discover new locators when page selectors break, following the priority order (data-testid → role+label → CSS) and adding them as fallback candidates.

## Instructions

### When Invoked
Fix broken locators following this process:

1. **Identify Broken Locator**
   - Find which test is failing
   - Identify which page object element is broken
   - Note the current locator strategy

2. **Discover New Locators**
   - Use Playwright Inspector to examine the page
   - Find element using priority order:
     1. **data-testid** (most stable)
     2. **role + label/name** (accessible, stable)
     3. **CSS selector** (brittle, last resort)

3. **Add as Fallback Candidate**
   ```python
   # In page object, add new candidate at front (most stable first)
   ELEMENT_CANDIDATES = [
       LocatorCandidate("data-testid", lambda p: p.get_by_test_id("new-id")),  # New
       LocatorCandidate("role+label", lambda p: p.get_by_role("button", name="Old")),  # Old
       LocatorCandidate("css", lambda p: p.locator("#old-css")),  # Fallback
   ]
   ```

4. **Test Discovery**
   - Run affected test: `pytest tests/test_scenarios.py::TestClass::test_method -v -s`
   - Verify locator resolves correctly
   - Check Postgres locator_health table

5. **Query Locator Health**
   ```bash
   psql playwright_mcp
   SELECT element_name, strategy, candidate_index, resolved 
   FROM locator_health 
   ORDER BY created_at DESC LIMIT 10;
   ```

### Locator Discovery Steps

**Step 1: Open Playwright Inspector**
```bash
# In test, use Inspector to inspect element
# Right-click element → Inspect → Copy selector
```

**Step 2: Test Selector**
```python
# Verify selector works
page.get_by_test_id("element-id")  # Works? Use this!
page.get_by_role("button", name="Label")  # Works? Use this!
page.locator("#css-id")  # Last resort
```

**Step 3: Add as Candidate**
```python
ELEMENT_CANDIDATES = [
    LocatorCandidate("data-testid", lambda p: p.get_by_test_id("new-value")),
    LocatorCandidate("role+label", lambda p: p.get_by_role("button", name="Text")),
    LocatorCandidate("css", lambda p: p.locator(".old-selector")),
]
```

**Step 4: Run Test**
```bash
pytest tests/test_scenarios.py -v -s
# Check which candidate resolved
```

### Locator Priority Reference
| Priority | Strategy | Stability | Example |
|----------|----------|-----------|---------|
| 1st | data-testid | ⭐⭐⭐⭐⭐ | `p.get_by_test_id("email")` |
| 2nd | role + label | ⭐⭐⭐⭐ | `p.get_by_role("button", name="Add")` |
| 3rd | CSS selector | ⭐⭐ | `p.locator("#btn-add")` |

## Key References
- `SKILL_LOCATOR_STRATEGY.md` - Locator priority order
- `pages/base_page.py` - Self-healing resolve() method
- `SKILL_KOHLS_PAGE_STRUCTURE.md` - Known Kohls locators
- Postgres `locator_health` table - Healing statistics

## Common Scenarios

**Element Moved (CSS broke)**
```python
# Old CSS might not work anymore
LocatorCandidate("css", lambda p: p.locator(".product-card .price")),

# But data-testid still works
LocatorCandidate("data-testid", lambda p: p.get_by_test_id("price")),
```

**Label Changed (role+label broke)**
```python
# Button label changed from "Add" to "Add to Cart"
LocatorCandidate("role+label", lambda p: p.get_by_role("button", name="Add to Cart")),
```

**ID Changed (testid broke)**
```python
# ID changed but CSS still works
LocatorCandidate("css", lambda p: p.locator("button.add-to-cart")),
```

## Do NOT
- ❌ Replace all candidates (keep working ones!)
- ❌ Remove old candidates (they're fallbacks)
- ❌ Use brittle selectors (index-based, nth-child)
- ❌ Hardcode wait times (use explicit waits)
- ❌ Skip testing the new locator
