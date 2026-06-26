#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_TEST_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"
HAP_PATH="${SPEC_TEST_ROOT}/entry/build/default/outputs/default/entry-default-unsigned.hap"
TARGET_URL="spec_cases/04-common-capability/03-common-attributes/01-layout-attributes/Feat-01-size-properties/suites/suite-01-width-height-basic/cases/case_001_width_height_basic"
OPENHARMONY_ROOT=""

usage() {
  cat <<'EOF'
Usage:
  ./run_inspector_only.sh [target_url] [--openharmony-root <path>]

Options:
  --openharmony-root  OpenHarmony source root used by build and Previewer lookup
  -h, --help          Show this help message
EOF
}

log_progress() {
  printf '\033[1;33m%s\033[0m\n' "$*"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --openharmony-root)
      OPENHARMONY_ROOT="${2:?missing value for --openharmony-root}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
    *)
      TARGET_URL="$1"
      shift
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

PREVIEWER_BIN="$(resolve_previewer_bin "${SPEC_TEST_ROOT}" || true)"
PREVIEWER_NAME="$(resolve_previewer_name)"
COMMAND_PIPE="/tmp/${PREVIEWER_NAME}_commandPipe"

RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${SPEC_TEST_ROOT}/.report/${RUN_ID}/inspector_only"
LOG_PATH="${OUT_DIR}/previewer.log"
OUT_PATH="${OUT_DIR}/inspector_runtime_response.txt"

mkdir -p "${OUT_DIR}"

if [[ -z "${PREVIEWER_BIN}" ]]; then
  echo "Failed to resolve Previewer bin."
  echo "Set PREVIEWER_BIN, or provide OHOS_BASE_SDK_HOME/DEVECO_SDK_HOME with previewer/common/bin."
  exit 1
fi

log_progress "[1/3] Build SpecTest"
cd "${SPEC_TEST_ROOT}"
if [[ -n "${OPENHARMONY_ROOT}" ]]; then
  ./build.sh build --openharmony-root "${OPENHARMONY_ROOT}"
else
  ./build.sh build
fi

log_progress "[2/3] Start previewer and collect inspector"
cd "${PREVIEWER_BIN}"
rm -f "${COMMAND_PIPE}" "${OUT_PATH}"

XVFB_PIDS_BEFORE="$(mktemp)"
snapshot_xvfb_pids > "${XVFB_PIDS_BEFORE}"

(timeout 25s xvfb-run -a ./Previewer \
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
  > "${LOG_PATH}" 2>&1) &
PID=$!

cleanup() {
  ./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command exit --version 1.0.1 >/dev/null 2>&1 || true
  kill "${PID}" >/dev/null 2>&1 || true
  wait "${PID}" >/dev/null 2>&1 || true
  cleanup_new_xvfb_processes "${XVFB_PIDS_BEFORE}"
  rm -f "${XVFB_PIDS_BEFORE}"
}
trap cleanup EXIT

for _ in $(seq 1 80); do
  if rg -q "LoadPage Success" "${LOG_PATH}"; then
    break
  fi
  sleep 0.25
done

if ! rg -q "LoadPage Success" "${LOG_PATH}"; then
  echo "Preview load failed."
  rg -n "Bind failed|command pipe connect failed|LoadPage Success|Cannot find module|Failed to open display" "${LOG_PATH}" | sed -n '1,120p' || true
  exit 2
fi

./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command inspector --version 1.0.1 > "${OUT_PATH}"

if ! rg -q "Response:" "${OUT_PATH}"; then
  echo "Inspector response invalid."
  sed -n '1,80p' "${OUT_PATH}" || true
  exit 3
fi

log_progress "[3/3] Done"
echo "previewer_bin=${PREVIEWER_BIN}"
echo "previewer_name=${PREVIEWER_NAME}"
echo "preview_log=${LOG_PATH}"
echo "inspector_output=${OUT_PATH}"
echo "target_url=${TARGET_URL}"
