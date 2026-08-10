from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from spec_eval import ci_worker
from spec_eval.ci_worker import (
    COMMENT_MARKER,
    WorkerContext,
    compute_changed_files,
    ensure_specs_at_sha,
    load_receipts,
    main,
    mark_processed,
    passes_whitelist,
    post_or_update_comment,
    process_receipt,
    processed_set,
    render_comment,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).parent / "fixtures" / "ci"


def _receipt(
    *,
    iid: int = 61,
    project: str = "arkui_architecture/arkui-specs",
    delivery: str = "61_probe-delivery-0001",
    tested: str = "936b9f4abffee0f35cf189242f463a9ada73edee",
    target: str = "dd3687695c63a60226bd8c7cf62defff957dee74",
) -> dict:
    return {
        "delivery_id": delivery,
        "action": "update",
        "state": "opened",
        "received_at": "2026-08-10T09:53:05.191Z",
        "project": {"path_with_namespace": project, "web_url": "https://gitcode.com/" + project},
        "pull_request": {
            "iid": iid,
            "source_branch": "test/next-010-gitcode-webhook",
            "target_branch": "main",
            "url": f"https://gitcode.com/{project}/merge_requests/{iid}",
        },
        "revisions": {"tested": tested, "target": target, "source": tested},
    }


def _ctx(tmp_path: Path, **overrides: object) -> WorkerContext:
    base = dict(
        repo_root=REPO_ROOT,
        specs_root=REPO_ROOT / "specs",
        receipts=tmp_path / "receipts.ndjson",
        processed_ledger=tmp_path / "processed.ndjson",
        baseline=REPO_ROOT / "specs/evaluation/baselines/current.json",
        output_root=tmp_path / "ci",
        ci_runner=REPO_ROOT / "specs/tools/spec_eval/ci_runner.py",
        repo="arkui_architecture/arkui-specs",
        allow_projects=("arkui_architecture/arkui-specs",),
        bot_login="sunfei2021",
        top=5,
        no_cache=False,
        dry_run=False,
        no_comment=False,
        auto_checkout=False,
        oh_gc="oh-gc",
        python="python3",
    )
    base.update(overrides)
    return WorkerContext(**base)  # type: ignore[arg-type]


class RenderCommentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = _receipt()

    def test_zero_affected_reports_no_new_errors(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        body = render_comment(summary, self.receipt, shas={"tested": "936b9f4abc", "target": "dd3687695c"}, ensure_action="matched")
        self.assertIn(COMMENT_MARKER, body)
        self.assertIn("report-only", body)
        self.assertIn("!61", body)
        self.assertIn("0 affected Functions", body)
        self.assertIn("no new errors", body)
        # must never claim "0 errors" (baseline debt is not resolved)
        self.assertNotIn("0 errors", body)

    def test_n_affected_with_added_surfaces_new_errors(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-n-affected-with-added.json").read_text(encoding="utf-8"))
        body = render_comment(summary, _receipt(iid=9, delivery="9_probe"), shas={"tested": "936b9f4abc", "target": "dd3687695c"}, ensure_action="matched")
        self.assertIn(COMMENT_MARKER, body)
        self.assertIn("new error(s)", body)
        self.assertIn("REF-NOT-FOUND-001", body)
        self.assertIn("Major", body)
        self.assertIn("02-divider", body)
        # added count from delta drives the headline
        self.assertIn("2 new error", body)

    def test_incomplete_banner(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-incomplete.json").read_text(encoding="utf-8"))
        body = render_comment(summary, _receipt(iid=9, delivery="9_probe"), shas={"tested": "936b9f4abc", "target": "dd3687695c"}, ensure_action="matched", exit_code=3)
        self.assertIn("evaluation incomplete", body)
        self.assertIn("05-01-02", body)
        self.assertIn("simulated orchestrator failure", body)


class WhitelistAndLedgerTest(unittest.TestCase):
    def test_whitelist(self) -> None:
        self.assertTrue(passes_whitelist(_receipt(project="arkui_architecture/arkui-specs"), ("arkui_architecture/arkui-specs",)))
        self.assertFalse(passes_whitelist(_receipt(project="someone/else"), ("arkui_architecture/arkui-specs",)))

    def test_load_receipts_skips_blank_and_invalid(self) -> None:
        path = FIXTURES.parent / "_tmp_receipts.ndjson"
        path.write_text(
            json.dumps(_receipt(delivery="a")) + "\n\n" + json.dumps(_receipt(delivery="b")) + "\n",
            encoding="utf-8",
        )
        try:
            self.assertEqual([r["delivery_id"] for r in load_receipts(path)], ["a", "b"])
        finally:
            path.unlink()

    def test_processed_ledger_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "processed.ndjson"
            self.assertEqual(processed_set(ledger), set())
            mark_processed(ledger, "d1", status="ok", archive="/x")
            mark_processed(ledger, "d2", status="tool_error")
            self.assertEqual(processed_set(ledger), {"d1", "d2"})


class EnsureSpecsAndDiffTest(unittest.TestCase):
    def test_ensure_matched(self) -> None:
        with mock.patch.object(ci_worker, "_git") as git:
            git.return_value = mock.Mock(returncode=0, stdout=(_receipt().get("revisions")["tested"]))
            current, ok, action, restore = ensure_specs_at_sha(Path("/tmp/specs"), _receipt().get("revisions")["tested"], auto_checkout=False)
        self.assertTrue(ok)
        self.assertEqual(action, "matched")
        self.assertIsNone(restore)

    def test_ensure_skips_mismatch_without_auto_checkout(self) -> None:
        with mock.patch.object(ci_worker, "_git") as git:
            git.return_value = mock.Mock(returncode=0, stdout="ffffffffffffffffffffffffffffffffffffffff\n")
            current, ok, action, restore = ensure_specs_at_sha(Path("/tmp/specs"), "936b9f4" + "0" * 36, auto_checkout=False)
        self.assertFalse(ok)
        self.assertEqual(action, "skipped_mismatch")
        self.assertIsNone(restore)

    def test_compute_changed_files_prepends_specs_prefix(self) -> None:
        # git -C specs diff emits specs-root-relative paths (no specs/ prefix).
        git_output = "tools/spec_eval/gitcode_webhook.py\n05-ui-components/01-layout-components/02-divider/Feat-01-divider-spec.md\n"
        with mock.patch.object(ci_worker, "_git") as git:
            git.return_value = mock.Mock(returncode=0, stdout=git_output)
            files, status = compute_changed_files(Path("/tmp/specs"), "dd36876", "936b9f4")
        self.assertEqual(status, "ok")
        self.assertTrue(all(path.startswith("specs/") for path in files), files)
        self.assertIn("specs/tools/spec_eval/gitcode_webhook.py", files)
        self.assertIn("specs/05-ui-components/01-layout-components/02-divider/Feat-01-divider-spec.md", files)

    def test_compute_changed_files_requires_both_shas(self) -> None:
        files, status = compute_changed_files(Path("/tmp/specs"), None, "936b9f4")
        self.assertEqual(status, "missing_target_sha")
        self.assertEqual(files, [])


class ResolverPrefixContractTest(unittest.TestCase):
    """The specs/ prefix is load-bearing: the resolver joins candidates onto repo_root."""

    @classmethod
    def setUpClass(cls) -> None:
        from spec_eval.config import EvaluationConfig
        from spec_eval.discovery import ChangedFunctionResolver
        from spec_eval.orchestrator import EvaluationOrchestrator

        config = EvaluationConfig.discover()
        cls.resolver = ChangedFunctionResolver(EvaluationOrchestrator(config).locator)

    def test_prefixed_real_spec_resolves_to_function(self) -> None:
        contexts = self.resolver.resolve(["specs/05-ui-components/01-layout-components/02-divider/Feat-01-divider-spec.md"])
        self.assertTrue({c.func_id for c in contexts}, "expected non-empty resolution")
        self.assertIn("05-01-02", {c.func_id for c in contexts})

    def test_prefixed_tooling_file_resolves_to_zero(self) -> None:
        contexts = self.resolver.resolve(["specs/tools/spec_eval/gitcode_webhook.py"])
        self.assertEqual([c.func_id for c in contexts], [])

    def test_prefixed_global_tool_root_triggers_all_functions(self) -> None:
        contexts = self.resolver.resolve(["specs/tools/spec_eval/discovery/registry_loader.py"])
        self.assertGreater(len(contexts), 50, "global tool root should trigger a full re-scan")


class PostOrUpdateCommentTest(unittest.TestCase):
    @staticmethod
    def _proc(stdout: str = "", returncode: int = 0) -> mock.Mock:
        return mock.Mock(returncode=returncode, stdout=stdout, stderr="")

    def test_creates_when_no_existing(self) -> None:
        responses = iter([self._proc("[]"), self._proc('{"id": 99, "url": "https://gitcode.com/c/99"}')])
        with mock.patch.object(ci_worker, "_oh_gc", side_effect=lambda *a, **k: next(responses)):
            result = post_or_update_comment("arkui_architecture/arkui-specs", 61, COMMENT_MARKER + " body")
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["id"], 99)

    def test_edits_when_marker_present(self) -> None:
        existing = [{"id": 5, "url": "https://gitcode.com/c/5", "body": COMMENT_MARKER + "\nold"}]
        # list returns the comments JSON; edit returns empty stdout (oh-gc quirk) but exit 0.
        responses = iter([self._proc(json.dumps(existing)), self._proc("")])
        with mock.patch.object(ci_worker, "_oh_gc", side_effect=lambda *a, **k: next(responses)):
            result = post_or_update_comment("arkui_architecture/arkui-specs", 61, COMMENT_MARKER + " new")
        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["id"], 5)
        self.assertEqual(result["url"], "https://gitcode.com/c/5")

    def test_dry_run_does_not_call_oh_gc(self) -> None:
        with mock.patch.object(ci_worker, "_oh_gc") as ohgc:
            result = post_or_update_comment("arkui_architecture/arkui-specs", 61, "body", dry_run=True)
        ohgc.assert_not_called()
        self.assertEqual(result["action"], "dry-run")


class ProcessReceiptTest(unittest.TestCase):
    def test_skips_non_whitelisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(Path(tmp), allow_projects=("arkui_architecture/arkui-specs",))
            result = process_receipt(_receipt(project="someone/else"), ctx)
        self.assertEqual(result["status"], "skipped_whitelist")

    def test_sha_mismatch_skips_without_ci_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(Path(tmp))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("deadbeef", False, "skipped_mismatch", None)), \
                 mock.patch.object(ci_worker, "run_ci_runner") as runner:
                result = process_receipt(_receipt(), ctx)
        runner.assert_not_called()
        self.assertEqual(result["status"], "skipped_mismatch")

    def test_happy_path_archives_and_marks(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(Path(tmp), dry_run=True)
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/tools/spec_eval/gitcode_webhook.py"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1234.0, "")) as runner:
                result = process_receipt(_receipt(), ctx)
            self.assertEqual(result["status"], "ok")
            runner.assert_called_once()
            archive = Path(result["archive_dir"])
            self.assertTrue((archive / "run-meta.json").is_file())
            self.assertTrue((archive / "comment-body.md").is_file())
            self.assertTrue((archive / "comment.json").is_file())
            meta = json.loads((archive / "run-meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["status"], "ok")
            self.assertEqual(meta["affected_function_count"], 0)


class MainIdempotencyTest(unittest.TestCase):
    def _write_receipts(self, path: Path, receipts: list[dict]) -> None:
        path.write_text("\n".join(json.dumps(r) for r in receipts) + "\n", encoding="utf-8")

    def test_process_once_then_skip_on_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._write_receipts(tmp_path / "receipts.ndjson", [_receipt(delivery="61_once")])
            args = ["--receipts", str(tmp_path / "receipts.ndjson"),
                    "--processed-ledger", str(tmp_path / "processed.ndjson"),
                    "--output-root", str(tmp_path / "ci"),
                    "--specs-root", str(REPO_ROOT / "specs"),
                    "--repo", "arkui_architecture/arkui-specs",
                    "--dry-run", "--json"]
            summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/tools/spec_eval/gitcode_webhook.py"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")) as runner:
                self.assertEqual(main(args), 0)
                self.assertEqual(runner.call_count, 1)
                # re-run over the same receipts: nothing new is processed
                self.assertEqual(main(args), 0)
                self.assertEqual(runner.call_count, 1)
            self.assertEqual(processed_set(tmp_path / "processed.ndjson"), {"61_once"})

    def test_whitelist_filters_in_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._write_receipts(tmp_path / "receipts.ndjson", [
                _receipt(delivery="ok", project="arkui_architecture/arkui-specs"),
                _receipt(delivery="skip", project="someone/else"),
            ])
            args = ["--receipts", str(tmp_path / "receipts.ndjson"),
                    "--processed-ledger", str(tmp_path / "processed.ndjson"),
                    "--output-root", str(tmp_path / "ci"),
                    "--specs-root", str(REPO_ROOT / "specs"),
                    "--allow-project", "arkui_architecture/arkui-specs",
                    "--dry-run", "--json"]
            summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")) as runner:
                main(args)
            self.assertEqual(runner.call_count, 1, "only the whitelisted receipt should run ci_runner")
            # both deliveries are marked processed (skip is recorded so it never re-loops)
            self.assertEqual(processed_set(tmp_path / "processed.ndjson"), {"ok", "skip"})


class WatchModeTest(unittest.TestCase):
    def test_watch_drains_then_exits_on_interrupt(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "receipts.ndjson").write_text(json.dumps(_receipt(delivery="w1")) + "\n", encoding="utf-8")
            args = ["--receipts", str(tmp_path / "receipts.ndjson"),
                    "--processed-ledger", str(tmp_path / "processed.ndjson"),
                    "--output-root", str(tmp_path / "ci"),
                    "--specs-root", str(REPO_ROOT / "specs"),
                    "--repo", "arkui_architecture/arkui-specs",
                    "--watch", "--poll-interval", "0", "--dry-run", "--json"]
            # first sleep returns (after draining w1); second sleep breaks the loop
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")) as runner, \
                 mock.patch.object(ci_worker.time, "sleep", side_effect=[None, KeyboardInterrupt()]):
                self.assertEqual(main(args), 0)
            # the worker processed the receipt exactly once across the ticks, then idled
            self.assertEqual(runner.call_count, 1)
            self.assertEqual(processed_set(tmp_path / "processed.ndjson"), {"w1"})


@unittest.skipUnless(os.environ.get("SPECEVAL_LONG"), "slow; set SPECEVAL_LONG=1 to run the in-place regression integration test")
class NewErrorDetectionIntegrationTest(unittest.TestCase):
    """Inject a bogus source citation into a real Function spec and prove the
    delta surfaces as a NEW error in render_comment. Restores the spec in cleanup.
    """

    SPEC = REPO_ROOT / "specs/05-ui-components/01-layout-components/02-divider/Feat-01-divider-spec.md"
    # A bare file-like path is skipped by the citation parser unless it carries
    # a line range or is a complete backtick code span (citation_parser.py:45).
    # The ``:1-2`` range forces it to be parsed, then it fails to resolve.
    PROBE = "\n\n> ci-worker regression probe: frameworks/zzz_nonexistent_probe_xyz/zzz_nonexistent_probe.cpp:1-2\n"

    def test_new_finding_surfaces_in_comment(self) -> None:
        self.assertTrue(self.SPEC.is_file(), f"spec not found: {self.SPEC}")
        original = self.SPEC.read_bytes()
        self.addCleanup(self.SPEC.write_bytes, original)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            files_from = tmp_path / "files-from.txt"
            files_from.write_text("specs/05-ui-components/01-layout-components/02-divider/Feat-01-divider-spec.md\n", encoding="utf-8")
            self.SPEC.write_text(self.SPEC.read_text(encoding="utf-8") + self.PROBE, encoding="utf-8")
            command = [
                "python3", str(REPO_ROOT / "specs/tools/spec_eval/ci_runner.py"),
                "--files-from", str(files_from),
                "--baseline", str(REPO_ROOT / "specs/evaluation/baselines/current.json"),
                "--output", str(tmp_path / "out"),
                "--no-cache", "--top", "5", "--json", "--quiet",
            ]
            proc = subprocess.run(command, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, f"ci_runner failed: {proc.stderr[-800:]}")
            summary = json.loads(proc.stdout)
            self.assertGreaterEqual(int((summary.get("delta") or {}).get("added", 0)), 1, f"expected added>=1; stderr={proc.stderr[-400:]}")
            body = render_comment(summary, _receipt(iid=9, delivery="9_integration"), shas={"tested": "936b9f4abc", "target": "dd3687695c"}, ensure_action="matched")
            self.assertIn("new error(s)", body)


if __name__ == "__main__":
    unittest.main()
