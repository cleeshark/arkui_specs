"""Aggregate deterministic evaluator performance metrics."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


class PerformanceReporter:
    def build(
        self,
        values: Iterable[dict[str, Any]],
        *,
        source_revision: str,
        total_ms: float,
        preparation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        functions = sorted(
            (dict(value) for value in values if value),
            key=lambda value: str(value.get("func_id", "")),
        )
        durations = [float(value.get("total_ms", 0.0) or 0.0) for value in functions]
        phase_totals: dict[str, float] = defaultdict(float)
        for value in functions:
            for name, duration in value.get("phases_ms", {}).items():
                phase_totals[str(name)] += float(duration or 0.0)
        return {
            "schema_version": 1,
            "source_revision": source_revision,
            "total_ms": round(float(total_ms), 3),
            "function_count": len(functions),
            "cached_function_count": sum(1 for value in functions if value.get("cached")),
            "function_duration_ms": {
                "p50": self._percentile(durations, 0.50),
                "p95": self._percentile(durations, 0.95),
                "max": round(max(durations), 3) if durations else 0.0,
            },
            "phase_totals_ms": {name: round(value, 3) for name, value in sorted(phase_totals.items())},
            "preparation": preparation or {},
            "functions": functions,
        }

    @staticmethod
    def write(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = max(0, math.ceil(len(ordered) * percentile) - 1)
        return round(ordered[index], 3)
