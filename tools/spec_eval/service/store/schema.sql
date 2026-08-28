-- SQLite schema for the semantic evaluation service Job Store (schema_version 8).
-- Loaded idempotently by sqlite_store._run_migrations. PRAGMAs are applied in
-- code (they are connection-scoped / must run outside a transaction). The
-- load-bearing constraints are:
--   events           PRIMARY KEY (job_id, seq)           -> monotonic seq
--   attempts         UNIQUE (job_id, run_id, feat_id, stage)
--                                                       -> checkpoint idempotency
--                     (run_id/feat_id are NOT NULL DEFAULT '' so NULL never
--                      bypasses the UNIQUE check; the repo maps None <-> '')
--   artifacts        UNIQUE (job_id, kind)              -> "latest validated"
--   dependency_snapshots PRIMARY KEY (job_id, repo_name)-> task-level freeze

CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('schema_version', '8');

-- schema v6 (protocol 0.2.0 S3, design R6): six-state lifecycle + stage.
CREATE TABLE IF NOT EXISTS jobs (
    job_id            TEXT PRIMARY KEY,
    func_id           TEXT NOT NULL,
    source_revision   TEXT NOT NULL,
    run_count         INTEGER NOT NULL CHECK (run_count >= 1),
    selected_run_ids  TEXT NOT NULL DEFAULT '[]',
    status            TEXT NOT NULL CHECK (status IN (
        'queued', 'running', 'waiting', 'completed', 'failed', 'cancelled'
    )),
    stage             TEXT NOT NULL CHECK (stage IN (
        'preparing', 'evidence', 'observation', 'aggregation', 'report',
        'archive', 'projection'
    )),
    progress_json     TEXT NOT NULL,
    executor_config   TEXT NOT NULL,
    protocol_version  TEXT NOT NULL,
    evaluator_version TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status        ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_func_revision ON jobs (func_id, source_revision);

CREATE TABLE IF NOT EXISTS job_statistics (
    job_id                       TEXT PRIMARY KEY REFERENCES jobs (job_id) ON DELETE CASCADE,
    started_at                   TEXT,
    finished_at                  TEXT,
    run_started_at               TEXT,
    active_elapsed_ms            INTEGER NOT NULL DEFAULT 0 CHECK (active_elapsed_ms >= 0),
    executor_invocations         INTEGER NOT NULL DEFAULT 0 CHECK (executor_invocations >= 0),
    usage_reported_invocations   INTEGER NOT NULL DEFAULT 0 CHECK (usage_reported_invocations >= 0),
    telemetry_reported_invocations INTEGER NOT NULL DEFAULT 0 CHECK (telemetry_reported_invocations >= 0),
    executor_elapsed_ms          INTEGER NOT NULL DEFAULT 0 CHECK (executor_elapsed_ms >= 0),
    executor_tool_calls          INTEGER NOT NULL DEFAULT 0 CHECK (executor_tool_calls >= 0),
    executor_command_calls       INTEGER NOT NULL DEFAULT 0 CHECK (executor_command_calls >= 0),
    input_paths_accessed         INTEGER NOT NULL DEFAULT 0 CHECK (input_paths_accessed >= 0),
    evidence_paths_accessed      INTEGER NOT NULL DEFAULT 0 CHECK (evidence_paths_accessed >= 0),
    input_tokens                 INTEGER NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
    cached_input_tokens          INTEGER NOT NULL DEFAULT 0 CHECK (cached_input_tokens >= 0),
    cache_write_input_tokens     INTEGER NOT NULL DEFAULT 0 CHECK (cache_write_input_tokens >= 0),
    output_tokens                INTEGER NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
    reasoning_output_tokens      INTEGER NOT NULL DEFAULT 0 CHECK (reasoning_output_tokens >= 0),
    total_tokens                 INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    updated_at                   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id   TEXT PRIMARY KEY,
    job_id       TEXT NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    run_id       TEXT NOT NULL DEFAULT '',
    feat_id      TEXT NOT NULL DEFAULT '',
    stage        TEXT NOT NULL CHECK (stage IN (
        'preparing', 'evidence', 'semantic', 'aggregation', 'archive', 'site_history'
    )),
    status       TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    exit_code    INTEGER,
    artifact_dir TEXT,
    UNIQUE (job_id, run_id, feat_id, stage)
);
CREATE INDEX IF NOT EXISTS idx_attempts_job   ON attempts (job_id);
CREATE INDEX IF NOT EXISTS idx_attempts_stage ON attempts (job_id, stage, status);

CREATE TABLE IF NOT EXISTS events (
    job_id       TEXT NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    seq          INTEGER NOT NULL,
    event_type   TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (job_id, seq)
);

-- Add a statistics projection for jobs created by pre-v3 service versions.
-- Historical timing is recoverable from lifecycle events; historical Codex
-- token counts were never persisted and therefore remain explicit zeroes.
INSERT OR IGNORE INTO job_statistics (
    job_id, started_at, finished_at, updated_at
)
SELECT
    jobs.job_id,
    (SELECT MIN(events.created_at) FROM events
        WHERE events.job_id = jobs.job_id AND events.event_type = 'enter_preparing'),
    CASE WHEN jobs.status IN ('completed', 'failed', 'cancelled') THEN
        (SELECT MAX(events.created_at) FROM events WHERE events.job_id = jobs.job_id)
    ELSE NULL END,
    jobs.updated_at
FROM jobs;

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    job_id      TEXT NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    kind        TEXT NOT NULL,
    path        TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    size        INTEGER NOT NULL CHECK (size >= 0),
    created_at  TEXT NOT NULL,
    UNIQUE (job_id, kind)
);

