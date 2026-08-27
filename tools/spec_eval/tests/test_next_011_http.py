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
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from spec_eval.service.app import SemanticServiceApp
from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import Artifact
from spec_eval.service.http.routes import route_request
from spec_eval.service.http.server import make_server
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    ArtifactRepository,
    EventRepository,
    JobRepository,
)
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
        self.assertFalse(job["executor_telemetry"]["reported"])
        job_id = job["job_id"]

        status, jobs = self._req("GET", "/api/jobs")
        self.assertEqual(status, 200)
        self.assertTrue(any(j["job_id"] == job_id for j in jobs))

        status, detail = self._req("GET", f"/api/jobs/{job_id}")
        self.assertEqual(status, 200)
        self.assertEqual(detail["job_id"], job_id)
        self.assertIn("executor_duration_ms", detail["timing"])
        self.assertIn("total_tokens", detail["usage"])
        self.assertIn("command_calls", detail["executor_telemetry"])

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

    def test_events_are_unbounded_by_default_and_can_be_limited(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-02-02"})
        events = EventRepository(self.app.store)
        for index in range(250):
            events.append(job["job_id"], "test_event", {"index": index})

        status, all_events = self._req(
            "GET", f"/api/jobs/{job['job_id']}/events"
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(all_events), 252)  # create + submit + 250
        self.assertEqual(all_events[-1]["payload"]["index"], 249)

        status, limited_events = self._req(
            "GET", f"/api/jobs/{job['job_id']}/events?limit=10"
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(limited_events), 10)
        self.assertEqual(
            [event["seq"] for event in limited_events],
            [event["seq"] for event in all_events[:10]],
        )

        status, tail_events = self._req(
            "GET", f"/api/jobs/{job['job_id']}/events?tail=1&limit=10"
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            [event["seq"] for event in tail_events],
            [event["seq"] for event in all_events[-10:]],
        )
        self.assertEqual(tail_events[-1]["payload"]["index"], 249)

        status, resumed_events = self._req(
            "GET",
            f"/api/jobs/{job['job_id']}/events"
            f"?since_seq={all_events[199]['seq']}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(resumed_events), 52)

    def test_events_reject_negative_query_values(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-02-02"})
        for query in (
            "since_seq=-1",
            "limit=-1",
            "limit=not-a-number",
            "tail=not-a-boolean",
        ):
            status, body = self._req(
                "GET", f"/api/jobs/{job['job_id']}/events?{query}"
            )
            self.assertEqual(status, 400)
            self.assertIn("non-negative integers", body["error"])


class CancelRetryTest(_HttpTestBase):
    def test_cancel_queued_job_immediately(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")
        self.assertEqual(status, 200)
        self.assertTrue(body["cancelled"])
        self.assertEqual(body["outcome"], "cancelled")
        self.assertEqual(JobRepository(self.app.store).get_job(job["job_id"]).status, S.CANCELLED)

    def test_cancel_active_job_reports_request_accepted(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        jobs = JobRepository(self.app.store)
        jobs.transition_status(job["job_id"], S.RUNNING, event_type="enter_running")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="enter_evidence")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="enter_observation")

        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")

        self.assertEqual(status, 202)
        self.assertFalse(body["cancelled"])
        self.assertEqual(body["outcome"], "cancellation_requested")
        self.assertEqual(jobs.get_job(job["job_id"]).status, S.RUNNING)

        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")
        self.assertEqual(status, 202)
        self.assertEqual(body["outcome"], "cancellation_already_requested")

    def test_cancel_unknown_job_is_404(self) -> None:
        status, body = self._req("POST", "/api/jobs/no-such-job/cancel")
        self.assertEqual(status, 404)
        self.assertEqual(body["outcome"], "not_found")

    def test_cancel_completed_job_reports_terminal_state(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        jobs = JobRepository(self.app.store)
        jobs.transition_status(job["job_id"], S.RUNNING, event_type="enter_running")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="enter_evidence")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="enter_observation")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_AGGREGATION, event_type="enter_aggregation")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_ARCHIVE, event_type="enter_archive")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_ARCHIVE, event_type="enter_site_history")
        jobs.transition_status(job["job_id"], S.COMPLETED, event_type="job_completed")

        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")

        self.assertEqual(status, 409)
        self.assertEqual(body["outcome"], "already_terminal")
        self.assertEqual(body["status"], S.COMPLETED)

    def test_cancel_archive_job_reports_stage_not_cancellable(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        jobs = JobRepository(self.app.store)
        jobs.transition_status(job["job_id"], S.RUNNING, event_type="enter_running")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="enter_evidence")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="enter_observation")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_AGGREGATION, event_type="enter_aggregation")
        jobs.transition_status(job["job_id"], S.RUNNING, stage=S.STAGE_ARCHIVE, event_type="enter_archive")

        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")

        self.assertEqual(status, 409)
        self.assertEqual(body["outcome"], "stage_not_cancellable")
        self.assertEqual(body["status"], S.RUNNING)
        self.assertIn("archive", body["message"])

    def test_retry_cancelled_job(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        # move to cancelled so retry is legal
        JobRepository(self.app.store).cancel(job["job_id"])
        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/retry")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "queued")

    def test_retry_latest_specs_action(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        JobRepository(self.app.store).cancel(job["job_id"])
        self.app.retry_latest_specs = lambda job_id: ("queued", "a" * 40)

        status, body = self._req(
            "POST", f"/api/jobs/{job['job_id']}/retry-latest-specs"
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "queued")
        self.assertEqual(body["specs_revision"], "a" * 40)

    def test_retry_latest_specs_clears_correction_pending_state(self) -> None:
        """Verify that retry_latest_specs clears CORRECTION_PENDING to allow retry."""
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        job_id = job["job_id"]
        # Simulate an aggregation failure with CORRECTION_PENDING state
        jobs_repo = JobRepository(self.app.store)
        jobs_repo.transition_status(job_id, S.RUNNING, event_type="test_setup", payload={})
        jobs_repo.transition_status(
            job_id, S.RUNNING, stage=S.STAGE_AGGREGATION, event_type="test_setup", payload={}
        )
        jobs_repo.transition_status(job_id, S.FAILED, event_type="test_setup", payload={})

        # Create run-state.json with CORRECTION_PENDING and another non-CORRECTION_PENDING state
        run_state_path = (
            self.settings.jobs_root / job_id / "runs" / "run-1" / "staged" / "run-state.json"
        )
        run_state_path.parent.mkdir(parents=True, exist_ok=True)
        initial_state = {
            "validated_work_items": [],
            "pseudo_work_item_states": {
                "aggregation:final": "CORRECTION_PENDING",
                "feature:Feat-01": "GENERATED_VALID",
            },
            "current_phase": "aggregation",
        }
        run_state_path.write_text(
            json.dumps(initial_state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # Mock the workspace refresh to avoid real git operations
        from spec_eval.service.workspace.manager import RevisionWorkspaceManager
        from spec_eval.service.workspace.models import EvaluationWorkspace

        def mock_refresh(self, job):
            return EvaluationWorkspace(
                workspace_root=self.settings.data_root / "mock_workspace",
                repo_root=self.settings.data_root / "mock_repo",
                specs_root=self.settings.data_root / "mock_specs",
                schemas_root=self.settings.data_root / "mock_schemas",
                revisions={"ace_engine": "a"*40, "sdk-js": "b"*40, "sdk_c": "c"*40, "specs": "e"*40},
            )

        original_refresh = RevisionWorkspaceManager.refresh_specs_revision
        RevisionWorkspaceManager.refresh_specs_revision = mock_refresh

        try:
            # Execute retry_latest_specs
            self.app.retry_latest_specs(job_id)
        finally:
            # Restore
            RevisionWorkspaceManager.refresh_specs_revision = original_refresh

        # Verify CORRECTION_PENDING was cleared but other states preserved
        run_state = json.loads(run_state_path.read_text(encoding="utf-8"))
        pseudo = run_state.get("pseudo_work_item_states", {})
        self.assertNotIn("aggregation:final", pseudo, "CORRECTION_PENDING state should be cleared")
        self.assertIn("feature:Feat-01", pseudo, "Other states should be preserved")
        self.assertEqual(pseudo["feature:Feat-01"], "GENERATED_VALID")


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

    def test_ui_reports_cancel_and_retry_action_errors(self) -> None:
        status, body = self._req("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('id="action-error"', body)
        js_status, js = self._req("GET", "/static/app.js")
        self.assertEqual(js_status, 200)
        self.assertIn("runJobAction", js)
        self.assertIn("if (!res.ok)", js)
        self.assertIn("retry-latest-specs", js)
        self.assertIn("latest specs", js)

    def test_ui_contains_independent_function_and_job_pagination(self) -> None:
        status, body = self._req("GET", "/")
        self.assertEqual(status, 200)
        for prefix in ("functions", "jobs"):
            self.assertIn(f'id="{prefix}-page-size"', body)
            self.assertIn(f'id="{prefix}-page-prev"', body)
            self.assertIn(f'id="{prefix}-page-next"', body)
            self.assertIn(f'id="{prefix}-page-info"', body)
        self.assertEqual(body.count('<option value="10">10</option>'), 2)
        self.assertEqual(body.count('<option value="50">50</option>'), 2)
        self.assertEqual(body.count('<option value="100">100</option>'), 2)

    def test_ui_paginates_filtered_results_and_resets_pages_from_controls(self) -> None:
        js_status, js = self._req("GET", "/static/app.js")
        self.assertEqual(js_status, 200)
        self.assertIn("function paginate(items, page, pageSize)", js)
        self.assertIn("let functionsPage = 1", js)
        self.assertIn("let jobsPage = 1", js)
        self.assertIn("functionsPage = 1", js)
        self.assertIn("jobsPage = 1", js)
        self.assertIn('functionsPageSize.addEventListener("change"', js)
        self.assertIn('jobsPageSize.addEventListener("change"', js)
        self.assertIn('functionsPagePrev.addEventListener("click"', js)
        self.assertIn('functionsPageNext.addEventListener("click"', js)
        self.assertIn('jobsPagePrev.addEventListener("click"', js)
        self.assertIn('jobsPageNext.addEventListener("click"', js)

    def test_static_traversal_rejected(self) -> None:
        status, _ = self._req("GET", "/static/../../etc/passwd")
        self.assertEqual(status, 404)


class CancelLifecycleEndToEndTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))

        def blocking_runner(job_id: str, cancel: threading.Event) -> None:
            jobs = JobRepository(self.app.store)
            jobs.transition_status(job_id, S.RUNNING, event_type="enter_running")
            jobs.transition_status(
                job_id, S.RUNNING, stage=S.STAGE_PREPARING, event_type="enter_preparing"
            )
            jobs.transition_status(
                job_id, S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="enter_evidence"
            )
            jobs.transition_status(
                job_id, S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="enter_observation"
            )
            while not cancel.is_set():
                time.sleep(0.01)

        self.app = SemanticServiceApp(
            self.settings, max_workers=1, job_runner=blocking_runner, token=None
        )
        self.app.start()

    def tearDown(self) -> None:
        self.app.stop()
        self.tmp.cleanup()

    def _req(self, method: str, path: str, body=None) -> tuple[int, object]:
        raw_body = b"" if body is None else json.dumps(body).encode("utf-8")
        resp = route_request(method, path, raw_body, {}, self.app)
        return resp.status, json.loads(resp.body.decode("utf-8"))

    def test_cancel_reaches_terminal_state_and_second_request_is_truthful(self) -> None:
        _, job = self._req("POST", "/api/jobs", {"func_id": "04-01-01"})
        jobs = JobRepository(self.app.store)
        deadline = time.monotonic() + 3.0
        while (
            jobs.get_job(job["job_id"]).stage != S.STAGE_OBSERVATION
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        self.assertEqual(jobs.get_job(job["job_id"]).status, S.RUNNING)

        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")
        self.assertEqual(status, 202)
        self.assertEqual(body["outcome"], "cancellation_requested")

        deadline = time.monotonic() + 3.0
        while jobs.get_job(job["job_id"]).status != S.CANCELLED and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(jobs.get_job(job["job_id"]).status, S.CANCELLED)

        status, body = self._req("POST", f"/api/jobs/{job['job_id']}/cancel")
        self.assertEqual(status, 409)
        self.assertEqual(body["outcome"], "already_terminal")
        self.assertEqual(body["status"], S.CANCELLED)


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
