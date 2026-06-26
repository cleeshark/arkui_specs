#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_TEST_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"
SPEC_ROOT="${SPEC_TEST_ROOT}/entry/src/main/ets/spec_cases"
MAIN_PAGES_JSON="${SPEC_TEST_ROOT}/entry/src/main/resources/base/profile/main_pages.json"
HAP_PATH="${SPEC_TEST_ROOT}/entry/build/default/outputs/default/entry-default-unsigned.hap"

SUITE_ID=""
CASE_ID=""
ARCHIVE_SCREENSHOT="false"
OPENHARMONY_ROOT=""

usage() {
  cat <<'EOF'
Usage:
  ./run_feature.sh [--suite-id <suite_id>] [--case-id <case_id>] [--archive-screenshot] [--openharmony-root <path>]

Options:
  --suite-id          Run a specific suite id
  --case-id           Run a specific case id
  --archive-screenshot Archive screenshots into the report
  --openharmony-root  OpenHarmony source root used by build and Previewer lookup
  -h, --help          Show this help message
EOF
}

log_progress() {
  printf '\033[1;33m%s\033[0m\n' "$*"
}

log_summary_value() {
  local key="$1"
  local value="$2"
  local color="$3"
  printf '\033[%sm%s=%s\033[0m\n' "${color}" "${key}" "${value}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite-id)
      SUITE_ID="${2:-}"
      shift 2
      ;;
    --case-id)
      CASE_ID="${2:-}"
      shift 2
      ;;
    --archive-screenshot)
      if [[ $# -gt 1 && ( "${2}" == "true" || "${2}" == "false" ) ]]; then
        echo "--archive-screenshot does not take a value. Use it as a flag only."
        echo "Example: $0 --case-id case-001-width-height-basic --archive-screenshot"
        exit 1
      fi
      ARCHIVE_SCREENSHOT="true"
      shift 1
      ;;
    --openharmony-root)
      OPENHARMONY_ROOT="${2:?missing value for --openharmony-root}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -n "${OPENHARMONY_ROOT}" ]]; then
  if [[ ! -d "${OPENHARMONY_ROOT}" ]]; then
    echo "Error: OpenHarmony root does not exist: ${OPENHARMONY_ROOT}" >&2
    exit 1
  fi
  OPENHARMONY_ROOT="$(cd "${OPENHARMONY_ROOT}" && pwd)"
  if [[ "${OPENHARMONY_ROOT}" == "/" ]]; then
    echo "Error: OPENHARMONY_ROOT resolved to filesystem root (/)." >&2
    echo "Hint: try adding --openharmony-root <OpenHarmonyRoot>." >&2
    exit 1
  fi
  export OPENHARMONY_ROOT
fi

RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_ROOT="${SPEC_TEST_ROOT}/.report/${RUN_ID}/run_feature"
PLAN_JSON="${RUN_ROOT}/case_plan.json"
RUN_XVFB_PIDS_BEFORE="$(mktemp)"
snapshot_xvfb_pids > "${RUN_XVFB_PIDS_BEFORE}"

cleanup_run_xvfb() {
  cleanup_new_xvfb_processes "${RUN_XVFB_PIDS_BEFORE}"
  rm -f "${RUN_XVFB_PIDS_BEFORE}"
}
trap cleanup_run_xvfb EXIT

cd "${SPEC_TEST_ROOT}"

log_progress "[1/6] Build SpecTest HAP"
if [[ -n "${OPENHARMONY_ROOT}" ]]; then
  ./build.sh build --openharmony-root "${OPENHARMONY_ROOT}"
else
  ./build.sh build
fi

log_progress "[2/6] Resolve case plan from manifests + main_pages route table"
python3 "${SCRIPT_DIR}/resolve_case_plan.py" \
  --spec-root "${SPEC_ROOT}" \
  --main-pages-json "${MAIN_PAGES_JSON}" \
  --suite-id "${SUITE_ID}" \
  --case-id "${CASE_ID}" \
  --out "${PLAN_JSON}"

log_progress "[3/6] Execute selected cases by url"
python3 - <<'PY' "${PLAN_JSON}" > "${RUN_ROOT}/case_lines.txt"
import base64, json, sys
plan = json.load(open(sys.argv[1], encoding='utf-8'))
for c in plan["cases"]:
    ops = c.get("operationSequence", [])
    ops_b64 = base64.urlsafe_b64encode(
        json.dumps(ops, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    print(f'{c["suiteId"]}\t{c["caseId"]}\t{c["url"]}\t{c["expectedFile"]}\t{ops_b64}')
PY

TOTAL="$(wc -l < "${RUN_ROOT}/case_lines.txt" | tr -d ' ')"
IDX=0
FAIL=0

while IFS=$'\t' read -r suite_id case_id url expected_file ops_b64; do
  IDX=$((IDX + 1))
  CASE_OUT_DIR="${RUN_ROOT}/${suite_id}/${case_id}"
  OPERATIONS_FILE="${CASE_OUT_DIR}/operations.json"
  INSPECTOR_RAW="${CASE_OUT_DIR}/inspector_runtime_response.txt"
  SCREENSHOT_FILE="${CASE_OUT_DIR}/screenshot.png"
  REPORT_JSON="${CASE_OUT_DIR}/report.json"
  REPORT_MD="${CASE_OUT_DIR}/report.md"

  mkdir -p "${CASE_OUT_DIR}"
  python3 - <<'PY' "${ops_b64}" "${OPERATIONS_FILE}"
import base64, json, pathlib, sys

ops_b64 = sys.argv[1]
out_file = pathlib.Path(sys.argv[2])
decoded = base64.urlsafe_b64decode(ops_b64.encode("ascii")).decode("utf-8") if ops_b64 else "[]"
ops = json.loads(decoded)
if not isinstance(ops, list):
    raise RuntimeError("operationSequence decoded value is not a list")
out_file.write_text(json.dumps(ops, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  log_progress "[3/6] [${IDX}/${TOTAL}] Collect inspector for ${suite_id}/${case_id}"
  "${SCRIPT_DIR}/collect_inspector.sh" "${HAP_PATH}" "${CASE_OUT_DIR}" "${url}" "${ARCHIVE_SCREENSHOT}" "${OPERATIONS_FILE}"

  log_progress "[4/6] [${IDX}/${TOTAL}] Assert ${suite_id}/${case_id}"
  if ! python3 "${SCRIPT_DIR}/assert_cases.py" \
    --inspector-response "${INSPECTOR_RAW}" \
    --screenshot-file "${SCREENSHOT_FILE}" \
    --expected "${expected_file}" \
    --suite-id "${suite_id}" \
    --case-id "${case_id}" \
    --report-json "${REPORT_JSON}" \
    --report-md "${REPORT_MD}"; then
    FAIL=$((FAIL + 1))
  fi
done < "${RUN_ROOT}/case_lines.txt"

SUMMARY_JSON="${RUN_ROOT}/summary_report.json"
SUMMARY_MD="${RUN_ROOT}/summary_report.md"

log_progress "[5/6] Merge summary report"
python3 "${SCRIPT_DIR}/merge_report.py" \
  --run-root "${RUN_ROOT}" \
  --plan-json "${PLAN_JSON}" \
  --out-json "${SUMMARY_JSON}" \
  --out-md "${SUMMARY_MD}"

log_progress "[6/6] Done"
echo "run_root=${RUN_ROOT}"
echo "plan_json=${PLAN_JSON}"
echo "summary_json=${SUMMARY_JSON}"
echo "summary_md=${SUMMARY_MD}"
echo "archive_screenshot=${ARCHIVE_SCREENSHOT}"
log_summary_value "total_cases" "${TOTAL}" "1;36"
if [[ "${FAIL}" -gt 0 ]]; then
  log_summary_value "failed_cases" "${FAIL}" "1;31"
else
  log_summary_value "failed_cases" "${FAIL}" "1;32"
fi

if [[ "${FAIL}" -gt 0 ]]; then
  exit 1
fi
