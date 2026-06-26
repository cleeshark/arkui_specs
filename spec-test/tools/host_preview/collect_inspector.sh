#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_TEST_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <hap_path> <output_dir> [target_url] [archive_screenshot] [operations_file] [openharmony_root]"
  exit 1
fi

HAP_PATH="$1"
OUTPUT_DIR="$2"
TARGET_URL="${3:-pages/Index}"
ARCHIVE_SCREENSHOT="${4:-false}"
OPERATIONS_FILE="${5:-}"
OPENHARMONY_ROOT="${6:-${OPENHARMONY_ROOT:-}}"
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
fi
PREVIEWER_BIN="$(resolve_previewer_bin "${SPEC_TEST_ROOT}" "${OPENHARMONY_ROOT}" || true)"
PREVIEWER_NAME="$(resolve_previewer_name)"
COMMAND_PIPE="/tmp/${PREVIEWER_NAME}_commandPipe"
RUN_LOG="${OUTPUT_DIR}/previewer.log"
INSPECTOR_RAW="${OUTPUT_DIR}/inspector_runtime_response.txt"
OPERATIONS_RAW="${OUTPUT_DIR}/operations_runtime_response.txt"
SCREENSHOT_RAW="${OUTPUT_DIR}/screenshot_runtime_response.txt"
SCREENSHOT_FILE="${OUTPUT_DIR}/screenshot.png"

if [[ -z "${PREVIEWER_BIN}" ]]; then
  echo "Failed to resolve Previewer bin."
  echo "Set PREVIEWER_BIN, or provide OHOS_BASE_SDK_HOME/DEVECO_SDK_HOME with previewer/common/bin."
  exit 1
fi

if [[ "${ARCHIVE_SCREENSHOT}" != "true" && "${ARCHIVE_SCREENSHOT}" != "false" ]]; then
  echo "Invalid archive_screenshot value: ${ARCHIVE_SCREENSHOT} (expected true or false)"
  exit 1
fi

printf '\033[1;36m%s\033[0m %s\n' "Previewer bin:" "${PREVIEWER_BIN}"

mkdir -p "${OUTPUT_DIR}"
rm -f "${OPERATIONS_RAW}" "${SCREENSHOT_RAW}" "${SCREENSHOT_FILE}"

cd "${PREVIEWER_BIN}"

# Cleanup stale previewer processes that may hold previewer_commandPipe.
while read -r pid _; do
  kill "${pid}" >/dev/null 2>&1 || true
done < <(pgrep -af "./Previewer -s ${PREVIEWER_NAME}" || true)
sleep 1
rm -f "${COMMAND_PIPE}"

XVFB_PIDS_BEFORE="$(mktemp)"
snapshot_xvfb_pids > "${XVFB_PIDS_BEFORE}"

# Expand run.sh inline so we can choose page url explicitly.
xvfb-run -a ./Previewer \
  -s "${PREVIEWER_NAME}" \
  -gui \
  -hap "${HAP_PATH}" \
  -refresh region \
  -cpm false \
  -device phone \
  -shape rect \
  -sd 160 \
  -or 432 936 \
  -cr 432 936 \
  -n entry \
  -av ACE_2_0 \
  -url "${TARGET_URL}" \
  -pages main_pages \
  -pm Stage \
  -l en_US \
  -cm light \
  -o portrait \
  > "${RUN_LOG}" 2>&1 &
PREVIEWER_PID=$!

cleanup() {
  ./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command exit --version 1.0.1 >/dev/null 2>&1 || true
  kill "${PREVIEWER_PID}" >/dev/null 2>&1 || true
  wait "${PREVIEWER_PID}" >/dev/null 2>&1 || true
  cleanup_new_xvfb_processes "${XVFB_PIDS_BEFORE}"
  rm -f "${XVFB_PIDS_BEFORE}"
}
trap cleanup EXIT

run_previewer_action() {
  local command="$1"
  local output_file="$2"
  shift 2
  local -a extra_args=("$@")

  local attempt=0
  local max_attempts=40
  while [[ "${attempt}" -lt "${max_attempts}" ]]; do
    attempt=$((attempt + 1))
    if timeout 8s ./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command "${command}" --version 1.0.1 "${extra_args[@]}" > "${output_file}" 2>&1; then
      return 0
    fi
    if rg -qi "connect socket failed|Unable to connect to server socket|command pipe connect failed" "${output_file}" 2>/dev/null; then
      sleep 0.1
      continue
    fi
    return 1
  done
  return 1
}

