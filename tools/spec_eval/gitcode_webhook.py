#!/usr/bin/env python3
"""Minimal GitCode Merge Request webhook receiver for report-only CI."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import html
import ipaddress
import json
import logging
import mimetypes
import os
import re
import threading
import time
from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_WEBHOOK_PATH = "/webhooks/gitcode"
DEFAULT_EVENTS_FILE = Path("specs/.evaluator/webhook/receipts.ndjson")
DEFAULT_MAX_BODY_BYTES = 1024 * 1024
DEFAULT_SITE_BASE_PATH = "/arkui_specs"
# URL segment, appended to the site base path, under which per-delivery CI
# archives (report.md / static-result.json / ci-summary.json) are served so PR
# authors can browse and download the full report the comment only samples.
# ci_worker builds report links against ``<site_base_path>/<segment>/pr-<iid>/<delivery>/``;
# keep the two in sync.
ARCHIVE_URL_SEGMENT = "ci"
MERGE_REQUEST_EVENT = "Merge Request Hook"
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40,64}$")
# Served files carry mtime+size validators and must-revalidate caching so a
# polling dashboard pays one conditional request instead of a full re-download
# (issue #96: 30s full-data polling produced 10GB+/day of tunnel egress).
CACHE_CONTROL_REVALIDATE = "no-cache"
# Header (or ``?token=`` query parameter, for links pasted into PR comments)
# that authorizes the public CI-archive route when a token is configured.
ARCHIVE_TOKEN_HEADER = "X-Archive-Token"
DEFAULT_ARCHIVE_TOKEN_ENV = "SPEC_EVAL_ARCHIVE_TOKEN"
DEFAULT_ARCHIVE_RATE_LIMIT = 120
DEFAULT_ARCHIVE_RATE_WINDOW = 60.0
# Upper bound on per-client rate-limiter bookkeeping so a source-IP-rotating
# crawler cannot grow the table without bound.
MAX_TRACKED_CLIENTS = 4096

LOGGER = logging.getLogger("spec_eval.gitcode_webhook")


class WebhookRequestError(ValueError):
    """Request failure that maps to a deterministic HTTP response."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class ReceiptStore:
    """Append-only NDJSON store with delivery-id deduplication."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._delivery_ids = self._load_delivery_ids()

    def _load_delivery_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        delivery_ids: set[str] = set()
        with self.path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"invalid receipt JSON at {self.path}:{line_number}: {error.msg}"
                    ) from error
                delivery_id = value.get("delivery_id")
                if isinstance(delivery_id, str) and delivery_id:
                    delivery_ids.add(delivery_id)
        return delivery_ids

    def append(self, receipt: dict[str, Any]) -> bool:
        """Append a receipt; return False when the delivery already exists."""

        delivery_id = str(receipt["delivery_id"])
        line = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with self._lock:
            if delivery_id in self._delivery_ids:
                return False
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
            self._delivery_ids.add(delivery_id)
        return True


def _header(headers: Mapping[str, str], name: str) -> str:
    value = headers.get(name, "")
    return value.strip() if isinstance(value, str) else ""


def verify_authentication(
    headers: Mapping[str, str],
    raw_body: bytes,
    *,
    token: str | None,
    signature_secret: str | None,
) -> None:
    """Verify configured GitCode token and raw-body SHA-256 signature."""

    if token is not None:
        supplied_token = _header(headers, "X-GitCode-Token")
        if not supplied_token or not hmac.compare_digest(supplied_token, token):
            raise WebhookRequestError(401, "INVALID_TOKEN", "GitCode webhook token verification failed")

    if signature_secret is not None:
        supplied_signature = _header(headers, "X-GitCode-Signature-256")
        expected_signature = "sha256=" + hmac.new(
            signature_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if not supplied_signature or not hmac.compare_digest(supplied_signature, expected_signature):
            raise WebhookRequestError(
                401,
                "INVALID_SIGNATURE",
                "GitCode webhook signature verification failed",
            )


def _required_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WebhookRequestError(400, "INVALID_PAYLOAD", f"{field} must be an object")
    return value


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WebhookRequestError(400, "INVALID_PAYLOAD", f"{field} must be a non-empty string")
    return value.strip()


def _optional_sha(value: Any, field: str, *, required: bool) -> str | None:
    if value in (None, "") and not required:
        return None
    revision = _required_string(value, field)
    if not SHA_PATTERN.fullmatch(revision):
        raise WebhookRequestError(400, "INVALID_REVISION", f"{field} must be a Git commit SHA")
    return revision.lower()


def build_receipt(
    headers: Mapping[str, str],
    payload: dict[str, Any],
    *,
    received_at: str | None = None,
) -> dict[str, Any]:
    """Validate a GitCode merge-request payload and build a privacy-minimized receipt."""

    event_name = _required_string(_header(headers, "X-GitCode-Event"), "X-GitCode-Event")
    if event_name != MERGE_REQUEST_EVENT:
        raise WebhookRequestError(400, "UNSUPPORTED_EVENT", f"unsupported GitCode event: {event_name}")
    delivery_id = _required_string(_header(headers, "X-GitCode-Delivery"), "X-GitCode-Delivery")
    if payload.get("event_type") != "merge_request" or payload.get("object_kind") != "merge_request":
        raise WebhookRequestError(
            400,
            "INVALID_EVENT_KIND",
            "event_type and object_kind must both be merge_request",
        )

    attributes = _required_mapping(payload.get("object_attributes"), "object_attributes")
    project = _required_mapping(payload.get("project"), "project")
    action = _required_string(attributes.get("action"), "object_attributes.action")
    project_path = _required_string(project.get("path_with_namespace"), "project.path_with_namespace")
    iid = attributes.get("iid")
    if not isinstance(iid, int) or isinstance(iid, bool) or iid <= 0:
        raise WebhookRequestError(400, "INVALID_PAYLOAD", "object_attributes.iid must be a positive integer")

    last_commit = attributes.get("last_commit")
    source_revision = None
    if isinstance(last_commit, dict):
        source_revision = _optional_sha(last_commit.get("id"), "object_attributes.last_commit.id", required=False)
    tested_revision = _optional_sha(
        payload.get("git_commit_no") or source_revision,
        "git_commit_no",
        required=False,
    )
    target_branch_commit = attributes.get("target_branch_commit")
    target_revision_value = payload.get("git_target_branch_commit_no")
    if not target_revision_value and isinstance(target_branch_commit, dict):
        target_revision_value = target_branch_commit.get("id")
    target_revision = _optional_sha(
        target_revision_value,
        "git_target_branch_commit_no",
        required=False,
    )

    timestamp = received_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "received_at": timestamp,
        "delivery_id": delivery_id,
        "event": event_name,
        "event_uuid": payload.get("uuid"),
        "action": action,
        "state": attributes.get("state"),
        "project": {
            "id": project.get("id"),
            "path_with_namespace": project_path,
            "web_url": project.get("web_url"),
        },
        "pull_request": {
            "id": attributes.get("id"),
            "iid": iid,
            "url": attributes.get("url"),
            "source_branch": attributes.get("source_branch"),
            "target_branch": attributes.get("target_branch"),
            "work_in_progress": bool(attributes.get("work_in_progress", False)),
            "conflict": bool(attributes.get("conflict", False)),
        },
        "revisions": {
            "tested": tested_revision,
            "target": target_revision,
            "source": source_revision,
        },
        "virtual_merge_build": bool(payload.get("virtual_merge_build", False)),
        "manual_build": bool(payload.get("manual_build", False)),
        "git_branch": payload.get("git_branch"),
    }


class RateLimiter:
    """Sliding-window per-client request counter for the public archive route."""

    def __init__(self, limit: int, window: float) -> None:
        if limit < 0:
            raise ValueError("rate limit must not be negative")
        if window <= 0:
            raise ValueError("rate window must be positive")
        self.limit = limit
        self.window = window
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = {}

    def allow(self, client: str, *, now: float | None = None) -> bool:
        """Record a request for ``client``; return False when over the limit."""

        if self.limit <= 0:
            return True
        moment = time.monotonic() if now is None else now
        with self._lock:
            hits = [hit for hit in self._hits.get(client, []) if moment - hit < self.window]
            if len(hits) >= self.limit:
                self._hits[client] = hits
                return False
            hits.append(moment)
            self._hits[client] = hits
            if len(self._hits) > MAX_TRACKED_CLIENTS:
                for key, moments in list(self._hits.items()):
                    if key != client and (not moments or moment - moments[-1] >= self.window):
                        del self._hits[key]
            return True


def client_identity(handler: BaseHTTPRequestHandler, *, trust_forwarded_for: bool) -> str:
    """Return the client address to log and rate-limit against.

    FRP loopback forwarding makes every peer look like ``127.0.0.1``, which
    erases the real source from the access log. With ``trust_forwarded_for`` and
    a reverse proxy in front that sets ``X-Forwarded-For``, the left-most entry
    is used instead. Only enable it behind such a proxy: a client that can reach
    the port directly can otherwise spoof the header.
    """

    peer = handler.client_address[0] if handler.client_address else "-"
    if not trust_forwarded_for or not _is_loopback_host(peer):
        return peer
    headers = getattr(handler, "headers", None)
    if headers is None:
        return peer
    for part in _header(headers, "X-Forwarded-For").split(","):
        candidate = part.strip()
        if not candidate:
            continue
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        return candidate
    return peer


def _weak_etag(info: os.stat_result) -> str:
    """Weak validator derived from mtime+size; cheap and stable per revision."""

    return f'W/"{info.st_mtime_ns:x}-{info.st_size:x}"'


def _etag_matches(header_value: str, etag: str) -> bool:
    def normalize(value: str) -> str:
        return value[2:] if value.startswith("W/") else value

    candidates = [part.strip() for part in header_value.split(",") if part.strip()]
    if "*" in candidates:
        return True
    return any(normalize(candidate) == normalize(etag) for candidate in candidates)


def _client_copy_is_current(headers: Mapping[str, str], *, etag: str, mtime: float) -> bool:
    """Evaluate ``If-None-Match`` first, then ``If-Modified-Since`` (RFC 9110)."""

    if_none_match = _header(headers, "If-None-Match")
    if if_none_match:
        return _etag_matches(if_none_match, etag)
    if_modified_since = _header(headers, "If-Modified-Since")
    if if_modified_since:
        try:
            since = parsedate_to_datetime(if_modified_since)
        except (TypeError, ValueError):
            return False
        if since is None:
            return False
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        return int(mtime) <= int(since.timestamp())
    return False


def _json_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    value: dict[str, Any],
    *,
    extra_headers: Mapping[str, str] | None = None,
) -> None:
    body = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for name, header_value in (extra_headers or {}).items():
        handler.send_header(name, header_value)
    handler.end_headers()
    handler.wfile.write(body)


def _send_file(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    """Send a file body, or a 304 when the client already holds this revision."""

    try:
        info = path.stat()
    except OSError:
        _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
        return
    etag = _weak_etag(info)
    last_modified = formatdate(info.st_mtime, usegmt=True)
    if _client_copy_is_current(handler.headers, etag=etag, mtime=info.st_mtime):
        handler.send_response(304)
        handler.send_header("ETag", etag)
        handler.send_header("Last-Modified", last_modified)
        handler.send_header("Cache-Control", CACHE_CONTROL_REVALIDATE)
        handler.end_headers()
        return
    data = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("ETag", etag)
    handler.send_header("Last-Modified", last_modified)
    handler.send_header("Cache-Control", CACHE_CONTROL_REVALIDATE)
    handler.end_headers()
    handler.wfile.write(data)


def _serve_site_path(
    handler: BaseHTTPRequestHandler,
    raw_path: str,
    site_root: Path,
    base_path: str,
) -> None:
    """Serve a static file from ``site_root`` for a ``base_path``-prefixed URL.

    Used to host the rebuilt Docusaurus site on the same HTTP server that
    receives webhooks. Public (unauthenticated) read; path traversal outside
    ``site_root`` resolves to a 404. Directory requests serve ``index.html``.
    Responses carry mtime+size validators so a repeat fetch of an unchanged
    data file costs a 304 instead of the full payload.
    """
    url_path = raw_path.split("?", 1)[0]
    rel = url_path[len(base_path):].lstrip("/")
    site_root_resolved = site_root.resolve()
    candidate = (site_root_resolved / rel) if rel else site_root_resolved
    try:
        candidate.resolve().relative_to(site_root_resolved)
    except ValueError:
        _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
        return
    if candidate.is_dir():
        candidate = candidate / "index.html"
    elif not candidate.is_file() and not url_path.endswith("/"):
        # Docusaurus trailingSlash:false emits /foo as foo.html.  Keep a
        # trailing slash directory-only so /foo/ does not silently serve it.
        html_candidate = candidate.with_name(f"{candidate.name}.html")
        if html_candidate.is_file():
            candidate = html_candidate
    try:
        candidate.resolve().relative_to(site_root_resolved)
    except ValueError:
        _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
        return
    if not candidate.is_file():
        _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
        return
    content_type, _ = mimetypes.guess_type(str(candidate))
    if content_type is None:
        content_type = "application/octet-stream"
    elif content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
        content_type = f"{content_type}; charset=utf-8"
    _send_file(handler, candidate, content_type)


def _archive_authorized(handler: BaseHTTPRequestHandler, token: str | None) -> bool:
    """Check the archive token, taken from the header or the ``token`` query.

    The query parameter exists because archive links are pasted into PR comments
    and opened in a browser, which cannot set a header. Query tokens land in
    access logs, so keep the token low-value and rotatable.
    """

    if token is None:
        return True
    supplied = _header(handler.headers, ARCHIVE_TOKEN_HEADER).strip()
    if not supplied:
        query = parse_qs(urlsplit(handler.path).query)
        supplied = (query.get("token") or [""])[0].strip()
    if not supplied:
        return False
    return hmac.compare_digest(supplied, token)


def _serve_archive_path(
    handler: BaseHTTPRequestHandler,
    raw_path: str,
    archive_root: Path,
    archive_base: str,
    *,
    listing: bool = True,
) -> None:
    """Serve a CI archive file, or an HTML directory listing, under ``archive_base``.

    Lets PR authors browse and download the full per-delivery report
    (``report.md`` / ``static-result.json`` / ``ci-summary.json`` and the
    per-Function ``out/<sha>/<func_id>/`` tree) that the PR comment only
    samples. Path traversal outside ``archive_root`` resolves to a 404. Unlike
    the Docusaurus site route, directory requests render a listing rather than
    an ``index.html`` — set ``listing=False`` to 404 them instead, so the tree
    cannot be walked (and bulk-downloaded) from a single entry URL. Callers are
    responsible for archive authorization and rate limiting before calling this.
    """
    url_path = raw_path.split("?", 1)[0]
    rel = url_path[len(archive_base):].lstrip("/")
    archive_root_resolved = archive_root.resolve()
    candidate = (archive_root_resolved / rel) if rel else archive_root_resolved
    try:
        resolved = candidate.resolve()
        resolved.relative_to(archive_root_resolved)
    except ValueError:
        _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
        return

    if resolved.is_dir():
        if not listing:
            _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
            return
        _serve_archive_listing(handler, resolved, url_path)
        return
    if not resolved.is_file():
        _json_response(handler, 404, {"status": "error", "code": "NOT_FOUND"})
        return

    content_type, _ = mimetypes.guess_type(str(resolved))
    if content_type is None:
        # Serve .md and other unknown text as UTF-8 text so browsers render it
        # inline instead of forcing a download of mojibake.
        content_type = "text/plain; charset=utf-8" if resolved.suffix == ".md" else "application/octet-stream"
    elif content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
        content_type = f"{content_type}; charset=utf-8"
    _send_file(handler, resolved, content_type)


def _serve_archive_listing(handler: BaseHTTPRequestHandler, directory: Path, url_path: str) -> None:
    """Render a minimal HTML directory listing for an archive directory."""
    base = url_path if url_path.endswith("/") else url_path + "/"
    entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))
    rows = ['<li><a href="../">../</a></li>']
    for entry in entries:
        name = entry.name + ("/" if entry.is_dir() else "")
        href = html.escape(base + name, quote=True)
        rows.append(f'<li><a href="{href}">{html.escape(name)}</a></li>')
    body = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(url_path)}</title></head><body>"
        f"<h1>Index of {html.escape(url_path)}</h1><ul>{''.join(rows)}</ul>"
        "</body></html>"
    ).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    # Listings reflect live directory contents; never let a proxy hold them.
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def create_server(
    host: str,
    port: int,
    *,
    store: ReceiptStore,
    token: str | None = None,
    signature_secret: str | None = None,
    webhook_path: str = DEFAULT_WEBHOOK_PATH,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
    site_root: Path | None = None,
    site_base_path: str = DEFAULT_SITE_BASE_PATH,
    archive_root: Path | None = None,
    archive_token: str | None = None,
    archive_listing: bool = True,
    archive_rate_limit: int = 0,
    archive_rate_window: float = DEFAULT_ARCHIVE_RATE_WINDOW,
    trust_forwarded_for: bool = False,
) -> ThreadingHTTPServer:
    """Create a configured HTTP server without starting its event loop."""

    if not webhook_path.startswith("/"):
        raise ValueError("webhook_path must start with /")
    if max_body_bytes <= 0:
        raise ValueError("max_body_bytes must be positive")
    if not site_base_path.startswith("/"):
        raise ValueError("site_base_path must start with /")
    if site_root is not None and not site_root.is_dir():
        # The build dir is produced by the first merge-rebuild; until it
        # exists, /arkui_specs simply 404s at request time. Do not abort
        # startup, or the webhook can never receive the merge that builds it.
        LOGGER.warning(
            "site_root %s does not exist yet; %s will 404 until a rebuild creates it",
            site_root, site_base_path,
        )
    # Per-delivery CI archives are served at <site_base_path>/ci/... . This is a
    # sub-path of the site base, so it must be matched before the site route.
    archive_base = f"{site_base_path.rstrip('/')}/{ARCHIVE_URL_SEGMENT}"
    archive_limiter = (
        RateLimiter(archive_rate_limit, archive_rate_window) if archive_rate_limit > 0 else None
    )

    class GitCodeWebhookHandler(BaseHTTPRequestHandler):
        server_version = "ArkUISpecEvalWebhook/0.1"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            LOGGER.info(
                "http client=%s message=%s",
                client_identity(self, trust_forwarded_for=trust_forwarded_for),
                format % args,
            )

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            url_path = self.path.split("?", 1)[0]
            # Archive route first: <site_base_path>/ci/... is a sub-path of the
            # site base, so the more specific prefix must win.
            if archive_root is not None and (url_path == archive_base or url_path.startswith(archive_base + "/")):
                client = client_identity(self, trust_forwarded_for=trust_forwarded_for)
                if not _archive_authorized(self, archive_token):
                    LOGGER.warning("archive unauthorized client=%s path=%s", client, url_path)
                    _json_response(
                        self,
                        401,
                        {
                            "status": "error",
                            "code": "ARCHIVE_UNAUTHORIZED",
                            "message": f"archive access requires the {ARCHIVE_TOKEN_HEADER} header or ?token=",
                        },
                    )
                    return
                if archive_limiter is not None and not archive_limiter.allow(client):
                    LOGGER.warning("archive rate limited client=%s path=%s", client, url_path)
                    _json_response(
                        self,
                        429,
                        {
                            "status": "error",
                            "code": "ARCHIVE_RATE_LIMITED",
                            "message": (
                                f"archive requests limited to {archive_rate_limit} per "
                                f"{int(archive_rate_window)}s per client"
                            ),
                        },
                        extra_headers={"Retry-After": str(max(1, int(archive_rate_window)))},
                    )
                    return
                _serve_archive_path(
                    self, self.path, archive_root, archive_base, listing=archive_listing
                )
                return
            if site_root is not None and (url_path == site_base_path or url_path.startswith(site_base_path + "/")):
                _serve_site_path(self, self.path, site_root, site_base_path)
                return
            if self.path not in {"/healthz", webhook_path}:
                _json_response(self, 404, {"status": "error", "code": "NOT_FOUND"})
                return
            _json_response(self, 200, {"status": "ok", "webhook_path": webhook_path})

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path != webhook_path:
                _json_response(self, 404, {"status": "error", "code": "NOT_FOUND"})
                return
            try:
                content_type = self.headers.get_content_type()
                if content_type != "application/json":
                    raise WebhookRequestError(415, "UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json")
                content_length = self.headers.get("Content-Length")
                if content_length is None:
                    raise WebhookRequestError(411, "CONTENT_LENGTH_REQUIRED", "Content-Length is required")
                try:
                    body_length = int(content_length)
                except ValueError as error:
                    raise WebhookRequestError(400, "INVALID_CONTENT_LENGTH", "invalid Content-Length") from error
                if body_length < 0 or body_length > max_body_bytes:
                    raise WebhookRequestError(413, "PAYLOAD_TOO_LARGE", "webhook payload exceeds size limit")
                raw_body = self.rfile.read(body_length)
                verify_authentication(
                    self.headers,
                    raw_body,
                    token=token,
                    signature_secret=signature_secret,
                )
                try:
                    payload = json.loads(raw_body)
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise WebhookRequestError(400, "INVALID_JSON", "request body must be valid UTF-8 JSON") from error
                if not isinstance(payload, dict):
                    raise WebhookRequestError(400, "INVALID_PAYLOAD", "request body must be a JSON object")
                event_name = _required_string(
                    _header(self.headers, "X-GitCode-Event"),
                    "X-GitCode-Event",
                )
                if event_name != MERGE_REQUEST_EVENT:
                    delivery_id = _header(self.headers, "X-GitCode-Delivery")
                    LOGGER.info("ignored delivery=%s event=%s", delivery_id, event_name)
                    _json_response(
                        self,
                        202,
                        {
                            "status": "ignored",
                            "delivery_id": delivery_id or None,
                            "event": event_name,
                        },
                    )
                    return
                receipt = build_receipt(self.headers, payload)
                created = store.append(receipt)
                LOGGER.info(
                    "delivery=%s project=%s pr=%s action=%s duplicate=%s",
                    receipt["delivery_id"],
                    receipt["project"]["path_with_namespace"],
                    receipt["pull_request"]["iid"],
                    receipt["action"],
                    not created,
                )
                _json_response(
                    self,
                    202,
                    {
                        "status": "accepted",
                        "delivery_id": receipt["delivery_id"],
                        "duplicate": not created,
                        "action": receipt["action"],
                    },
                )
            except WebhookRequestError as error:
                LOGGER.warning("rejected code=%s message=%s", error.code, error)
                _json_response(self, error.status, {"status": "error", "code": error.code, "message": str(error)})
            except OSError as error:
                LOGGER.exception("failed to persist webhook receipt")
                _json_response(
                    self,
                    500,
                    {"status": "error", "code": "RECEIPT_WRITE_FAILED", "message": str(error)},
                )

    server = ThreadingHTTPServer((host, port), GitCodeWebhookHandler)
    server.daemon_threads = True
    return server


def _is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Receive GitCode Merge Request webhook messages")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--path", default=DEFAULT_WEBHOOK_PATH, help="Webhook endpoint path")
    parser.add_argument("--events-file", type=Path, default=DEFAULT_EVENTS_FILE)
    parser.add_argument("--max-body-bytes", type=int, default=DEFAULT_MAX_BODY_BYTES)
    parser.add_argument("--site-root", type=Path, default=None,
                        help="Directory of the rebuilt Docusaurus site to serve at --site-base-path (default: site not served)")
    parser.add_argument("--site-base-path", default=DEFAULT_SITE_BASE_PATH,
                        help=f"URL path prefix for the served site (default {DEFAULT_SITE_BASE_PATH})")
    parser.add_argument("--archive-root", type=Path, default=None,
                        help=("Directory of per-delivery CI archives (ci_worker --output-root, "
                              f"e.g. specs/.evaluator/ci) to serve at <site-base-path>/{ARCHIVE_URL_SEGMENT} "
                              "for full-report browsing/download (default: not served)"))
    parser.add_argument("--archive-token-env", default=DEFAULT_ARCHIVE_TOKEN_ENV,
                        help=("Environment variable holding a shared token required to read the "
                              f"archive route, via the {ARCHIVE_TOKEN_HEADER} header or ?token= "
                              f"(default {DEFAULT_ARCHIVE_TOKEN_ENV}; unset = public archives)"))
    parser.add_argument("--no-archive-listing", dest="archive_listing", action="store_false",
                        help="404 archive directory requests instead of rendering a browsable listing")
    parser.add_argument("--archive-rate-limit", type=int, default=DEFAULT_ARCHIVE_RATE_LIMIT,
                        help=("Max archive requests per client per --archive-rate-window "
                              f"(default {DEFAULT_ARCHIVE_RATE_LIMIT}; 0 disables)"))
    parser.add_argument("--archive-rate-window", type=float, default=DEFAULT_ARCHIVE_RATE_WINDOW,
                        help=f"Archive rate-limit window in seconds (default {DEFAULT_ARCHIVE_RATE_WINDOW})")
    parser.add_argument("--trust-forwarded-for", action="store_true",
                        help=("Log and rate-limit against the left-most X-Forwarded-For entry when the "
                              "peer is loopback. Only enable behind a reverse proxy that sets it; "
                              "otherwise clients can spoof the header"))
    parser.add_argument("--token-env", default="GITCODE_WEBHOOK_TOKEN")
    parser.add_argument("--signature-secret-env", default="GITCODE_WEBHOOK_SIGNATURE_SECRET")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    token = os.environ.get(args.token_env) or None
    signature_secret = os.environ.get(args.signature_secret_env) or None
    archive_token = (os.environ.get(args.archive_token_env) or "").strip() or None
    if not token and not signature_secret and not _is_loopback_host(args.host):
        parser.error("non-loopback listeners require a webhook token or signature secret")
    try:
        store = ReceiptStore(args.events_file)
        server = create_server(
            args.host,
            args.port,
            store=store,
            token=token,
            signature_secret=signature_secret,
            webhook_path=args.path,
            max_body_bytes=args.max_body_bytes,
            site_root=args.site_root,
            site_base_path=args.site_base_path,
            archive_root=args.archive_root,
            archive_token=archive_token,
            archive_listing=args.archive_listing,
            archive_rate_limit=args.archive_rate_limit,
            archive_rate_window=args.archive_rate_window,
            trust_forwarded_for=args.trust_forwarded_for,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    LOGGER.info(
        "listening host=%s port=%s path=%s receipts=%s token=%s signature=%s "
        "archive_token=%s archive_listing=%s archive_rate=%s/%ss",
        args.host,
        server.server_address[1],
        args.path,
        args.events_file,
        bool(token),
        bool(signature_secret),
        bool(archive_token),
        args.archive_listing,
        args.archive_rate_limit,
        int(args.archive_rate_window),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
