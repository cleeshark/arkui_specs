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
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping


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


def _json_response(handler: BaseHTTPRequestHandler, status: int, value: dict[str, Any]) -> None:
    body = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


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
    data = candidate.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _serve_archive_path(
    handler: BaseHTTPRequestHandler,
    raw_path: str,
    archive_root: Path,
    archive_base: str,
) -> None:
    """Serve a CI archive file, or an HTML directory listing, under ``archive_base``.

    Lets PR authors browse and download the full per-delivery report
    (``report.md`` / ``static-result.json`` / ``ci-summary.json`` and the
    per-Function ``out/<sha>/<func_id>/`` tree) that the PR comment only
    samples. Public (unauthenticated) read; path traversal outside
    ``archive_root`` resolves to a 404. Unlike the Docusaurus site route,
    directory requests render a listing rather than an ``index.html``.
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
    data = resolved.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


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

    class GitCodeWebhookHandler(BaseHTTPRequestHandler):
        server_version = "ArkUISpecEvalWebhook/0.1"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            LOGGER.info("http client=%s message=%s", self.client_address[0], format % args)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            url_path = self.path.split("?", 1)[0]
            # Archive route first: <site_base_path>/ci/... is a sub-path of the
            # site base, so the more specific prefix must win.
            if archive_root is not None and (url_path == archive_base or url_path.startswith(archive_base + "/")):
                _serve_archive_path(self, self.path, archive_root, archive_base)
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
    parser.add_argument("--token-env", default="GITCODE_WEBHOOK_TOKEN")
    parser.add_argument("--signature-secret-env", default="GITCODE_WEBHOOK_SIGNATURE_SECRET")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    token = os.environ.get(args.token_env) or None
    signature_secret = os.environ.get(args.signature_secret_env) or None
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
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    LOGGER.info(
        "listening host=%s port=%s path=%s receipts=%s token=%s signature=%s",
        args.host,
        server.server_address[1],
        args.path,
        args.events_file,
        bool(token),
        bool(signature_secret),
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
