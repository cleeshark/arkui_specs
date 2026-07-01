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

run_previewer_action() {
  local previewer_bin="$1"
  local previewer_name="$2"
  local command="$3"
  local output_file="$4"
  shift 4
  local -a extra_args=("$@")

  local attempt=0
  local max_attempts=40
  while [[ "${attempt}" -lt "${max_attempts}" ]]; do
    attempt=$((attempt + 1))
    if timeout 8s "${previewer_bin}/PreviewerCLI" --name "${previewer_name}" -- --type action --command "${command}" --version 1.0.1 "${extra_args[@]}" > "${output_file}" 2>&1; then
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

count_load_page_success() {
  local log_file="$1"
  rg -c "LoadPage Success" "${log_file}" 2>/dev/null || echo "0"
}

wait_for_load_page() {
  local log_file="$1"
  local expected_count="$2"
  local max_wait="${3:-30}"
  local elapsed=0
  while [[ "${elapsed}" -lt "${max_wait}" ]]; do
    local current
    current="$(count_load_page_success "${log_file}")"
    if [[ "${current}" -ge "${expected_count}" ]]; then
      return 0
    fi
    sleep 0.5
    elapsed=$((elapsed + 1))
  done
  return 1
}

start_persistent_previewer() {
  local previewer_bin="$1"
  local previewer_name="$2"
  local hap_path="$3"
  local initial_url="$4"
  local run_log="$5"

  local command_pipe="/tmp/${previewer_name}_commandPipe"

  while read -r pid _; do
    kill "${pid}" >/dev/null 2>&1 || true
  done < <(pgrep -af "./Previewer -s ${previewer_name}" || true)
  sleep 1
  rm -f "${command_pipe}"

  xvfb-run -a "${previewer_bin}/Previewer" \
    -s "${previewer_name}" \
    -gui \
    -hap "${hap_path}" \
    -refresh region \
    -cpm false \
    -device phone \
    -shape rect \
    -sd 160 \
    -or 432 936 \
    -cr 432 936 \
    -n entry \
    -av ACE_2_0 \
    -url "${initial_url}" \
    -pages main_pages \
    -pm Stage \
    -l en_US \
    -cm light \
    -o portrait \
    > "${run_log}" 2>&1 &
  echo "$!"
}

route_to_page() {
  local previewer_bin="$1"
  local previewer_name="$2"
  local url="$3"
  local run_log="$4"
  local load_count_before="$5"

  local expected_count=$((load_count_before + 1))
  local tmp_out
  tmp_out="$(mktemp)"

  if ! run_previewer_action "${previewer_bin}" "${previewer_name}" "RouterReplace" "${tmp_out}" --args -url "${url}"; then
    rm -f "${tmp_out}"
    return 1
  fi
  rm -f "${tmp_out}"

  if ! wait_for_load_page "${run_log}" "${expected_count}" 30; then
    return 1
  fi
  sleep 0.3
  return 0
}

collect_screenshot_from_running() {
  local previewer_bin="$1"
  local previewer_name="$2"
  local screenshot_file="$3"

  local before_snapshot after_snapshot tmp_out
  before_snapshot="$(mktemp)"
  after_snapshot="$(mktemp)"
  tmp_out="$(mktemp)"

  find "${previewer_bin}" -maxdepth 1 -type f \
    \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) \
    -printf '%T@ %p\n' | sort -n > "${before_snapshot}" || true

  if run_previewer_action "${previewer_bin}" "${previewer_name}" "ScreenShot" "${tmp_out}"; then
    find "${previewer_bin}" -maxdepth 1 -type f \
      \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) \
      -printf '%T@ %p\n' | sort -n > "${after_snapshot}" || true
    local new_file
    new_file="$(comm -13 "${before_snapshot}" "${after_snapshot}" | tail -n 1 | cut -d' ' -f2-)"
    if [[ -n "${new_file}" && -f "${new_file}" ]]; then
      cp -f "${new_file}" "${screenshot_file}"
    fi
  fi

  rm -f "${before_snapshot}" "${after_snapshot}" "${tmp_out}"
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
