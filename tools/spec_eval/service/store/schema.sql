-- SQLite schema for the semantic evaluation service Job Store (schema_version 1).
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
INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('schema_version', '1');

CREATE TABLE IF NOT EXISTS jobs (
    job_id            TEXT PRIMARY KEY,
    func_id           TEXT NOT NULL,
    source_revision   TEXT NOT NULL,
    run_count         INTEGER NOT NULL CHECK (run_count >= 1),
    selected_run_ids  TEXT NOT NULL DEFAULT '[]',
    status            TEXT NOT NULL CHECK (status IN (
        'queued', 'preparing', 'evidence', 'semantic', 'awaiting_executor',
        'aggregation', 'archive', 'site_history', 'completed', 'failed', 'cancelled'
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
