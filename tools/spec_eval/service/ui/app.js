// Polling SPA for the semantic evaluation service. No build step, vanilla JS.
"use strict";

const POLL_MS = 2000;
let selectedJob = null;

const status = (document.getElementById("status"));
const filter = (document.getElementById("filter"));
const tbody = document.querySelector("#jobs tbody");
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

function progressText(job) {
  const p = job.progress || {};
  const note = p.note ? ` · ${esc(p.note)}` : "";
  return `${esc(p.stage || "—")}${note}`;
}

function renderJobs(jobs) {
  const f = filter.value;
  const visible = f ? jobs.filter((j) => j.status === f) : jobs;
  status.textContent = `${jobs.length} job(s)`;
  tbody.innerHTML = visible.map((job) => `
    <tr data-id="${esc(job.job_id)}">
      <td>${esc(job.func_id)}</td>
      <td class="badge ${esc(job.status)}">${esc(job.status)}</td>
      <td>${progressText(job)}</td>
      <td class="muted">${esc(job.updated_at)}</td>
      <td>${rowActions(job)} <button data-act="detail" data-id="${esc(job.job_id)}">detail</button></td>
    </tr>`).join("") || `<tr><td class="muted" colspan="5">no jobs</td></tr>`;
}

async function refresh() {
  const { ok, json } = await api("GET", "/api/jobs");
  if (ok && Array.isArray(json)) {
    renderJobs(json);
    if (selectedJob) loadDetail(selectedJob);
  } else {
    status.textContent = "error";
  }
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
  const { ok, json } = await api("POST", "/api/jobs", payload);
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
});

filter.addEventListener("change", refresh);
refresh();
setInterval(refresh, POLL_MS);
