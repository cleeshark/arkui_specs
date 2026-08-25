"""The executor prompt requires Simplified-Chinese natural-language output.

Constrains only the semantic evaluator's free-text judgment fields (message,
reason, rationale, recommendation, notes); machine identifiers and enums stay
verbatim. Static scan messages are produced by Python rules and never pass
through this prompt, so they are unaffected.
"""

from __future__ import annotations

import unittest

from spec_eval.service.executors import contract as C
from spec_eval.service.executors._prompt import build_executor_prompt


def _work(prompt_extras: dict) -> C.WorkItemInput:
    return C.WorkItemInput(
        job_id="job-1",
        func_id="01-01-01",
        run_id="run-1",
        work_item_id="wi-1",
        work_item={"kind": "feature"},
        run_dir="/tmp/run",
        input_paths=(),
        executor_result_path="/tmp/out.json",
        repo_root="/tmp/repo",
        skill_version="skill@test",
        protocol_version="0.2.0",
        prompt_extras=prompt_extras,
    )


class ChineseOutputConstraintTest(unittest.TestCase):
    def _constraints(self, prompt_extras: dict) -> str:
        import json
        prompt = json.loads(build_executor_prompt(_work(prompt_extras)))
        return " ".join(prompt["constraints"])

    def test_observe_mode_requires_chinese(self) -> None:
        text = self._constraints({"mode": "observe"})
        self.assertIn("简体中文", text)
        self.assertIn("recommendation", text)
        # machine identifiers stay verbatim
        self.assertIn("rule_id", text)
        self.assertIn("verbatim", text)

    def test_aggregation_mode_requires_chinese(self) -> None:
        text = self._constraints({"mode": "observe", "observation_profile": "aggregation"})
        self.assertIn("简体中文", text)

    def test_correct_mode_requires_chinese(self) -> None:
        text = self._constraints({"mode": "correct"})
        self.assertIn("简体中文", text)

    def test_enums_and_ids_kept_untranslated(self) -> None:
        text = self._constraints({"mode": "observe"})
        for token in ("criterion_id", "conclusion", "severity", "gate", "evidence paths"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
