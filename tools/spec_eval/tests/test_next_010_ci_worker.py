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
    SpecCheckResult,
    WorkerContext,
    compute_changed_files,
    current_pr_head_sha,
    decide_test_pass,
    ensure_specs_at_sha,
    load_receipts,
    main,
    mark_processed,
    mark_pr_test_passed,
    passes_whitelist,
    post_comment,
    process_receipt,
    processed_set,
    render_comment,
    reset_pr_test,
    run_specs_checks,
    specs_checks_passed,
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
        # Specs integrity checks default ON in production; tests opt in via
        # SpecsCheckTest so the rest of the suite stays isolated from the
        # global specs checkout state.
        specs_checks_enabled=False,
        oh_gc="oh-gc",
        python="python3",
    )
    base.update(overrides)
    return WorkerContext(**base)  # type: ignore[arg-type]


def _check(name: str, exit_code: int, *, stdout: str = "", stderr: str = "") -> SpecCheckResult:
    return SpecCheckResult(
        name=name,
        command=["python3", f"tools/{name}.py"],
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        elapsed_ms=5.0,
    )


def _specs_ok() -> list:
    return [
        _check("generate_index", 0, stdout="index.md is up to date"),
        _check("validate_specs", 0, stdout="validate_specs: 0 error(s), 0 warning(s)"),
    ]


def _specs_failed() -> list:
    # generate_index passes; validate_specs fails with two ERROR lines on stdout.
    return [
        _check("generate_index", 0, stdout="index.md is up to date"),
        _check("validate_specs", 1, stdout="validate_specs: 2 error(s), 0 warning(s)",
               stderr="ERROR: Feat-01-x-spec.md: missing AC entries\nERROR: Feat-02-y-spec.md: invalid status `Draftx`"),
    ]


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


