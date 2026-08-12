#!/usr/bin/env python3
"""Local semantic evaluation service entrypoint (TASK-011-06 / TASK-011-09).

Default action is ``serve`` (HTTP + scheduler). Governance subcommands export
metrics, clean disposable run dirs, and back up the DB.

    python3 specs/tools/spec_eval/service_cli.py serve --port 8765
    python3 specs/tools/spec_eval/service_cli.py metrics --write metrics.json
    python3 specs/tools/spec_eval/service_cli.py cleanup --retention-days 14
    python3 specs/tools/spec_eval/service_cli.py backup

Binds 127.0.0.1 by default. Pass --host 0.0.0.0 only together with --token.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_eval.service.app import SemanticServiceApp  # noqa: E402
from spec_eval.service.http.server import make_server  # noqa: E402
from spec_eval.service.settings import ServiceSettings  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local semantic evaluation service")
    parser.add_argument("--data-root", type=Path, default=None, help="runtime data root")
    sub = parser.add_subparsers(dest="action")

    serve = sub.add_parser("serve", help="run the HTTP server + scheduler (default)")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--max-workers", type=int, default=2)
    serve.add_argument("--token", default=None)

    metrics = sub.add_parser("metrics", help="export metrics and exit")
    metrics.add_argument("--write", type=Path, required=True, help="destination path")
    metrics.add_argument("--format", choices=["json", "csv"], default="json")

    cleanup = sub.add_parser("cleanup", help="delete disposable run dirs for old terminal jobs")
    cleanup.add_argument("--retention-days", type=int, default=14)

    sub.add_parser("backup", help="checkpoint WAL, copy the DB, verify it restores")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    action = args.action or "serve"
    settings = ServiceSettings.discover(data_root=args.data_root)

    if action == "serve":
        return _serve(settings, args)
    if action == "metrics":
        return _metrics(settings, args)
    if action == "cleanup":
        return _cleanup(settings, args)
    if action == "backup":
        return _backup(settings)
    return 2


def _serve(settings: ServiceSettings, args) -> int:
    if args.host not in ("127.0.0.1", "localhost") and not args.token:
        print("WARNING: binding non-loopback without --token; API will be open", file=sys.stderr)
    app = SemanticServiceApp(settings, max_workers=args.max_workers, token=args.token)
    app.start()
    server = make_server(app, args.host, args.port)
    bound = server.server_address
    print(f"semantic service listening on http://{bound[0]}:{bound[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        app.stop()
    return 0


def _metrics(settings: ServiceSettings, args) -> int:
    from spec_eval.service.app import SemanticServiceApp
    from spec_eval.service.metrics import write_metrics_csv, write_metrics_json

    app = SemanticServiceApp(settings, max_workers=1)
    try:
        metrics = app.metrics()
    finally:
        app.stop()
    if args.format == "csv":
        write_metrics_csv(metrics, args.write)
    else:
        write_metrics_json(metrics, args.write)
    print(f"wrote metrics to {args.write}", flush=True)
    return 0


def _cleanup(settings: ServiceSettings, args) -> int:
    from spec_eval.service.app import SemanticServiceApp
    from spec_eval.service.governance import cleanup_temp

    app = SemanticServiceApp(settings, max_workers=1)
    try:
        summary = cleanup_temp(settings, app.store, retention_days=args.retention_days)
    finally:
        app.stop()
    print(
        f"cleanup: freed {summary['freed_bytes']} bytes across "
        f"{len(summary['cleaned_job_ids'])} job(s) (retention={summary['retention_days']}d)",
        flush=True,
    )
    return 0


def _backup(settings: ServiceSettings) -> int:
    from spec_eval.service.app import SemanticServiceApp
    from spec_eval.service.governance import backup_database

    app = SemanticServiceApp(settings, max_workers=1)
    try:
        dest = backup_database(settings)
    finally:
        app.stop()
    print(f"backup verified at {dest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
