"""Deterministic Observation correction and JSON Patch support.

Correction is deliberately split into two paths:

* safe structural/ownership repairs are applied by the service without a
  model call; and
* evidence or semantic errors are sent to the executor as a bounded JSON Patch
  turn.

Patches target the already-normalized published candidate.  The service owns
  patch application and validation; the executor never replaces the complete
  staged document during a correction turn.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Iterable

from spec_eval.kernel import contracts as K
from spec_eval.kernel.errors import TypedError
from spec_eval.kernel.normalize import DEFECT_KEY


# Correction routing is intentionally conservative.  Only evidence and
# semantic-content errors may consume a model turn.  Field/enum/coverage/
# ownership/mapping errors are service-owned: a safe canonical repair is
# attempted, otherwise the work item terminates without asking the model to
# invent structure or IDs.
MODEL_CORRECTION_ERROR_CODES = frozenset({
    # Evidence declaration, path and cardinality problems.
    "EVIDENCE_DECLARATION_INVALID",
    "EVIDENCE_KEY_DUPLICATED",
    "EVIDENCE_PATH_NOT_ALLOWED",
    "EVIDENCE_PATH_NOT_FOUND",
    "EVIDENCE_KEY_UNKNOWN",
    "EVIDENCE_CARDINALITY_VIOLATED",
    "NV_INSPECTION_EVIDENCE_MISSING",
    "GAP_MISSING_FOR_NV",
    "GAP_FIELD_INSUFFICIENT",
    "CRITERION_EVIDENCE_UNKNOWN",
    "FINDING_EVIDENCE_UNKNOWN",
    "EVIDENCE_TYPE_MISSING",
    "EVIDENCE_REQUIRED_MISSING",
    # Semantic prose and semantic basis problems.
    "REASON_PLACEHOLDER",
    "REASON_LOW_INFORMATION",
    "MODELING_BASIS_MISSING",
    "MODELING_BASIS_INVALID",
    "POLICY_BASIS_INVALID",
    "CONTRADICTION_BASIS_INVALID",
    "MAPPING_CONCLUSION_FORBIDDEN",
    "MAPPING_NV_REQUIRED",
    "SEVERITY_BELOW_FLOOR",
    "NOT_APPLICABLE_FORBIDDEN",
    "CROSS_FEAT_NOT_REVIEWED",
    "QUALITY_HIGH_NV_RATIO",
    "QUALITY_DUPLICATE_TEXT",
    "QUALITY_OBSERVATION_DENSITY",
})

# These codes are safe to handle without asking a model to re-evaluate the
# document.  The set is the complement of MODEL_CORRECTION_ERROR_CODES for
# known validator errors; keeping the explicit name preserves the routing API
# used by the pipeline and tests.
DETERMINISTIC_ERROR_CODES = frozenset({
    "CLAIM_SET_MISMATCH",
    "CLAIM_ROW_DUPLICATED",
    "CLAIM_OUTCOME_INVALID",
    "UNIT_ROW_INVALID",
    "UNIT_CLAIM_OUTCOME_CONFLICT",
    "CHECK_COVERAGE_INCOMPLETE",
    "CRITERION_UNKNOWN",
    "OBSERVATION_CLAIM_UNEXPECTED",
    "OBSERVATION_CLAIM_IDS_EMPTY",
    "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE",
    "OBSERVATION_FIELD_INVALID",
    "DEFECT_KEYS_INVALID",
    "DEFECT_KEY_UNDEFINED",
    "CRITERION_SET_MISMATCH",
    "MAPPING_CLAIM_UNMAPPED",
    "FINDING_CARDINALITY_VIOLATED",
    "FINDING_OWNER_UNKNOWN",
    "FINDING_MULTI_OWNED",
    "CRITICAL_NOT_PRIMARY",
    "DUPLICATE_DEFECT_OWNER",
})


def is_deterministic_error(error: TypedError | dict[str, Any]) -> bool:
    code = error.code if isinstance(error, TypedError) else error.get("code")
    # Unknown codes are never delegated implicitly.  New semantic/evidence
    # codes must be added to MODEL_CORRECTION_ERROR_CODES deliberately.
    return str(code) not in MODEL_CORRECTION_ERROR_CODES


def is_model_correction_error(error: TypedError | dict[str, Any]) -> bool:
    code = error.code if isinstance(error, TypedError) else error.get("code")
    return str(code) in MODEL_CORRECTION_ERROR_CODES


def _rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _canonical_outcome(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = re.sub(r"[^A-Za-z]+", "_", value.strip()).upper().strip("_")
    return normalized if normalized in K.LOCAL_OUTCOMES else None


def _path_index(path: str, collection: str) -> int | None:
    match = re.search(rf"{re.escape(collection)}\[(\d+)\]", path)
    return int(match.group(1)) if match else None


def _claim_owned_defects(document: dict[str, Any], claim_id: str) -> set[str]:
    result: set[str] = set()
    for row in _rows(document.get("observations")):
        if claim_id in (row.get("claim_ids") or []):
            key = row.get("defect_key")
            if isinstance(key, str) and key:
                result.add(key)
    return result


def apply_deterministic_correction(
    document: dict[str, Any],
    errors: Iterable[TypedError | dict[str, Any]],
) -> tuple[dict[str, Any], list[str], list[TypedError]]:
    """Apply only safe structural repairs and return unresolved errors.

    A defect key is mapped only when the Claim's Observation ownership yields
    one unambiguous key.  No semantic conclusion, reason, evidence or source
    assertion is inferred here.
    """
    corrected = copy.deepcopy(document)
    changes: list[str] = []
    unresolved: list[TypedError] = []
    for raw_error in errors:
        error = raw_error if isinstance(raw_error, TypedError) else TypedError.from_dict(raw_error)
        if not is_deterministic_error(error):
            continue

        if error.code == "CLAIM_OUTCOME_INVALID":
            index = _path_index(error.path, "claim_reviews")
            rows = _rows(corrected.get("claim_reviews"))
            canonical = _canonical_outcome(rows[index].get("local_outcome")) if index is not None and index < len(rows) else None
            if canonical is None:
                unresolved.append(error)
            else:
                rows[index]["local_outcome"] = canonical
                changes.append(f"claim_reviews[{index}].local_outcome canonicalized")
            continue

        if error.code == "DEFECT_KEYS_INVALID":
            if ".claim_reviews[" in error.path:
                index = _path_index(error.path, "claim_reviews")
                rows = _rows(corrected.get("claim_reviews"))
                if index is None or index >= len(rows):
                    unresolved.append(error)
                    continue
                if rows[index].get("local_outcome") not in {"CONFLICT", "MISSING"}:
                    rows[index]["defect_keys"] = []
                    changes.append(f"claim_reviews[{index}].defect_keys cleared")
                else:
                    values = [str(value).strip().lower() for value in rows[index].get("defect_keys", []) if isinstance(value, str) and value.strip()]
                    if all(DEFECT_KEY.fullmatch(value) for value in values):
                        rows[index]["defect_keys"] = values
                        changes.append(f"claim_reviews[{index}].defect_keys canonicalized")
                    else:
                        unresolved.append(error)
            elif ".observations[" in error.path:
                index = _path_index(error.path, "observations")
                rows = _rows(corrected.get("observations"))
                if index is None or index >= len(rows):
                    unresolved.append(error)
                    continue
                if rows[index].get("local_outcome") not in {"CONFLICT", "MISSING"}:
                    rows[index]["defect_key"] = None
                    rows[index]["primary_criterion_id"] = None
                    changes.append(f"observations[{index}] defect ownership cleared")
                else:
                    key = rows[index].get("defect_key")
                    if isinstance(key, str) and DEFECT_KEY.fullmatch(key.strip().lower()):
                        rows[index]["defect_key"] = key.strip().lower()
                        changes.append(f"observations[{index}].defect_key canonicalized")
                    else:
                        unresolved.append(error)
            else:
                unresolved.append(error)
            continue

        if error.code != "DEFECT_KEY_UNDEFINED":
            # Structural field/mapping errors without a safe canonical repair
            # are terminal service errors; they are never delegated to a
            # semantic model correction.
            unresolved.append(error)
            continue

        # DEFECT_KEY_UNDEFINED: bind a Claim to its owning Observation only
        # when the relationship has exactly one possible defect key.
        index = _path_index(error.path, "claim_reviews")
        rows = _rows(corrected.get("claim_reviews"))
        if index is None or index >= len(rows):
            unresolved.append(error)
            continue
        claim_id = rows[index].get("claim_id")
        candidates = _claim_owned_defects(corrected, str(claim_id))
        if len(candidates) != 1:
            unresolved.append(error)
            continue
        rows[index]["defect_keys"] = [next(iter(candidates))]
        changes.append(f"claim_reviews[{index}].defect_keys mapped to owning observation")

    return corrected, changes, unresolved


def _decode_pointer(path: str) -> list[str]:
    if path == "":
        return []
    if not path.startswith("/"):
        raise ValueError("JSON Patch path must be an absolute JSON Pointer")
    return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]


def _index_or_key(token: str, parent: Any, *, allow_append: bool = False) -> int | str:
    if isinstance(parent, list):
        if token == "-" and allow_append:
            return len(parent)
        try:
            index = int(token)
        except ValueError as exc:
            raise ValueError(f"array JSON Pointer token is not an index: {token}") from exc
        if index < 0 or index > len(parent):
            raise ValueError(f"array JSON Pointer index out of range: {token}")
        return index
    if isinstance(parent, dict):
        return token
    raise ValueError("JSON Patch parent is not an object or array")


def apply_json_patch(document: dict[str, Any], patches: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Apply a small RFC-6902 subset (add/remove/replace) to a copy."""
    result = copy.deepcopy(document)
    for patch in patches:
        if not isinstance(patch, dict):
            raise ValueError("patch entry must be an object")
        operation = patch.get("op")
        path = patch.get("path")
        if operation not in {"add", "remove", "replace"} or not isinstance(path, str):
            raise ValueError("patch requires op in add/remove/replace and a path")
        raw_value = patch.get("value")
        if isinstance(raw_value, str):
            try:
                patch_value = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"patch value is not valid JSON: {exc}") from exc
        else:
            # Native values are accepted by the service helper for unit tests
            # and internal callers; executor transport remains string-only.
            patch_value = raw_value
        tokens = _decode_pointer(path)
        if not tokens:
            if operation == "remove":
                raise ValueError("cannot remove the document root")
            value = patch_value
            if not isinstance(value, dict):
                raise ValueError("document root replacement must be an object")
            result = copy.deepcopy(value)
            continue
        parent: Any = result
        for token in tokens[:-1]:
            if isinstance(parent, list):
                parent = parent[int(token)]
            elif isinstance(parent, dict) and token in parent:
                parent = parent[token]
            else:
                raise ValueError(f"JSON Patch parent does not exist: {path}")
        token = tokens[-1]
        if isinstance(parent, list):
            index = _index_or_key(token, parent, allow_append=operation == "add")
            assert isinstance(index, int)
            if operation == "add":
                parent.insert(index, copy.deepcopy(patch_value))
            elif operation == "replace":
                if index >= len(parent):
                    raise ValueError(f"JSON Patch replace index out of range: {path}")
                parent[index] = copy.deepcopy(patch_value)
            else:
                if index >= len(parent):
                    raise ValueError(f"JSON Patch remove index out of range: {path}")
                parent.pop(index)
        elif isinstance(parent, dict):
            if operation == "add" or operation == "replace":
                if operation == "replace" and token not in parent:
                    raise ValueError(f"JSON Patch replace key does not exist: {path}")
                parent[token] = copy.deepcopy(patch_value)
            else:
                if token not in parent:
                    raise ValueError(f"JSON Patch remove key does not exist: {path}")
                del parent[token]
        else:
            raise ValueError(f"JSON Patch parent is not patchable: {path}")
    return result


