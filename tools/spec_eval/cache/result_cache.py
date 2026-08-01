"""Persist exact-input evaluation results outside the specs source tree."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ResultCache:
    def __init__(self, output_root: Path) -> None:
        self.root = output_root / ".cache"

    def path_for(self, func_id: str, fingerprint: str) -> Path:
        return self.root / func_id / f"{fingerprint}.json"

    def load(self, func_id: str, fingerprint: str) -> dict[str, Any] | None:
        path = self.path_for(func_id, fingerprint)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, func_id: str, fingerprint: str, result: dict[str, Any]) -> Path:
        path = self.path_for(func_id, fingerprint)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

