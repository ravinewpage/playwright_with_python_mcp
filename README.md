# playwright_with_python_mcp

Python + Playwright web automation for Kohls.com, built on the Page Object
Model, backed by three MCP servers configured in [`.mcp.json`](.mcp.json):

- **GitHub MCP** (`@modelcontextprotocol/server-github`) — repo access as
  `ravinewpage`, no `gh`/`git` CLI usage.
- **Postgres/SQL MCP** (`mcp-postgres`) — logs every test run, login
  attempt, network API call, order, and self-healing locator event. Note:
  the official `@modelcontextprotocol/server-postgres` is read-only by
  design (wraps queries in a read-only transaction), so this project uses
  `mcp-postgres` instead, which supports real inserts/updates.
- **Playwright MCP** (`@playwright/mcp`) — used during development to
  explore the live site and verify selectors before encoding them into
  page objects.

## Hard constraints (enforced in code, not just convention)

- **No password is ever typed by automation.** `pages/login_page.py`'s
  `wait_for_manual_password_entry()` pauses and waits for the human to type
  it in the live browser — for both the deliberately-failing login and the
  real one.
- **No card CVV/expiry is ever typed by automation.**
  `pages/checkout_page.py`'s `wait_for_manual_card_entry()` pauses the same
  way at checkout.
- **No password is ever stored.** `db/schema.sql`'s `login_attempts` table
  has no password column — only email, result, and timestamp.
- These rules apply identically to the Phase 2 API-replay script
  ([`scripts/api_replay_run.py`](scripts/api_replay_run.py)): it reuses an
  already-authenticated session instead of replaying a login call, and
  still pauses for manual CVV/expiry before the place-order request.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/playwright install chromium
cp .env.example .env   # fill in GITHUB_TOKEN
```

Postgres (already provisioned locally in this environment):

```bash
brew install postgresql@16
brew services start postgresql@16
createdb playwright_mcp
psql playwright_mcp -f db/schema.sql
```

## Structure

- `pages/` — Page Object Model classes, one per Kohls.com page, each with
  self-healing locator resolution (ordered candidate lists, see
  `pages/base_page.py`) and retry logic for transient UI actions. The
  deliberately-failing login step is explicitly excluded from self-healing
  and retry — it's asserted directly so a real UI regression can't be
  masked as a pass.
- `tests/test_kohls_flow.py` — orchestrates the 15-step scenario: two
  logins (fail, then success) → search → product details/price check →
  size/cart → checkout → place order → confirmation → track order →
  cancel order. Every step's network calls are captured and logged to
  Postgres.
- `db_logger.py` — MCP-only Postgres client (talks to the `postgres` MCP
  server over stdio; no raw `psycopg2`).
- `scripts/api_replay_run.py` — Phase 2: replays the flow via direct HTTP
  calls using the shapes captured in `api_calls`, no browser.

## Running

```bash
./.venv/bin/pytest tests/test_kohls_flow.py -v -s
```

`-s` is required so the manual password/CVV pause prompts are visible.