class EnsureSpecsFetchTest(unittest.TestCase):
    """issue #8: the worker must fetch the tested SHA before evaluating,
    otherwise every PR hits skipped_mismatch because the worktree (parked on
    main) never contains the PR source branch head."""

    @staticmethod
    def _proc(returncode: int = 0, stdout: str = "") -> mock.Mock:
        return mock.Mock(returncode=returncode, stdout=stdout)

    def test_object_exists_reflects_cat_file(self) -> None:
        with mock.patch.object(ci_worker, "_git", side_effect=[self._proc(0), self._proc(1)]):
            self.assertTrue(ci_worker._object_exists(Path("/tmp/specs"), "abc123"))
            self.assertFalse(ci_worker._object_exists(Path("/tmp/specs"), "abc123"))

    def test_object_exists_empty_sha_skips_git(self) -> None:
        with mock.patch.object(ci_worker, "_git") as git:
            self.assertFalse(ci_worker._object_exists(Path("/tmp/specs"), ""))
            self.assertFalse(ci_worker._object_exists(Path("/tmp/specs"), None))  # type: ignore[arg-type]
        git.assert_not_called()

    def test_matched_skips_fetch(self) -> None:
        with mock.patch.object(ci_worker, "_git", side_effect=[
            self._proc(0, stdout="abc123\n"),  # rev-parse HEAD -> current == tested
        ]) as git:
            _, ok, action, restore = ensure_specs_at_sha(
                Path("/tmp/specs"), "abc123", auto_checkout=True, source_branch="feature/x")
        self.assertTrue(ok)
        self.assertEqual(action, "matched")
        self.assertIsNone(restore)
        self.assertEqual(git.call_count, 1)

    def test_fetches_source_branch_then_checks_out(self) -> None:
        with mock.patch.object(ci_worker, "_git", side_effect=[
            self._proc(0, stdout="main\n"),    # rev-parse -> current=main (!= tested)
            self._proc(1),                     # cat-file -> absent (trigger fetch)
            self._proc(0),                     # fetch origin feature/x -> ok
            self._proc(0),                     # cat-file -> present (_fetch_into hit)
            self._proc(0, stdout="main\n"),    # symbolic-ref -> restore=main
            self._proc(0),                     # checkout --detach -> ok
        ]) as git:
            _, ok, action, restore = ensure_specs_at_sha(
                Path("/tmp/specs"), "abc123", auto_checkout=True, source_branch="feature/x")
        self.assertTrue(ok)
        self.assertEqual(action, "checked_out")
        self.assertEqual(restore, "main")
        self.assertEqual(git.call_args_list[2].args[1:], ("fetch", "origin", "feature/x"))

    def test_falls_back_to_origin_when_source_branch_lacks_commit(self) -> None:
        with mock.patch.object(ci_worker, "_git", side_effect=[
            self._proc(0, stdout="main\n"),    # rev-parse
            self._proc(1),                     # cat-file -> absent
            self._proc(0),                     # fetch origin feature/x -> ok
            self._proc(1),                     # cat-file -> still absent (branch lacks it)
            self._proc(0),                     # fetch origin -> ok (fallback)
            self._proc(0),                     # cat-file -> present
            self._proc(0, stdout="main\n"),    # symbolic-ref
            self._proc(0),                     # checkout
        ]) as git:
            _, ok, action, _ = ensure_specs_at_sha(
                Path("/tmp/specs"), "abc123", auto_checkout=True, source_branch="feature/x")
        self.assertTrue(ok)
        self.assertEqual(action, "checked_out")
        self.assertEqual(git.call_args_list[4].args[1:], ("fetch", "origin"))

    def test_fetches_origin_directly_when_no_source_branch(self) -> None:
        with mock.patch.object(ci_worker, "_git", side_effect=[
            self._proc(0, stdout="main\n"),    # rev-parse
            self._proc(1),                     # cat-file -> absent
            self._proc(0),                     # fetch origin (no source branch)
            self._proc(0),                     # cat-file -> present
            self._proc(0, stdout="main\n"),    # symbolic-ref
            self._proc(0),                     # checkout
        ]) as git:
            _, ok, action, _ = ensure_specs_at_sha(
                Path("/tmp/specs"), "abc123", auto_checkout=True, source_branch=None)
        self.assertTrue(ok)
        self.assertEqual(action, "checked_out")
        self.assertEqual(git.call_args_list[2].args[1:], ("fetch", "origin"))

    def test_fetch_command_failure_reports_fetch_failed(self) -> None:
        with mock.patch.object(ci_worker, "_git", side_effect=[
            self._proc(0, stdout="main\n"),    # rev-parse
            self._proc(1),                     # cat-file -> absent
            self._proc(1),                     # fetch origin feature/x -> fail
            self._proc(1),                     # fetch origin -> fail
        ]):
            _, ok, action, restore = ensure_specs_at_sha(
                Path("/tmp/specs"), "abc123", auto_checkout=True, source_branch="feature/x")
        self.assertFalse(ok)
        self.assertEqual(action, "fetch_failed")
        self.assertIsNone(restore)

    def test_force_pushed_absent_after_fetch_reports_skipped_mismatch(self) -> None:
        # fetch commands succeed but the commit is gone (force-pushed away).
        with mock.patch.object(ci_worker, "_git", side_effect=[
            self._proc(0, stdout="main\n"),    # rev-parse
            self._proc(1),                     # cat-file -> absent
            self._proc(0),                     # fetch origin feature/x -> ok
            self._proc(1),                     # cat-file -> still absent
            self._proc(0),                     # fetch origin -> ok
            self._proc(1),                     # cat-file -> still absent
        ]):
            _, ok, action, restore = ensure_specs_at_sha(
                Path("/tmp/specs"), "abc123", auto_checkout=True, source_branch="feature/x")
        self.assertFalse(ok)
        self.assertEqual(action, "skipped_mismatch")
        self.assertIsNone(restore)


class ResolverPrefixContractTest(unittest.TestCase):
    """The specs/ prefix is load-bearing: the resolver joins candidates onto repo_root."""

    @classmethod
    def setUpClass(cls) -> None:
        from spec_eval.config import EvaluationConfig
        from spec_eval.discovery.changed_function_resolver import ChangedFunctionResolver
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


