// Polling SPA for the semantic evaluation service. No build step, vanilla JS.
"use strict";

const POLL_MS = 2000;
const METRICS_POLL_MS = 10000;
const ACTIVE_STATES = new Set(["running", "waiting"]);
let selectedJob = null;
let lastMetricsAt = 0;
let latestJobs = [];
let latestFunctions = [];
let jobsPage = 1;
let jobsPageSizeValue = 10;
let functionsPage = 1;
let functionsPageSizeValue = 10;
let agentProfiles = [];
let selectedAgent = null;
let agentOverrides = new Set();

const status = (document.getElementById("status"));
const filter = (document.getElementById("filter"));
const tbody = document.querySelector("#jobs tbody");
const functionBody = document.querySelector("#functions tbody");
const freshnessFilter = document.getElementById("freshness-filter");
const functionsPageSize = document.getElementById("functions-page-size");
const functionsPagePrev = document.getElementById("functions-page-prev");
const functionsPageNext = document.getElementById("functions-page-next");
const functionsPageInfo = document.getElementById("functions-page-info");
const jobsPageSize = document.getElementById("jobs-page-size");
const jobsPagePrev = document.getElementById("jobs-page-prev");
const jobsPageNext = document.getElementById("jobs-page-next");
const jobsPageInfo = document.getElementById("jobs-page-info");
const form = document.getElementById("create-form");
const createError = document.getElementById("create-error");
const actionError = document.getElementById("action-error");
const agentSelect = document.getElementById("agent-select");
const agentParams = document.getElementById("agent-params");
const agentReset = document.getElementById("agent-reset");

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
}

function paginate(items, page, pageSize) {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(Math.max(1, page), totalPages);
  const offset = (currentPage - 1) * pageSize;
  return {
    items: items.slice(offset, offset + pageSize),
    page: currentPage,
    totalPages,
    total,
    start: total ? offset + 1 : 0,
    end: Math.min(offset + pageSize, total),
  };
}

function updatePagination(result, info, previous, next) {
  info.textContent = `Page ${result.page} of ${result.totalPages} · ${result.start}–${result.end} of ${result.total}`;
  previous.disabled = result.page <= 1;
  next.disabled = result.page >= result.totalPages;
}

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const text = await res.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch (e) { /* keep null */ }
  return { ok: res.ok, status: res.status, json };
}

function rowActions(job) {
  const cancel = (
    job.status === "queued" || job.status === "running" || job.status === "waiting"
  )
    ? `<button data-act="cancel" data-id="${esc(job.job_id)}">cancel</button>` : "";
  const retry = (job.status === "failed" || job.status === "cancelled")
    ? `<button data-act="retry" data-id="${esc(job.job_id)}">retry</button>` : "";
  const retryLatestSpecs = (
    (job.status === "failed" || job.status === "cancelled") &&
    (job.stage === "aggregation" || job.stage === "report")
  )
    ? `<button data-act="retry-latest-specs" data-id="${esc(job.job_id)}"` +
      ` title="Refresh the specs workspace to current HEAD before retrying">` +
      `retry (latest specs)</button>` : "";
  return `${cancel}${retry}${retryLatestSpecs}`;
}

function archivedPath(job) {
  if (job.status !== "completed") return "";
  const note = String((job.progress || {}).note || "");
  const prefix = "archived at ";
  return note.startsWith(prefix) ? note.slice(prefix.length).trim() : "";
}

function progressHtml(job) {
  const pipeline = job.pipeline || [];
  const p = job.progress || {};
  const archive = archivedPath(job);

  if (!pipeline.length) {
    const note = p.note ? ` · ${esc(p.note)}` : "";
    return `<span>${esc(p.stage || job.stage || "—")}${note}</span>`;
  }

  const archiveHtml = archive
    ? ` <button type="button" class="archive-link" data-act="copy-archive"
        data-path="${esc(archive)}" aria-label="Copy archive path">link</button>`
    : "";
  const running = job.status === "running";
  const activeStage = pipeline.find(s => s.state === "active" || s.state === "waiting");
  const label = activeStage ? activeStage.stage
    : job.status === "completed" ? "done"
    : job.status === "failed" ? "failed"
    : job.stage || "—";

  const segs = pipeline.map(s =>
    `<span class="seg ${esc(s.state)}" title="${esc(s.stage)}"></span>`
  ).join("");

  return `<div class="pipeline-progress">
    <div class="pipeline-bar">${segs}</div>
    <span class="pipeline-label">${running ? '<span class="activity-spinner" aria-hidden="true"></span>' : ""}${esc(label)}${archiveHtml}</span>
  </div>`;
}

