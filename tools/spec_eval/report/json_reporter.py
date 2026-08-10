"""Write Function result and evidence JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from spec_eval.models.result import EvaluationRun


class JsonReporter:
    MAX_EVIDENCE_SHARD_BYTES = 2 * 1024 * 1024
    MAX_FUNCTION_EVIDENCE_BYTES = 8 * 1024 * 1024

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
        total_shard_bytes = 0
        largest_shard_bytes = 0
        for shard, claims in sorted(claims_by_shard.items()):
            shard_path = evidence_dir / f"{shard}.json"
            shard_bytes = self._write(
                shard_path,
                {"func_id": run.context.func_id, "source_revision": run.context.source_revision, "claims": claims},
            )
            total_shard_bytes += shard_bytes
            largest_shard_bytes = max(largest_shard_bytes, shard_bytes)
            shards.append(
                {
                    "name": shard,
                    "path": shard_path.name,
                    "claim_count": len(claims),
                    "bytes": shard_bytes,
                    "over_budget": shard_bytes > self.MAX_EVIDENCE_SHARD_BYTES,
                }
            )
        warnings = []
        oversized_shards = [item["name"] for item in shards if item["over_budget"]]
        if oversized_shards:
            warnings.append(
                {
                    "code": "EVIDENCE_SHARD_BUDGET_EXCEEDED",
                    "shards": oversized_shards,
                    "limit_bytes": self.MAX_EVIDENCE_SHARD_BYTES,
                }
            )
        if total_shard_bytes > self.MAX_FUNCTION_EVIDENCE_BYTES:
            warnings.append(
                {
                    "code": "EVIDENCE_FUNCTION_BUDGET_EXCEEDED",
                    "actual_bytes": total_shard_bytes,
                    "limit_bytes": self.MAX_FUNCTION_EVIDENCE_BYTES,
                }
            )
        self._write(
            target / "evidence-manifest.json",
            {
                "func_id": run.context.func_id,
                "source_revision": run.context.source_revision,
                "metrics": run.evidence.metrics,
                "shards": shards,
                "archive": {
                    "total_shard_bytes": total_shard_bytes,
                    "largest_shard_bytes": largest_shard_bytes,
                    "over_budget": bool(warnings),
                    "warnings": warnings,
                    "budget": {
                        "max_shard_bytes": self.MAX_EVIDENCE_SHARD_BYTES,
                        "max_function_bytes": self.MAX_FUNCTION_EVIDENCE_BYTES,
                    },
                },
            },
        )
        return target

    @staticmethod
    def _write(path: Path, value: dict) -> int:
        content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        path.write_text(content, encoding="utf-8")
        return len(content.encode("utf-8"))
