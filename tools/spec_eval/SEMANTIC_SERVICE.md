# Local Semantic Evaluation Service

A local, loopback-bound service that turns Function-level semantic evaluation
into a queued, resumable, observable rolling-report workflow. It drives the
existing `spec_eval` evidence pipeline and staged-run skill scripts, calls a
Codex CLI executor per work item, deterministically scores and aggregates the
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
  -d '{"run_count":1,"source_revision":"HEAD"}'
```

`source_revision` is resolved in `ace_engine`; it may be a full commit, branch,
tag, or `HEAD`. At submission time the service also resolves the current
`specs`, `sdk-js`, and `sdk_c` commits. The four exact SHAs become the immutable
revision set for the Job.

An active request with the same FuncID, revision set, evaluator/protocol
version, and run count is deduplicated. A new request allocates the next
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

The executor uses a strict v2 response envelope. All envelope properties are
required; `observation_json` carries a serialized executor-owned payload,
`notes` is an array, and `error` is nullable. Identity, revision, input paths,
expected claim/check lists and derived completion fields remain owned by the
initialized staged template. The service freezes that template before invoking Codex, merges only
the allowlisted mutable payload fields, derives completion fields, validates a
candidate with the real staged-run validator, and atomically publishes it only
after validation succeeds. Observation and aggregation use separate payload
contracts. A nested `identity`/`input` document or any other extra field is
rejected without overwriting the initialized template.

Evaluator 0.1.12 also generates `output-contract.json` from the same Rubric and Skill validator
constants. The service embeds the relevant section into every Codex prompt, including evidence
types, `EV-`/`sha256:` formats, legal Criterion IDs and conditional defect ownership. If an
observation candidate fails only the allowlisted mechanical contract checks, the service makes one
repair call restricted to the candidate, initialized template and machine contract. It does not
reopen evidence or silently normalize output. Both executor calls retain separate result files and
are included in Job duration/Token statistics.

Evaluator 0.1.13 additionally generates `aggregation-context.json` after all observations pass.
The file records each observation document hash and the authoritative observation, Claim, and
atomic-unit mapping for every Criterion. Aggregation `claim_ids` are citations only and cannot
narrow that scope. Mapped `CONFLICT`/`MISSING` units forbid Supported/Not Applicable, and a sole
mapped Not Verifiable gap requires Not Verifiable. If an aggregation candidate fails only these
mapping-consistency checks, the service performs at most one bounded reconciliation call. Its four
inputs are the candidate, initialized aggregation template, `output-contract.json`, and
`aggregation-context.json`; source, SDK, Spec, Design, Registry, evidence shards, and published
observations are outside scope. Structural or evidence validation failures are not reconciled.
The second invocation has its own `aggregation.executor-result.reconcile-1.json`, events, duration,
and Token accounting. A failed reconciliation leaves the initialized aggregation template
unchanged.

Evaluator 0.1.14 additionally publishes the validator-owned observation evidence cardinality table
through `output-contract.json`. Every observation except Not Verifiable requires at least one
evidence object, including Not Applicable observations that must prove why the checked unit does not
apply. When this is the only validation failure, the service may perform one evidence completion
call using the candidate and original scoped frozen inputs. The repaired payload is rejected unless
all outcomes, facts, mappings, ownership fields, non-target evidence, and ordering are unchanged.

Evaluator 0.1.15 additionally publishes the final Finding and Criterion-result definitions from
`semantic-result.schema.json` in `output-contract.json`. Every aggregation candidate is assembled
in memory and final-validated before replacing the initialized template. The service performs at
most one deterministic, model-free contract repair: an unambiguous `problem` alias becomes
`message`, an existing evidence-backed N/A reason becomes `applicability_reason`, and Finding IDs
plus ownership references are rewritten from stable FuncID/defect/Criterion/Claim identity.
Different simultaneous `message` and `problem` values fail without publishing the candidate. The
repair is observable through `aggregation_contract_repair_started`, `_completed`, and `_failed`
events and remains separate from 0.1.13 mapping reconciliation.

Evaluator 0.1.16 moves canonical Finding IDs and ownership secondary Criteria fully behind the
service boundary. Executor Finding IDs are unique provisional correlation keys; the service does
not trust or require model-generated hashes. Before the first aggregation validation it always
runs one deterministic normalization for any frozen contract containing `final_contract`, including
in-flight 0.1.15 runs. The pass canonicalizes Finding and ownership IDs, derives secondary Criteria
from actual owned Findings, and performs the existing unambiguous alias/N/A normalization. Mixed
repairable and non-repairable errors can no longer suppress the deterministic pass. Remaining
structural errors still fail, while mapping-only errors continue into bounded reconciliation.

The service also audits every structured-output schema object node for
`additionalProperties: false` and complete `required` coverage before starting
Codex. A locally invalid output schema therefore fails at service startup
without consuming a model request.

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

Successful 0.1.13 archives also retain `aggregation-context-<run_id>.json` beside each semantic
result so a historical Criterion conclusion can be audited against the exact published mapping.

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
  the job; retry re-runs semantic + aggregation. For 0.1.13 mapping failures, inspect
  `aggregation-context.json` and the `aggregation_reconciliation_*` events. Only mapping-consistency
  errors receive one reconciliation attempt. For 0.1.15+ final-contract normalization, inspect the
  `aggregation_contract_repair_*` events; ambiguous aliases and unrepaired structural errors fail
  before assemble.
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