class PostCommentTest(unittest.TestCase):
    @staticmethod
    def _proc(stdout: str = "", returncode: int = 0) -> mock.Mock:
        return mock.Mock(returncode=returncode, stdout=stdout, stderr="")

    def test_creates_comment(self) -> None:
        # A fresh comment is posted every time; no listing/edit-in-place, so
        # _oh_gc is called exactly once (the create call).
        responses = iter([self._proc('{"id": 99, "url": "https://gitcode.com/c/99"}')])
        with mock.patch.object(ci_worker, "_oh_gc", side_effect=lambda *a, **k: next(responses)) as ohgc:
            result = post_comment("arkui_architecture/arkui-specs", 61, COMMENT_MARKER + " body")
        self.assertEqual(ohgc.call_count, 1)
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["id"], 99)

    def test_always_creates_new_comment(self) -> None:
        # Even when a marker comment already exists on the PR, we post a new
        # comment rather than editing it in place.
        responses = iter([self._proc('{"id": 7, "url": "https://gitcode.com/c/7"}')])
        with mock.patch.object(ci_worker, "_oh_gc", side_effect=lambda *a, **k: next(responses)) as ohgc:
            result = post_comment("arkui_architecture/arkui-specs", 61, COMMENT_MARKER + " new")
        self.assertEqual(ohgc.call_count, 1)
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["id"], 7)

    def test_dry_run_does_not_call_oh_gc(self) -> None:
        with mock.patch.object(ci_worker, "_oh_gc") as ohgc:
            result = post_comment("arkui_architecture/arkui-specs", 61, "body", dry_run=True)
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


