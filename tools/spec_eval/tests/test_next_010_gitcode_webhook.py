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
                self.assertEqual(json.loads(response.read()), {"status": "ok"})
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


if __name__ == "__main__":
    unittest.main()
