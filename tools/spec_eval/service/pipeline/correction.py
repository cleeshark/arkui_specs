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
from spec_eval.kernel.errors import (
    FATAL_INPUT,
    MODEL_CORRECTION,
    SERVICE_NORMALIZATION,
    TypedError,
    repairability_of,
)
from spec_eval.kernel.normalize import DEFECT_KEY


_OBSERVATION_SET_FIELDS = frozenset({"criterion_ids", "check_ids", "claim_ids"})
_CLAIM_SET_FIELDS = frozenset({"criterion_ids", "evidence_ids", "defect_keys"})
_UNIT_SET_FIELDS = frozenset({"evidence_ids"})
_PUBLISHED_FINDING_SEVERITIES = ("Info", "Minor", "Major", "Critical")


def error_repairability(error: TypedError | dict[str, Any]) -> str:
    """Return the Kernel-owned routing class; unknown codes fail closed."""
    code = error.code if isinstance(error, TypedError) else error.get("code")
    try:
        return repairability_of(str(code))
    except ValueError:
        return FATAL_INPUT


def is_deterministic_error(error: TypedError | dict[str, Any]) -> bool:
    return error_repairability(error) == SERVICE_NORMALIZATION


def is_model_correction_error(error: TypedError | dict[str, Any]) -> bool:
    return error_repairability(error) == MODEL_CORRECTION


def is_fatal_error(error: TypedError | dict[str, Any]) -> bool:
    return error_repairability(error) == FATAL_INPUT


def _rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


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


def _finding_by_identity(
    document: dict[str, Any], identity: str,
) -> tuple[int, int, dict[str, Any]] | None:
    for criterion_index, criterion in enumerate(_rows(document.get("criterion_results"))):
        for finding_index, finding in enumerate(_rows(criterion.get("findings"))):
            if identity in {finding.get("finding_id"), finding.get("key")}:
                return criterion_index, finding_index, finding
    return None


def _severity_floor(expected: str) -> str | None:
    match = re.search(r"severity\s*>=\s*(Info|Minor|Major|Critical)", expected)
    return match.group(1) if match else None


def _deduplicate_string_field(row: dict[str, Any], field: str) -> bool:
    values = row.get(field)
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value for value in values
    ):
        return False
    unique_values = list(dict.fromkeys(values))
    if unique_values == values:
        return False
    row[field] = unique_values
    return True


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

        if error.code == "SEVERITY_BELOW_FLOOR":
            located = _finding_by_identity(corrected, error.entity_id)
            floor = _severity_floor(error.expected)
            if located is None or floor is None:
                unresolved.append(error)
                continue
            criterion_index, finding_index, finding = located
            actual = finding.get("severity")
            if (
                actual not in _PUBLISHED_FINDING_SEVERITIES
                or _PUBLISHED_FINDING_SEVERITIES.index(actual)
                >= _PUBLISHED_FINDING_SEVERITIES.index(floor)
            ):
                unresolved.append(error)
                continue
            finding["severity"] = floor
            changes.append(
                f"criterion_results[{criterion_index}].findings[{finding_index}]."
                f"severity raised to {floor}"
            )
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

        if error.code == "OBSERVATION_FIELD_INVALID":
            field = error.path.rsplit(".", 1)[-1]
            row: dict[str, Any] | None = None
            label: str | None = None
            allowed_fields: frozenset[str] = frozenset()
            if ".unit_reviews[" in error.path:
                allowed_fields = _UNIT_SET_FIELDS
                claim_index = _path_index(error.path, "claim_reviews")
                claim_rows = _rows(corrected.get("claim_reviews"))
                unit_index = _path_index(error.path, "unit_reviews")
                if claim_index is not None and claim_index < len(claim_rows):
                    unit_rows = _rows(claim_rows[claim_index].get("unit_reviews"))
                    if unit_index is not None and unit_index < len(unit_rows):
                        row = unit_rows[unit_index]
                        label = (
                            f"claim_reviews[{claim_index}].unit_reviews[{unit_index}]"
                        )
            elif ".claim_reviews[" in error.path:
                allowed_fields = _CLAIM_SET_FIELDS
                index = _path_index(error.path, "claim_reviews")
                rows = _rows(corrected.get("claim_reviews"))
                if index is not None and index < len(rows):
                    row = rows[index]
                    label = f"claim_reviews[{index}]"
            elif ".observations[" in error.path:
                allowed_fields = _OBSERVATION_SET_FIELDS
                index = _path_index(error.path, "observations")
                rows = _rows(corrected.get("observations"))
                if index is not None and index < len(rows):
                    row = rows[index]
                    label = f"observations[{index}]"
            if (
                field not in allowed_fields
                or row is None
                or label is None
                or not _deduplicate_string_field(row, field)
            ):
                unresolved.append(error)
            else:
                changes.append(f"{label}.{field} deduplicated")
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
                elif error.path.endswith(".primary_criterion_id"):
                    primary = rows[index].get("primary_criterion_id")
                    criterion_ids = rows[index].get("criterion_ids")
                    if not isinstance(primary, str) or not isinstance(criterion_ids, list):
                        unresolved.append(error)
                    elif primary not in criterion_ids:
                        criterion_ids.append(primary)
                        changes.append(
                            f"observations[{index}].criterion_ids added primary criterion"
                        )
                    else:
                        unresolved.append(error)
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
            except json.JSONDecodeError:
                # Older correction contracts transport every value as a
                # string, but a plain scalar string (for example
                # ``"Critical"``) is already a valid RFC-6902 value and is
                # not itself a JSON document. Preserve it when the legacy
                # decoding attempt does not apply.
                patch_value = raw_value
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
    """Convert a validator path to a diagnostic JSON Pointer-like path.

    Validator paths may use semantic list selectors such as
    ``criterion_results[CRITERION-ID]`` or ``findings[]``.  Those selectors
    are useful in errors and prompts, but are not executable RFC-6901 array
    indices.  Use :func:`resolve_typed_error_json_path` before exposing a path
    as a Correction ``allowed_path``.
    """
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