class DecideTestPassTest(unittest.TestCase):
    def test_passes_when_ok_and_no_new_errors(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        self.assertTrue(decide_test_pass(summary, status="ok", incomplete=False))

    def test_withholds_when_new_errors(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-n-affected-with-added.json").read_text(encoding="utf-8"))
        self.assertFalse(decide_test_pass(summary, status="ok", incomplete=False))

    def test_withholds_when_incomplete_or_not_ok(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        self.assertFalse(decide_test_pass(summary, status="incomplete", incomplete=True))
        self.assertFalse(decide_test_pass(summary, status="skipped_mismatch", incomplete=False))
        self.assertFalse(decide_test_pass(None, status="ok", incomplete=False))


class MarkPrTestPassedTest(unittest.TestCase):
    def test_reads_current_pr_head_before_pass(self) -> None:
        with mock.patch.object(
            ci_worker, "_oh_gc_json", return_value={"head": {"sha": "new-head"}}
        ) as oh_gc_json:
            self.assertEqual(
                current_pr_head_sha("arkui_architecture/arkui-specs", 61),
                "new-head",
            )
        oh_gc_json.assert_called_once_with(
            ["pr", "view", "61", "--repo", "arkui_architecture/arkui-specs", "--json"],
            oh_gc="oh-gc",
        )

    def test_invokes_pr_test(self) -> None:
        captured: list[list[str]] = []

        def fake_oh_gc(args, *, oh_gc):
            captured.append(args)
            return mock.Mock()

        with mock.patch.object(ci_worker, "_oh_gc", side_effect=fake_oh_gc):
            result = mark_pr_test_passed("arkui_architecture/arkui-specs", 61)
        self.assertEqual(result["action"], "test_passed")
        self.assertEqual(captured[0], ["pr", "test", "61", "--repo", "arkui_architecture/arkui-specs"])

    def test_force_inserts_force_flag(self) -> None:
        captured: list[list[str]] = []

        def fake_oh_gc(args, *, oh_gc):
            captured.append(args)
            return mock.Mock()

        with mock.patch.object(ci_worker, "_oh_gc", side_effect=fake_oh_gc):
            mark_pr_test_passed("arkui_architecture/arkui-specs", 61, force=True)
        self.assertIn("--force", captured[0])


class ResetPrTestTest(unittest.TestCase):
    def test_calls_documented_patch_endpoint_for_current_tester_only(self) -> None:
        with mock.patch.object(ci_worker, "_gitcode_api_json", return_value={"ok": True}) as api:
            result = reset_pr_test("arkui_architecture/arkui-specs", 61)
        api.assert_called_once_with(
            "PATCH",
            "/repos/arkui_architecture/arkui-specs/pulls/61/testers",
            body={"reset_all": False},
        )
        self.assertEqual(result["action"], "test_reset")

    def test_force_mode_resets_all_testers(self) -> None:
        with mock.patch.object(ci_worker, "_gitcode_api_json", return_value={}) as api:
            result = reset_pr_test("arkui_architecture/arkui-specs", 60, reset_all=True)
        api.assert_called_once_with(
            "PATCH",
            "/repos/arkui_architecture/arkui-specs/pulls/60/testers",
            body={"reset_all": True},
        )
        self.assertEqual(result["action"], "test_reset_all")

    def test_rejects_invalid_repo(self) -> None:
        with self.assertRaises(ValueError):
            reset_pr_test("arkui-specs", 61)


class ProcessReceiptTestResultTest(unittest.TestCase):
    def _passing_ctx(self, tmp_path: Path, **overrides: object) -> WorkerContext:
        base: dict[str, object] = {"test_on_pass": True, "dry_run": False}
        base.update(overrides)
        return _ctx(tmp_path, **base)

    def test_marks_test_passed_when_enabled(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "created"}), \
                 mock.patch.object(ci_worker, "reset_pr_test", return_value={"action": "test_reset"}) as reset, \
                 mock.patch.object(ci_worker, "current_pr_head_sha", return_value=_receipt()["revisions"]["tested"]), \
                 mock.patch.object(ci_worker, "mark_pr_test_passed", return_value={"action": "test_passed"}) as mark_test:
                result = process_receipt(_receipt(), ctx)
            reset.assert_called_once_with("arkui_architecture/arkui-specs", 61, reset_all=False)
            mark_test.assert_called_once()
            self.assertEqual(result["test"]["reset"]["action"], "test_reset")
            self.assertEqual(result["test"]["pass"]["action"], "test_passed")
            self.assertTrue((Path(tmp) / "ci/pr-61/61_probe-delivery-0001/test-result.json").is_file())

    def test_skips_test_writeback_echo_for_same_head(self) -> None:
        # Same tested SHA already processed -> echo from the pr-test writeback;
        # must skip without resetting/posting/marking (breaks the echo loop).
        tested = _receipt()["revisions"]["tested"]
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp))
            with mock.patch.object(ci_worker, "_last_processed_head_for", return_value=tested), \
                 mock.patch.object(ci_worker, "reset_pr_test") as reset, \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test, \
                 mock.patch.object(ci_worker, "post_comment") as comment:
                result = process_receipt(_receipt(), ctx)
            self.assertEqual(result["status"], "skipped_unchanged_head")
            reset.assert_not_called()
            mark_test.assert_not_called()
            comment.assert_not_called()

    def test_does_not_mark_test_passed_when_new_errors(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-n-affected-with-added.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "created"}), \
                 mock.patch.object(ci_worker, "reset_pr_test", return_value={"action": "test_reset"}) as reset, \
                 mock.patch.object(ci_worker, "current_pr_head_sha") as current_head, \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test:
                result = process_receipt(_receipt(), ctx)
            reset.assert_called_once()
            current_head.assert_not_called()
            mark_test.assert_not_called()
            self.assertEqual(result["test"]["pass"]["reason"], "evaluation_not_passed")

    def test_does_not_mark_test_passed_in_dry_run(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp), dry_run=True)
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "dry-run"}), \
                 mock.patch.object(ci_worker, "reset_pr_test") as reset, \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test:
                process_receipt(_receipt(), ctx)
            reset.assert_not_called()
            mark_test.assert_not_called()

    def test_disabled_by_default(self) -> None:
        # _ctx defaults test_on_pass=False
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(Path(tmp))  # test_on_pass defaults off
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "created"}), \
                 mock.patch.object(ci_worker, "reset_pr_test") as reset, \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test:
                process_receipt(_receipt(), ctx)
            reset.assert_not_called()
            mark_test.assert_not_called()

    def test_withholds_pass_if_pr_head_changed_during_evaluation(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "created"}), \
                 mock.patch.object(ci_worker, "reset_pr_test", return_value={"action": "test_reset"}), \
                 mock.patch.object(ci_worker, "current_pr_head_sha", return_value="newer-head"), \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test:
                result = process_receipt(_receipt(), ctx)
            mark_test.assert_not_called()
            self.assertEqual(result["test"]["pass"]["reason"], "stale_head")

    def test_withholds_pass_if_old_test_state_cannot_be_reset(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp))
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "created"}), \
                 mock.patch.object(ci_worker, "reset_pr_test", side_effect=RuntimeError("reset unavailable")), \
                 mock.patch.object(ci_worker, "current_pr_head_sha") as current_head, \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test:
                result = process_receipt(_receipt(), ctx)
            current_head.assert_not_called()
            mark_test.assert_not_called()
            self.assertEqual(result["test"]["reset"]["action"], "error")
            self.assertEqual(result["test"]["pass"]["reason"], "test_reset_failed")

    def test_resets_old_pass_even_when_local_specs_head_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp))
            with mock.patch.object(
                ci_worker, "ensure_specs_at_sha", return_value=("old-head", False, "skipped_mismatch", None)
            ), mock.patch.object(
                ci_worker, "reset_pr_test", return_value={"action": "test_reset"}
            ) as reset:
                result = process_receipt(_receipt(), ctx)
            reset.assert_called_once()
            self.assertEqual(result["status"], "skipped_mismatch")
            self.assertEqual(result["test"]["reset"]["action"], "test_reset")

    def test_force_mode_uses_admin_reset_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._passing_ctx(Path(tmp), force_test=True)
            with mock.patch.object(
                ci_worker, "ensure_specs_at_sha", return_value=("old-head", False, "skipped_mismatch", None)
            ), mock.patch.object(
                ci_worker, "reset_pr_test", return_value={"action": "test_reset_all"}
            ) as reset:
                process_receipt(_receipt(), ctx)
            reset.assert_called_once_with("arkui_architecture/arkui-specs", 61, reset_all=True)


