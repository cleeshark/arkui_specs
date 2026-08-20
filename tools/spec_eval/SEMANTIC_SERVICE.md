# Local Semantic Evaluation Service

A local, loopback-bound service that turns Function-level semantic evaluation
into a queued, resumable, observable rolling-report workflow. It drives the
existing `spec_eval` evidence pipeline and staged-run skill scripts, calls the
selected Agent executor per work item, deterministically scores and aggregates the
result, then publishes an immutable automated archive.

The current scheduler is deliberately manual: an operator chooses a FuncID and
starts a refresh. Periodic scanning, automatic selection of stale Functions,
and daily token budgets are future work.

> Scope: the service evaluates existing content. It does **not** modify frozen
> Specs/Design/Registry, confirmed Reviews, the confirmed site archives, or the
> CI delta gate. Automated reports, history, and exports live under the service
> data root in a separate `automated` namespace.

## Quick start

From the ace_engine root:

```bash
# 1. verify the local executor
codex --version
codex login status

# 2. serve (HTTP + scheduler), default port 8790, loopback only
python3 specs/tools/spec_eval/service_cli.py serve --port 8790 --max-workers 2

# 3. open the UI
xdg-open http://127.0.0.1:8790/   # create a job for a FuncID, watch it progress

# 4. one-shot governance
python3 specs/tools/spec_eval/service_cli.py metrics  --write metrics.json
python3 specs/tools/spec_eval/service_cli.py cleanup  --retention-days 14
python3 specs/tools/spec_eval/service_cli.py backup
```

`codex --version` verifies installation; `codex login status` verifies the
configured login. The four local repositories used by the evidence envelope
must also exist:

- `foundation/arkui/ace_engine`
- `foundation/arkui/ace_engine/specs`
- `interface/sdk-js`
- `interface/sdk_c`

Without Codex, jobs pause in `awaiting_executor` during the semantic stage.

## Manual rolling refresh

Use the Function refresh endpoint for rolling reports:

```bash
curl -sX POST http://127.0.0.1:8790/api/functions/04-01-01/refresh \
  -H 'Content-Type: application/json' \
  -d '{"run_count":1,"source_revision":"HEAD","agent_id":"codex","agent_params":{"timeout_seconds":900}}'
```

`source_revision` is resolved in `ace_engine`; it may be a full commit, branch,
tag, or `HEAD`. At submission time the service also resolves the current
`specs`, `sdk-js`, and `sdk_c` commits. The four exact SHAs become the immutable
revision set for the Job.

An active request with the same FuncID, revision set, evaluator/protocol
version, run count, Agent and resolved Agent parameters is deduplicated. A new request allocates the next
Function generation. Generation-checked promotion prevents an older Job that
finishes late from replacing a newer desired report; it remains queryable in
history instead.

`POST /api/jobs` remains a lower-level compatibility endpoint. It does not
create a refresh target and therefore does not advance the rolling Function
report head.

## HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| GET    | `/api/functions[?freshness=&refresh_status=&func_id=]` | list Function report heads |
| GET    | `/api/agents` | list enabled Agents, parameter Schema and defaults |
| GET    | `/api/functions/{func_id}` | current report, freshness, refresh state |
| GET    | `/api/functions/{func_id}/history` | immutable report history and Finding delta |
| GET    | `/api/functions/{func_id}/freshness` | compact expiry/staleness projection |
| POST   | `/api/functions/{func_id}/refresh` | recommended manual rolling refresh |
| GET    | `/api/freshness-policies` | list global and per-Function policies |
| PUT    | `/api/freshness-policies/global` | update the global expiry policy |
| PUT    | `/api/freshness-policies/{func_id}` | update a Function-specific policy |
| POST   | `/api/site/export` | write deterministic automated site JSON |
| POST   | `/api/jobs` | low-level job creation without rolling promotion |
| GET    | `/api/jobs[?status=]` | list jobs |
| GET    | `/api/jobs/{id}` | job detail |
| GET    | `/api/jobs/{id}/events?since_seq=` | monotonic event log |
| POST   | `/api/jobs/{id}/cancel` | state-aware immediate/cooperative cancel |
| POST   | `/api/jobs/{id}/retry` | failed/cancelled → queued |
| GET    | `/api/jobs/{id}/artifacts/{kind}` | artifact download (path-traversal guarded) |
| GET    | `/api/metrics` | operational metrics |

