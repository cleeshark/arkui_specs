# Local Semantic Evaluation Service

A local, loopback-bound service that turns Function-level semantic evaluation
into a queued, resumable, observable workflow. It drives the existing
`spec_eval` evidence pipeline and the staged-run skill scripts, calls a Codex
CLI executor per work item, then deterministically scores/aggregates and writes
an isolated automated archive.

> Scope: this service automates evaluation. It does **not** modify frozen
> Specs/Design/Registry, confirmed Reviews, the site archives, or the CI delta
> gate. Automated results live in a separate `automated` namespace.

## Quick start

From the ace_engine root:

```bash
# 1. serve (HTTP + scheduler), default port 8790, loopback only
python3 specs/tools/spec_eval/service_cli.py serve --port 8790 --max-workers 2

# 2. open the UI
xdg-open http://127.0.0.1:8790/   # create a job for a FuncID, watch it progress

# 3. one-shot governance
python3 specs/tools/spec_eval/service_cli.py metrics  --write metrics.json
python3 specs/tools/spec_eval/service_cli.py cleanup  --retention-days 14
python3 specs/tools/spec_eval/service_cli.py backup
```

Codex CLI must be installed and authenticated (`codex --version`). Without it,
jobs pause in `awaiting_executor` (semantic stage) or fail (aggregation stage).

## HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| POST   | `/api/jobs` | create `{func_id, run_count?, source_revision?, job_id?}` |
| GET    | `/api/jobs[?status=]` | list jobs |
| GET    | `/api/jobs/{id}` | job detail |
| GET    | `/api/jobs/{id}/events?since_seq=` | monotonic event log |
| POST   | `/api/jobs/{id}/cancel` | cooperative cancel |
| POST   | `/api/jobs/{id}/retry` | failed/cancelled → queued |
| GET    | `/api/jobs/{id}/artifacts/{kind}` | artifact download (path-traversal guarded) |
| GET    | `/api/metrics` | operational metrics |

Static UI is served at `/` and `/static/*`. Bind `0.0.0.0` only with `--token`
(bearer auth then required for all API calls).

## Executor configuration (Phase-1 default)

```json
{
  "type": "codex-cli",
  "command": "codex",
  "model": null,
  "sandbox": "read-only",
  "timeout_seconds": 3600,
  "max_parallel": 2,
  "output_schema": "executor-result.schema.json"
}
```

`codex exec --cd <repo> --sandbox read-only --add-dir <run-dir> --ephemeral
--json --output-schema <schema> --output-last-message <result> -` (prompt via
stdin). `--dangerously-bypass-approvals-and-sandbox` is never used.

## Data directory (`--data-root`, default `specs/.evaluator/service-data/`)

```
db/service.sqlite3                 # only mutable state (jobs/attempts/events/artifacts/snapshots)
jobs/<job_id>/runs/<run_id>/       # disposable: evidence/, staged/, logs/
aggregate/                         # deterministic score/stability/report
archives/automated/<rev>/<func>/<job>/   # immutable automated archive + manifest
site-history-automated.jsonl       # append-only automated history log
locks/                             # recoverable resource-lock markers
logs/  backups/
```

Large files live on disk; the DB stores paths, SHA-256, sizes, and status.

## Lifecycle & recovery

Job states: `queued → preparing → evidence → semantic → aggregation → archive
→ site_history → completed` (plus `awaiting_executor`, `failed`, `cancelled`).
On restart, any worker-owned active state is reset to `queued` and re-picked-up
(`awaiting_executor` is left for the scheduler). Per-Feat checkpoints are
append-only and idempotent, so a resumed run skips already-validated work items.

## Governance (TASK-011-09)

- **metrics**: `GET /api/metrics` or `service_cli.py metrics --write <path>
  [--format csv|json]` — status counts, queue/run duration summary, executor
  errors, artifact/archive bytes, and Finding added/resolved/reclassified deltas
  (derived from the automated history log).
- **cleanup**: `service_cli.py cleanup --retention-days N` — deletes only
  disposable `jobs/<id>/runs/` dirs for terminal jobs older than N days.
  Archives are **never** deleted.
- **backup**: `service_cli.py backup` — WAL checkpoint + DB copy + restore
  verification into `backups/`.

## Troubleshooting

- **stuck in `awaiting_executor`**: `codex` not on PATH or not authenticated.
  Fix and the scheduler re-checks availability.
- **`failed` during aggregation**: the frozen state matrix has no
  `aggregation → awaiting_executor` edge, so an unavailable executor there fails
  the job; retry re-runs semantic + aggregation.
- **archive not reproducible**: re-run the job for the same FuncID + revision;
  deterministic score/report + content-hashed manifest make bytes match.
- **`spec_eval evidence exited 1` / `score exited 1`**: exit 1 from the
  spec_eval CLI means a *gate* is `fail` (static findings exist) — this is a
  normal outcome, outputs are still written, and the job continues. Only
  exit >= 2 (`SpecEvalError` / gate `error`) fails the stage.