_LIST_IDENTITY_FIELDS: dict[str, tuple[str, ...]] = {
    "criterion_results": ("criterion_id",),
    "findings": ("finding_id", "key"),
}


def _encode_pointer(tokens: Iterable[str]) -> str:
    return "/" + "/".join(
        token.replace("~", "~0").replace("/", "~1")
        for token in tokens
    )


def _identity_index(
    rows: list[Any], *, collection: str, selector: str,
) -> int:
    fields = _LIST_IDENTITY_FIELDS.get(collection)
    if not fields:
        raise ValueError(
            f"validator path uses a named selector for unsupported list {collection!r}"
        )
    matches = [
        index
        for index, row in enumerate(rows)
        if isinstance(row, dict)
        and any(row.get(field) == selector for field in fields)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"validator path cannot uniquely locate {collection}[{selector}]: "
            f"matched {len(matches)} rows"
        )
    return matches[0]


def resolve_typed_error_json_path(
    document: dict[str, Any], error: TypedError | dict[str, Any],
) -> str:
    """Resolve one validator path to an executable RFC-6901 JSON Pointer.

    Named selectors are resolved against the immutable Correction candidate.
    Empty selectors such as ``findings[]`` use the typed error ``entity_id``.
    Resolution is fail-closed: a missing, duplicate, or unsupported identity
    never reaches the model as an ambiguous ``allowed_path``.
    """
    typed = error if isinstance(error, TypedError) else TypedError.from_dict(error)
    tokens = _decode_pointer(typed_error_json_path(typed.path))
    resolved: list[str] = []
    parent: Any = document
    collection = ""

    for position, raw_token in enumerate(tokens):
        last = position == len(tokens) - 1
        if isinstance(parent, dict):
            wildcard_collection = (
                raw_token[:-2]
                if raw_token.endswith("[]")
                else ""
            )
            token = wildcard_collection or raw_token
            resolved.append(token)
            if last:
                break
            if token not in parent:
                raise ValueError(
                    f"validator path parent does not exist: {typed.path}"
                )
            parent = parent[token]
            collection = token
            if wildcard_collection:
                if not isinstance(parent, list):
                    raise ValueError(
                        f"validator path wildcard is not a list: {typed.path}"
                    )
                if not typed.entity_id:
                    raise ValueError(
                        f"validator path wildcard requires entity_id: {typed.path}"
                    )
                index = _identity_index(
                    parent, collection=collection, selector=typed.entity_id,
                )
                resolved.append(str(index))
                parent = parent[index]
            continue

        if isinstance(parent, list):
            if raw_token.isdigit():
                index = int(raw_token)
                if index < 0 or index >= len(parent):
                    raise ValueError(
                        f"validator path array index out of range: {typed.path}"
                    )
            else:
                selector = raw_token or typed.entity_id
                if not selector:
                    raise ValueError(
                        f"validator path list selector is empty: {typed.path}"
                    )
                index = _identity_index(
                    parent, collection=collection, selector=selector,
                )
            resolved.append(str(index))
            if not last:
                parent = parent[index]
            continue

        raise ValueError(f"validator path is not traversable: {typed.path}")

    return _encode_pointer(resolved) if resolved else ""


