#!/usr/bin/env python3
"""Minimal GitCode Merge Request webhook receiver for report-only CI."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import logging
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

    requires_revisions = action in {"open", "update"}
    tested_revision = _optional_sha(payload.get("git_commit_no"), "git_commit_no", required=requires_revisions)
    target_revision = _optional_sha(
        payload.get("git_target_branch_commit_no"),
        "git_target_branch_commit_no",
        required=requires_revisions,
    )
    last_commit = attributes.get("last_commit")
    source_revision = None
    if isinstance(last_commit, dict):
        source_revision = _optional_sha(last_commit.get("id"), "object_attributes.last_commit.id", required=False)

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


def create_server(
    host: str,
    port: int,
    *,
    store: ReceiptStore,
    token: str | None = None,
    signature_secret: str | None = None,
    webhook_path: str = DEFAULT_WEBHOOK_PATH,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> ThreadingHTTPServer:
    """Create a configured HTTP server without starting its event loop."""

    if not webhook_path.startswith("/"):
        raise ValueError("webhook_path must start with /")
    if max_body_bytes <= 0:
        raise ValueError("max_body_bytes must be positive")

    class GitCodeWebhookHandler(BaseHTTPRequestHandler):
        server_version = "ArkUISpecEvalWebhook/0.1"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            LOGGER.info("http client=%s message=%s", self.client_address[0], format % args)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path != "/healthz":
                _json_response(self, 404, {"status": "error", "code": "NOT_FOUND"})
                return
            _json_response(self, 200, {"status": "ok"})

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
