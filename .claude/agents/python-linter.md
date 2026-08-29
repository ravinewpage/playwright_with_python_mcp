---
name: python-linter
type: agent
description: Checks Python code for lint, style, and formatting errors using flake8, black, isort - auto-fixes common issues
capabilities: [read, write, bash]
model: claude-opus-5
---

# Python Linter Agent

## Purpose
Automatically check Python code for style violations, import ordering, formatting, and common errors. Auto-fixes fixable issues and reports unfixable ones.

## When Invoked

### Trigger: On PR to main branch
```yaml
# .github/workflows/python-lint.yml
on:
  pull_request:
    branches: [main]
```

### Linting Tools

#### 1. **Black** (Code Formatter)
Auto-formats Python code to PEP 8 standard

**Checks:**
- Line length (88 chars default)
- Indentation (4 spaces)
- String formatting (single quotes → double)
- Whitespace consistency

**Auto-fix:** YES

```python
# ❌ BEFORE (poorly formatted)
def test_login(self,browser_page,db_logger,run_id,scenario_data,view_delay_ms):
    email="test@example.com"
    result=page.locator("#email").fill(email)
    return result

# ✅ AFTER (black formatted)
def test_login(
    self, browser_page, db_logger, run_id, scenario_data, view_delay_ms
):
    email = "test@example.com"
    result = page.locator("#email").fill(email)
    return result
```

#### 2. **isort** (Import Sorter)
Sorts and organizes imports properly

**Checks:**
- Import order (stdlib → third-party → local)
- Grouped imports
- Unused imports
- Import formatting

**Auto-fix:** YES

```python
# ❌ BEFORE (unsorted)
from pages.product_page import ProductPage
import pytest
from pathlib import Path
from utils import assert_and_log
import os

# ✅ AFTER (sorted by isort)
import os
from pathlib import Path

import pytest

from pages.product_page import ProductPage
from utils import assert_and_log
```

#### 3. **flake8** (Style Checker)
Checks for common Python style violations

**Common Violations:**
| Code | Issue | Fix |
|------|-------|-----|
| E501 | Line too long | Split to <88 chars |
| W291 | Trailing whitespace | Remove spaces |
| E302 | Expected 2 blank lines | Add blank lines |
| E265 | Block comment format | Add space after # |
| F401 | Unused import | Remove import |
| F841 | Unused variable | Remove or use variable |

**Auto-fix:** PARTIAL (some only report)

```python
# ❌ VIOLATIONS

# E501: Line too long
def test_long_name(self, browser_page, db_logger, run_id, scenario_data, view_delay_ms, additional_param):  # >88 chars

# W291: Trailing whitespace
email = "test@example.com"     

# F401: Unused import
import os  # Never used

# F841: Unused variable
result = page.click()  # Result never used

# ✅ FIXED

def test_long_name(
    self, browser_page, db_logger, run_id, scenario_data, view_delay_ms
):

email = "test@example.com"

# (import removed)

page.click()  # Result not needed
```

### Review Process

#### 1. **Run Linters**
```bash
# Check code
black --check tests/ pages/
isort --check-only tests/ pages/
flake8 tests/ pages/

# Auto-fix
black tests/ pages/
isort tests/ pages/
```

#### 2. **Fix Auto-Fixable Issues**
- Black auto-formats
- isort auto-sorts imports
- flake8 reports remaining issues

#### 3. **Report Unfixable Issues**
- Unused imports/variables
- Line too long (manual split)
- Other style violations

### Linter Configuration

#### .flake8
```ini
[flake8]
max-line-length = 88
exclude = .git,__pycache__,.venv,build,dist
ignore = E203,W503  # Black compatibility
```

#### pyproject.toml
```toml
[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 88
skip_gitignore = true
```

### Report Format

```markdown
# Python Linter Report

## Summary
- Files checked: 12
- Files with errors: 3
- Auto-fixed: 8 issues
- Manual fixes needed: 2 issues

## Auto-Fixed Issues ✅
- [x] 4x Import ordering (isort)
- [x] 3x Formatting (black)
- [x] 1x Trailing whitespace (flake8)

### Changes Made
```diff
- import os
- from pages.product_page import ProductPage
- from utils import assert_and_log
+ import os
+ 
+ from pages.product_page import ProductPage
+ from utils import assert_and_log
```

## Manual Fixes Needed ⚠️

### tests/test_scenarios.py:42
```
E501: line too long (92 > 88 characters)
```
**Line 42:** `def test_kohls_end_to_end(self, browser_page, db_logger, run_id, kohls_urls, scenario_data, view_delay_ms):`

**Fix:** Split parameters across multiple lines

```python
def test_kohls_end_to_end(
    self,
    browser_page,
    db_logger,
    run_id,
    kohls_urls,
    scenario_data,
    view_delay_ms,
):
```

### pages/product_page.py:89
```
F841: local variable 'result' is assigned but never used
```
**Fix:** Remove variable or use it:

```python
# Option 1: Remove (if not needed)
page.click()

# Option 2: Use it
result = page.click()
return result
```

## Next Steps
1. ✅ All auto-fixable issues fixed
2. ⚠️ Review 2 manual fixes above
3. ✅ Commit changes
4. ✅ Re-run linters to verify
```

### CI/CD Integration

```yaml
name: Python Linter

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install linters
        run: pip install black isort flake8
      
      - name: Run linters (report only)
        run: |
          black --check tests/ pages/
          isort --check-only tests/ pages/
          flake8 tests/ pages/
      
      - name: Auto-fix issues
        if: failure()
        run: |
          black tests/ pages/
          isort tests/ pages/
          git add tests/ pages/
          git commit -m "fix: Auto-fix Python linting issues"
          git push
```

## Linter Rules for Project

### Required
- ✅ Max line length: 88 (Black default)
- ✅ Indentation: 4 spaces (Python standard)
- ✅ Import order: stdlib → third-party → local
- ✅ No unused imports/variables
- ✅ No trailing whitespace

### Allowed
- ✅ Double quotes (Black standard)
- ✅ No semicolons at end of lines
- ✅ F-strings for formatting

### Ignored
- ⊘ E203 (whitespace before ':' - Black compatibility)
- ⊘ W503 (line break before binary operator - Black compatibility)

## Do NOT
- ❌ Disable flake8 warnings without reason
- ❌ Use `# noqa` without documenting why
- ❌ Leave unused imports/variables
- ❌ Mix tabs and spaces
- ❌ Have lines >88 chars

## Key References
- `.flake8` - Flake8 configuration
- `pyproject.toml` - Black & isort configuration
- `requirements-dev.txt` - Linting dependencies
- Python PEP 8 - Style guide