Static UI is served at `/` and `/static/*`. It provides manual refresh,
Function freshness/history, concurrent Job progress, cancel, and retry views.
Function reports and Jobs are paginated independently after their respective
freshness/status filters are applied. Both tables show 10 rows by default and
offer 10, 50, or 100 rows per page; polling preserves the current page and
clamps it when refreshed data no longer has that page.
Active Jobs show an indeterminate activity animation and a duration counter that
updates every second. Completed/failed/cancelled Jobs retain their final wall
duration, cumulative executor time, executor invocation count, and Codex token
usage in the list and detail views. The statistics cards summarize all persisted
Jobs; a missing Codex usage event is shown as `not reported`, never estimated as
an exact count.

Cancellation responses distinguish lifecycle outcomes instead of reporting a
process signal as a completed state transition:

- HTTP 200 `cancelled`: `queued` or `awaiting_executor` was persisted directly.
- HTTP 202 `cancellation_requested`: an active worker received a cooperative flag.
- HTTP 409 `already_terminal` / `stage_not_cancellable`: the request cannot change the Job.
- HTTP 404 `not_found`: the Job does not exist.

Semantic and aggregation workers must persist `cancelled` before releasing their
workspace and cancellation registration. A worker that returns while its Job is
still active is failed with `worker_returned_nonterminal`, preventing live zombie
Jobs. Startup recovery remains a second line of defence and resets interrupted
worker-owned states to `queued`.

Bind `0.0.0.0` only with `--token`; every request must then carry
`Authorization: Bearer <token>`. The built-in UI has no token input field, so
remote browser access requires a reverse proxy or browser setup that injects
the header. Loopback UI access remains the recommended deployment.

## Revision-isolated workspaces

Each manual refresh writes a reservation manifest before creating four detached
Git worktrees under `workspaces/<job_id>/oh/`. The directory layout mirrors the
OpenHarmony checkout, so evidence, SDK lookup, evaluator scripts, Rubric, and
schemas all read from the same frozen revision envelope.

- Dirty files in the operator's original checkouts are not read or modified.
- A retry reuses the reservation manifest instead of resolving new commits.
- Dependency snapshots are append-only and cannot be overwritten by a later
  observation.
- Terminal Jobs release their detached worktrees but retain the manifest for
  audit and retry reconstruction.
- `--max-workers` controls global Job concurrency; the Function resource lock
  prevents conflicting work for the same FuncID.

## Agent selection and parameter defaults

The service startup option only selects the default Agent:

```bash
python3 specs/tools/spec_eval/service_cli.py serve --default-agent claude
```

`--executor` remains accepted as a compatibility alias. It does not configure
per-job parameters. Manual refresh accepts either the flat form
`{"agent_id":"claude","agent_params":{...}}` or the nested form
`{"agent":{"id":"claude","params":{...}}}`.

Every exposed optional parameter has an Agent-specific default and is
overridable for the current refresh. The service validates the override against
the Agent Schema, fills omitted parameters from the default, and stores the
complete resolved snapshot in the immutable Job. The precedence is:

```text
manual override > selected Agent default > global safety limit
```

The `GET /api/agents` response drives the UI form. Resetting a parameter removes
the override and returns it to the Agent default. Retry uses the original Job
snapshot, even if the service default or Agent profile changes later.

Sandbox mode, CLI command, output schema and service-wide worker concurrency
remain service-controlled and are intentionally not exposed as per-refresh
overrides.

Example request:

```json
{
  "agent_id": "claude",
  "agent_params": {
    "model": "claude-sonnet",
    "timeout_seconds": 900
  }
}
```

