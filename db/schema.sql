-- Playwright + MCP Kohls automation schema

CREATE TABLE IF NOT EXISTS test_runs (
    id SERIAL PRIMARY KEY,
    test_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    notes TEXT
);

-- No password column, ever: only non-secret metadata about login attempts.
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id),
    email TEXT NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('success', 'fail')),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS api_calls (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id),
    step_name TEXT NOT NULL,
    api_name TEXT,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    request_payload JSONB,
    response_status INTEGER,
    response_payload JSONB,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id),
    order_id TEXT,
    subtotal NUMERIC(10, 2),
    status TEXT NOT NULL DEFAULT 'pending',
    placed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

-- Self-healing locator telemetry: which candidate selector actually matched.
CREATE TABLE IF NOT EXISTS locator_health (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id),
    element_name TEXT NOT NULL,
    candidate_index INTEGER NOT NULL,
    candidate_strategy TEXT NOT NULL,
    matched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every business-rule check performed during a run (price/subtotal/total
-- thresholds, etc.), so the pass/fail criteria and the actual observed
-- value are auditable after the fact -- not just asserted in Python and
-- discarded. See config.py/ScenarioData for where the thresholds come
-- from, and db_logger.log_assertion() for how rows land here.
CREATE TABLE IF NOT EXISTS test_assertions (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES test_runs(id),
    step_name TEXT NOT NULL,
    assertion_name TEXT NOT NULL,
    expected_condition TEXT NOT NULL,
    actual_value NUMERIC(10, 2),
    passed BOOLEAN NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
