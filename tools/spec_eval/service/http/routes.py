"""HTTP route dispatch (TASK-011-06).

``route_request`` is a pure function over (method, path, body, headers, app) so
the API can be tested without sockets. The server handler is a thin wrapper
around it. All state mutations go through the app's repository/dispatcher
methods; the HTTP layer never touches SQLite or starts subprocesses directly.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ..domain.errors import DuplicateJobError, IllegalTransitionError, JobNotFoundError
from . import serializers
from .security import safe_resolve, token_ok

FUNC_ID_RE = re.compile(r"^[0-9]{2}-[0-9]{2}-[0-9]{2}$")


@dataclass
class Response:
    status: int
    body: bytes
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def json(cls, status: int, obj: Any) -> "Response":
        return cls(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json")

    @classmethod
    def text(cls, status: int, text: str, content_type: str = "text/plain; charset=utf-8") -> "Response":
        return cls(status, text.encode("utf-8"), content_type)

    @classmethod
    def file(cls, status: int, data: bytes, content_type: str) -> "Response":
        return cls(status, data, content_type)


def _error(status: int, message: str) -> Response:
    return Response.json(status, {"error": message})


def route_request(
    method: str,
    raw_path: str,
    body: bytes,
    headers: dict[str, str],
    app: Any,
) -> Response:
    if not token_ok(headers, getattr(app, "token", None)):
        return _error(401, "unauthorized")

    split = urlsplit(raw_path)
    path = split.path.rstrip("/") or "/"
    query = _parse_query(split.query)
    segments = [s for s in path.split("/") if s]

    # --- static UI -------------------------------------------------------
    if method == "GET" and path == "/":
        return _serve_static(app.ui_dir, "index.html", "text/html; charset=utf-8")
    if method == "GET" and len(segments) == 2 and segments[0] == "static":
        ctype = _content_type_for(segments[1])
        return _serve_static(app.ui_dir, segments[1], ctype)

    # --- /api/metrics ----------------------------------------------------
    if segments == ["api", "metrics"] and method == "GET":
        return Response.json(200, app.metrics())

    if segments == ["api", "site", "export"] and method == "POST":
        return Response.json(200, {key: str(path) for key, path in app.export_site().items()})

    # --- /api/freshness-policies -----------------------------------------
    if segments[:2] == ["api", "freshness-policies"]:
        return _route_freshness_policies(method, segments[2:], body, app)

    # --- /api/functions/{func_id}/refresh --------------------------------
    if (
        len(segments) == 4
        and segments[:2] == ["api", "functions"]
        and segments[3] == "refresh"
    ):
        return _refresh_function(method, segments[2], body, app)

    if segments[:2] == ["api", "functions"]:
        return _route_functions(method, segments[2:], query, app)

    # --- /api/jobs -------------------------------------------------------
    if segments[:2] == ["api", "jobs"]:
        return _route_jobs(method, segments[2:], query, body, app)

    return _error(404, "not found")


# --- /api/jobs dispatch -----------------------------------------------------

def _route_jobs(method: str, rest: list[str], query: dict[str, str], body: bytes, app: Any) -> Response:
    # /api/jobs
    if not rest:
        if method == "GET":
            status = query.get("status")
            jobs = app.list_jobs(status)
            return Response.json(200, [_job_to_dict(app, job) for job in jobs])
        if method == "POST":
            return _create_job(body, app)
        return _error(405, "method not allowed")

    job_id = rest[0]
    # /api/jobs/{id}
    if len(rest) == 1:
        if method == "GET":
            try:
                return Response.json(200, _job_to_dict(app, app.get_job(job_id)))
            except JobNotFoundError:
                return _error(404, "job not found")
        return _error(405, "method not allowed")

    action = rest[1]
    # /api/jobs/{id}/events
    if action == "events" and len(rest) == 2 and method == "GET":
        since = int(query.get("since_seq", "0"))
        try:
            events = app.list_events(job_id, since)
        except JobNotFoundError:
            return _error(404, "job not found")
        return Response.json(200, [serializers.event_to_dict(e) for e in events])

    # /api/jobs/{id}/cancel
    if action == "cancel" and len(rest) == 2 and method == "POST":
        result = app.cancel(job_id)
        payload = {
            "job_id": job_id,
            "cancelled": result.outcome == "cancelled",
            "outcome": result.outcome,
            "status": result.status,
            "message": result.message,
        }
        if result.accepted:
            status = 202 if result.outcome.startswith("cancellation_") else 200
            return Response.json(status, payload)
        payload["error"] = result.message
        return Response.json(404 if result.outcome == "not_found" else 409, payload)

    # /api/jobs/{id}/retry
    if action == "retry" and len(rest) == 2 and method == "POST":
        try:
            status = app.retry(job_id)
        except (JobNotFoundError, IllegalTransitionError) as exc:
            return _error(409, str(exc))
        return Response.json(200, {"job_id": job_id, "status": status})

    # /api/jobs/{id}/artifacts/{kind}
    if action == "artifacts" and len(rest) == 3 and method == "GET":
        return _serve_artifact(job_id, rest[2], app)

    return _error(404, "not found")


def _create_job(body: bytes, app: Any) -> Response:
    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(400, "invalid JSON body")
    if not isinstance(payload, dict):
        return _error(400, "body must be a JSON object")
    func_id = payload.get("func_id")
    if not isinstance(func_id, str) or not FUNC_ID_RE.match(func_id):
        return _error(400, "func_id must match NN-NN-NN")
    run_count = int(payload.get("run_count", 1))
    if run_count < 1 or run_count > 10:
        return _error(400, "run_count must be between 1 and 10")
    source_revision = payload.get("source_revision") or app.default_source_revision()
    job_id = payload.get("job_id")
    try:
        job = app.create_job(
            func_id=func_id,
            run_count=run_count,
            source_revision=source_revision,
            job_id=job_id,
        )
    except DuplicateJobError as exc:
        return _error(409, f"duplicate job: {exc}")
    return Response.json(201, _job_to_dict(app, job))


def _refresh_function(method: str, func_id: str, body: bytes, app: Any) -> Response:
    if method != "POST":
        return _error(405, "method not allowed")
    if not FUNC_ID_RE.match(func_id):
        return _error(400, "func_id must match NN-NN-NN")
    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(400, "invalid JSON body")
    if not isinstance(payload, dict):
        return _error(400, "body must be a JSON object")
    try:
        run_count = int(payload.get("run_count", 1))
    except (TypeError, ValueError):
        return _error(400, "run_count must be an integer")
    if run_count < 1 or run_count > 10:
        return _error(400, "run_count must be between 1 and 10")
    source_revision = payload.get("source_revision")
    if source_revision is not None and not isinstance(source_revision, str):
        return _error(400, "source_revision must be a string")
    try:
        result = app.refresh_function(
            func_id=func_id, source_revision=source_revision, run_count=run_count
        )
    except Exception as exc:
        return _error(409, str(exc))
    return Response.json(
        200 if result.deduplicated else 202,
        {
            "job": _job_to_dict(app, result.job),
            "desired_generation": result.target.generation,
            "deduplicated": result.deduplicated,
        },
    )


def _route_functions(
    method: str, rest: list[str], query: dict[str, str], app: Any
) -> Response:
    if method != "GET":
        return _error(405, "method not allowed")
    if not rest:
        functions = app.list_functions()
        for key in ("freshness", "refresh_status", "func_id"):
            value = query.get(key)
            if value:
                functions = [item for item in functions if str(item.get(key)) == value]
        return Response.json(200, functions)
    func_id = rest[0]
    if not FUNC_ID_RE.match(func_id):
        return _error(400, "func_id must match NN-NN-NN")
    if len(rest) == 1:
        return Response.json(200, app.get_function(func_id))
    if len(rest) == 2 and rest[1] == "history":
        return Response.json(200, app.function_history(func_id))
    if len(rest) == 2 and rest[1] == "freshness":
        function = app.get_function(func_id)
        return Response.json(
            200,
            {
                key: function[key]
                for key in (
                    "func_id", "freshness", "stale_reasons", "warn_at", "expires_at",
                    "remaining_days", "refresh_status", "active_job_id", "last_refresh_error",
                )
            },
        )
    return _error(404, "not found")


def _route_freshness_policies(method: str, rest: list[str], body: bytes, app: Any) -> Response:
    if not rest:
        if method != "GET":
            return _error(405, "method not allowed")
        return Response.json(
            200,
            [serializers.freshness_policy_to_dict(item) for item in app.freshness_policies()],
        )
    if method != "PUT" or len(rest) != 1:
        return _error(405, "method not allowed")
    scope = rest[0]
    scope_type, scope_key = ("global", "*") if scope == "global" else ("func", scope)
    if scope_type == "func" and not FUNC_ID_RE.match(scope_key):
        return _error(400, "policy scope must be global or a FuncID")
    try:
        payload = json.loads(body.decode("utf-8"))
        max_age_days = int(payload["max_age_days"])
        warning_days = int(payload["warning_days"])
        policy = app.set_freshness_policy(
            scope_type=scope_type,
            scope_key=scope_key,
            max_age_days=max_age_days,
            warning_days=warning_days,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _error(400, f"invalid freshness policy: {exc}")
    except Exception as exc:
        return _error(409, str(exc))
    return Response.json(200, serializers.freshness_policy_to_dict(policy))


def _serve_artifact(job_id: str, kind: str, app: Any) -> Response:
    artifact = app.artifact(job_id, kind)
    if artifact is None:
        return _error(404, "artifact not found")
    safe = safe_resolve(app.settings.data_root, Path(artifact.path))
    if safe is None:
        return _error(404, "artifact not found")
    return Response.file(200, safe.read_bytes(), _content_type_for(safe.name))


def _serve_static(ui_dir: Path, name: str, content_type: str) -> Response:
    safe = safe_resolve(ui_dir, ui_dir / name)
    if safe is None:
        return _error(404, "not found")
    resp = Response.file(200, safe.read_bytes(), content_type)
    resp.headers["Cache-Control"] = "no-cache"
    return resp


def _parse_query(query: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in query.split("&"):
        if not pair:
            continue
        key, _, value = pair.partition("=")
        out[key] = value
    return out


def _content_type_for(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".js"):
        return "text/javascript; charset=utf-8"
    if lower.endswith(".css"):
        return "text/css; charset=utf-8"
    if lower.endswith(".html"):
        return "text/html; charset=utf-8"
    if lower.endswith(".json"):
        return "application/json"
    return "application/octet-stream"


def _job_to_dict(app: Any, job: Any) -> dict[str, Any]:
    return serializers.job_to_dict(job, app.job_statistics(job.job_id))
