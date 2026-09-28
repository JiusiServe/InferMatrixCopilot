"""``infermatrix-copilot kb`` — operate the knowledge service.

    kb keygen --out PATH              create a signing key (0600) and print its public key
    kb status                         repositories, modes, generations, queues
    kb pause  (--repo R | --all) --reason TEXT
    kb resume (--repo R | --all)
    kb control                        refresh the signed control record and hold list now

Pause/resume bump the repository's generation, so every outbox item issued
before it is void; they then re-sign the control record and hold list at once.
"""

from __future__ import annotations

import argparse
import json
import os
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
    args = parser.parse_args(argv)

    if args.command == "keygen":
        from ..knowledge_service.signing import generate_private_key, public_key_text

        key = generate_private_key(args.out)
        print(public_key_text(key.public_key()))
        return 0

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
                     "human_queue": len(ledger.human_queue(row["repo"])) if row["repo"] != "*" else None}
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
            else:
                generation = _outbox(state_dir, ledger).transition(
                    lambda: ledger.resume(repo), public_repos=_public(registry))
            print(f"{args.command}d {repo}: generation {generation}")
            return 0
        if args.command == "control":
            _refresh(state_dir, ledger, registry)
            return 0
    finally:
        ledger.close()
    return 2