## Executor configuration (Codex default)

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

The executor uses the strict protocol 0.2.0 envelope v3. All envelope properties are required;
`payload` is a real nested object and historical `observation_json`/schema v1-v2 responses are
rejected. Identity, revision, input paths, expected claim/check lists and derived completion fields
remain owned by the initialized staged template. The service freezes that template before invoking
Codex, normalizes service-owned IDs/hashes, validates a candidate with the kernel and atomically
publishes it only after validation succeeds. Observation and aggregation use separate payload
contracts, and one generic typed correction turn is the only model retry.

The service generates `output-contract.json` from the kernel contracts and embeds the relevant
section into every Codex prompt. Typed validation failures use the single generic correction turn;
there are no version-specific repair calls or legacy fallbacks.

The service additionally generates `aggregation-context.json` after all observations pass. It
records the authoritative observation, Claim and atomic-unit mapping for every Criterion. Context
schema v2 also re-keys observation evidence into deterministic run-global IDs and exposes a
Criterion-scoped evidence catalog. Aggregation selects only those canonical IDs; the normalizer
copies the inherited evidence rows into the published Criterion and rejects unknown references.
Mapped adverse or unverifiable units constrain aggregate conclusions. Evidence cardinality, NV
inspection quality, Finding cardinality and canonical Finding identity are enforced by the 0.2.0 kernel.
Validation errors are typed and enter the one generic correction turn; there are no version-specific
repair modes, reconciliation calls, or historical fallback branches.

The aggregation contract also requires conclusion-level Finding cardinality. Every Criterion whose
conclusion is `PARTIALLY_SUPPORTED`, `CONTRADICTED`, or `MISSING` must contain at least one
evidence-backed Finding, and each Finding must cite evidence belonging to that Criterion. The
staged aggregation validator reports this rule before final assembly. If no valid defect key is
available, the candidate remains failed. A completed
`aggregation.executor-result.json` is reused on retry only when its work-item ID, status, error,
and observation payload pass structural checks; malformed or incomplete results are rejected and
the executor is invoked again.

The service also audits every structured-output schema object node for
`additionalProperties: false` and complete `required` coverage before starting
Codex. It also applies a conservative OpenAI Structured Outputs keyword
compatibility profile to both generated observation and aggregation schemas at
service startup, then rechecks the exact run-local schema before each executor
call. A locally invalid or unsupported output schema therefore fails without
consuming a model request.

## Data directory (`--data-root`, default `specs/.evaluator/service-data/`)

```
db/service.sqlite3                 # mutable query/control state
jobs/<job_id>/evidence/            # frozen static evidence for the Job
jobs/<job_id>/runs/<run_id>/       # disposable staged semantic runs and logs
jobs/<job_id>/aggregate/           # deterministic score/stability/report/delta
archives/automated/<rev>/<func>/<job>/   # immutable automated archive + manifest
archives/automated/site-history-automated.jsonl  # append-only automated history log
workspaces/<job_id>/workspace-manifest.json  # four-repo revision reservation
exports/                           # deterministic Function index/summary/history JSON
locks/  logs/  backups/
```

Large files live on disk. SQLite stores Jobs, attempts, events, artifact paths
and hashes, dependency snapshots, immutable report indexes, Function heads,
refresh generations, freshness policies, Finding-delta summaries, and the
`job_statistics` projection. The projection contains start/finish timestamps,
cumulative executor milliseconds, invocation/reporting counts, and integer-only
input/cached/cache-write/output/reasoning/total token counters. It does not store
prompts, response text, credentials, rate-limit data, or authentication state.

Codex usage is extracted from JSONL before log redaction. The adapter accepts the
observed `turn.completed.usage` and `token_count.info.total_token_usage` shapes;
unknown shapes safely leave usage unreported. JSONL written to events/logs remains
redacted, so secret-bearing fields are not exposed through the UI.

Archive publication is atomic and content-verified. Once
`archive-manifest.json` exists, retry reuses the published archive and never
replaces its bytes.

