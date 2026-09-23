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

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 command not found." >&2
  exit 1
fi

if [[ ! -d "${SRC_DIR}" ]]; then
  echo "Error: source directory does not exist: ${SRC_DIR}" >&2
  exit 1
fi

declare -a COMPONENTS=(ets js native previewer toolchains)
declare -A ZIP_BY_COMPONENT=()
PACKAGE_VERSION=""
SDK_API_VERSION=""

read_component_metadata() {
  local package="$1"
  local component="$2"

  python3 - "${package}" "${component}" <<'PY'
import json
import re
import sys
import zipfile


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


package, component = sys.argv[1:]
metadata_path = f"{component}/oh-uni-package.json"

try:
    with zipfile.ZipFile(package) as archive:
        metadata = json.loads(archive.read(metadata_path))
except KeyError:
    fail(f"metadata file not found in {package}: {metadata_path}")
except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as error:
    fail(f"cannot read SDK metadata from {package}: {error}")

if not isinstance(metadata, dict):
    fail(f"SDK metadata is not an object in {package}: {metadata_path}")


def string_field(name, required=False):
    value = metadata.get(name)
    if value is None:
        value = ""
    if not isinstance(value, str):
        fail(f"metadata field '{name}' must be a string in {package}")
    if required and not value:
        fail(f"metadata field '{name}' is missing in {package}")
    return value


component_path = string_field("path", required=True)
api_version = string_field("apiVersion", required=True)
platform_version = string_field("platformVersion")
full_api_version = string_field("fullApiVersion")
sdk_version = string_field("version", required=True)
release_type = string_field("releaseType")

if component_path != component:
    fail(
        f"metadata path mismatch in {package}: "
        f"expected '{component}', got '{component_path}'"
    )

api_major_match = re.fullmatch(r"([1-9]\d{0,2})(?:\.\d{1,3}){0,2}", api_version)
if not api_major_match:
    fail(f"invalid apiVersion '{api_version}' in {package}")

api_major = int(api_major_match.group(1))
dot_api_pattern = re.compile(r"[1-9]\d?\.(?:[0-9]|[1-9]\d)\.(?:[0-9]|[1-9]\d)")
legacy_api_pattern = re.compile(
    r"(?:[1-9]\d{0,2}|[1-9]\d{0,2}\.[1-9]\d{0,2}|"
    r"[1-9]\d{0,2}\.(?:0|[1-9]\d{0,2})\.[1-9]\d{0,2})"
)

if api_major >= 26:
    if not dot_api_pattern.fullmatch(platform_version):
        fail(
            f"API {api_version} requires a valid three-part platformVersion "
            f"in {package}, got '{platform_version or '<empty>'}'"
        )
    install_api_version = platform_version
else:
    install_api_version = full_api_version or api_version
    if not legacy_api_pattern.fullmatch(install_api_version):
        fail(f"invalid SDK API version '{install_api_version}' in {package}")

if not re.fullmatch(r"\d+(?:\.\d+){3}", sdk_version):
    fail(f"invalid SDK package version '{sdk_version}' in {package}")

package_version = sdk_version
if release_type:
    package_version += f"-{release_type}"

print(f"{install_api_version}\t{package_version}")
PY
}

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

  metadata="$(read_component_metadata "${selected}" "${component}")"
  IFS=$'\t' read -r component_api_version metadata_package_version <<< "${metadata}"

  if [[ "${metadata_package_version}" != "${component_version}" ]]; then
    echo "Error: package filename and metadata version do not match." >&2
    echo "  package : ${base_name}" >&2
    echo "  filename: ${component_version}" >&2
    echo "  metadata: ${metadata_package_version}" >&2
    exit 1
  fi

  if [[ -z "${PACKAGE_VERSION}" ]]; then
    PACKAGE_VERSION="${component_version}"
    SDK_API_VERSION="${component_api_version}"
  else
    if [[ "${component_version}" != "${PACKAGE_VERSION}" ]]; then
      echo "Error: inconsistent package versions found." >&2
      echo "  expected: ${PACKAGE_VERSION}" >&2
      echo "  got     : ${component_version} (${base_name})" >&2
      exit 1
    fi
    if [[ "${component_api_version}" != "${SDK_API_VERSION}" ]]; then
      echo "Error: inconsistent SDK API versions found." >&2
      echo "  expected: ${SDK_API_VERSION}" >&2
      echo "  got     : ${component_api_version} (${base_name})" >&2
      exit 1
    fi
  fi
done

TARGET_VERSION_DIR="${DST_DIR}/${SDK_API_VERSION}"

echo "Source dir      : ${SRC_DIR}"
echo "OpenHarmony root: ${OPENHARMONY_ROOT}"
echo "Target linux dir: ${DST_DIR}"
echo "SDK package     : ${PACKAGE_VERSION}"
echo "SDK API version : ${SDK_API_VERSION}"
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
