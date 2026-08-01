"""Write Function result and evidence JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from spec_eval.models import EvaluationRun


class JsonReporter:
    def write(self, run: EvaluationRun, output_root: Path, repo_root: Path) -> Path:
        target = output_root / run.context.source_revision / run.context.func_id
        target.mkdir(parents=True, exist_ok=True)
        self._write(target / "function-context.json", run.context.to_dict(repo_root))
        self._write(target / "static-result.json", run.static_result.to_dict())
        evidence_dir = target / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        claims_by_shard: dict[str, list[dict]] = {}
        for claim in run.evidence.claims:
            shard = claim.feat_id or "design"
            claims_by_shard.setdefault(shard, []).append(claim.to_dict())
        shards = []
        for shard, claims in sorted(claims_by_shard.items()):
            shard_path = evidence_dir / f"{shard}.json"
            self._write(shard_path, {"func_id": run.context.func_id, "source_revision": run.context.source_revision, "claims": claims})
            shards.append({"name": shard, "path": shard_path.name, "claim_count": len(claims)})
        self._write(
            target / "evidence-manifest.json",
            {
                "func_id": run.context.func_id,
                "source_revision": run.context.source_revision,
                "metrics": run.evidence.metrics,
                "shards": shards,
            },
        )
        return target

    @staticmethod
    def _write(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