CREATE TABLE IF NOT EXISTS dependency_snapshots (
    job_id    TEXT NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    repo_name TEXT NOT NULL,
    branch    TEXT NOT NULL,
    sha       TEXT NOT NULL,
    status    TEXT NOT NULL CHECK (status IN ('frozen', 'stale')),
    created_at TEXT NOT NULL,
    PRIMARY KEY (job_id, repo_name)
);

CREATE TABLE IF NOT EXISTS evaluation_reports (
    report_id             TEXT PRIMARY KEY,
    job_id                TEXT NOT NULL UNIQUE REFERENCES jobs (job_id) ON DELETE RESTRICT,
    func_id               TEXT NOT NULL,
    source_revision       TEXT NOT NULL,
    revision_set_json     TEXT NOT NULL,
    input_fingerprint     TEXT NOT NULL,
    evidence_fingerprint  TEXT NOT NULL,
    evaluator_version     TEXT NOT NULL,
    protocol_version      TEXT NOT NULL,
    rubric_version        TEXT NOT NULL,
    selected_run_id       TEXT NOT NULL,
    run_count             INTEGER NOT NULL CHECK (run_count >= 1),
    target_generation     INTEGER NOT NULL CHECK (target_generation >= 0),
    completed_at          TEXT NOT NULL,
    archive_path          TEXT NOT NULL,
    manifest_sha256       TEXT NOT NULL,
    summary_json          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evaluation_reports_func_completed
    ON evaluation_reports (func_id, completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluation_reports_func_generation
    ON evaluation_reports (func_id, target_generation);

CREATE TABLE IF NOT EXISTS function_report_heads (
    func_id                    TEXT PRIMARY KEY,
    current_report_id          TEXT REFERENCES evaluation_reports (report_id) ON DELETE RESTRICT,
    desired_generation         INTEGER NOT NULL DEFAULT 0 CHECK (desired_generation >= 0),
    desired_revision           TEXT,
    desired_input_fingerprint  TEXT,
    freshness                  TEXT NOT NULL DEFAULT 'MISSING' CHECK (freshness IN (
        'FRESH', 'EXPIRING', 'EXPIRED_TIME', 'STALE_INPUT', 'MISSING'
    )),
    stale_reasons_json         TEXT NOT NULL DEFAULT '[]',
    warn_at                    TEXT,
    expires_at                 TEXT,
    refresh_status             TEXT NOT NULL DEFAULT 'IDLE' CHECK (refresh_status IN (
        'IDLE', 'REFRESHING', 'REFRESH_FAILED'
    )),
    active_job_id              TEXT REFERENCES jobs (job_id) ON DELETE SET NULL,
    last_refresh_error         TEXT,
    updated_at                 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_function_report_heads_freshness
    ON function_report_heads (freshness, refresh_status);

CREATE TABLE IF NOT EXISTS refresh_targets (
    job_id                   TEXT PRIMARY KEY REFERENCES jobs (job_id) ON DELETE CASCADE,
    func_id                  TEXT NOT NULL,
    generation               INTEGER NOT NULL CHECK (generation >= 1),
    desired_revision         TEXT NOT NULL,
    revision_set_json        TEXT NOT NULL,
    provisional_fingerprint  TEXT NOT NULL,
    input_fingerprint        TEXT,
    evidence_fingerprint     TEXT,
    dedupe_key               TEXT NOT NULL,
    status                   TEXT NOT NULL CHECK (status IN ('ACTIVE', 'COMPLETED', 'FAILED')),
    created_at               TEXT NOT NULL,
    updated_at               TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_refresh_targets_active_dedupe
    ON refresh_targets (dedupe_key) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_refresh_targets_func_generation
    ON refresh_targets (func_id, generation DESC);

CREATE TABLE IF NOT EXISTS freshness_policies (
    scope_type    TEXT NOT NULL CHECK (scope_type IN ('global', 'func')),
    scope_key     TEXT NOT NULL,
    max_age_days  INTEGER NOT NULL CHECK (max_age_days > 0),
    warning_days  INTEGER NOT NULL CHECK (warning_days >= 0 AND warning_days < max_age_days),
    version       INTEGER NOT NULL CHECK (version >= 1),
    updated_at    TEXT NOT NULL,
    PRIMARY KEY (scope_type, scope_key)
);

CREATE TABLE IF NOT EXISTS report_deltas (
    report_id          TEXT PRIMARY KEY REFERENCES evaluation_reports (report_id) ON DELETE CASCADE,
    previous_report_id TEXT REFERENCES evaluation_reports (report_id) ON DELETE SET NULL,
    summary_json       TEXT NOT NULL,
    details_path       TEXT
);

-- schema v6 (protocol 0.2.0 S3, design R6): asynchronous projection outbox.
-- One row per completed job; report_id is the idempotency key — a projection
-- never executes twice for one report and failures never touch the job.
CREATE TABLE IF NOT EXISTS projection_requests (
    job_id         TEXT PRIMARY KEY REFERENCES jobs ON DELETE CASCADE,
    report_id      TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    attempts       INTEGER NOT NULL DEFAULT 0,
    last_error     TEXT,
    requested_at   TEXT NOT NULL,
    finished_at    TEXT,
    archive_dir    TEXT NOT NULL DEFAULT '',
    aggregate_dir  TEXT NOT NULL DEFAULT '',
    selected_run_id TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_projection_requests_status
  ON projection_requests (status);

-- schema v5 (protocol 0.2.0, design R6): per-executor-call invocations
CREATE TABLE IF NOT EXISTS executor_calls (
  call_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id       TEXT NOT NULL REFERENCES jobs ON DELETE CASCADE,
  run_id       TEXT NOT NULL DEFAULT '',
  work_item_id TEXT NOT NULL,
  attempt_type TEXT NOT NULL CHECK (attempt_type IN ('observe', 'correct')),
  executor     TEXT NOT NULL,
  status       TEXT NOT NULL,
  started_at   TEXT NOT NULL,
  duration_ms  INTEGER NOT NULL DEFAULT 0,
  usage_json   TEXT NOT NULL DEFAULT '{}',
  telemetry_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_executor_calls_job ON executor_calls (job_id);
CREATE INDEX IF NOT EXISTS idx_executor_calls_work_item
  ON executor_calls (job_id, run_id, work_item_id);

-- Finding Ledger: per-FuncID lifecycle tracking for convergence (0.2.1 S3).
CREATE TABLE IF NOT EXISTS finding_ledger (
  finding_id             TEXT PRIMARY KEY,
  func_id                TEXT NOT NULL,
  criterion_id           TEXT NOT NULL,
  severity               TEXT NOT NULL DEFAULT 'Major',
  message                TEXT NOT NULL DEFAULT '',
  status                 TEXT NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active','resolved','refuted','superseded','out_of_scope')),
  first_seen_run_id      TEXT NOT NULL,
  first_seen_at          TEXT NOT NULL,
  last_confirmed_run_id  TEXT,
  last_confirmed_at      TEXT,
  confirmation_count     INTEGER NOT NULL DEFAULT 1,
  executor_set           TEXT NOT NULL DEFAULT '[]',
  disposition_history    TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_ledger_func ON finding_ledger (func_id);
CREATE INDEX IF NOT EXISTS idx_ledger_status ON finding_ledger (func_id, status);
