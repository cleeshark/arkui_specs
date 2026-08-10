"""Stable Function input fingerprints."""

from __future__ import annotations

import hashlib
from pathlib import Path

from spec_eval.config import EvaluationConfig
from spec_eval.models.function import FunctionContext


def function_fingerprint(config: EvaluationConfig, context: FunctionContext) -> str:
    digest = hashlib.sha256()
    digest.update(context.func_id.encode())
    digest.update(context.source_revision.encode())
    digest.update(context.tool_version.encode())
    digest.update(context.rule_version.encode())
    paths = list(context.all_documents()) + [config.functions_registry, config.features_registry]
    if config.rules_root.is_dir():
        paths.extend(sorted(config.rules_root.glob("*.yaml")))
    for path in sorted(set(paths)):
        digest.update(path.as_posix().encode())
        if path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing>")
    return digest.hexdigest()