class RunSpecsChecksTest(unittest.TestCase):
    @staticmethod
    def _proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> mock.Mock:
        return mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)

    def test_returns_one_result_per_check_in_stable_order(self) -> None:
        with mock.patch("spec_eval.ci_worker.subprocess.run", side_effect=[
            self._proc(0, "index.md is up to date\n"),
            self._proc(0, "validate_specs: 0 error(s)\n"),
        ]):
            results = run_specs_checks(specs_root=Path("/tmp/specs"))
        self.assertEqual([r.name for r in results], ["generate_index", "validate_specs"])
        self.assertTrue(all(r.passed for r in results))

    def test_invokes_expected_scripts_with_specs_root_cwd(self) -> None:
        captured: list = []

        def fake_run(cmd, **kw):
            captured.append((cmd, kw.get("cwd")))
            return self._proc()

        with mock.patch("spec_eval.ci_worker.subprocess.run", side_effect=fake_run):
            run_specs_checks(specs_root=Path("/tmp/specs"), python="python3.11")
        self.assertEqual(captured[0][0], ["python3.11", "/tmp/specs/tools/generate_index.py", "--check"])
        self.assertEqual(captured[1][0], ["python3.11", "/tmp/specs/tools/validate_specs.py"])
        self.assertEqual(captured[0][1], "/tmp/specs")

    def test_records_nonzero_without_raising(self) -> None:
        with mock.patch("spec_eval.ci_worker.subprocess.run", return_value=self._proc(1, "", "boom")):
            results = run_specs_checks(specs_root=Path("/tmp/specs"))
        self.assertEqual([r.exit_code for r in results], [1, 1])
        self.assertFalse(any(r.passed for r in results))
        self.assertEqual(results[0].stderr, "boom")


class SpecsChecksPassedTest(unittest.TestCase):
    def test_none_or_empty_is_passed(self) -> None:
        self.assertTrue(specs_checks_passed(None))
        self.assertTrue(specs_checks_passed([]))

    def test_all_passed(self) -> None:
        self.assertTrue(specs_checks_passed(_specs_ok()))

    def test_one_failed(self) -> None:
        self.assertFalse(specs_checks_passed(_specs_failed()))


class RenderCommentSpecsTest(unittest.TestCase):
    def _summary(self) -> dict:
        return json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))

    def test_specs_failure_block_present_and_keeps_ci_result(self) -> None:
        body = render_comment(
            self._summary(), _receipt(),
            shas={"tested": "936b9f4abc", "target": "dd3687695c"},
            ensure_action="matched", specs_checks=_specs_failed(),
        )
        self.assertIn(COMMENT_MARKER, body)
        self.assertIn("完整性检查失败", body)
        self.assertIn("已拦截", body)
        self.assertIn("validate_specs", body)
        self.assertIn("missing AC entries", body)
        # Header table summarizes pass/fail per check.
        self.assertIn("✅ generate_index", body)
        self.assertIn("❌ validate_specs", body)
        self.assertIn("python3 tools/generate_index.py --check", body)
        self.assertIn("python3 tools/validate_specs.py", body)
        # ci_runner still ran (continue-on-failure policy); its result stays visible.
        self.assertIn("report-only", body)

    def test_specs_passed_omits_block(self) -> None:
        body = render_comment(
            self._summary(), _receipt(),
            shas={"tested": "936b9f4abc", "target": "dd3687695c"},
            ensure_action="matched", specs_checks=_specs_ok(),
        )
        self.assertNotIn("完整性检查失败", body)
        self.assertNotIn("已拦截", body)
        # Header table surfaces a one-line ✅ confirmation when checks ran clean.
        self.assertIn("| **Specs checks**", body)
        self.assertIn("✅ generate_index", body)
        self.assertIn("✅ validate_specs", body)

    def test_specs_none_is_backward_compatible(self) -> None:
        body = render_comment(
            self._summary(), _receipt(),
            shas={"tested": "936b9f4abc", "target": "dd3687695c"},
            ensure_action="matched",
        )
        self.assertNotIn("完整性检查失败", body)
        self.assertNotIn("Specs checks", body)

    def test_long_output_is_truncated(self) -> None:
        long_stderr = "\n".join(f"ERROR: file-{i}.md: boom" for i in range(200))
        results = [_check("generate_index", 0), _check("validate_specs", 1, stderr=long_stderr)]
        body = render_comment(
            self._summary(), _receipt(),
            shas={"tested": "936b9f4abc", "target": "dd3687695c"},
            ensure_action="matched", specs_checks=results,
        )
        self.assertIn("truncated", body)


