from __future__ import annotations

import contextlib
import hashlib
import hmac
import http.client
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from spec_eval import gitcode_webhook
from spec_eval.gitcode_webhook import (
    MERGE_REQUEST_EVENT,
    ReceiptStore,
    WebhookRequestError,
    build_receipt,
    create_server,
    verify_authentication,
)


class Next010GitCodeWebhookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_path = (
            Path(__file__).parent / "fixtures" / "gitcode" / "merge-request-open.json"
        )
        cls.payload = json.loads(cls.fixture_path.read_text(encoding="utf-8"))
        cls.raw_body = json.dumps(cls.payload, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def headers(delivery_id: str = "delivery-001", token: str | None = None) -> dict[str, str]:
        values = {
            "Content-Type": "application/json",
            "X-GitCode-Event": MERGE_REQUEST_EVENT,
            "X-GitCode-Delivery": delivery_id,
        }
        if token is not None:
            values["X-GitCode-Token"] = token
        return values

    def test_build_receipt_keeps_ci_fields_and_omits_description_and_author(self) -> None:
        receipt = build_receipt(
            self.headers(),
            self.payload,
            received_at="2026-08-10T12:00:00Z",
        )
        self.assertEqual(receipt["delivery_id"], "delivery-001")
        self.assertEqual(receipt["project"]["path_with_namespace"], "arkui_architecture/arkui-specs")
        self.assertEqual(receipt["pull_request"]["iid"], 27)
        self.assertEqual(receipt["pull_request"]["source_branch"], "feature/waterflow-spec")
        self.assertEqual(receipt["revisions"]["tested"], self.payload["git_commit_no"])
        self.assertEqual(receipt["revisions"]["target"], self.payload["git_target_branch_commit_no"])
        serialized = json.dumps(receipt)
        self.assertNotIn("description", serialized)
        self.assertNotIn("author", serialized)

    def test_update_falls_back_to_last_commit_when_top_level_revision_is_empty(self) -> None:
        payload = json.loads(json.dumps(self.payload))
        payload["git_commit_no"] = ""
        payload["git_target_branch_commit_no"] = ""
        receipt = build_receipt(self.headers(), payload)
        self.assertEqual(receipt["revisions"]["tested"], payload["object_attributes"]["last_commit"]["id"])
        self.assertIsNone(receipt["revisions"]["target"])

    def test_token_and_signature_authentication(self) -> None:
        signature_secret = "signature-secret"
        signature = "sha256=" + hmac.new(
            signature_secret.encode("utf-8"), self.raw_body, hashlib.sha256
        ).hexdigest()
        verify_authentication(
            {
                "X-GitCode-Token": "token-value",
                "X-GitCode-Signature-256": signature,
            },
            self.raw_body,
            token="token-value",
            signature_secret=signature_secret,
        )
        with self.assertRaises(WebhookRequestError) as context:
            verify_authentication(
                {"X-GitCode-Token": "wrong"},
                self.raw_body,
                token="token-value",
                signature_secret=None,
            )
        self.assertEqual(context.exception.status, 401)
        self.assertEqual(context.exception.code, "INVALID_TOKEN")

    def test_delivery_deduplication_survives_store_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.ndjson"
            receipt = build_receipt(self.headers(), self.payload)
            self.assertTrue(ReceiptStore(receipt_path).append(receipt))
            self.assertFalse(ReceiptStore(receipt_path).append(receipt))
            self.assertEqual(len(receipt_path.read_text(encoding="utf-8").splitlines()), 1)

    def test_cli_rejects_unsigned_non_loopback_listener(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                gitcode_webhook.main(["--host", "0.0.0.0", "--port", "0"])
        self.assertEqual(context.exception.code, 2)

    def test_http_receiver_accepts_health_message_and_deduplicates_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.ndjson"
            server = create_server(
                "127.0.0.1",
                0,
                store=ReceiptStore(receipt_path),
                token="token-value",
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                connection.request("GET", "/healthz")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(
                    json.loads(response.read()),
                    {"status": "ok", "webhook_path": "/webhooks/gitcode"},
                )
                connection.close()

                connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                connection.request("GET", "/webhooks/gitcode")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(
                    json.loads(response.read()),
                    {"status": "ok", "webhook_path": "/webhooks/gitcode"},
                )
                connection.close()

                first = self._post(server, self.headers(token="token-value"))
                self.assertEqual(first[0], 202)
                self.assertFalse(first[1]["duplicate"])

                duplicate = self._post(server, self.headers(token="token-value"))
                self.assertEqual(duplicate[0], 202)
                self.assertTrue(duplicate[1]["duplicate"])

                receipts = [
                    json.loads(line)
                    for line in receipt_path.read_text(encoding="utf-8").splitlines()
                    if line
                ]
                self.assertEqual(len(receipts), 1)
                self.assertEqual(receipts[0]["delivery_id"], "delivery-001")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_receiver_rejects_invalid_token_without_writing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.ndjson"
            server = create_server(
                "127.0.0.1",
                0,
                store=ReceiptStore(receipt_path),
                token="token-value",
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertLogs("spec_eval.gitcode_webhook", level="WARNING"):
                    status, response = self._post(server, self.headers(token="wrong"))
                self.assertEqual(status, 401)
                self.assertEqual(response["code"], "INVALID_TOKEN")
                self.assertFalse(receipt_path.exists())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_receiver_acknowledges_non_merge_request_events_without_persisting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.ndjson"
            server = create_server(
                "127.0.0.1",
                0,
                store=ReceiptStore(receipt_path),
                token="token-value",
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                headers = self.headers(token="token-value")
                headers["X-GitCode-Event"] = "Push Hook"
                status, response = self._post(server, headers)
                self.assertEqual(status, 202)
                self.assertEqual(response["status"], "ignored")
                self.assertEqual(response["event"], "Push Hook")
                self.assertFalse(receipt_path.exists())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def _post(
        self,
        server,
        headers: dict[str, str],
    ) -> tuple[int, dict[str, object]]:
        connection = http.client.HTTPConnection(*server.server_address, timeout=5)
        connection.request("POST", "/webhooks/gitcode", body=self.raw_body, headers=headers)
        response = connection.getresponse()
        value = json.loads(response.read())
        connection.close()
        return response.status, value


class SiteStaticServeTest(unittest.TestCase):
    """The webhook server optionally serves the rebuilt Docusaurus site at a path."""

    def setUp(self) -> None:
        self._servers: list = []

    def tearDown(self) -> None:
        for server, thread in self._servers:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def _serve(self, site_root: Path | None) -> tuple:
        receipts = Path(tempfile.mkdtemp()) / "receipts.ndjson"
        kwargs: dict = {"store": ReceiptStore(receipts)}
        if site_root is not None:
            kwargs["site_root"] = site_root
        server = create_server("127.0.0.1", 0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self._servers.append((server, thread))
        return server

    @staticmethod
    def _get(server: tuple, path: str) -> tuple[int, bytes, str]:
        connection = http.client.HTTPConnection(*server.server_address, timeout=5)
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        content_type = response.getheader("Content-Type", "")
        connection.close()
        return response.status, body, content_type

    def test_serves_index_and_asset_with_content_type(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "assets").mkdir()
            (root / "index.html").write_text("<html>home</html>", encoding="utf-8")
            (root / "assets" / "style.css").write_text("body{}", encoding="utf-8")
            server = self._serve(root)
            status, body, content_type = self._get(server, "/arkui_specs/")
            self.assertEqual(status, 200)
            self.assertIn(b"home", body)
            self.assertIn("text/html", content_type)
            status, body, content_type = self._get(server, "/arkui_specs/assets/style.css")
            self.assertEqual(status, 200)
            self.assertEqual(body, b"body{}")
            self.assertIn("text/css", content_type)

    def test_serves_docusaurus_clean_url_from_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            page = b"<html>spec evaluation</html>"
            (root / "spec-evaluation.html").write_bytes(page)
            server = self._serve(root)

            status, body, content_type = self._get(
                server, "/arkui_specs/spec-evaluation"
            )
            self.assertEqual(status, 200)
            self.assertEqual(body, page)
            self.assertIn("text/html", content_type)

            status, body, _ = self._get(
                server, "/arkui_specs/spec-evaluation.html"
            )
            self.assertEqual(status, 200)
            self.assertEqual(body, page)

    def test_clean_url_fallback_keeps_trailing_slash_as_directory(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "spec-evaluation.html").write_text("page", encoding="utf-8")
            server = self._serve(root)

            status, _, _ = self._get(server, "/arkui_specs/spec-evaluation/")
            self.assertEqual(status, 404)

    def test_clean_url_fallback_rechecks_site_root(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            root = directory / "site"
            root.mkdir()
            outside = directory / "outside.html"
            outside.write_text("secret", encoding="utf-8")
            (root / "escaped.html").symlink_to(outside)
            server = self._serve(root)

            status, _, _ = self._get(server, "/arkui_specs/escaped")
            self.assertEqual(status, 404)

    def test_traversal_outside_site_root_is_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "index.html").write_text("ok", encoding="utf-8")
            server = self._serve(root)
            status, _, _ = self._get(server, "/arkui_specs/../../../../etc/passwd")
            self.assertEqual(status, 404)

    def test_site_root_none_is_backward_compatible(self) -> None:
        server = self._serve(None)
        status, _, _ = self._get(server, "/arkui_specs/")
        self.assertEqual(status, 404)
        status, _, _ = self._get(server, "/healthz")
        self.assertEqual(status, 200)

    def test_missing_site_root_dir_starts_and_404s(self) -> None:
        # Fresh deploy: build dir is absent until the first merge-rebuild.
        # The server must still start, and /arkui_specs/ 404s at request time.
        missing = Path(tempfile.mkdtemp()) / "never-built"
        server = self._serve(missing)
        status, _, _ = self._get(server, "/arkui_specs/")
        self.assertEqual(status, 404)
        status, _, _ = self._get(server, "/healthz")
        self.assertEqual(status, 200)

    def test_healthz_and_site_coexist(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "index.html").write_text("<html>x</html>", encoding="utf-8")
            server = self._serve(root)
            status, _, _ = self._get(server, "/healthz")
            self.assertEqual(status, 200)
            status, _, _ = self._get(server, "/arkui_specs/")
            self.assertEqual(status, 200)


class ArchiveServeTest(unittest.TestCase):
    """The webhook server serves per-delivery CI archives at <base>/ci/... ."""

    def setUp(self) -> None:
        self._servers: list = []

    def tearDown(self) -> None:
        for server, thread in self._servers:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def _serve(self, *, archive_root: Path | None = None, site_root: Path | None = None, **extra):
        receipts = Path(tempfile.mkdtemp()) / "receipts.ndjson"
        kwargs: dict = {"store": ReceiptStore(receipts)}
        if archive_root is not None:
            kwargs["archive_root"] = archive_root
        if site_root is not None:
            kwargs["site_root"] = site_root
        kwargs.update(extra)
        server = create_server("127.0.0.1", 0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self._servers.append((server, thread))
        return server

    @classmethod
    def _get(cls, server, path: str, headers: dict[str, str] | None = None) -> tuple[int, bytes, str]:
        status, body, response_headers = cls._request(server, path, headers)
        return status, body, response_headers.get("Content-Type", "")

    @staticmethod
    def _request(
        server, path: str, headers: dict[str, str] | None = None
    ) -> tuple[int, bytes, dict[str, str]]:
        connection = http.client.HTTPConnection(*server.server_address, timeout=5)
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        response_headers = {key: value for key, value in response.getheaders()}
        connection.close()
        return response.status, body, response_headers

    def _delivery(self) -> Path:
        root = Path(tempfile.mkdtemp())
        d = root / "pr-225" / "225_abc"
        (d / "out" / "sha1" / "03-01-01").mkdir(parents=True)
        (d / "ci-summary.json").write_text('{"affected_function_count": 1}', encoding="utf-8")
        (d / "out" / "sha1" / "03-01-01" / "report.md").write_text("# full report\n", encoding="utf-8")
        return root

    def test_serves_archive_file_as_utf8(self) -> None:
        root = self._delivery()
        server = self._serve(archive_root=root)
        status, body, content_type = self._get(
            server, "/arkui_specs/ci/pr-225/225_abc/out/sha1/03-01-01/report.md"
        )
        self.assertEqual(status, 200)
        self.assertIn(b"full report", body)
        self.assertIn("charset=utf-8", content_type)

    def test_serves_json_finding_summary(self) -> None:
        root = self._delivery()
        server = self._serve(archive_root=root)
        status, body, content_type = self._get(server, "/arkui_specs/ci/pr-225/225_abc/ci-summary.json")
        self.assertEqual(status, 200)
        self.assertIn(b"affected_function_count", body)
        self.assertIn("application/json", content_type)

    def test_directory_listing_links_entries(self) -> None:
        root = self._delivery()
        server = self._serve(archive_root=root)
        status, body, content_type = self._get(server, "/arkui_specs/ci/pr-225/225_abc/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"ci-summary.json", body)
        self.assertIn(b"out/", body)  # subdirectory linked with trailing slash

    def test_traversal_outside_archive_root_is_404(self) -> None:
        root = self._delivery()
        server = self._serve(archive_root=root)
        status, _, _ = self._get(server, "/arkui_specs/ci/../../../../etc/passwd")
        self.assertEqual(status, 404)

    def test_archive_route_wins_over_site_route(self) -> None:
        # /arkui_specs/ci is a sub-path of the site base; the archive must win.
        archive = self._delivery()
        with tempfile.TemporaryDirectory() as site_dir:
            site = Path(site_dir)
            (site / "index.html").write_text("<html>site</html>", encoding="utf-8")
            server = self._serve(archive_root=archive, site_root=site)
            status, body, _ = self._get(server, "/arkui_specs/ci/pr-225/225_abc/ci-summary.json")
            self.assertEqual(status, 200)
            self.assertIn(b"affected_function_count", body)
            # site route still works for non-ci paths
            status, body, _ = self._get(server, "/arkui_specs/")
            self.assertEqual(status, 200)
            self.assertIn(b"site", body)

    def test_archive_root_none_is_404(self) -> None:
        server = self._serve(archive_root=None)
        status, _, _ = self._get(server, "/arkui_specs/ci/pr-225/225_abc/ci-summary.json")
        self.assertEqual(status, 404)

    def test_archive_file_revalidates_with_etag_and_304(self) -> None:
        server = self._serve(archive_root=self._delivery())
        path = "/arkui_specs/ci/pr-225/225_abc/ci-summary.json"
        status, body, headers = self._request(server, path)
        self.assertEqual(status, 200)
        self.assertTrue(headers["ETag"].startswith('W/"'))
        self.assertEqual(headers["Cache-Control"], "no-cache")
        status, cached_body, _ = self._request(server, path, {"If-None-Match": headers["ETag"]})
        self.assertEqual(status, 304)
        self.assertEqual(cached_body, b"")
        self.assertNotEqual(body, b"")

    def test_if_modified_since_returns_304(self) -> None:
        server = self._serve(archive_root=self._delivery())
        path = "/arkui_specs/ci/pr-225/225_abc/ci-summary.json"
        _, _, headers = self._request(server, path)
        status, _, _ = self._request(server, path, {"If-Modified-Since": headers["Last-Modified"]})
        self.assertEqual(status, 304)

    def test_stale_etag_re_sends_body(self) -> None:
        server = self._serve(archive_root=self._delivery())
        path = "/arkui_specs/ci/pr-225/225_abc/ci-summary.json"
        status, body, _ = self._request(server, path, {"If-None-Match": 'W/"0-0"'})
        self.assertEqual(status, 200)
        self.assertIn(b"affected_function_count", body)

    def test_listing_is_not_cached(self) -> None:
        server = self._serve(archive_root=self._delivery())
        status, _, headers = self._request(server, "/arkui_specs/ci/pr-225/225_abc/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_listing_can_be_disabled(self) -> None:
        server = self._serve(archive_root=self._delivery(), archive_listing=False)
        status, _, _ = self._get(server, "/arkui_specs/ci/pr-225/225_abc/")
        self.assertEqual(status, 404)
        # files stay reachable when listings are off
        status, _, _ = self._get(server, "/arkui_specs/ci/pr-225/225_abc/ci-summary.json")
        self.assertEqual(status, 200)

    def test_archive_token_gates_access(self) -> None:
        server = self._serve(archive_root=self._delivery(), archive_token="s3cret")
        path = "/arkui_specs/ci/pr-225/225_abc/ci-summary.json"
        status, _, _ = self._get(server, path)
        self.assertEqual(status, 401)
        status, _, _ = self._get(server, path, {"X-Archive-Token": "wrong"})
        self.assertEqual(status, 401)
        status, body, _ = self._get(server, path, {"X-Archive-Token": "s3cret"})
        self.assertEqual(status, 200)
        self.assertIn(b"affected_function_count", body)
        status, _, _ = self._get(server, path + "?token=s3cret")
        self.assertEqual(status, 200)

    def test_archive_rate_limit_returns_429(self) -> None:
        server = self._serve(archive_root=self._delivery(), archive_rate_limit=2)
        path = "/arkui_specs/ci/pr-225/225_abc/ci-summary.json"
        codes = [self._get(server, path)[0] for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_healthz_is_not_rate_limited(self) -> None:
        server = self._serve(archive_root=self._delivery(), archive_rate_limit=1)
        self._get(server, "/arkui_specs/ci/pr-225/225_abc/ci-summary.json")
        for _ in range(3):
            self.assertEqual(self._get(server, "/healthz")[0], 200)


class RateLimiterTest(unittest.TestCase):
    """Sliding-window accounting for the archive route."""

    def test_window_expiry_frees_budget(self) -> None:
        limiter = gitcode_webhook.RateLimiter(2, 60.0)
        self.assertTrue(limiter.allow("a", now=0.0))
        self.assertTrue(limiter.allow("a", now=1.0))
        self.assertFalse(limiter.allow("a", now=2.0))
        self.assertTrue(limiter.allow("a", now=61.5))

    def test_clients_are_counted_separately(self) -> None:
        limiter = gitcode_webhook.RateLimiter(1, 60.0)
        self.assertTrue(limiter.allow("a", now=0.0))
        self.assertFalse(limiter.allow("a", now=0.0))
        self.assertTrue(limiter.allow("b", now=0.0))

    def test_zero_limit_disables_limiting(self) -> None:
        limiter = gitcode_webhook.RateLimiter(0, 60.0)
        self.assertTrue(all(limiter.allow("a", now=0.0) for _ in range(10)))

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            gitcode_webhook.RateLimiter(-1, 60.0)
        with self.assertRaises(ValueError):
            gitcode_webhook.RateLimiter(1, 0.0)


class ClientIdentityTest(unittest.TestCase):
    """X-Forwarded-For is honoured only for loopback peers, and only when trusted."""

    class _Handler:
        def __init__(self, peer: str, forwarded: str | None = None) -> None:
            self.client_address = (peer, 4242)
            self.headers = {"X-Forwarded-For": forwarded} if forwarded else {}

    def test_untrusted_mode_uses_peer(self) -> None:
        handler = self._Handler("127.0.0.1", "203.0.113.9")
        self.assertEqual(
            gitcode_webhook.client_identity(handler, trust_forwarded_for=False), "127.0.0.1"
        )

    def test_trusted_loopback_uses_leftmost_forwarded_entry(self) -> None:
        handler = self._Handler("127.0.0.1", "203.0.113.9, 10.0.0.1")
        self.assertEqual(
            gitcode_webhook.client_identity(handler, trust_forwarded_for=True), "203.0.113.9"
        )

    def test_non_loopback_peer_ignores_forwarded_header(self) -> None:
        handler = self._Handler("198.51.100.4", "203.0.113.9")
        self.assertEqual(
            gitcode_webhook.client_identity(handler, trust_forwarded_for=True), "198.51.100.4"
        )

    def test_garbage_forwarded_value_falls_back_to_peer(self) -> None:
        handler = self._Handler("127.0.0.1", "not-an-ip")
        self.assertEqual(
            gitcode_webhook.client_identity(handler, trust_forwarded_for=True), "127.0.0.1"
        )


if __name__ == "__main__":
    unittest.main()