function formatDuration(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "—";
  const total = Math.floor(ms / 1000);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  if (hours) return `${hours}h ${String(minutes).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
  if (minutes) return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
  return `${seconds}s`;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("en-US");
}

function formatTime(isoString) {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return String(isoString);
    return d.toLocaleString(undefined, {
      month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  } catch (_) { return String(isoString); }
}

function durationHtml(job) {
  const timing = job.timing || {};
  const live = ACTIVE_STATES.has(job.status) && timing.started_at && !timing.finished_at;
  const activeDurationMs = Number(timing.active_duration_ms || 0);
  const executorMs = Number(timing.executor_duration_ms || 0);
  const title = `Total wall time: ${formatDuration(Number(timing.duration_ms || 0))}\nExecutor: ${formatDuration(executorMs)}`;
  if (live) {
    return `<span class="job-duration live-duration"
      data-run-started-at="${esc(timing.started_at)}"
      data-active-base-ms="${activeDurationMs}"
      title="${esc(title)}">${formatDuration(activeDurationMs)}</span>`;
  }
  return `<span class="job-duration" title="${esc(title)}">${formatDuration(activeDurationMs)}</span>`;
}

function tokenHtml(job) {
  const usage = job.usage || {};
  if (!usage.executor_invocations) return '<span class="muted">—</span>';
  if (!usage.reported) return '<span class="muted" title="Codex did not report usage">not reported</span>';
  const suffix = usage.complete ? "" : " *";
  const completeTitle = usage.complete ? "All executor invocations reported usage" : "Partial: one or more invocations did not report usage";
  const breakdown = [
    `Total: ${formatNumber(usage.total_tokens)}`,
    `Input: ${formatNumber(usage.input_tokens)}`,
    `Output: ${formatNumber(usage.output_tokens)}`,
  ];
  if (usage.cached_input_tokens > 0) {
    breakdown.push(`Cached: ${formatNumber(usage.cached_input_tokens)}`);
  }
  const title = `${completeTitle}\n${breakdown.join('\n')}`;
  return `<span title="${esc(title)}">${formatNumber(usage.total_tokens)}${suffix}</span>`;
}

function renderJobs(jobs = latestJobs) {
  const f = filter.value;
  const filtered = f ? jobs.filter((j) => j.status === f) : jobs;
  const paged = paginate(filtered, jobsPage, jobsPageSizeValue);
  jobsPage = paged.page;
  const running = jobs.filter((j) => ACTIVE_STATES.has(j.status)).length;
  status.textContent = `${jobs.length} job(s) · ${running} running`;
  tbody.innerHTML = paged.items.map((job) => `
    <tr data-id="${esc(job.job_id)}" class="${ACTIVE_STATES.has(job.status) ? "job-active" : ""}">
      <td>${esc(job.func_id)}</td>
      <td class="badge ${esc(job.status)}">${esc(job.status)}</td>
      <td>${progressHtml(job)}</td>
      <td>${durationHtml(job)}</td>
      <td>${tokenHtml(job)}</td>
      <td class="muted" title="${esc(job.updated_at)}">${formatTime(job.updated_at)}</td>
      <td>${rowActions(job)} <button data-act="detail" data-id="${esc(job.job_id)}">detail</button></td>
    </tr>`).join("") || `<tr><td class="muted" colspan="7">no jobs</td></tr>`;
  updatePagination(paged, jobsPageInfo, jobsPagePrev, jobsPageNext);
}

function renderMetrics(metrics) {
  const duration = metrics.duration_summary || {};
  const executor = metrics.executor_duration_summary || {};
  const usage = metrics.token_usage || {};
  const states = metrics.status_counts || {};
  const running = Array.from(ACTIVE_STATES).reduce((sum, key) => sum + Number(states[key] || 0), 0);
  document.getElementById("metric-jobs").textContent = formatNumber(metrics.job_total);
  document.getElementById("metric-running").textContent = formatNumber(running);
  document.getElementById("metric-duration").textContent = duration.count ? formatDuration(duration.avg_ms) : "—";
  document.getElementById("metric-executor").textContent = executor.count ? formatDuration(executor.avg_ms) : "—";
  const invocations = Number(metrics.executor_invocations || 0);
  const reportedInvocations = Number(usage.reported_invocations || 0);
  document.getElementById("metric-tokens").textContent = !invocations ? "—"
    : !reportedInvocations ? "not reported"
      : `${formatNumber(usage.total_tokens)}${reportedInvocations < invocations ? " *" : ""}`;
  document.getElementById("metric-coverage").textContent = metrics.executor_invocations
    ? `${Math.round(Number(usage.reporting_coverage || 0) * 100)}%` : "—";
  document.getElementById("metrics-updated").textContent = `updated ${new Date().toLocaleTimeString()}`;
}

async function refreshMetrics(force = false) {
  if (!force && Date.now() - lastMetricsAt < METRICS_POLL_MS) return;
  const result = await api("GET", "/api/metrics");
  if (result.ok && result.json) {
    lastMetricsAt = Date.now();
    renderMetrics(result.json);
  }
}

function paramInput(param, value) {
  const key = esc(param.key);
  const id = `agent-param-${key}`;
  if (param.type === "enum") {
    const options = (param.enum || []).map((item) =>
      `<option value="${esc(item)}" ${String(item) === String(value) ? "selected" : ""}>${esc(item)}</option>`
    ).join("");
    return `<select id="${id}" data-param="${key}">${options}</select>`;
  }
  const type = param.type === "integer" ? "number" : "text";
  const min = param.minimum == null ? "" : ` min="${esc(param.minimum)}"`;
  const max = param.maximum == null ? "" : ` max="${esc(param.maximum)}"`;
  const display = value == null ? "" : String(value);
  return `<input id="${id}" data-param="${key}" type="${type}" value="${esc(display)}"${min}${max} />`;
}

function renderAgentParams(profile) {
  selectedAgent = profile;
  agentOverrides = new Set();
  if (!profile) {
    agentParams.innerHTML = '<span class="muted">No Agent available</span>';
    agentReset.hidden = true;
    return;
  }
  agentParams.innerHTML = (profile.params || []).map((param) => {
    const defaultValue = profile.defaults ? profile.defaults[param.key] : param.default;
    const defaultText = defaultValue == null ? "local/default" : String(defaultValue);
    return `<label>${esc(param.label || param.key)}
      ${paramInput(param, defaultValue)}
      <span class="param-source muted" data-source="${esc(param.key)}">default: ${esc(defaultText)}</span>
    </label>`;
  }).join("");
  agentReset.hidden = true;
}

async function loadAgents() {
  const result = await api("GET", "/api/agents");
  if (!result.ok || !Array.isArray(result.json)) return;
  agentProfiles = result.json;
  agentSelect.innerHTML = agentProfiles.map((profile) =>
    `<option value="${esc(profile.id)}" ${profile.default ? "selected" : ""}>${esc(profile.name || profile.id)}${profile.default ? " (default)" : ""}</option>`
  ).join("");
  renderAgentParams(agentProfiles.find((profile) => profile.default) || agentProfiles[0]);
}

function readAgentOverrides() {
  const params = {};
  if (!selectedAgent) return params;
  (selectedAgent.params || []).forEach((param) => {
    if (!agentOverrides.has(param.key)) return;
    const input = document.querySelector(`[data-param="${CSS.escape(param.key)}"]`);
    if (!input) return;
    let value = input.value;
    if (param.type === "integer") value = Number(value);
    if (param.type === "string" && value === "" && param.nullable) value = null;
    params[param.key] = value;
  });
  return params;
}

agentSelect.addEventListener("change", () => {
  const profile = agentProfiles.find((item) => item.id === agentSelect.value);
  renderAgentParams(profile);
});

agentParams.addEventListener("input", (event) => {
  const key = event.target && event.target.dataset ? event.target.dataset.param : null;
  if (!key || !selectedAgent) return;
  const param = (selectedAgent.params || []).find((item) => item.key === key);
  const defaultValue = selectedAgent.defaults ? selectedAgent.defaults[key] : param.default;
  let value = event.target.value;
  if (param.type === "integer") value = Number(value);
  if (param.type === "string" && value === "" && param.nullable) value = null;
  if (String(value) === String(defaultValue)) agentOverrides.delete(key);
  else agentOverrides.add(key);
  const source = document.querySelector(`[data-source="${CSS.escape(key)}"]`);
  if (source) source.textContent = agentOverrides.has(key) ? "manual override" : `default: ${defaultValue == null ? "local/default" : defaultValue}`;
  agentReset.hidden = agentOverrides.size === 0;
});

agentReset.addEventListener("click", () => renderAgentParams(selectedAgent));

function tickDurations() {
  const now = Date.now();
  document.querySelectorAll(".live-duration").forEach((node) => {
    const runStartedAt = node.dataset.runStartedAt;
    const baseMs = Number(node.dataset.activeBaseMs || 0);
    if (runStartedAt) {
      const segment = Math.max(0, now - new Date(runStartedAt).getTime());
      node.textContent = formatDuration(baseMs + segment);
    }
  });
}

function renderFunctions(functions = latestFunctions) {
  const wanted = freshnessFilter.value;
  const filtered = wanted ? functions.filter((item) => item.freshness === wanted) : functions;
  const paged = paginate(filtered, functionsPage, functionsPageSizeValue);
  functionsPage = paged.page;
  functionBody.innerHTML = paged.items.map((item) => {
    const report = item.current_report;
    const summary = report && report.summary || {};
    const refresh = item.refresh_status === "REFRESHING"
      ? `running ${esc(item.active_job_id || "")}`
      : item.refresh_status === "REFRESH_FAILED"
        ? `failed: ${esc(item.last_refresh_error || "")}` : "idle";
    return `<tr>
      <td>${esc(item.func_id)}</td><td>${esc(item.title)}</td>
      <td><span class="badge freshness ${esc(item.freshness)}">${esc(item.freshness)}</span></td>
      <td>${report ? esc(report.source_revision.slice(0, 10)) : "—"}</td>
      <td>${report ? `${esc(summary.published_score == null ? "—" : summary.published_score)} / ${esc(summary.gate || "—")}` : "—"}</td>
      <td>${refresh}</td>
      <td><button data-act="function-detail" data-id="${esc(item.func_id)}">${esc(item.history_count)}</button></td>
    </tr>`;
  }).join("") || `<tr><td class="muted" colspan="7">no functions</td></tr>`;
  updatePagination(paged, functionsPageInfo, functionsPagePrev, functionsPageNext);
}

async function refresh() {
  const [jobsResult, functionsResult] = await Promise.all([
    api("GET", "/api/jobs"), api("GET", "/api/functions")
  ]);
  if (jobsResult.ok && Array.isArray(jobsResult.json)) {
    latestJobs = jobsResult.json;
    renderJobs();
    if (functionsResult.ok && Array.isArray(functionsResult.json)) {
      latestFunctions = functionsResult.json;
      renderFunctions();
    }
    if (selectedJob) loadDetail(selectedJob);
    refreshMetrics();
  } else {
    status.textContent = "error";
  }
}

async function loadFunctionDetail(funcId) {
  const [detail, history] = await Promise.all([
    api("GET", `/api/functions/${encodeURIComponent(funcId)}`),
    api("GET", `/api/functions/${encodeURIComponent(funcId)}/history`),
  ]);
  const panel = document.getElementById("function-detail");
  if (!detail.ok) { panel.hidden = true; return; }
  panel.hidden = false;
  document.getElementById("function-detail-title").textContent = `Function ${funcId} history`;
  document.getElementById("function-detail-state").textContent = JSON.stringify({
    current: detail.json, history: history.json || []
  }, null, 2);
}

async function loadDetail(jobId) {
  selectedJob = jobId;
  const [jobRes, evRes] = await Promise.all([
    api("GET", `/api/jobs/${encodeURIComponent(jobId)}`),
    api("GET", `/api/jobs/${encodeURIComponent(jobId)}/events?tail=1&limit=100`),
  ]);
  const detail = document.getElementById("detail");
  if (!jobRes.ok) { detail.hidden = true; return; }
  detail.hidden = false;
  document.getElementById("detail-title").textContent = `Job ${jobRes.json.func_id} (${jobRes.json.status})`;
  const timing = jobRes.json.timing || {};
  const usage = jobRes.json.usage || {};
  const telemetry = jobRes.json.executor_telemetry || {};
  document.getElementById("detail-stats").innerHTML = `
    <div class="metric"><span>Duration</span><strong>${durationHtml(jobRes.json)}</strong></div>
    <div class="metric"><span>Wall time</span><strong>${formatDuration(Number(timing.duration_ms || 0))}</strong></div>
    <div class="metric"><span>Executor time</span><strong>${formatDuration(Number(timing.executor_duration_ms || 0))}</strong></div>
    <div class="metric"><span>Total tokens</span><strong>${usage.reported ? formatNumber(usage.total_tokens) : "not reported"}</strong></div>
    <div class="metric"><span>Input / Output</span><strong>${usage.reported ? `${formatNumber(usage.input_tokens)} / ${formatNumber(usage.output_tokens)}` : "—"}</strong></div>
    <div class="metric"><span>Cached input</span><strong>${usage.reported && usage.cached_input_tokens > 0 ? formatNumber(usage.cached_input_tokens) : "—"}</strong></div>
    <div class="metric"><span>Tool / command calls</span><strong>${telemetry.reported ? `${formatNumber(telemetry.tool_calls)} / ${formatNumber(telemetry.command_calls)}` : "not reported"}</strong></div>
    <div class="metric"><span>Input / evidence paths</span><strong>${telemetry.reported ? `${formatNumber(telemetry.input_paths_accessed)} / ${formatNumber(telemetry.evidence_paths_accessed)}` : "—"}</strong></div>`;
  document.getElementById("detail-state").textContent = JSON.stringify(jobRes.json, null, 2);
  const events = Array.isArray(evRes.json) ? evRes.json : [];
  document.getElementById("events").innerHTML = events.slice(-40).reverse().map((e) =>
    `<li><b>${esc(e.seq)}</b> ${esc(e.event_type)} <span class="muted" title="${esc(e.created_at)}">${formatTime(e.created_at)}</span><br/><pre>${esc(JSON.stringify(e.payload))}</pre></li>`
  ).join("");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  createError.hidden = true;
  const fd = new FormData(form);
  const payload = { func_id: fd.get("func_id"), run_count: Number(fd.get("run_count")) || 1 };
  const rev = fd.get("source_revision");
  if (rev) payload.source_revision = rev;
  payload.agent_id = fd.get("agent_id") || undefined;
  payload.agent_params = readAgentOverrides();
  const { ok, json } = await api(
    "POST", `/api/functions/${encodeURIComponent(payload.func_id)}/refresh`,
    {
      run_count: payload.run_count,
      source_revision: payload.source_revision,
      agent_id: payload.agent_id,
      agent_params: payload.agent_params,
    }
  );
  if (ok) {
    form.reset();
    const defaultProfile = agentProfiles.find((profile) => profile.default) || agentProfiles[0];
    if (defaultProfile) {
      agentSelect.value = defaultProfile.id;
      renderAgentParams(defaultProfile);
    }
    refresh();
  }
  else { createError.textContent = (json && json.error) || "create failed"; createError.hidden = false; }
});

async function runJobAction(button, action, id) {
  actionError.hidden = true;
  button.disabled = true;
  try {
    const res = await api("POST", `/api/jobs/${encodeURIComponent(id)}/${action}`);
    if (!res.ok) {
      actionError.textContent = (res.json && (res.json.error || res.json.message)) ||
        `${action} failed (${res.status})`;
      actionError.hidden = false;
    }
    await refresh();
  } catch (error) {
    actionError.textContent = `${action} request failed: ${error && error.message ? error.message : error}`;
    actionError.hidden = false;
  } finally {
    button.disabled = false;
  }
}

async function copyArchivePath(button) {
  const path = button.dataset.path || "";
  if (!path) return;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(path);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = path;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      const copied = document.execCommand("copy");
      textarea.remove();
      if (!copied) throw new Error("clipboard unavailable");
    }
    button.textContent = "copied";
    window.setTimeout(() => { button.textContent = "link"; }, 1200);
  } catch (error) {
    actionError.textContent = `copy failed: ${error && error.message ? error.message : error}`;
    actionError.hidden = false;
  }
}

document.addEventListener("click", async (e) => {
  const t = e.target;
  if (!t.dataset || !t.dataset.act) return;
  if (t.dataset.act === "copy-archive") { await copyArchivePath(t); return; }
  const id = t.dataset.id;
  if (t.dataset.act === "cancel") { await runJobAction(t, "cancel", id); }
  if (t.dataset.act === "retry") { await runJobAction(t, "retry", id); }
  if (t.dataset.act === "retry-latest-specs") {
    await runJobAction(t, "retry-latest-specs", id);
  }
  if (t.dataset.act === "detail") { loadDetail(id); }
  if (t.dataset.act === "function-detail") { loadFunctionDetail(id); }
});

filter.addEventListener("change", () => {
  jobsPage = 1;
  renderJobs();
});
freshnessFilter.addEventListener("change", () => {
  functionsPage = 1;
  renderFunctions();
});
functionsPageSize.addEventListener("change", () => {
  functionsPageSizeValue = Number(functionsPageSize.value);
  functionsPage = 1;
  renderFunctions();
});
jobsPageSize.addEventListener("change", () => {
  jobsPageSizeValue = Number(jobsPageSize.value);
  jobsPage = 1;
  renderJobs();
});
functionsPagePrev.addEventListener("click", () => {
  functionsPage -= 1;
  renderFunctions();
});
functionsPageNext.addEventListener("click", () => {
  functionsPage += 1;
  renderFunctions();
});
jobsPagePrev.addEventListener("click", () => {
  jobsPage -= 1;
  renderJobs();
});
jobsPageNext.addEventListener("click", () => {
  jobsPage += 1;
  renderJobs();
});
refresh();
loadAgents();
setInterval(refresh, POLL_MS);
setInterval(tickDurations, 1000);
