"""ExecutorRegistry + UI pipeline stepper tests (protocol 0.2.0 wrap-up)."""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import Job, default_progress
from spec_eval.service.executors import registry
from spec_eval.service.http.serializers import job_to_dict


# ---------------------------------------------------------------------------
# ExecutorRegistry tests
# ---------------------------------------------------------------------------


class ExecutorRegistryTest(unittest.TestCase):
    """Verify the pluggable executor registry (design §10)."""

    def test_codex_is_registered_by_default(self) -> None:
        self.assertIn("codex", registry.available())

    def test_default_executor_is_codex(self) -> None:
        self.assertEqual(registry.DEFAULT_EXECUTOR, "codex")

    def test_get_factory_returns_callable(self) -> None:
        factory = registry.get_factory("codex")
        self.assertTrue(callable(factory))

    def test_unknown_executor_raises_key_error(self) -> None:
        with self.assertRaises(KeyError) as cm:
            registry.get_factory("nonexistent")
        self.assertIn("nonexistent", str(cm.exception))

    def test_register_and_unregister(self) -> None:
        sentinel = object()

        def fake_factory(config: dict, schemas_root: Path) -> Any:
            return sentinel

        registry.register("test_fake", fake_factory)
        try:
            self.assertIn("test_fake", registry.available())
            self.assertIs(registry.get_factory("test_fake"), fake_factory)
        finally:
            removed = registry.unregister("test_fake")
            self.assertIs(removed, fake_factory)
        self.assertNotIn("test_fake", registry.available())

    def test_unregister_missing_returns_none(self) -> None:
        self.assertIsNone(registry.unregister("never_registered"))

    def test_register_rejects_invalid_name(self) -> None:
        with self.assertRaises(ValueError):
            registry.register("", lambda c, s: None)
        with self.assertRaises(ValueError):
            registry.register("has-dash", lambda c, s: None)

    def test_register_replaces_existing(self) -> None:
        original = registry.get_factory("codex")
        replacement = lambda c, s: None  # noqa: E731
        registry.register("codex", replacement)
        try:
            self.assertIs(registry.get_factory("codex"), replacement)
        finally:
            registry.register("codex", original)

    def test_available_returns_sorted_tuple(self) -> None:
        result = registry.available()
        self.assertIsInstance(result, tuple)
        self.assertEqual(list(result), sorted(result))


# ---------------------------------------------------------------------------
# UI pipeline stepper tests
# ---------------------------------------------------------------------------


def _make_job(
    status: str = S.QUEUED,
    stage: str = S.STAGE_PREPARING,
) -> Job:
    return Job(
        job_id="t" * 40,
        func_id="01-01-01",
        source_revision="a" * 40,
        run_count=1,
        selected_run_ids=(),
        status=status,
        stage=stage,
        progress=default_progress(status),
        executor_config={},
        protocol_version="0.2.0",
        evaluator_version="test",
        created_at="2026-08-17T00:00:00+00:00",
        updated_at="2026-08-17T00:00:00+00:00",
    )


class PipelineStepperTest(unittest.TestCase):
    """Verify the six-segment pipeline stepper in job_to_dict (design D4)."""

    def test_queued_job_all_pending(self) -> None:
        doc = job_to_dict(_make_job(S.QUEUED, S.STAGE_PREPARING))
        self.assertEqual(doc["stage"], S.STAGE_PREPARING)
        pipeline = doc["pipeline"]
        self.assertEqual(len(pipeline), len(S.STAGES))
        for seg in pipeline:
            self.assertEqual(seg["state"], "pending")

    def test_running_at_observation(self) -> None:
        doc = job_to_dict(_make_job(S.RUNNING, S.STAGE_OBSERVATION))
        pipeline = doc["pipeline"]
        states = {seg["stage"]: seg["state"] for seg in pipeline}
        self.assertEqual(states[S.STAGE_PREPARING], "completed")
        self.assertEqual(states[S.STAGE_EVIDENCE], "completed")
        self.assertEqual(states[S.STAGE_OBSERVATION], "active")
        self.assertEqual(states[S.STAGE_AGGREGATION], "pending")
        self.assertEqual(states[S.STAGE_REPORT], "pending")
        self.assertEqual(states[S.STAGE_ARCHIVE], "pending")
        self.assertEqual(states[S.STAGE_PROJECTION], "pending")

    def test_waiting_at_evidence(self) -> None:
        doc = job_to_dict(_make_job(S.WAITING, S.STAGE_EVIDENCE))
        pipeline = doc["pipeline"]
        states = {seg["stage"]: seg["state"] for seg in pipeline}
        self.assertEqual(states[S.STAGE_PREPARING], "completed")
        self.assertEqual(states[S.STAGE_EVIDENCE], "waiting")
        self.assertEqual(states[S.STAGE_OBSERVATION], "pending")

    def test_completed_job_all_completed(self) -> None:
        doc = job_to_dict(_make_job(S.COMPLETED, S.STAGE_PROJECTION))
        pipeline = doc["pipeline"]
        for seg in pipeline:
            self.assertEqual(seg["state"], "completed", seg["stage"])

    def test_failed_at_aggregation(self) -> None:
        doc = job_to_dict(_make_job(S.FAILED, S.STAGE_AGGREGATION))
        pipeline = doc["pipeline"]
        states = {seg["stage"]: seg["state"] for seg in pipeline}
        self.assertEqual(states[S.STAGE_PREPARING], "completed")
        self.assertEqual(states[S.STAGE_EVIDENCE], "completed")
        self.assertEqual(states[S.STAGE_OBSERVATION], "completed")
        self.assertEqual(states[S.STAGE_AGGREGATION], "failed")
        self.assertEqual(states[S.STAGE_REPORT], "skipped")
        self.assertEqual(states[S.STAGE_ARCHIVE], "skipped")
        self.assertEqual(states[S.STAGE_PROJECTION], "skipped")

    def test_cancelled_at_observation(self) -> None:
        doc = job_to_dict(_make_job(S.CANCELLED, S.STAGE_OBSERVATION))
        pipeline = doc["pipeline"]
        states = {seg["stage"]: seg["state"] for seg in pipeline}
        self.assertEqual(states[S.STAGE_PREPARING], "completed")
        self.assertEqual(states[S.STAGE_EVIDENCE], "completed")
        self.assertEqual(states[S.STAGE_OBSERVATION], "skipped")
        self.assertEqual(states[S.STAGE_REPORT], "skipped")

    def test_pipeline_stage_names_match_states_module(self) -> None:
        doc = job_to_dict(_make_job(S.RUNNING, S.STAGE_PREPARING))
        stage_names = [seg["stage"] for seg in doc["pipeline"]]
        self.assertEqual(stage_names, list(S.STAGES))

    def test_stage_field_present_in_serialized_job(self) -> None:
        doc = job_to_dict(_make_job(S.RUNNING, S.STAGE_ARCHIVE))
        self.assertEqual(doc["stage"], S.STAGE_ARCHIVE)

    def test_running_at_first_stage(self) -> None:
        doc = job_to_dict(_make_job(S.RUNNING, S.STAGE_PREPARING))
        pipeline = doc["pipeline"]
        self.assertEqual(pipeline[0]["state"], "active")
        for seg in pipeline[1:]:
            self.assertEqual(seg["state"], "pending", seg["stage"])


if __name__ == "__main__":
    unittest.main()
