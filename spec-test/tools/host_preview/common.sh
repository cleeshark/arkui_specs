#!/usr/bin/env bash

print_openharmony_root_hint() {
  echo "Error: OPENHARMONY_ROOT resolved to filesystem root (/)." >&2
  echo "Hint: try adding --openharmony-root <OpenHarmonyRoot>." >&2
}

snapshot_xvfb_pids() {
  pgrep -u "$(id -u)" -x Xvfb 2>/dev/null || true
}

cleanup_new_xvfb_processes() {
  local before_file="$1"
  local current_pid=""
  local before_pid=""
  local found=0
  local -a cleanup_pids=()

  if [[ ! -f "${before_file}" ]]; then
    return 0
  fi

  while read -r current_pid; do
    [[ -z "${current_pid}" ]] && continue
    found=0
    while read -r before_pid; do
      if [[ "${current_pid}" == "${before_pid}" ]]; then
        found=1
        break
      fi
    done < "${before_file}"
    if [[ "${found}" -eq 0 ]]; then
      cleanup_pids+=("${current_pid}")
    fi
  done < <(snapshot_xvfb_pids)

  if [[ "${#cleanup_pids[@]}" -eq 0 ]]; then
    return 0
  fi

  printf '\033[1;33m%s\033[0m %s\n' "Cleaning Xvfb processes:" "${cleanup_pids[*]}"
  kill "${cleanup_pids[@]}" >/dev/null 2>&1 || true
  sleep 0.2
  for current_pid in "${cleanup_pids[@]}"; do
    if kill -0 "${current_pid}" >/dev/null 2>&1; then
      kill -9 "${current_pid}" >/dev/null 2>&1 || true
    fi
  done
}

resolve_previewer_bin() {
  local spec_test_root="$1"
  local explicit_openharmony_root="${2:-${OPENHARMONY_ROOT:-}}"
  local openharmony_root

  if [[ -n "${explicit_openharmony_root}" ]]; then
    if [[ ! -d "${explicit_openharmony_root}" ]]; then
      return 1
    fi
    openharmony_root="$(cd "${explicit_openharmony_root}" && pwd)"
  else
    openharmony_root="$(cd "${spec_test_root}/../../../../.." && pwd)"
  fi
  if [[ "${openharmony_root}" == "/" ]]; then
    print_openharmony_root_hint
    return 1
  fi

  local -a candidates=()
  if [[ -n "${PREVIEWER_BIN:-}" ]]; then
    candidates+=("${PREVIEWER_BIN}")
  fi
  if [[ -n "${OHOS_BASE_SDK_HOME:-}" ]]; then
    candidates+=("${OHOS_BASE_SDK_HOME}/previewer/common/bin")
  fi
  if [[ -n "${DEVECO_SDK_HOME:-}" ]]; then
    candidates+=("${DEVECO_SDK_HOME}/previewer/common/bin")
  fi
  candidates+=("${openharmony_root}/out/sdk/ohos-sdk/linux/previewer/common/bin")
  candidates+=("${openharmony_root}/prebuilts/ohos-sdk/linux/previewer/common/bin")

  local candidate=""
  for candidate in "${candidates[@]}"; do
    if [[ -x "${candidate}/Previewer" && -x "${candidate}/PreviewerCLI" ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

sanitize_socket_name() {
  local raw_name="${1:-}"
  local sanitized
  sanitized="$(printf '%s' "${raw_name}" | tr -c 'A-Za-z0-9_-' '_')"

  if [[ -z "${sanitized}" || -z "${sanitized//_/}" ]]; then
    echo "previewer"
    return 0
  fi

  echo "${sanitized}"
}

resolve_previewer_name() {
  if [[ -n "${PREVIEWER_INSTANCE_NAME:-}" ]]; then
    sanitize_socket_name "${PREVIEWER_INSTANCE_NAME}"
    return 0
  fi

  local current_user="${USER:-}"
  if [[ -z "${current_user}" ]]; then
    current_user="$(id -un 2>/dev/null || true)"
  fi
  if [[ -z "${current_user}" ]]; then
    current_user="user"
  fi

  sanitize_socket_name "previewer_${current_user}"
}