0.2.0 archives retain `aggregation-context-<run_id>.json` beside each semantic result so a
Criterion conclusion can be audited against the exact published mapping.

`service_cli.py purge --yes` removes the mutable runtime tree for a cold 0.2.0 restart;
`purge --legacy-artifacts --yes` removes only pre-0.2.0 staged/archive JSON artifacts. Both modes
are idempotent, and `--export` takes a verified database snapshot before the full purge.

## Lifecycle & recovery

Job states: `queued → preparing → evidence → semantic → aggregation → archive
→ site_history → completed` (plus `awaiting_executor`, `failed`, `cancelled`).
On restart, any worker-owned active state is reset to `queued` and re-picked-up
(`awaiting_executor` is left for the scheduler). Per-Feat checkpoints are
append-only and idempotent, so a resumed run skips already-validated work items.

## Freshness and history

The default policy is 30 valid days with a 7-day warning window. A FuncID policy
overrides the global policy. Policies require
`0 <= warning_days < max_age_days`.

```bash
curl -s http://127.0.0.1:8790/api/freshness-policies
curl -sX PUT http://127.0.0.1:8790/api/freshness-policies/global \
  -H 'Content-Type: application/json' \
  -d '{"max_age_days":30,"warning_days":7}'
curl -sX PUT http://127.0.0.1:8790/api/freshness-policies/04-01-01 \
  -H 'Content-Type: application/json' \
  -d '{"max_age_days":14,"warning_days":3}'
```

| Status | Meaning |
|--------|---------|
| `MISSING` | no current automated report |
| `FRESH` | current input target and outside the warning window |
| `EXPIRING` | valid but inside the warning window |
| `EXPIRED_TIME` | older than `max_age_days` |
| `STALE_INPUT` | a newer revision/input target is registered while the current report is older |

Each completed refresh creates an immutable report record. History retains its
revision set, evaluator/protocol/Rubric versions, fingerprints, selected run,
archive manifest hash, score/Gate summary, and Finding delta from the previous
current report.

## Static site export

The live UI reads SQLite directly through the service API. Static consumers can
request a deterministic export:

```bash
curl -sX POST http://127.0.0.1:8790/api/site/export
```

The service writes these files under `exports/`:

- `automated-function-index.json`
- `automated-site-summary.json`
- `automated-function-history/<func_id>.json`

Reports are intentionally rolling, not tied to one repository-wide baseline.
Different Functions may point to different source revisions. The summary
therefore records `mixed_revisions` and the exact `report_revisions` instead of
pretending the export represents one global revision.

## Governance (TASK-011-09)

- **metrics**: `GET /api/metrics` or `service_cli.py metrics --write <path>
  [--format csv|json]` — status counts, queue/run duration summary, executor
  duration/invocations, Token totals and reporting coverage, executor errors,
  artifact/archive bytes, and Finding added/resolved/reclassified deltas.
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
  the job; retry reuses an existing final-validated semantic result, otherwise it
  re-runs aggregation. Inspect the preserved candidate and typed-error checkpoint;
  stale or legacy artifacts are rejected and require a cold-start purge.
- **archive not reproducible**: re-run the job for the same FuncID + revision;
  deterministic score/report + content-hashed manifest make bytes match.
- **refresh returns `deduplicated: true`**: an equivalent active refresh already
  owns the target. Follow the returned Job instead of creating another one.
- **report is `STALE_INPUT`**: a newer manual refresh target was registered but
  has not yet become current. Check `active_job_id` or `last_refresh_error`.
- **report is `EXPIRED_TIME`**: trigger a manual refresh. This version does not
  schedule expired Functions automatically.
- **`spec_eval evidence exited 1` / `score exited 1`**: exit 1 from the
  spec_eval CLI means a *gate* is `fail` (static findings exist) — this is a
  normal outcome, outputs are still written, and the job continues. Only
  exit >= 2 (`SpecEvalError` / gate `error`) fails the stage.
