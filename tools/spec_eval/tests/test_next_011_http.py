"""Host unit + end-to-end tests for the Phase 3 HTTP API (TASK-011-06).

Routes are tested via the pure ``route_request`` function (no sockets). One test
starts a real ``SemanticHTTPServer`` on an ephemeral port and exercises it over
HTTP with ``urllib``.

    python3 -m unittest spec_eval.tests.test_next_011_http -v
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from spec_eval.service.app import SemanticServiceApp
from spec_eval.service.domain.models import Artifact
from spec_eval.service.http.routes import route_request
from spec_eval.service.http.server import make_server
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import ArtifactRepository, JobRepository
from spec_eval.service.store.sqlite_store import utc_now


def _no_op_runner(job_id: str, cancel: threading.Event) -> None:
    """A job_runner that does nothing (the dispatcher is not started for route tests)."""
    return None


class _HttpTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.app = SemanticServiceApp(
            self.settings, max_workers=1, job_runner=_no_op_runner, token=None
        )
        # dispatcher intentionally not started: jobs stay queued

    def tearDown(self) -> None:
        self.app.stop()
        self.tmp.cleanup()

    def _req(self, method: str, path: str, body=None, headers=None) -> tuple[int, object]:
        raw_body = b"" if body is None else json.dumps(body).encode("utf-8")
        resp = route_request(method, path, raw_body, headers or {}, self.app)
        try:
            parsed = json.loads(resp.body.decode("utf-8")) if resp.body else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = resp.body.decode("utf-8", "replace")
        return resp.status, parsed


class CreateListDetailTest(_HttpTestBase):
    def test_create_then_list_then_detail(self) -> None:
        status, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        self.assertEqual(status, 201)
        self.assertEqual(job["func_id"], "04-01-01")
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["timing"]["duration_ms"], 0)
        self.assertFalse(job["usage"]["reported"])
        job_id = job["job_id"]

        status, jobs = self._req("GET", "/api/jobs")
        self.assertEqual(status, 200)
        self.assertTrue(any(j["job_id"] == job_id for j in jobs))

        status, detail = self._req("GET", f"/api/jobs/{job_id}")
        self.assertEqual(status, 200)
        self.assertEqual(detail["job_id"], job_id)
        self.assertIn("executor_duration_ms", detail["timing"])
        self.assertIn("total_tokens", detail["usage"])

    def test_invalid_func_id_rejected(self) -> None:
        status, body = self._req("POST", "/api/jobs", {"func_id": "bad"})
        self.assertEqual(status, 400)
        self.assertIn("func_id", body["error"])

    def test_unknown_job_is_404(self) -> None:
        status, _ = self._req("GET", "/api/jobs/nope")
        self.assertEqual(status, 404)


class EventsTest(_HttpTestBase):
    def test_events_returned_with_seq(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-02-02"})
        status, events = self._req("GET", f"/api/jobs/{job['job_id']}/events")
        self.assertEqual(status, 200)
        types = [e["event_type"] for e in events]
        self.assertIn("job_created", types)
        self.assertIn("job_submitted", types)
        seqs = [e["seq"] for e in events]
        self.assertEqual(seqs, sorted(seqs))


class CancelRetryTest(_HttpTestBase):
    def test_cancel_running_job(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")
        self.assertEqual(status, 200)
        self.assertTrue(body["cancelled"])

    def test_retry_cancelled_job(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        # move to cancelled so retry is legal
        JobRepository(self.app.store).cancel(job["job_id"])
        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/retry")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "queued")


class ArtifactDownloadTest(_HttpTestBase):
    def test_artifact_served_within_data_root(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        target = self.settings.data_root / "evidence.json"
        target.write_text('{"ok": true}', encoding="utf-8")
        ArtifactRepository(self.app.store).record(
            Artifact(
                artifact_id="x", job_id=job["job_id"], kind="function_context",
                path=str(target), sha256="sha256:" + "0" * 64, size=12, created_at=utc_now(),
            )
        )
        status, _ = self._req("GET", f"/api/jobs/{job['job_id']}/artifacts/function_context")
        self.assertEqual(status, 200)

    def test_path_traversal_rejected(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        # record an artifact pointing outside the data root
        outside = Path(self.tmp.name + "_outside")
        outside.write_text("secret", encoding="utf-8")
        self.addCleanup(outside.unlink)
        ArtifactRepository(self.app.store).record(
            Artifact(
                artifact_id="y", job_id=job["job_id"], kind="leaked",
                path=str(outside), sha256="sha256:" + "0" * 64, size=6, created_at=utc_now(),
            )
        )
        status, _ = self._req("GET", f"/api/jobs/{job['job_id']}/artifacts/leaked")
        self.assertEqual(status, 404)

    def test_unknown_artifact_is_404(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        status, _ = self._req("GET", f"/api/jobs/{job['job_id']}/artifacts/no_such_kind")
        self.assertEqual(status, 404)


class TokenSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.app = SemanticServiceApp(
            self.settings, max_workers=1, job_runner=_no_op_runner, token="s3cret"
        )

    def tearDown(self) -> None:
        self.app.stop()
        self.tmp.cleanup()

    def test_missing_token_is_401(self) -> None:
        resp = route_request("GET", "/api/jobs", b"", {}, self.app)
        self.assertEqual(resp.status, 401)

    def test_wrong_token_is_401(self) -> None:
        resp = route_request("GET", "/api/jobs", b"", {"Authorization": "Bearer nope"}, self.app)
        self.assertEqual(resp.status, 401)

    def test_correct_token_allowed(self) -> None:
        resp = route_request("GET", "/api/jobs", b"", {"Authorization": "Bearer s3cret"}, self.app)
        self.assertEqual(resp.status, 200)


class StaticUITest(_HttpTestBase):
    def test_index_html_served(self) -> None:
        status, body = self._req("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Semantic Evaluation Service", body)

    def test_static_asset_served(self) -> None:
        status, _ = self._req("GET", "/static/style.css")
        self.assertEqual(status, 200)

    def test_ui_contains_execution_statistics_and_activity_animation(self) -> None:
        status, body = self._req("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Execution statistics", body)
        css_status, css = self._req("GET", "/static/style.css")
        self.assertEqual(css_status, 200)
        self.assertIn("@keyframes activity-spin", css)

    def test_static_traversal_rejected(self) -> None:
        status, _ = self._req("GET", "/static/../../etc/passwd")
        self.assertEqual(status, 404)


class EndToEndServerTest(unittest.TestCase):
    """Real HTTP over sockets against a running SemanticHTTPServer."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.app = SemanticServiceApp(
            self.settings, max_workers=1, job_runner=_no_op_runner, token=None
        )
        self.server = make_server(self.app, "127.0.0.1", 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.app.stop()
        self.tmp.cleanup()

    def _http(self, method: str, path: str, body=None) -> tuple[int, object]:
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = resp.read()
                try:
                    parsed = json.loads(raw) if raw else None
                except (json.JSONDecodeError, UnicodeDecodeError):
                    parsed = raw.decode("utf-8", "replace")
                return resp.status, parsed
        except urllib.error.HTTPError as exc:
            return exc.code, None

    def test_create_and_list_over_http(self) -> None:
        status, job = self._http("POST", "/api/jobs", {"func_id": "04-05-06"})
        self.assertEqual(status, 201)
        status, jobs = self._http("GET", "/api/jobs")
        self.assertEqual(status, 200)
        self.assertTrue(any(j["job_id"] == job["job_id"] for j in jobs))

    def test_index_served_over_http(self) -> None:
        status, _ = self._http("GET", "/")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
