#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENHARMONY_ROOT_DEFAULT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"
OPENHARMONY_ROOT="${OPENHARMONY_ROOT:-${OPENHARMONY_ROOT_DEFAULT}}"

DST_DIR_DEFAULT="${SCRIPT_DIR}/sdk/linux"

SRC_DIR=""
DST_DIR="${DST_DIR_DEFAULT}"
FORCE=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  ./release_sdk_from_packages.sh [--openharmony-root <path>] [--src <packages_dir>] [--dst <sdk_linux_dir>] [--force] [--dry-run]

Description:
  Release SDK zip artifacts from out/sdk/packages/ohos-sdk/linux to a standalone SDK directory,
  with the same layout as prebuilts/ohos-sdk/linux:
    <sdk_linux_dir>/<api_version>/{ets,js,native,previewer,toolchains}

Options:
  --openharmony-root OpenHarmony source root used for the default --src path
  --src      SDK package directory (default: <OpenHarmonyRoot>/out/sdk/packages/ohos-sdk/linux)
  --dst      Target SDK linux directory (default: <SpecTest>/sdk/linux)
  --force    Replace existing <sdk_linux_dir>/<api_version> if it already exists
  --dry-run  Print actions without extracting
  -h, --help Show this help message
EOF
}

while (($# > 0)); do
  case "$1" in
    --openharmony-root)
      OPENHARMONY_ROOT="${2:?missing value for --openharmony-root}"
      shift 2
      ;;
    --src)
      SRC_DIR="${2:?missing value for --src}"
      shift 2
      ;;
    --dst)
      DST_DIR="${2:?missing value for --dst}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
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

if [[ -z "${SRC_DIR}" ]]; then
  SRC_DIR="${OPENHARMONY_ROOT}/out/sdk/packages/ohos-sdk/linux"
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "Error: unzip command not found." >&2
  exit 1
fi

if [[ ! -d "${SRC_DIR}" ]]; then
  echo "Error: source directory does not exist: ${SRC_DIR}" >&2
  exit 1
fi

declare -a COMPONENTS=(ets js native previewer toolchains)
declare -A ZIP_BY_COMPONENT=()
FULL_VERSION=""
MAJOR_VERSION=""

for component in "${COMPONENTS[@]}"; do
  mapfile -t matches < <(find "${SRC_DIR}" -maxdepth 1 -type f -name "${component}-linux-x64-*.zip" | sort -V)
  if [[ "${#matches[@]}" -eq 0 ]]; then
    echo "Error: package not found for component '${component}' in ${SRC_DIR}" >&2
    exit 1
  fi
  selected="${matches[${#matches[@]}-1]}"
  ZIP_BY_COMPONENT["${component}"]="${selected}"

  base_name="$(basename "${selected}")"
  if [[ ! "${base_name}" =~ ^${component}-linux-x64-(.+)\.zip$ ]]; then
    echo "Error: cannot parse version from package name: ${base_name}" >&2
    exit 1
  fi
  component_version="${BASH_REMATCH[1]}"
  component_major="${component_version%%.*}"

  if [[ -z "${FULL_VERSION}" ]]; then
    FULL_VERSION="${component_version}"
    MAJOR_VERSION="${component_major}"
  else
    if [[ "${component_version}" != "${FULL_VERSION}" ]]; then
      echo "Error: inconsistent package versions found." >&2
      echo "  expected: ${FULL_VERSION}" >&2
      echo "  got     : ${component_version} (${base_name})" >&2
      exit 1
    fi
  fi
done

TARGET_VERSION_DIR="${DST_DIR}/${MAJOR_VERSION}"

echo "Source dir      : ${SRC_DIR}"
echo "OpenHarmony root: ${OPENHARMONY_ROOT}"
echo "Target linux dir: ${DST_DIR}"
echo "SDK version     : ${FULL_VERSION}"
echo "API dir         : ${TARGET_VERSION_DIR}"
echo
echo "Packages:"
for component in "${COMPONENTS[@]}"; do
  echo "  - ${component}: $(basename "${ZIP_BY_COMPONENT[${component}]}")"
done
echo

if [[ -d "${TARGET_VERSION_DIR}" ]]; then
  if [[ "${FORCE}" -eq 1 ]]; then
    echo "Removing existing directory: ${TARGET_VERSION_DIR}"
    if [[ "${DRY_RUN}" -eq 0 ]]; then
      rm -rf "${TARGET_VERSION_DIR}"
    fi
  else
    echo "Error: target version directory already exists: ${TARGET_VERSION_DIR}" >&2
    echo "Use --force to replace it." >&2
    exit 1
  fi
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "Dry-run mode: no files were extracted."
  exit 0
fi

mkdir -p "${TARGET_VERSION_DIR}"

for component in "${COMPONENTS[@]}"; do
  package="${ZIP_BY_COMPONENT[${component}]}"
  echo "Extracting ${component} ..."
  unzip -q "${package}" -d "${TARGET_VERSION_DIR}"
done

echo
echo "Done."
echo "Standalone SDK root: ${DST_DIR}"
echo "You can set SpecTest sdk.dir to:"
echo "  ${DST_DIR}"
