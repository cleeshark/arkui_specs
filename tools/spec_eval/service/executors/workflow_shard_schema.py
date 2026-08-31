"""Per-shard JSON schemas for the Claude workflow-shards observation path.

The workflow session writes one small shard file per claim / criterion instead
of one large structured payload.  Each shard must satisfy the SAME nested
schema the canonical envelope enforces (types, enums, minItems, nested
verification_gap arrays, ...), otherwise the assembled envelope fails the final
schema gate.

The Claude session cannot see the envelope's ``--json-schema`` (its structured
output is only the tiny completion signal), so the service must:

  1. hand the model the precise per-shard schema (this module derives it), and
  2. give the model an AUTHORITATIVE validation script so each shard is checked
     against that schema on disk — not by a model-authored field-name check.

Both concerns are served from here so the schema the model is shown and the
schema the validator enforces are guaranteed identical.
"""

from __future__ import annotations

import json
from typing import Any

from spec_eval.kernel.schema_gen import build_envelope_schema

# Shard kinds -> the $def that is the shard's root object.
CLAIM_SHARD_DEF = "claimJudgment"
OBSERVATION_SHARD_DEF = "observationJudgment"


def _observation_defs() -> dict[str, Any]:
    return build_envelope_schema("observation")["$defs"]


def _root_schema_for_def(def_name: str) -> dict[str, Any]:
    """Return a standalone JSON schema whose root is ``$defs[def_name]``.

    All sibling ``$defs`` are carried along so local ``$ref`` links (e.g.
    claimJudgment -> unitJudgment -> verificationGap) still resolve.
    """
    defs = _observation_defs()
    if def_name not in defs:
        raise KeyError(f"unknown observation $def: {def_name!r}")
    schema = dict(defs[def_name])
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$defs"] = defs
    return schema


def claim_shard_schema() -> dict[str, Any]:
    """Standalone schema for one claim shard (a single claimJudgment object)."""
    return _root_schema_for_def(CLAIM_SHARD_DEF)


def criterion_item_schema() -> dict[str, Any]:
    """Standalone schema for ONE observationJudgment item.

    A criterion shard file is a JSON array of these; the validation script
    checks each element against this schema so array-level errors are attributed
    per item.
    """
    return _root_schema_for_def(OBSERVATION_SHARD_DEF)


# Filenames written into the shard directory by the manifest generator.
CLAIM_SCHEMA_FILE = "claim.schema.json"
CRITERION_ITEM_SCHEMA_FILE = "criterion-item.schema.json"
VALIDATE_SCRIPT_FILE = "validate_shard.py"


def _validate_script_source() -> str:
    """The authoritative shard validation script (runs on disk, no LLM).

    Usage inside the session:
        python3 validate_shard.py claim   claims/claim-<id>.json
        python3 validate_shard.py criterion criteria/obs-<crit>.json

    Prints "OK" on success; on failure prints each schema error (one per line)
    and exits non-zero.  A claim file is validated as one object; a criterion
    file is validated as an array whose every element must match the item
    schema (empty array is allowed = NOT_APPLICABLE).
    """
    # Kept dependency-free (stdlib + the repo's validator on PYTHONPATH). The
    # session runs it via Bash with the same interpreter that ran the manifest.
    return r'''import json, sys
from pathlib import Path

# Resolve the repo validator; the session runs with spec_eval on PYTHONPATH.
try:
    from spec_eval.protocol_validator import JsonSchemaSubsetValidator
except Exception as exc:  # pragma: no cover - environment guard
    print(f"cannot import validator: {exc}")
    sys.exit(2)

HERE = Path(__file__).resolve().parent


def _validate(instance, schema_file):
    v = JsonSchemaSubsetValidator(HERE)
    return v.validate_file(instance, HERE / schema_file)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("claim", "criterion"):
        print("usage: validate_shard.py {claim|criterion} <file>")
        return 2
    kind, path = sys.argv[1], sys.argv[2]
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"not valid JSON: {exc}")
        return 1

    errors = []
    if kind == "claim":
        if not isinstance(data, dict):
            print("claim shard must be a JSON object")
            return 1
        errors = _validate(data, "claim.schema.json")
    else:
        if not isinstance(data, list):
            print("criterion shard must be a JSON array")
            return 1
        for i, item in enumerate(data):
            for e in _validate(item, "criterion-item.schema.json"):
                errors.append(f"[{i}]{e}")

    if errors:
        for e in errors:
            print(e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def write_shard_schemas(shard_dir) -> dict[str, str]:
    """Write claim/criterion schemas + the validation script into ``shard_dir``.

    Returns a mapping of logical name -> relative filename for the manifest.
    """
    from pathlib import Path

    shard_dir = Path(shard_dir)
    shard_dir.mkdir(parents=True, exist_ok=True)
    (shard_dir / CLAIM_SCHEMA_FILE).write_text(
        json.dumps(claim_shard_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (shard_dir / CRITERION_ITEM_SCHEMA_FILE).write_text(
        json.dumps(criterion_item_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (shard_dir / VALIDATE_SCRIPT_FILE).write_text(
        _validate_script_source(), encoding="utf-8",
    )
    return {
        "claim_schema": CLAIM_SCHEMA_FILE,
        "criterion_item_schema": CRITERION_ITEM_SCHEMA_FILE,
        "validate_script": VALIDATE_SCRIPT_FILE,
    }