for _ in $(seq 1 60); do
  if rg -q "LoadPage Success" "${RUN_LOG}"; then
    break
  fi
  sleep 0.5
done

if ! rg -q "LoadPage Success" "${RUN_LOG}"; then
  echo "Preview load failed. Log: ${RUN_LOG}"
  tail -n 120 "${RUN_LOG}" || true
  exit 1
fi

if [[ -n "${OPERATIONS_FILE}" ]]; then
  if [[ ! -f "${OPERATIONS_FILE}" ]]; then
    echo "Operations file not found: ${OPERATIONS_FILE}"
    exit 1
  fi
  # Warm up PreviewerCLI connection before operation injection.
  if ! run_previewer_action "inspectorDefault" "${OUTPUT_DIR}/inspector_warmup_response.txt"; then
    echo "Failed to warm up PreviewerCLI action connection. Log: ${OUTPUT_DIR}/inspector_warmup_response.txt"
    tail -n 120 "${OUTPUT_DIR}/inspector_warmup_response.txt" || true
    exit 1
  fi
  if ! python3 "${SCRIPT_DIR}/execute_operations.py" \
    --previewer-bin "${PREVIEWER_BIN}" \
    --previewer-name "${PREVIEWER_NAME}" \
    --operations-file "${OPERATIONS_FILE}" \
    --output-log "${OPERATIONS_RAW}"; then
    echo "Failed to execute operations. Log: ${OPERATIONS_RAW}"
    tail -n 120 "${OPERATIONS_RAW}" || true
    exit 1
  fi
fi

if ! run_previewer_action "inspector" "${INSPECTOR_RAW}"; then
  echo "Failed to get inspector response. Log: ${RUN_LOG}"
  tail -n 120 "${INSPECTOR_RAW}" || true
  tail -n 120 "${RUN_LOG}" || true
  exit 1
fi

if ! rg -q "Response:" "${INSPECTOR_RAW}"; then
  echo "Invalid inspector response. Raw file: ${INSPECTOR_RAW}"
  cat "${INSPECTOR_RAW}" || true
  exit 1
fi

if [[ "${ARCHIVE_SCREENSHOT}" == "true" ]]; then
  # Best-effort screenshot collection for report archive.
  before_snapshot="$(mktemp)"
  after_snapshot="$(mktemp)"
  find "${PREVIEWER_BIN}" -maxdepth 1 -type f \
    \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) \
    -printf '%T@ %p\n' | sort -n > "${before_snapshot}" || true

  if run_previewer_action "ScreenShot" "${SCREENSHOT_RAW}"; then
    find "${PREVIEWER_BIN}" -maxdepth 1 -type f \
      \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) \
      -printf '%T@ %p\n' | sort -n > "${after_snapshot}" || true
    new_file="$(comm -13 "${before_snapshot}" "${after_snapshot}" | tail -n 1 | cut -d' ' -f2-)"
    if [[ -n "${new_file}" && -f "${new_file}" ]]; then
      cp -f "${new_file}" "${SCREENSHOT_FILE}"
    fi
  else
    echo "Warn: ScreenShot command failed, continue without screenshot." >> "${RUN_LOG}"
  fi

  rm -f "${before_snapshot}" "${after_snapshot}"
fi

echo "inspector_response=${INSPECTOR_RAW}"
echo "preview_log=${RUN_LOG}"
echo "previewer_bin=${PREVIEWER_BIN}"
echo "previewer_name=${PREVIEWER_NAME}"
echo "target_url=${TARGET_URL}"
echo "archive_screenshot=${ARCHIVE_SCREENSHOT}"
if [[ -f "${OPERATIONS_RAW}" ]]; then
  echo "operations_log=${OPERATIONS_RAW}"
fi
if [[ -f "${SCREENSHOT_FILE}" ]]; then
  echo "screenshot_file=${SCREENSHOT_FILE}"
fi
