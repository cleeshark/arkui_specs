// Polling SPA for the semantic evaluation service. No build step, vanilla JS.
"use strict";

const POLL_MS = 2000;
const METRICS_POLL_MS = 10000;
const ACTIVE_STATES = new Set(["preparing", "evidence", "semantic", "aggregation", "archive", "site_history"]);
let selectedJob = null;
let lastMetricsAt = 0;

const status = (document.getElementById("status"));
const filter = (document.getElementById("filter"));
const tbody = document.querySelector("#jobs tbody");
const functionBody = document.querySelector("#functions tbody");
const freshnessFilter = document.getElementById("freshness-filter");
const form = document.getElementById("create-form");
const createError = document.getElementById("create-error");

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
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
  const cancel = (job.status === "queued" || job.status === "preparing" || job.status === "evidence" || job.status === "semantic" || job.status === "awaiting_executor")
    ? `<button data-act="cancel" data-id="${esc(job.job_id)}">cancel</button>` : "";
  const retry = (job.status === "failed" || job.status === "cancelled")
    ? `<button data-act="retry" data-id="${esc(job.job_id)}">retry</button>` : "";
  return `${cancel}${retry}`;
}

function progressHtml(job) {
  const p = job.progress || {};
  const note = p.note ? ` · ${esc(p.note)}` : "";
  const active = ACTIVE_STATES.has(job.status);
  return `<div class="progress-wrap ${active ? "active" : ""}">
    ${active ? '<span class="activity-spinner" aria-hidden="true"></span>' : ""}
    <span>${esc(p.stage || "—")}${note}</span>
  </div>${active ? '<div class="activity-track" aria-label="job running"><span></span></div>' : ""}`;
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

function durationHtml(job) {
  const timing = job.timing || {};
  const live = ACTIVE_STATES.has(job.status) && timing.started_at && !timing.finished_at;
  const title = `Executor: ${formatDuration(Number(timing.executor_duration_ms || 0))}`;
  return `<span class="job-duration ${live ? "live-duration" : ""}"
    data-duration-ms="${Number(timing.duration_ms || 0)}"
    data-rendered-at="${Date.now()}" title="${esc(title)}">${formatDuration(Number(timing.duration_ms || 0))}</span>`;
}

function tokenHtml(job) {
  const usage = job.usage || {};
  if (!usage.executor_invocations) return '<span class="muted">—</span>';
  if (!usage.reported) return '<span class="muted" title="Codex did not report usage">not reported</span>';
  const suffix = usage.complete ? "" : " *";
  const title = usage.complete ? "All executor invocations reported usage" : "Partial: one or more invocations did not report usage";
  return `<span title="${esc(title)}">${formatNumber(usage.total_tokens)}${suffix}</span>`;
}

function renderJobs(jobs) {
  const f = filter.value;
  const visible = f ? jobs.filter((j) => j.status === f) : jobs;
  const running = jobs.filter((j) => ACTIVE_STATES.has(j.status)).length;
  status.textContent = `${jobs.length} job(s) · ${running} running`;
  tbody.innerHTML = visible.map((job) => `
    <tr data-id="${esc(job.job_id)}" class="${ACTIVE_STATES.has(job.status) ? "job-active" : ""}">
      <td>${esc(job.func_id)}</td>
      <td class="badge ${esc(job.status)}">${esc(job.status)}</td>
      <td>${progressHtml(job)}</td>
      <td>${durationHtml(job)}</td>
      <td>${tokenHtml(job)}</td>
      <td class="muted">${esc(job.updated_at)}</td>
      <td>${rowActions(job)} <button data-act="detail" data-id="${esc(job.job_id)}">detail</button></td>
    </tr>`).join("") || `<tr><td class="muted" colspan="7">no jobs</td></tr>`;
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

function tickDurations() {
  document.querySelectorAll(".live-duration").forEach((node) => {
    const base = Number(node.dataset.durationMs || 0);
    const rendered = Number(node.dataset.renderedAt || Date.now());
    node.textContent = formatDuration(base + Math.max(0, Date.now() - rendered));
  });
}

function renderFunctions(functions) {
  const wanted = freshnessFilter.value;
  const visible = wanted ? functions.filter((item) => item.freshness === wanted) : functions;
  functionBody.innerHTML = visible.map((item) => {
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
}

async function refresh() {
  const [jobsResult, functionsResult] = await Promise.all([
    api("GET", "/api/jobs"), api("GET", "/api/functions")
  ]);
  if (jobsResult.ok && Array.isArray(jobsResult.json)) {
    renderJobs(jobsResult.json);
    if (functionsResult.ok && Array.isArray(functionsResult.json)) renderFunctions(functionsResult.json);
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
    api("GET", `/api/jobs/${encodeURIComponent(jobId)}/events?since_seq=0`),
  ]);
  const detail = document.getElementById("detail");
  if (!jobRes.ok) { detail.hidden = true; return; }
  detail.hidden = false;
  document.getElementById("detail-title").textContent = `Job ${jobRes.json.func_id} (${jobRes.json.status})`;
  const timing = jobRes.json.timing || {};
  const usage = jobRes.json.usage || {};
  document.getElementById("detail-stats").innerHTML = `
    <div class="metric"><span>Duration</span><strong>${durationHtml(jobRes.json)}</strong></div>
    <div class="metric"><span>Executor time</span><strong>${formatDuration(Number(timing.executor_duration_ms || 0))}</strong></div>
    <div class="metric"><span>Total tokens</span><strong>${usage.reported ? formatNumber(usage.total_tokens) : "not reported"}</strong></div>
    <div class="metric"><span>Input / Output</span><strong>${usage.reported ? `${formatNumber(usage.input_tokens)} / ${formatNumber(usage.output_tokens)}` : "—"}</strong></div>`;
  document.getElementById("detail-state").textContent = JSON.stringify(jobRes.json, null, 2);
  const events = Array.isArray(evRes.json) ? evRes.json : [];
  document.getElementById("events").innerHTML = events.slice(-40).reverse().map((e) =>
    `<li><b>${esc(e.seq)}</b> ${esc(e.event_type)} <span class="muted">${esc(e.created_at)}</span><br/><pre>${esc(JSON.stringify(e.payload))}</pre></li>`
  ).join("");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  createError.hidden = true;
  const fd = new FormData(form);
  const payload = { func_id: fd.get("func_id"), run_count: Number(fd.get("run_count")) || 1 };
  const rev = fd.get("source_revision");
  if (rev) payload.source_revision = rev;
  const { ok, json } = await api(
    "POST", `/api/functions/${encodeURIComponent(payload.func_id)}/refresh`,
    { run_count: payload.run_count, source_revision: payload.source_revision }
  );
  if (ok) { form.reset(); refresh(); }
  else { createError.textContent = (json && json.error) || "create failed"; createError.hidden = false; }
});

document.addEventListener("click", async (e) => {
  const t = e.target;
  if (!t.dataset || !t.dataset.act) return;
  const id = t.dataset.id;
  if (t.dataset.act === "cancel") { await api("POST", `/api/jobs/${encodeURIComponent(id)}/cancel`); refresh(); }
  if (t.dataset.act === "retry") { await api("POST", `/api/jobs/${encodeURIComponent(id)}/retry`); refresh(); }
  if (t.dataset.act === "detail") { loadDetail(id); }
  if (t.dataset.act === "function-detail") { loadFunctionDetail(id); }
});

filter.addEventListener("change", refresh);
freshnessFilter.addEventListener("change", refresh);
refresh();
setInterval(refresh, POLL_MS);
setInterval(tickDurations, 1000);