class ProcessReceiptSpecsTest(unittest.TestCase):
    def _ctx_with_checks(self, tmp_path: Path, **overrides: object) -> WorkerContext:
        return _ctx(tmp_path, specs_checks_enabled=True, **overrides)

    def test_specs_failure_marks_failed_but_still_runs_ci_runner(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx_with_checks(Path(tmp), dry_run=True)
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "run_specs_checks", return_value=_specs_failed()), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")) as runner:
                result = process_receipt(_receipt(), ctx)
            self.assertEqual(result["status"], "specs_check_failed")
            runner.assert_called_once()  # continue-on-failure: ci_runner still runs
            archive = Path(result["archive_dir"])
            self.assertTrue((archive / "specs-checks.json").is_file())
            self.assertTrue((archive / "comment-body.md").is_file())
            meta = json.loads((archive / "run-meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["status"], "specs_check_failed")
            self.assertIsNotNone(meta["specs_checks"])
            self.assertTrue(meta["specs_checks"][0]["passed"])
            self.assertFalse(meta["specs_checks"][1]["passed"])

    def test_specs_failure_withholds_test_pass(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx_with_checks(Path(tmp), test_on_pass=True, dry_run=False)
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "run_specs_checks", return_value=_specs_failed()), \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")), \
                 mock.patch.object(ci_worker, "post_comment", return_value={"action": "created"}), \
                 mock.patch.object(ci_worker, "reset_pr_test", return_value={"action": "test_reset"}), \
                 mock.patch.object(ci_worker, "current_pr_head_sha") as current_head, \
                 mock.patch.object(ci_worker, "mark_pr_test_passed") as mark_test:
                result = process_receipt(_receipt(), ctx)
            current_head.assert_not_called()
            mark_test.assert_not_called()
            self.assertEqual(result["test"]["pass"]["reason"], "specs_check_failed")

    def test_specs_passed_proceeds_normally(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx_with_checks(Path(tmp), dry_run=True)
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "run_specs_checks", return_value=_specs_ok()) as specs_runner, \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")):
                result = process_receipt(_receipt(), ctx)
            specs_runner.assert_called_once()
            self.assertEqual(result["status"], "ok")
            archive = Path(result["archive_dir"])
            self.assertTrue((archive / "specs-checks.json").is_file())

    def test_disabled_when_specs_checks_enabled_false(self) -> None:
        summary = json.loads((FIXTURES / "ci-summary-0-affected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(Path(tmp), dry_run=True)  # _ctx default: specs_checks_enabled=False
            self.assertFalse(ctx.specs_checks_enabled)
            with mock.patch.object(ci_worker, "ensure_specs_at_sha", return_value=("936b9f4", True, "matched", None)), \
                 mock.patch.object(ci_worker, "run_specs_checks") as specs_runner, \
                 mock.patch.object(ci_worker, "compute_changed_files", return_value=(["specs/x"], "ok")), \
                 mock.patch.object(ci_worker, "run_ci_runner", return_value=(summary, 0, 1.0, "")):
                result = process_receipt(_receipt(), ctx)
            specs_runner.assert_not_called()
            self.assertEqual(result["status"], "ok")
            archive = Path(result["archive_dir"])
            self.assertFalse((archive / "specs-checks.json").is_file())


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