def resolve_typed_error_json_paths(
    document: dict[str, Any], error: TypedError | dict[str, Any],
) -> list[str]:
    """Resolve every coordinated Correction path for one typed error.

    Duplicate provisional Finding keys are a cross-document correlation error:
    correcting only one ``key`` or only the ownership list leaves the payload
    invalid.  Expose all duplicate key fields and every referencing
    ``finding_keys`` list in the same bounded patch turn.
    """
    typed = error if isinstance(error, TypedError) else TypedError.from_dict(error)

    if typed.code == "CHECK_COVERAGE_INCOMPLETE":
        # The validator path "observation.observations.check_ids" is document-level
        # and does not resolve to a traversable node via the generic resolver.
        # Expose the append token plus every existing entry's check_ids so the
        # model can either extend an existing observation or append a new one.
        paths = ["/observations/-"]
        for index, _ in enumerate(_rows(document.get("observations"))):
            paths.append(f"/observations/{index}/check_ids")
        return paths

    primary_path = resolve_typed_error_json_path(document, typed)

    if typed.code == "CRITERION_EVIDENCE_UNKNOWN":
        tokens = _decode_pointer(primary_path)
        paths = [primary_path]
        if len(tokens) >= 2 and tokens[0] == "criterion_results":
            criterion_index = int(tokens[1])
            criterion_rows = _rows(document.get("criterion_results"))
            if criterion_index < len(criterion_rows):
                for finding_index, finding in enumerate(
                    _rows(criterion_rows[criterion_index].get("findings"))
                ):
                    if isinstance(finding.get("evidence_ids"), list):
                        paths.append(
                            f"/criterion_results/{criterion_index}/findings/"
                            f"{finding_index}/evidence_ids"
                        )
        return paths

    if typed.code == "POLICY_BASIS_INVALID" and typed.entity_id:
        paths = [primary_path]
        for index, basis in enumerate(_rows(document.get("outcome_policy_bases"))):
            if basis.get("criterion_id") == typed.entity_id:
                basis_path = f"/outcome_policy_bases/{index}"
                if basis_path not in paths:
                    paths.append(basis_path)
        for index, criterion in enumerate(_rows(document.get("criterion_results"))):
            if criterion.get("criterion_id") == typed.entity_id:
                paths.extend([
                    f"/criterion_results/{index}/conclusion",
                    f"/criterion_results/{index}/findings",
                ])
        return list(dict.fromkeys(paths))

    if typed.code == "FINDING_CARDINALITY_VIOLATED":
        paths = [primary_path]
        tokens = _decode_pointer(primary_path)
        if len(tokens) >= 2 and tokens[0] == "criterion_results":
            criterion_index = int(tokens[1])
            criterion_rows = _rows(document.get("criterion_results"))
            identities: set[str] = set()
            if criterion_index < len(criterion_rows):
                for finding in _rows(criterion_rows[criterion_index].get("findings")):
                    identities.update(
                        value for value in (
                            finding.get("finding_id"), finding.get("key")
                        ) if isinstance(value, str) and value
                    )
            for owner_index, owner in enumerate(_rows(document.get("defect_ownership"))):
                for field in ("finding_ids", "finding_keys"):
                    if identities.intersection(_strings(owner.get(field))):
                        paths.append(f"/defect_ownership/{owner_index}/{field}")
        return list(dict.fromkeys(paths))

    if typed.code != "FINDING_KEY_DUPLICATE":
        return [primary_path]

    paths: list[str] = []
    for criterion_index, criterion in enumerate(_rows(document.get("criterion_results"))):
        for finding_index, finding in enumerate(_rows(criterion.get("findings"))):
            if finding.get("key") == typed.entity_id:
                paths.append(
                    f"/criterion_results/{criterion_index}/findings/{finding_index}/key"
                )
    for owner_index, owner in enumerate(_rows(document.get("defect_ownership"))):
        if typed.entity_id in _strings(owner.get("finding_keys")):
            paths.append(f"/defect_ownership/{owner_index}/finding_keys")
    if len(paths) < 2:
        raise ValueError(
            f"duplicate Finding key {typed.entity_id!r} could not be located "
            "with its ownership references"
        )
    return paths


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


def validate_patch_values(
    patches: Iterable[dict[str, Any]],
    *,
    allowed_values_by_path: dict[str, Iterable[str]],
) -> list[str]:
    """Validate enum-constrained patch values before applying a correction."""
    violations: list[str] = []
    allowed = {
        path: set(values) for path, values in allowed_values_by_path.items()
    }
    for patch in patches:
        path = patch.get("path") if isinstance(patch, dict) else None
        if path not in allowed:
            continue
        raw_value = patch.get("value")
        try:
            value = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
        except json.JSONDecodeError:
            violations.append(f"{path}: patch value is not valid JSON")
            continue
        if not isinstance(value, list) or not value or any(
            not isinstance(item, str) or item not in allowed[path]
            for item in value
        ):
            violations.append(
                f"{path}: every Criterion must be one of "
                f"{sorted(allowed[path])}"
            )
    return violations
