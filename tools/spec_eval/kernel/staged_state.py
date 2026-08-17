"""Staged run state maintenance for protocol 0.2.0 (service in-process).

Port of the skill-side ``update_progress`` so the service can checkpoint a
validated work item without a subprocess round-trip. The run-state.json /
work-items.json shapes are unchanged: the skill CLI and the service remain
interoperable on the same run directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Work item execution states (design v3 R3).
GENERATE_PENDING = "GENERATE_PENDING"
GENERATED_INVALID = "GENERATED_INVALID"
CORRECTION_PENDING = "CORRECTION_PENDING"
VALIDATED = "VALIDATED"
CORRECTION_INVALID_TERMINAL = "CORRECTION_INVALID_TERMINAL"


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def write_json_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def work_item_state(run_dir: Path, work_item_id: str) -> str | None:
    """Return the persisted execution state of one work item, if any."""
    items_path = run_dir / "work-items.json"
    if items_path.is_file():
        state = load_json_object(items_path)
        for item in state.get("items", []):
            if isinstance(item, dict) and item.get("id") == work_item_id:
                value = item.get("execution_state")
                return value if isinstance(value, str) else None
    run_state_path = run_dir / "run-state.json"
    if run_state_path.is_file():
        run_state = load_json_object(run_state_path)
        pseudo = run_state.get("pseudo_work_item_states", {})
        value = pseudo.get(work_item_id) if isinstance(pseudo, dict) else None
        return value if isinstance(value, str) else None
    return None


def set_work_item_state(
    run_dir: Path, work_item_id: str, execution_state: str
) -> None:
    """Persist one work item's execution state (state machine, design R3).

    Kept separate from the legacy ``status`` field: ``status`` remains the
    published-progress flag (pending/complete) that the skill CLI and
    show_next_work_item consume. Pseudo work items that are not listed in
    work-items.json (e.g. ``aggregation:final``) are recorded on the run
    state document instead.
    """
    path = run_dir / "work-items.json"
    state = load_json_object(path)
    for item in state.get("items", []):
        if isinstance(item, dict) and item.get("id") == work_item_id:
            item["execution_state"] = execution_state
            write_json_object(path, state)
            return
    run_state_path = run_dir / "run-state.json"
    run_state = (
        load_json_object(run_state_path)
        if run_state_path.is_file() else {}
    )
    pseudo = run_state.setdefault("pseudo_work_item_states", {})
    pseudo[work_item_id] = execution_state
    write_json_object(run_state_path, run_state)


def update_progress(
    run_dir: Path,
    state: dict[str, Any],
    work_items: dict[str, Any],
    *,
    stage: str,
    work_item_id: str | None = None,
) -> None:
    """Record one validated checkpoint (same semantics as the skill script)."""
    validated = set(state.get("validated_work_items", []))
    if work_item_id is not None:
        validated.add(work_item_id)
    elif stage in {"observations", "aggregation", "final"}:
        validated.update(
            item["id"] for item in work_items.get("items", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        )
    state["validated_work_items"] = [
        item["id"] for item in work_items.get("items", [])
        if isinstance(item, dict) and item.get("id") in validated
    ]
    for item in work_items.get("items", []):
        if isinstance(item, dict):
            item["status"] = "complete" if item.get("id") in validated else "pending"

    if stage in {"aggregation", "final"}:
        state["aggregation_validated"] = True
    if stage == "final":
        state["semantic_validated"] = True

    feature_ids = [
        item["id"] for item in work_items.get("items", [])
        if isinstance(item, dict) and item.get("type") == "feature"
    ]
    function_ids = [
        item["id"] for item in work_items.get("items", [])
        if isinstance(item, dict) and item.get("type") == "function_global"
    ]
    if any(item_id not in validated for item_id in feature_ids):
        phase = "feature_observations"
    elif any(item_id not in validated for item_id in function_ids):
        phase = "function_global"
    elif not state.get("aggregation_validated"):
        phase = "aggregation"
    elif not state.get("semantic_validated"):
        phase = "final_validation"
    else:
        phase = "complete"
    state["current_phase"] = phase
    write_json_object(run_dir / "work-items.json", work_items)
    write_json_object(run_dir / "run-state.json", state)
