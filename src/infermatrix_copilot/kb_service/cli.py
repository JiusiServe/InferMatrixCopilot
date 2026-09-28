"""``infermatrix-copilot kb`` — operate the knowledge service.

    kb keygen --out PATH              create a signing key (0600) and print its public key
    kb status                         repositories, modes, generations, queues
    kb pause  (--repo R | --all) --reason TEXT
    kb resume (--repo R | --all)
    kb control                        refresh the signed control record and hold list now
    kb run --playbook kb-intake --repo R   run one knowledge playbook once
    kb calibrate --repo R             run the judge over the repository's calibration set
    kb serve [--once]                 the scheduler (holds the single-writer lease)
    kb activate                       activate the knowledge snapshot of the repository's main now
    kb rollback --to SHA              point `active` back at an earlier snapshot
    kb holds-server [--host H] [--port P]                           serve ONLY the signed hold list (read-only)
    kb traces [--kind K] [--changeset ID] [--rule ID] [--limit N]   query trace/1 records
    kb replay --record ID --model PROVIDER:MODEL[:EFFORT]           re-ask a recorded call
    kb export --out FILE [--role judge|generator]                   dataset (calibration-safe)
    kb publish (--remote HOST:/STATE_DIR | --local DIR) [--once]
                                      the publisher (GPU box, owner's gh login): perform
                                      the signed outbox items; writes need ALLOW_POST=1
                                      (and ALLOW_PUSH=1 to push branches)

Pause/resume bump the repository's generation, so every outbox item issued
before it is void; they then re-sign the control record and hold list at once.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

DEFAULT_STATE_DIR = Path.home() / ".infermatrix-copilot" / "kb"


def _state_dir(value: str | None) -> Path:
    return Path(value or os.environ.get("KB_STATE_DIR") or DEFAULT_STATE_DIR).expanduser()


def _ledger(state_dir: Path):
    from .ledger import Ledger

    return Ledger(state_dir / "kb.db")


def _registry():
    from ..sdk._resources import adapters_root
    from .config import general_lifecycle, load_registry

    general = general_lifecycle(
        enabled=os.environ.get("KB_GENERAL_ENABLED", "0") == "1",
        mode=os.environ.get("KB_GENERAL_MODE", "shadow"),
    )
    return load_registry(Path(os.environ.get("ADAPTERS_DIR") or adapters_root()), general=general)


def _signing_key():
    from ..knowledge_service.signing import load_private_key

    path = os.environ.get("KB_SIGNING_KEY")
    if not path:
        raise SystemExit("KB_SIGNING_KEY is not set (path to the service's Ed25519 private key)")
    return load_private_key(path)


def _sync_repos(ledger, registry) -> bool:
    """Record configured modes; True when any mode changed (and so a
    generation was bumped and the signed control record must be re-issued)."""
    changed = False
    for lifecycle in registry.values():
        changed |= ledger.ensure_repo(lifecycle.repo, lifecycle.mode if lifecycle.enabled else "disabled")
    return changed


def _outbox(state_dir: Path, ledger):
    from .outbox import Outbox

    return Outbox(state_dir, _signing_key(), ledger, clock=time.time)


def _public(registry) -> set[str]:
    return {name for name, lifecycle in registry.items() if lifecycle.publishes}


def _unconfirmed(ledger, repo: str) -> int:
    from .merge import pause_unconfirmed

    return pause_unconfirmed(ledger, repo)


def _refresh(state_dir: Path, ledger, registry) -> None:
    _outbox(state_dir, ledger).transition(lambda: None, public_repos=_public(registry))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="infermatrix-copilot kb")
    parser.add_argument("--state-dir", help="default: $KB_STATE_DIR or ~/.infermatrix-copilot/kb")
    sub = parser.add_subparsers(dest="command", required=True)
    keygen = sub.add_parser("keygen")
    keygen.add_argument("--out", required=True)
    sub.add_parser("status")
    for name in ("pause", "resume"):
        cmd = sub.add_parser(name)
        target = cmd.add_mutually_exclusive_group(required=True)
        target.add_argument("--repo")
        target.add_argument("--all", action="store_true")
        if name == "pause":
            cmd.add_argument("--reason", required=True)
    sub.add_parser("control")
    run = sub.add_parser("run")
    run.add_argument("--playbook", required=True)
    run.add_argument("--repo", required=True)
    calibrate = sub.add_parser("calibrate")
    calibrate.add_argument("--repo", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--once", action="store_true")
    sub.add_parser("activate")
    rollback = sub.add_parser("rollback")
    rollback.add_argument("--to", required=True)
    holds = sub.add_parser("holds-server")
    holds.add_argument("--host", default="127.0.0.1", help="bind address; put TLS in front of it")
    holds.add_argument("--port", type=int, default=8765)
    traces = sub.add_parser("traces")
    traces.add_argument("--kind")
    traces.add_argument("--changeset")
    traces.add_argument("--rule")
    traces.add_argument("--run")
    traces.add_argument("--limit", type=int, default=50)
    replay = sub.add_parser("replay")
    replay.add_argument("--record", required=True)
    replay.add_argument("--model", required=True, help="provider:model[:effort], e.g. codex:gpt-6-mini:low")
    export = sub.add_parser("export")
    export.add_argument("--out", required=True)
    export.add_argument("--role", default="judge", choices=("judge", "generator"))
    publish = sub.add_parser("publish")
    where = publish.add_mutually_exclusive_group(required=True)
    where.add_argument("--remote", help="host:/absolute/path of the service state directory (over ssh)")
    where.add_argument("--local", help="the service state directory on this machine")
    publish.add_argument("--once", action="store_true")
    publish.add_argument("--interval", type=float, default=60.0)
    publish.add_argument("--publisher-state",
                         help="default: $KB_PUBLISHER_STATE or ~/.infermatrix-copilot/kb-publisher")
    args = parser.parse_args(argv)

    if args.command == "keygen":
        from ..knowledge_service.signing import generate_private_key, public_key_text

        key = generate_private_key(args.out)
        print(public_key_text(key.public_key()))
        return 0

    if args.command == "publish":
        return _publish(args)
    if args.command == "holds-server":
        from .holds_server import serve_holds

        serve_holds(_state_dir(args.state_dir), host=args.host, port=args.port)
        return 0
    if args.command in {"traces", "replay", "export"}:
        return _traces_command(args, _state_dir(args.state_dir))

    state_dir = _state_dir(args.state_dir)
    ledger = _ledger(state_dir)
    try:
        registry = _registry()
        if _sync_repos(ledger, registry) and os.environ.get("KB_SIGNING_KEY"):
            _refresh(state_dir, ledger, registry)
        if args.command == "status":
            report = {
                "state_dir": str(state_dir),
                "active_snapshot": ledger.active_snapshot(),
                "repos": [
                    {**row, "configured": row["repo"] in registry or row["repo"] == "*",
                     "open_changesets": len(ledger.changesets(row["repo"], ("open", "pr_open", "signed", "queued")))
                     if row["repo"] != "*" else None,
                     "human_queue": len(ledger.human_queue(row["repo"])) if row["repo"] != "*" else None,
                     # a breaker/rollback is not done while any of these remain
                     "pause_unconfirmed": _unconfirmed(ledger, row["repo"]) if row["repo"] != "*" else None}
                    for row in ledger.all_repo_states()
                ],
            }
            json.dump(report, sys.stdout, indent=2, sort_keys=True)
            print()
            return 0
        if args.command in {"pause", "resume"}:
            repo = "*" if args.all else args.repo
            if repo != "*" and repo not in registry:
                print(f"unknown repository: {repo}", file=sys.stderr)
                return 2
            # the state change and its signed publication happen under one
            # interprocess lock, so no concurrent refresh can publish a
            # pre-pause control record after the pause
            if args.command == "pause":
                generation = _outbox(state_dir, ledger).transition(
                    lambda: ledger.bump_generation(repo, pause=True, reason=args.reason),
                    public_repos=_public(registry))
                # the pause itself: dequeue + draft every open knowledge PR
                from . import merge

                outbox = _outbox(state_dir, ledger)
                paused_repos = list(registry) if repo == "*" else [repo]
                issued = sum(merge.pause_open_prs(ledger, outbox, r, args.reason) for r in paused_repos)
                print(f"pause items issued for {issued} open knowledge PR(s)")
            else:
                from . import merge

                def _resume():
                    generation = ledger.resume(repo)
                    for name in (list(registry) if repo == "*" else [repo]):
                        merge.resume_paused_prs(ledger, name)
                    return generation

                # paused PRs leave the hold list in the same published transition
                generation = _outbox(state_dir, ledger).transition(_resume, public_repos=_public(registry))
            print(f"{args.command}d {repo}: generation {generation}")
            return 0
        if args.command == "control":
            _refresh(state_dir, ledger, registry)
            return 0
        if args.command == "run":
            from ..config import Settings
            from .runner import run_playbook

            outcome, run_dir = run_playbook(Settings(), args.playbook, args.repo, state_dir=state_dir)
            print(f"{args.playbook} {args.repo}: {outcome.status} ({run_dir})")
            return 0 if outcome.status == "done" else 1
        if args.command in {"serve", "activate", "rollback"}:
            from ..config import Settings
            from .runtime import KbRuntime

            rt = KbRuntime.from_env(Settings(), state_dir=state_dir)
            if args.command == "serve":
                from .scheduler import Scheduler

                Scheduler(rt).serve(once=args.once)
                return 0
            from .activate import activate, rollback

            if args.command == "activate":
                print(activate(rt, rt.knowledge.fetch()))
            else:
                print(rollback(rt, args.to))
            return 0
        if args.command == "calibrate":
            from ..config import Settings
            from .calibration import run_calibration
            from .models import ModelGateway, roles_from_env

            lifecycle = registry.get(args.repo)
            if lifecycle is None or not lifecycle.calibration_set or lifecycle.adapter_dir is None:
                print(f"{args.repo} has no calibration_set", file=sys.stderr)
                return 2
            _generator, judge = roles_from_env()
            from .calibration import case_set_digest
            from .runtime import record_calibration

            case_dir = lifecycle.adapter_dir / lifecycle.calibration_set
            report = run_calibration(case_dir, gateway=ModelGateway(Settings()), judge=judge)
            # publication under auto_merge requires this record to match the
            # current judge and case set exactly
            record_calibration(ledger, args.repo, judge=judge.label(),
                               case_set=case_set_digest(case_dir), passed=report.passed, at=time.time())
            json.dump({"repo": args.repo, "judge": judge.label(), **report.to_dict()},
                      sys.stdout, indent=2, ensure_ascii=False)
            print()
            return 0 if report.passed else 1
    finally:
        ledger.close()
    return 2


def _publish(args) -> int:
    """The publisher never opens the service ledger: it only sees the outbox."""
    from ..knowledge_service.signing import load_private_key, load_public_key
    from .merge import knowledge_repository
    from .publisher import Gh, LocalTransport, Publisher, SshTransport

    for name in ("KB_SERVICE_PUBKEY", "KB_PUBLISHER_KEY", "KB_PUBLISHER_GIT_AUTHOR"):
        if not os.environ.get(name):
            raise SystemExit(f"{name} is not set")
    author = re.fullmatch(r"\s*(.+?)\s*<([^<>\s]+@[^<>\s]+)>\s*", os.environ["KB_PUBLISHER_GIT_AUTHOR"])
    if not author:
        raise SystemExit("KB_PUBLISHER_GIT_AUTHOR must look like 'Name <email>'")
    state = Path(args.publisher_state or os.environ.get("KB_PUBLISHER_STATE")
                 or Path.home() / ".infermatrix-copilot" / "kb-publisher").expanduser()
    state.mkdir(parents=True, exist_ok=True)
    registry = _registry()
    publisher = Publisher(
        transport=SshTransport.parse(args.remote) if args.remote else LocalTransport(Path(args.local)),
        service_public_key=load_public_key(Path(os.environ["KB_SERVICE_PUBKEY"]).read_text(encoding="utf-8")),
        publisher_key=load_private_key(os.environ["KB_PUBLISHER_KEY"]),
        github=Gh(knowledge_repository(), cwd=state),
        state_dir=state,
        author=(author.group(1), author.group(2)),
        repo_flags={name: (lc.publishes, lc.auto_merge) for name, lc in registry.items() if lc.enabled},
        allow_post=os.environ.get("ALLOW_POST") == "1",
        allow_push=os.environ.get("ALLOW_PUSH") == "1",
    )
    if args.once:
        json.dump(publisher.run_once(), sys.stdout, sort_keys=True)
        print()
        return 0
    publisher.serve(interval=args.interval)
    return 0


def _traces_command(args, state_dir: Path) -> int:
    """Read-only over the trace store (replay also calls the substitute model)."""
    from ..trace_store import TraceStore

    store = TraceStore(state_dir / "traces")
    if args.command == "traces":
        records = store.query(kind=args.kind, changeset_id=args.changeset, rule_id=args.rule,
                              run_id=args.run, limit=args.limit)
        for record in records:
            print(json.dumps({k: record[k] for k in ("id", "kind", "at", "context", "model", "result", "error")},
                             ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "replay":
        from ..config import Settings
        from .models import ModelGateway, ModelRole
        from .replay import replay
        from .runtime import trace_recorder

        role_name = (store.get(args.record).get("model") or {}).get("role") or "judge"
        gateway = ModelGateway(Settings(), recorder=trace_recorder(store))  # the replay call is traced too
        result = replay(store, args.record, gateway, ModelRole.parse(role_name, args.model))
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        print()
        return 0
    from ..sdk._resources import adapters_root
    from .replay import export_dataset

    adapters = Path(os.environ.get("ADAPTERS_DIR") or adapters_root())
    calibration = [p for p in sorted(adapters.glob("*/kb-calibration")) if p.is_dir()]
    json.dump(export_dataset(store, args.out, role=args.role, calibration_dirs=calibration), sys.stdout)
    print()
    return 0
