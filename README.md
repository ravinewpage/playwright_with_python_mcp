# playwright_with_python_mcp

A Python + Playwright web-automation practice project built entirely through
**MCP servers** (GitHub, Postgres/SQL, Playwright) instead of raw CLI
tooling. The reference scenario automates an end-to-end Kohls.com shopping
flow — login, search, add to cart, checkout, place order, track it, cancel
it — using the **Page Object Model**, with **self-healing locators** and
**flaky-test handling** built into the base page class, and every network
API call and test outcome logged to Postgres.

If you're picking up this repo to practice test automation, read
["What to do with this repo"](#what-to-do-with-this-repo) first.

---

## 1. The plan / architecture

### 1.1 Three MCP servers, no raw CLI

Everything that touches GitHub, Postgres, or the browser goes through an
MCP server declared in [`.mcp.json`](.mcp.json) — never `gh`, `git push`,
`psql`, or a raw `psycopg2`/browser-automation call outside that framing.

| Concern | MCP server | Why this one |
|---|---|---|
| GitHub (clone/read/push) | `@modelcontextprotocol/server-github` | Standard GitHub MCP server; used via its `get_file_contents`/`push_files`/etc. tools, authenticated with a PAT. Note: npm flags this package as no-longer-supported upstream — it still works, but if you're extending this repo, check whether GitHub's newer hosted/remote MCP server is a better fit for you. |
| Postgres (test data) | `mcp-postgres` | The **official** `@modelcontextprotocol/server-postgres` wraps every query in a read-only transaction and rejects `INSERT`/`UPDATE` — it cannot log test results. `mcp-postgres` exposes real `insert_data`/`query_data`/`execute_raw_query` tools with write support, which this project needs to persist run/login/API-call/order data. |
| Browser automation | `@playwright/mcp` | Used for live, interactive browser control — most usefully during page-object development (finding real selectors on the live site) and for the human-in-the-loop pause points described below. |

`db_logger.py` is a small, real **MCP client** (using the `mcp` Python SDK
over stdio) — it opens a session against the `mcp-postgres` server and
calls its tools. This is what "MCP-only" means concretely: even the
automated pytest run doesn't open a direct database connection itself.

### 1.2 Page Object Model

Each Kohls.com page/component the flow touches has its own class in
[`pages/`](pages/), exposing only high-level actions (`fill_email`,
`add_to_cart`, `get_subtotal`, ...) — tests never touch a raw CSS selector.
This is what makes the suite maintainable: when Kohls changes its markup,
you fix one page object, not every test that happens to visit that page.

```
pages/
  base_page.py             shared self-healing/retry machinery (see below)
  login_page.py             email fill, manual-password pause, success/fail checks
  search_page.py             search box, result selection
  product_page.py             full details, price check, size, add-to-cart
  cart_page.py                 view cart, subtotal check, proceed to checkout
  checkout_page.py              shipping/contact fields, manual-CVV pause, place order
  order_confirmation_page.py     "Thank you" + order ID capture
  track_order_page.py            order lookup
  my_purchases_page.py           cancel-order flow
```

### 1.3 Hard safety constraints (enforced in code, not just convention)

This automation **never** types a password or a card CVV/expiry — even
though both are supplied as literal test data for the scenario. That's a
deliberate boundary, not an oversight:

- `pages/login_page.py`'s `wait_for_manual_password_entry()` fills only the
  email, then pauses and prints a prompt asking a human to type the
  password in the live browser and submit — for **both** the
  deliberately-failing login and the real one.
- `pages/checkout_page.py`'s `wait_for_manual_card_entry()` fills every
  checkout field except CVV/expiry, then pauses the same way.
- `db/schema.sql`'s `login_attempts` table has **no password column** —
  only email, result (`success`/`fail`), and timestamp are ever persisted.
- [`scripts/api_replay_run.py`](scripts/api_replay_run.py) (the pure-API
  "Phase 2" replay, see below) follows the same rule: it reuses an
  already-authenticated session instead of replaying a login call, and
  still pauses for manual CVV/expiry immediately before the place-order
  request — a captured API shape is never a license to replay secrets.

If you fork this for a site where you control the test account, you can
loosen this — but treat it as a deliberate decision, not a default to
routinely bypass, especially before you're sure the target site isn't
production-real (see "shoes 9.5 shipped to nobody" note in §3).

### 1.4 Self-healing locators + flaky-test handling

This is the part most worth studying if you're new to resilient
automation. It all lives in [`pages/base_page.py`](pages/base_page.py).

**Self-healing locators.** Instead of one brittle selector per element,
each element is defined as an **ordered list of candidates**, most stable
first:

```python
EMAIL_CANDIDATES = [
    LocatorCandidate("data-testid", lambda p: p.get_by_test_id("email-input")),
    LocatorCandidate("role+label",  lambda p: p.get_by_role("textbox", name="Email")),
    LocatorCandidate("css#id",      lambda p: p.locator("#email, input[name='email']")),
]
```

`BasePage.resolve(element_name, candidates)` tries each candidate with a
short timeout and uses the first one that actually matches something on
the page. Which candidate worked gets logged to the `locator_health` table
via the SQL MCP server (element name, candidate index, strategy, run,
timestamp) — so if Kohls tweaks their markup and test 1's `data-testid`
candidate stops matching but the `role+label` fallback picks up the slack,
you *see that drift in the data* instead of the test just quietly staying
green (or silently breaking) forever. Query `locator_health` over time and
a rising "healed via fallback" rate for one element is your early warning
that the primary selector needs updating.

**Flaky-test handling.** Two extra pieces of default behavior, applied
automatically to every step:

- `BasePage.retry(action, attempts=2, delay_ms=500)` wraps transient UI
  actions (a click racing a loading spinner, a popup that hasn't finished
  animating in) in a short retry instead of failing on the first race.
- `BasePage.capture_failure_evidence(step_name)` takes a screenshot on
  failure so a real bug is easy to diagnose rather than just quietly
  masked.
- Explicit Playwright waits (`wait_for_load_state`, `expect`-style
  visibility waits) are used throughout instead of hard `sleep()` calls,
  which is the single biggest source of flakiness in most Playwright
  suites people write by hand.

**The one deliberate exception.** Step 1 of the scenario is a login that
is *supposed* to fail (wrong password, on purpose, to test the error
path). `LoginPage.assert_login_failed()` is called directly, with **no**
self-healing candidate expansion and **no** retry-until-success — because
self-healing logic that quietly "fixes" a negative test into a false pass
is worse than no self-healing at all. If you add more negative-path tests
to this suite, follow the same pattern: assert directly, skip the
resilience machinery, comment why.

### 1.5 Data logged to Postgres

`db/schema.sql` defines five tables, all written through `mcp-postgres`:

| Table | What it captures |
|---|---|
| `test_runs` | One row per pytest run: name, status, start/finish, notes |
| `login_attempts` | Email + result (`success`/`fail`) per login — no password |
| `api_calls` | Every network request/response seen during the run: step name, method, URL, JSON request/response payloads, status code |
| `orders` | The order placed during the run: subtotal, order ID, status, placed/cancelled timestamps |
| `locator_health` | Which candidate locator resolved each element, per run — the self-healing telemetry described above |

### 1.6 Phase 2: pure-API replay (no browser)

[`scripts/api_replay_run.py`](scripts/api_replay_run.py) demonstrates the
next maturity step for a suite like this: once you've captured real API
shapes from a browser run (via `api_calls`), you can replay most of the
flow as direct HTTP calls — much faster, no browser needed — reusing the
authenticated session from the browser run rather than logging in again.
It still pauses once, before the place-order call, for manual CVV/expiry,
for the same reason described in §1.3.

---

## 2. Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/playwright install chromium
cp .env.example .env   # fill in GITHUB_TOKEN and DATABASE_URL
```

Postgres:

```bash
brew install postgresql@16
brew services start postgresql@16
createdb playwright_mcp
psql playwright_mcp -f db/schema.sql
```

`.mcp.json` wires up the three MCP servers for any MCP-aware client (e.g.
Claude Code) working in this repo. `GITHUB_TOKEN` needs at minimum
**Contents: Read and write** on the target repo (fine-grained PAT) or the
`repo` scope (classic PAT) if you want the GitHub MCP server to push, not
just read.

## 3. Running the suite

```bash
./.venv/bin/pytest tests/test_kohls_flow.py -v -s
```

`-s` is required — it's what makes the manual password/CVV pause prompts
visible in your terminal. The run opens a real, visible Chromium window
(`headless=False` in `tests/conftest.py`) because you need to see it to
act on the pauses.

**Before you run this against a real site:** the reference scenario places
and then cancels a **real order** with **real payment details** on
whatever account you log into. Don't point this at a live account unless
you specifically intend that (e.g. you're deliberately testing the
cancel-order path) — for pure practice, prefer a site with a sandbox/test
mode, or adapt the scenario to stop before "place order" (the codebase
supports this trivially: just don't call `checkout.click_place_order()`).

## 4. What to do with this repo

If you're using this as a personal practice project:

1. **Read `pages/base_page.py` first.** It's the smallest file with the
   highest concept-density — self-healing resolution, retry, failure
   evidence. Everything else is an application of that pattern.
2. **Trace one full page object** (`pages/product_page.py` is a good
   size) against `tests/test_kohls_flow.py` to see how a POM class and its
   test caller divide responsibility: the page object knows *how* to do
   something on that page; the test knows *what* to do and in what order.
3. **Swap the target site.** The pattern (candidate-locator lists,
   pause-for-secrets hooks, MCP-logged API capture) generalizes to any
   site. Try retargeting `pages/` at a site you actually have a sandbox
   account for, and keep the same hard-constraint discipline from §1.3 —
   it's a good habit, not Kohls-specific.
4. **Break something on purpose to see self-healing catch it.** Change one
   candidate's selector in a page object to something that won't match,
   rerun, and check `locator_health` in Postgres — you should see the
   fallback candidate get used instead of a hard failure. Then try
   breaking *all* candidates for one element and confirm you get a clear
   `ElementNotFoundError`, not a silent pass.
5. **Try Phase 2.** Run the browser suite once to populate `api_calls`,
   then read `scripts/api_replay_run.py` and think through what it would
   take to make the replay actually complete (it currently stubs out
   session-header extraction — `get_session_headers()` — since that's
   genuinely site-specific).
6. **Query the data.** `psql playwright_mcp` (or the SQL MCP server) and
   look at `api_calls` after a run — this is a good way to build intuition
   for what a real e-commerce checkout flow actually calls over the wire.

## 5. Repo structure

```
.mcp.json               GitHub / Postgres / Playwright MCP server config
db/schema.sql            5-table Postgres schema (see §1.5)
db_logger.py              MCP-only Postgres client used by tests + scripts
pages/                     Page Object Model classes (see §1.2, §1.4)
tests/
  conftest.py               fixtures: db_logger, run_id, browser_page (with network capture)
  test_kohls_flow.py         orchestrates the 15-step scenario
scripts/
  api_replay_run.py          Phase 2: pure-API replay (see §1.6)
```