def typed_error_json_path(path: str) -> str:
    """Convert validator paths to a JSON Pointer prefix for correction scope."""
    value = path
    for prefix in ("observation.", "aggregation."):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    if value.startswith("$."):
        value = value[2:]
    elif value.startswith("$"):
        value = value[1:]
    value = re.sub(r"\.([A-Za-z_][A-Za-z0-9_-]*)", r"/\1", value)
    # Validator paths use both numeric list indices and string keys such as
    # criterion_results[FUNCTION-FEAT-COVERAGE]. Convert either form to a
    # JSON Pointer token and escape RFC-6901 special characters.
    value = re.sub(r"\[([^\]]+)\]", r"/\1", value)
    if not value.startswith("/"):
        value = "/" + value
    return "/".join(
        token.replace("~", "~0").replace("/", "~1")
        for token in value.split("/")
    )


def validate_patch_scope(
    patches: Iterable[dict[str, Any]],
    *,
    allowed_paths: Iterable[str],
    immutable_paths: Iterable[str],
) -> list[str]:
    """Return patch-scope violations before a patch is applied."""
    allowed = tuple(str(path).rstrip("/") for path in allowed_paths if path)
    immutable = tuple(str(path).rstrip("/") for path in immutable_paths if path)
    violations: list[str] = []
    for patch in patches:
        path = patch.get("path") if isinstance(patch, dict) else None
        if not isinstance(path, str):
            violations.append("patch path is not a string")
            continue
        normalized = path.rstrip("/") or "/"
        if any(
            normalized == prefix
            or normalized.startswith(prefix + "/")
            for prefix in immutable
        ):
            violations.append(f"immutable patch path: {path}")
            continue
        if allowed and not any(
            normalized == prefix
            or normalized.startswith(prefix + "/")
            for prefix in allowed
        ):
            violations.append(f"patch path outside correction scope: {path}")
    return violations
