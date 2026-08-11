#!/usr/bin/env bash
# ci_service.sh — start the GitCode webhook receiver + the CI Worker (watch mode)
# together so that an incoming PR hook auto-triggers a report-only evaluation.
#
# The receiver only authenticates / dedupes / appends a receipt and returns 202
# fast (handoff NEXT-010). The worker is a separate resident process that polls
# the receipt log and runs ci_runner + archives + posts the PR comment.
#
# Usage:
#   ./specs/tools/spec_eval/ci_service.sh
#
# Overrides (env):
#   GITCODE_WEBHOOK_TOKEN  webhook secret (else read from ~/.gitcode_webhook_token)
#   WEBHOOK_HOST / WEBHOOK_PORT   receiver bind (default 127.0.0.1 / 8765)
#   SPEC_EVAL_REPO          whitelisted GitCode owner/repo (default arkui_architecture/arkui-specs)
#   CI_POLL_INTERVAL        worker poll seconds (default 10)
#   CI_TEST_ON_PASS          set to 1 to mark the GitCode PR test passed when no new errors are found
#   CI_FORCE_TEST            set to 1 with CI_TEST_ON_PASS to pass --force to oh-gc pr test
#   CI_AUTO_CHECKOUT         set to 0 to skip fetch+checkout to the tested SHA (default 1; see issue #8)
#   CI_SPECS_CHECK          set to 0 to skip repo-level specs integrity checks (default: enabled)
#   CI_SYNC_ON_MERGE        set to 0 to skip force-syncing CI repos to tip on action=merge (default: enabled)
#   CI_FORCE_SYNC           set to 1 to reset --hard even repos with uncommitted local changes (default: off)
#   EXTRA_WORKER_ARGS       extra flags forwarded to ci_worker (e.g. "--dry-run")
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"   # ace_engine/ (spec_eval -> tools -> specs -> ace_engine)
cd "$REPO_ROOT"

if [ -z "${GITCODE_WEBHOOK_TOKEN:-}" ] && [ -f "$HOME/.gitcode_webhook_token" ]; then
    export GITCODE_WEBHOOK_TOKEN="$(tr -d '\n' < "$HOME/.gitcode_webhook_token")"
fi

REPO="${SPEC_EVAL_REPO:-arkui_architecture/arkui-specs}"
HOST="${WEBHOOK_HOST:-127.0.0.1}"
PORT="${WEBHOOK_PORT:-8765}"
POLL="${CI_POLL_INTERVAL:-10}"
RECEIPTS="specs/.evaluator/webhook/receipts.ndjson"
LEDGER="specs/.evaluator/ci/processed.ndjson"

mkdir -p specs/.evaluator/webhook specs/.evaluator/ci

echo "[ci_service] starting webhook receiver on ${HOST}:${PORT}"
python3 specs/tools/spec_eval/gitcode_webhook.py \
    --host "$HOST" --port "$PORT" --events-file "$RECEIPTS" &
RECEIVER_PID=$!

cleanup() {
    echo "[ci_service] stopping (receiver pid ${RECEIVER_PID})"
    kill "$RECEIVER_PID" 2>/dev/null || true
    wait "$RECEIVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Optional: report the automated GitCode PR test as passed when the run finds no new errors.
# Enabled by default; set CI_TEST_ON_PASS=0 to opt out.
TEST_ARGS=""
[ "${CI_TEST_ON_PASS:-1}" = "1" ] && TEST_ARGS="$TEST_ARGS --test-on-pass"
[ "${CI_FORCE_TEST:-0}" = "1" ] && TEST_ARGS="$TEST_ARGS --force-test"
# Fetch + detached-HEAD checkout to the tested SHA so evaluation runs on the PR
# head (default on; fixes issue #8 — otherwise every PR is skipped_mismatch).
# Set CI_AUTO_CHECKOUT=0 to opt out (evaluation is skipped when worktree != tested).
[ "${CI_AUTO_CHECKOUT:-1}" = "0" ] && TEST_ARGS="$TEST_ARGS --no-auto-checkout"
# Repo-level specs integrity checks (generate_index --check, validate_specs) run by default;
# set CI_SPECS_CHECK=0 to opt out (e.g. while triaging a repo-wide baseline breakage).
[ "${CI_SPECS_CHECK:-1}" = "0" ] && TEST_ARGS="$TEST_ARGS --no-specs-check"
# On action=merge receipts, force every CI repo (ace_engine/specs/sdk-js/sdk_c) to its
# default-branch tip so the next evaluation starts from a clean baseline. Enabled by default;
# set CI_SYNC_ON_MERGE=0 to opt out. Set CI_FORCE_SYNC=1 to reset --hard even repos that have
# uncommitted local changes (default: dirty repos are skipped to avoid discarding work).
[ "${CI_SYNC_ON_MERGE:-1}" = "0" ] && TEST_ARGS="$TEST_ARGS --no-sync-on-merge"
[ "${CI_FORCE_SYNC:-0}" = "1" ] && TEST_ARGS="$TEST_ARGS --force-sync"

echo "[ci_service] starting CI worker in watch mode (poll ${POLL}s, repo ${REPO})${TEST_ARGS:+ (test-on-pass)}"
# The worker runs in the foreground; exiting it (Ctrl-C) tears down the receiver.
exec python3 specs/tools/spec_eval/ci_worker.py \
    --repo "$REPO" --allow-project "$REPO" \
    --receipts "$RECEIPTS" --processed-ledger "$LEDGER" \
    --watch --poll-interval "$POLL" \
    $TEST_ARGS \
    ${EXTRA_WORKER_ARGS:-}
