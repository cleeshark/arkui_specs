#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENHARMONY_ROOT_DEFAULT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"
OPENHARMONY_ROOT="${OPENHARMONY_ROOT:-${OPENHARMONY_ROOT_DEFAULT}}"
LOCAL_PROPERTIES="${SCRIPT_DIR}/local.properties"

ACTION="build"

usage() {
  cat <<'EOF'
Usage:
  ./build.sh [clean|build|all] [--openharmony-root <path>]

Options:
  --openharmony-root  OpenHarmony source root used to resolve prebuilts/tool
  -h, --help          Show this help message
EOF
}

while (($# > 0)); do
  case "$1" in
    clean|build|all)
      ACTION="$1"
      shift
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

if [[ -f "${LOCAL_PROPERTIES}" ]]; then
  SDK_DIR_FROM_FILE="$(sed -n 's/^sdk\.dir=//p' "${LOCAL_PROPERTIES}" | tail -n 1)"
  NODE_DIR_FROM_FILE="$(sed -n 's/^nodejs\.dir=//p' "${LOCAL_PROPERTIES}" | tail -n 1)"
else
  SDK_DIR_FROM_FILE=""
  NODE_DIR_FROM_FILE=""
fi

OHOS_BASE_SDK_HOME="${OHOS_BASE_SDK_HOME:-${SDK_DIR_FROM_FILE}}"
NODE_HOME="${NODE_HOME:-${NODE_DIR_FROM_FILE}}"
HVIGOR_WRAPPER="${OPENHARMONY_ROOT}/prebuilts/tool/command-line-tools/6.x/hvigor/bin/hvigorw.js"

if [[ -z "${OHOS_BASE_SDK_HOME}" || ! -d "${OHOS_BASE_SDK_HOME}" ]]; then
  echo "Error: OHOS_BASE_SDK_HOME is not set or path does not exist: ${OHOS_BASE_SDK_HOME:-<empty>}"
  echo "Please configure sdk.dir in local.properties or export OHOS_BASE_SDK_HOME."
  exit 1
fi

if [[ -z "${NODE_HOME}" || ! -x "${NODE_HOME}/bin/node" ]]; then
  echo "Error: NODE_HOME is not set correctly: ${NODE_HOME:-<empty>}"
  echo "Please configure nodejs.dir in local.properties or export NODE_HOME."
  exit 1
fi

if [[ ! -f "${HVIGOR_WRAPPER}" ]]; then
  echo "Error: hvigor wrapper not found: ${HVIGOR_WRAPPER}"
  exit 1
fi

export OHOS_BASE_SDK_HOME
export NODE_HOME
export PATH="${NODE_HOME}/bin:${PATH}"

cd "${SCRIPT_DIR}"

echo "Project      : ${SCRIPT_DIR}"
echo "OpenHarmony : ${OPENHARMONY_ROOT}"
echo "SDK          : ${OHOS_BASE_SDK_HOME}"
echo "Node         : ${NODE_HOME}"
echo "Hvigor       : ${HVIGOR_WRAPPER}"
echo "Action       : ${ACTION}"
echo

run_hvigor() {
  node "${HVIGOR_WRAPPER}" "$@"
}

if [[ "${ACTION}" == "clean" || "${ACTION}" == "all" ]]; then
  run_hvigor \
    clean \
    --mode module \
    -p product=default \
    -p module=entry@default \
    -p buildMode=debug \
    --analyze=normal \
    --parallel \
    --incremental \
    --no-daemon
fi

if [[ "${ACTION}" == "build" || "${ACTION}" == "all" ]]; then
  run_hvigor \
    assembleHap \
    --mode module \
    -p product=default \
    -p module=entry@default \
    -p buildMode=debug \
    --analyze=normal \
    --parallel \
    --incremental \
    --no-daemon
  echo
  echo "Output: ${SCRIPT_DIR}/entry/build/default/outputs/default/entry-default-unsigned.hap"
fi
