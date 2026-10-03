"""Portable RFC commands, shared by standalone and Copilot entry points."""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

from .models import RFCError


def _data(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("JSON payload must be an object")
    return value


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="infermatrix-rfc", description="Create and track RFCs locally or through an RFC service")
    parser.add_argument("--state-dir", default=os.environ.get("RFC_STATE_DIR"))
    parser.add_argument("--config", default=os.environ.get("RFC_CONFIG"), help="Local provider JSON configuration")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--service-url", default=os.environ.get("RFC_SERVICE_URL", ""))
    target.add_argument("--local", action="store_true", help="Explicitly use local state even when RFC_SERVICE_URL is set")
    parser.add_argument("--token-env", default="RFC_TOKEN", help="Environment variable containing your RFC user token")
    commands = parser.add_subparsers(dest="command", required=True)
    bootstrap = commands.add_parser("bootstrap-admin", help="Create the first administrator and print its token once")
    bootstrap.add_argument("--name", default="Administrator")
    serve = commands.add_parser("serve", help="Run the local HTTP UI and background reconciler")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8765, type=int)
    serve.add_argument("--public-url")
    serve.add_argument("--no-worker", action="store_true")
    serve.add_argument("--interval", type=float, default=30)
    commands.add_parser("capabilities")
    request = commands.add_parser("request", help="Invoke a versioned RFC action")
    request.add_argument("action")
    request.add_argument("--data", help="JSON payload file; '-' reads stdin")
    draft = commands.add_parser("draft", help="Validate and store a structured draft without publishing")
    draft.add_argument("--data", required=True)
    imp = commands.add_parser("import", help="Store an existing Markdown RFC as a draft")
    imp.add_argument("--file", required=True)
    imp.add_argument("--repo", required=True, dest="repo_id")
    imp.add_argument("--title")
    imp.add_argument("--data", help="Optional extracted feature/criterion metadata JSON")
    imp.add_argument("--source", help="Optional SourceRef JSON file")
    listing = commands.add_parser("list")
    listing.add_argument("--repo", dest="repo_id", default="")
    for name in ("status", "next", "enroll", "decision", "work", "export"):
        command = commands.add_parser(name)
        command.add_argument("rfc_id")
        if name in {"enroll", "decision", "work"}:
            command.add_argument("--data")
        if name == "export":
            command.add_argument("--format", default="json", choices=("json", "markdown"))
            command.add_argument("--out")
    publish = commands.add_parser("publish", help="Queue publication of the exact previewed draft")
    publish.add_argument("rfc_id")
    publish.add_argument("--content-digest", required=True)
    publish.add_argument("--idempotency-key", required=True)
    publish.add_argument("--expected-revision", help="Require the reviewed tracking revision to remain current")
    publish.add_argument("--post", action="store_true", help="Explicitly authorize outward publication")
    publish.add_argument("--data", help="Additional source publication options JSON")
    sync = commands.add_parser("sync", help="Queue an RFC refresh or run the local reconciler")
    sync.add_argument("--rfc", dest="rfc_id")
    mode = sync.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--watch", action="store_true")
    sync.add_argument("--interval", type=float, default=30)
    sync.add_argument("--limit", type=int, default=10)
    operation = commands.add_parser("operation")
    operation.add_argument("operation_id")
    operations = commands.add_parser("operations")
    operations.add_argument("--data")
    migration = commands.add_parser("migrate-personal-agent", help="Preview or apply an authenticated legacy tracking import")
    migration.add_argument("--source-dir", required=True)
    migration.add_argument("--repo-id", required=True)
    migration.add_argument("--rfc-id", required=True)
    migration.add_argument("--apply", action="store_true", help="Apply the reviewed import; default is comparison only")
    return parser


