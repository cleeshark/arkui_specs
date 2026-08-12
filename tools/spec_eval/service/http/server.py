"""HTTP server (TASK-011-06): a stdlib threading server around route_request.

Binds loopback by default. The handler is a thin adapter: it reads the request
body, delegates to :func:`route_request`, and writes the :class:`Response`. All
policy (auth, routing, path safety) lives in ``routes``/``security``.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .routes import Response, route_request


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        self._handle("GET", b"")

    def do_HEAD(self) -> None:  # noqa: N802 - http.server API
        self._handle("HEAD", b"")

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        self._handle("POST", self._read_body())

    def _handle(self, method: str, body: bytes) -> None:
        app = self.server.app  # type: ignore[attr-defined]
        resp = route_request(method, self.path, body, dict(self.headers), app)
        self.send_response(resp.status)
        self.send_header("Content-Type", resp.content_type)
        self.send_header("Content-Length", str(len(resp.body)))
        for key, value in resp.headers.items():
            self.send_header(key, value)
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(resp.body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length > 0 else b""

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002 - silence default logging
        return


class SemanticHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(app: Any, host: str = "127.0.0.1", port: int = 0) -> SemanticHTTPServer:
    """Create a threading HTTP server bound to ``host:port`` serving ``app``."""
    server = SemanticHTTPServer((host, port), _Handler)
    server.app = app  # type: ignore[attr-defined]
    return server
