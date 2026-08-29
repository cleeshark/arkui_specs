"""Automated archive stage (TASK-011-07): immutable, self-verifying archive.

Copies the job's durable artifacts into the ``automated`` namespace under
``archives/automated/<revision>/<func_id>/<job_id>/`` and writes an
``archive-manifest.json`` recording every file's SHA-256 and size plus the
frozen version fingerprints. The write is atomic (temp dir + ``os.replace``),
so an interrupted archive never leaves a half-written tree.

The automated namespace is strictly separate from ``evaluation/reviews/**`` and
the confirmed site archives; this stage never writes outside ``data_root``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from ..domain.models import Job
from ..settings import ServiceSettings
from ..store.sqlite_store import utc_now

MANIFEST_SCHEMA_VERSION = 1


def archive_dir_for(settings: ServiceSettings, job: Job) -> Path:
    return (
        settings.archives_root
        / job.source_revision
        / job.func_id
        / job.job_id
    )


def write_archive(
    settings: ServiceSettings,
    job: Job,
    *,
    semantic_results: dict[str, Path],
    aggregate_outputs: dict[str, Path],
    run_ids: list[str],
    selected_run_id: str,
    site_snapshot_path: Path | None = None,
    aggregation_contexts: dict[str, Path] | None = None,
    confidence_result_path: Path | None = None,
) -> Path:
    """Atomically write the automated archive and return its directory."""
    target = archive_dir_for(settings, job)
    # A published archive is immutable. Retries after a crash reuse it; they do
    # not replace bytes that may already be referenced by evaluation_reports.
    if (target / "archive-manifest.json").is_file():
        return target
    tmp = target.with_name(target.name + ".tmp-" + os.getpid().__str__())
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    copied: list[tuple[str, Path]] = []  # (relative_name, src)

    for run_id, sr in semantic_results.items():
        copied.append((f"semantic-result-{run_id}.json", sr))
    for run_id, context_path in (aggregation_contexts or {}).items():
        copied.append((f"aggregation-context-{run_id}.json", context_path))
    for kind, path in aggregate_outputs.items():
        suffix = path.name
        copied.append((f"aggregate-{kind}-{suffix}", path))
    if site_snapshot_path is not None:
        copied.append(("site-history-snapshot.json", site_snapshot_path))
    # Kernel confidence (report-reliability, validation-violation deductions) is
    # written per-run to run_dir/confidence-result.json but is not otherwise a
    # durable artifact; archive the selected run's copy as a sibling so the site
    # and the Markdown report can surface it. Missing (older runs) is tolerated.
    if confidence_result_path is not None:
        copied.append(("confidence-result.json", confidence_result_path))

    files_meta = []
    for rel, src in copied:
        if not src.is_file():
            continue  # an optional artifact that was not produced
        dest = tmp / rel
        data = src.read_bytes()
        dest.write_bytes(data)
        _fsync(dest)
        files_meta.append({
            "path": rel,
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "source": str(src),
        })

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "namespace": "automated",
        "job_id": job.job_id,
        "func_id": job.func_id,
        "source_revision": job.source_revision,
        "evaluator_version": job.evaluator_version,
        "protocol_version": job.protocol_version,
        "run_count": job.run_count,
        "run_ids": run_ids,
        "selected_run_id": selected_run_id,
        "created_at": utc_now(),
        "files": files_meta,
    }
    manifest_path = tmp / "archive-manifest.json"
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    files_meta.append({
        "path": "archive-manifest.json",
        "sha256": "sha256:" + hashlib.sha256(manifest_bytes).hexdigest(),
        "size": len(manifest_bytes),
        "source": str(manifest_path),
    })
    _fsync(manifest_path)

    # atomic publish; target cannot exist as a completed archive here.
    if target.exists():
        raise RuntimeError(f"archive target exists without a manifest: {target}")
    os.replace(tmp, target)
    return target


def _fsync(path: Path) -> None:
    try:
        with open(path, "rb") as fh:
            os.fsync(fh.fileno())
    except OSError:
        pass