def _run_cycle(service, limit: int) -> dict[str, Any]:
    return {"sync": service.sync_due(), "processed": service.process_pending(limit=limit)}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    from ..sdk.v1.rfc import RFCClient, RFCClientError

    service_url = "" if args.local else args.service_url
    state = Path(args.state_dir).expanduser() if args.state_dir else Path.home() / ".infermatrix-copilot" / "rfc"
    try:
        command = args.command
        if command in {"bootstrap-admin", "serve"} or (command == "sync" and not args.rfc_id):
            if service_url:
                raise RFCClientError("This command requires local state; use --local explicitly")
            from .application import build_service

            service = build_service(state, config_path=args.config)
            if command == "bootstrap-admin":
                # Deliberately the only unauthenticated user-management command.
                # The service refuses a second bootstrap, and stores token hashes.
                _print(service.bootstrap_admin(args.name))
                return 0
            if args.interval <= 0:
                raise ValueError("interval must be positive")
            if command == "sync":
                if args.limit < 1:
                    raise ValueError("limit must be positive")
                while True:
                    _print(_run_cycle(service, args.limit))
                    if not args.watch:
                        return 0
                    time.sleep(args.interval)
            from .http import create_server

            server = create_server(service, host=args.host, port=args.port, public_url=args.public_url)
            stop = threading.Event()
            def worker():
                while not stop.is_set():
                    try:
                        _run_cycle(service, 10)
                    except Exception:
                        print("RFC reconciliation failed; inspect the operation and audit history", file=sys.stderr)
                    stop.wait(args.interval)
            thread = None
            if not args.no_worker:
                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
            print(f"RFC service: {server.public_url}", flush=True)
            try:
                server.serve_forever()
            finally:
                stop.set()
                server.server_close()
                if thread:
                    thread.join(timeout=2)
            return 0
        client = RFCClient(state_dir=state, service_url=service_url,
                           token=os.environ.get(args.token_env, ""), config_path=args.config)
        if command == "request":
            result = client.dispatch(args.action, _data(args.data))
        elif command == "migrate-personal-agent":
            if service_url:
                raise RFCClientError("Migration requires local state; use --local explicitly")
            from .application import build_service
            from .migration import migrate

            service = build_service(state, config_path=args.config)
            result = migrate(service, service.authenticate(os.environ.get(args.token_env, "")),
                             args.source_dir, args.repo_id, args.rfc_id, apply=args.apply)
        elif command == "capabilities":
            result = client.capabilities()
        elif command == "draft":
            result = client.draft(_data(args.data))
        elif command == "import":
            path = Path(args.file)
            with path.open(encoding="utf-8", newline="") as source_file:
                body = source_file.read()
            heading = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), path.stem)
            payload = {**_data(args.data), "repo_id": args.repo_id, "title": args.title or heading, "body": body}
            if args.source:
                payload["source"] = _data(args.source)
            result = client.draft(payload)
        elif command == "list":
            result = client.list_rfcs(args.repo_id)
        elif command == "status":
            result = client.status(args.rfc_id)
        elif command == "next":
            value = client.status(args.rfc_id)
            result = {"rfc_id": args.rfc_id, "next_actions": value.get("next_actions", [])}
        elif command in {"enroll", "decision", "work"}:
            result = client.dispatch("rfcs." + command, {**_data(args.data), "rfc_id": args.rfc_id})
        elif command == "publish":
            if not args.post:
                raise RFCClientError("Publication requires --post after reviewing the draft")
            payload = {**_data(args.data), "rfc_id": args.rfc_id,
                "content_digest": args.content_digest, "idempotency_key": args.idempotency_key, "post": True}
            if args.expected_revision is not None:
                payload["expected_revision"] = args.expected_revision
            result = client.dispatch("rfcs.publish", payload)
        elif command == "sync":
            if args.watch:
                raise RFCClientError("--watch reconciles local state; use sync --rfc for a queued refresh")
            result = client.sync(args.rfc_id)
        elif command == "operation":
            result = client.operation(args.operation_id)
        elif command == "operations":
            result = client.dispatch("operations.list", _data(args.data))
        else:  # export
            result = client.export(args.rfc_id, args.format)
            content = result.get("content", result.get("markdown")) if args.format == "markdown" else json.dumps(result, ensure_ascii=False, indent=2)
            if not isinstance(content, str):
                raise RFCClientError("RFC export did not return Markdown", code="invalid_response")
            if args.out:
                Path(args.out).write_text(content, encoding="utf-8", newline="")
                return 0
            if args.format == "markdown":
                print(content)
                return 0
        _print(result)
        return 0
    except (RFCError, RFCClientError, ValueError, OSError) as exc:
        code = getattr(exc, "code", "invalid_request")
        print(json.dumps({"error": {"code": code, "message": str(exc)}}, ensure_ascii=False), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
