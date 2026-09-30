"""``infermatrix-copilot improve`` — operate the meta-improvement engine.

    improve migrate-index   [--trace-root DIR] [--offline-confirmed] [--no-backup]
                            upgrade the live trace index to the current schema
                            (backup, ALTER, backfill, verify); refused unless
                            every writer is paused
    improve rebuild-index   [--to-schema 0|2] [--offline-confirmed]
                            rebuild the index from the JSONL records into a temp
                            file and swap it in atomically (same gate); --to-schema 0
                            is the pin-downgrade path
    improve rollback-index  alias of rebuild-index --to-schema 0
    improve compare-index   read-only: rebuild a throwaway copy and diff it
                            against the live index (safe with live writers)
    improve verify-index    read-only: id sets and schema-2 columns vs the records
    improve cycle           [--since EPOCH] [--until EPOCH] [--force] [--ledger-dir DIR]
                            run one weekly cycle now (Tier 1 lints, baselines,
                            ledger, report; dry-run — proposals stay local)
    improve ledger          [--workflow W] [--ledger-dir DIR]   show the ledgers
    improve lints           the Tier 1 lint catalogue (ids, versions, origins)
    improve gold draft --item repo#N [--gt-dir DIR]   draft a curated gold file from raw comments
    improve gold check [--gt-dir DIR]                  validate every curated gold file
    improve meta lint-check [--meta-dir DIR]           every meta lint sample triggers its lint

The writer-quiescence gate (design §7.1). Pause flags alone do not stop an
intake or sweep that is already running, so the gate requires evidence that
no writer is executing: the knowledge service's ledger shows every repository
(and the global row) paused AND holds no live lease (``kb serve`` renews its
lease while it runs; a stopped service has released it or let it expire), and
the review bot's pause marker file (``RB_REVIEW_PAUSE_MARKER``) exists and is
non-empty — the bot writes it, with its ack time, only after its in-flight
reviews have drained. ``--offline-confirmed`` skips the gate and is for an
operator who has verified quiescence by hand. Independently of the gate, the
migration and rebuild paths catch up any JSONL record the index lacks and
verify id-set equality before declaring the index good.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable

DEFAULT_KB_STATE_DIR = Path.home() / ".infermatrix-copilot" / "kb"


def _trace_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    env = os.environ.get("TRACE_STORE_ROOT")
    if env:
        return Path(env).expanduser()
    return Path(os.environ.get("KB_STATE_DIR") or DEFAULT_KB_STATE_DIR).expanduser() / "traces"


def writers_paused_check(kb_state_dir: Path | None = None, rb_marker: str | None = None,
                         environ: dict | None = None) -> Callable[[], tuple[bool, str]]:
    """The gate the store's migration commands call: ``(paused, detail)``."""
    env = os.environ if environ is None else environ
    state_dir = kb_state_dir or Path(env.get("KB_STATE_DIR") or DEFAULT_KB_STATE_DIR).expanduser()
    marker = rb_marker if rb_marker is not None else env.get("RB_REVIEW_PAUSE_MARKER", "")

    def check() -> tuple[bool, str]:
        problems: list[str] = []
        ledger_path = state_dir / "kb.db"
        if ledger_path.exists():
            from ..kb_service.ledger import Ledger

            ledger = Ledger(ledger_path)
            live = [row["repo"] for row in ledger.all_repo_states() if not int(row.get("paused") or 0)]
            if live:
                problems.append(f"knowledge service not paused for {live} (run `kb pause --all`)")
            holder = ledger.live_lease()
            if holder:
                problems.append(f"knowledge service is running (lease held by {holder}); stop `kb serve` first")
        if not marker:
            problems.append("RB_REVIEW_PAUSE_MARKER is unset: name the review bot's pause marker file")
        else:
            path = Path(marker).expanduser()
            if not path.exists():
                problems.append(f"review bot pause marker missing: {marker}")
            elif not path.read_text(encoding="utf-8").strip():
                problems.append(f"review bot pause marker is empty (no drain ack): {marker}")
        return (not problems, "; ".join(problems) or "all writers quiescent")

    return check


def _store(args):
    from ..trace_store import TraceStore

    return TraceStore(_trace_root(args.trace_root))


def _gate(args):
    return None if args.offline_confirmed else writers_paused_check()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="infermatrix-copilot improve",
                                     description="operate the meta-improvement engine's trace index")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("gold", "meta"):
        p = sub.add_parser(name)
        p.add_argument("action", choices=["draft", "check"] if name == "gold" else ["lint-check"])
        p.add_argument("--item", default="")
        p.add_argument("--gt-dir", default="eval/dataset/gt")
        p.add_argument("--meta-dir", default="eval/dataset/meta")
    for name in ("migrate-index", "rebuild-index", "rollback-index", "compare-index", "verify-index",
                 "cycle", "ledger", "lints"):
        p = sub.add_parser(name)
        p.add_argument("--trace-root", default=None, help="trace store root (TRACE_STORE_ROOT / KB_STATE_DIR/traces)")
        if name in ("migrate-index", "rebuild-index", "rollback-index"):
            p.add_argument("--offline-confirmed", action="store_true",
                           help="skip the writer-pause gate (operator verified both writers by hand)")
        if name == "migrate-index":
            p.add_argument("--no-backup", action="store_true")
        if name == "rebuild-index":
            p.add_argument("--to-schema", type=int, default=None, help="0 (pin downgrade) or the current schema")
        if name in ("cycle", "ledger"):
            p.add_argument("--ledger-dir", default=None)
        if name == "cycle":
            p.add_argument("--since", type=float, default=None)
            p.add_argument("--until", type=float, default=None)
            p.add_argument("--force", action="store_true", help="run even when improve_enabled is off (operator)")
        if name == "ledger":
            p.add_argument("--workflow", default=None)
    args = parser.parse_args(argv)
    if args.command in ("gold", "meta"):
        return _gold_meta_commands(args)
    if args.command == "lints":
        from .lints import catalogue

        print(json.dumps(catalogue(), ensure_ascii=False, indent=1))
        return 0
    if args.command in ("cycle", "ledger"):
        return _cycle_commands(args)
    store = _store(args)
    try:
        if args.command == "migrate-index":
            report = store.migrate_index(writers_paused=_gate(args), offline_confirmed=args.offline_confirmed,
                                         backup=not args.no_backup)
        elif args.command in ("rebuild-index", "rollback-index"):
            from ..trace_store import SCHEMA_VERSION

            target = 0 if args.command == "rollback-index" else (
                SCHEMA_VERSION if args.to_schema is None else args.to_schema)
            count = store.rebuild_index(to_schema=target, writers_paused=_gate(args),
                                        offline_confirmed=args.offline_confirmed)
            report = {"rebuilt": count, "schema": store.index_version(), "verify": store.verify_index()}
        elif args.command == "compare-index":
            report = store.compare_index()
        else:
            report = store.verify_index()
    except Exception as exc:  # noqa: BLE001 - the CLI reports, the exit code decides
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=1, default=str))
    return 0 if report.get("ok", True) else 1



def _ledger_dir(args) -> Path:
    from ..config import Settings
    from .cycle import ledger_dir_for

    return Path(args.ledger_dir).expanduser() if args.ledger_dir else ledger_dir_for(Settings())


def _cycle_commands(args) -> int:
    from ..config import Settings
    from .cycle import CycleRefused, run_cycle
    from .ledger import Ledger

    ledger_dir = _ledger_dir(args)
    if args.command == "ledger":
        ledger = Ledger(ledger_dir)
        names = [args.workflow] if args.workflow else ledger.workflows()
        out = {}
        for name in names:
            wl = ledger.load(name)
            out[name] = {"tier": wl.tier, "declared": wl.declared, "hold": wl.hold, "cycles": wl.cycles[-4:],
                         "proposals": [{"id": p.id, "state": p.state, "lint": p.lint, "stage": p.stage,
                                        "claim": p.claim, "issue": p.issue} for p in wl.proposals]}
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
        return 0
    store = _store(args)
    try:
        report = run_cycle(store, Settings(), ledger_dir, since=args.since, until=args.until,
                           dry_run=True, force=args.force)
    except CycleRefused as exc:
        print(json.dumps({"refused": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({k: report[k] for k in ("at", "since", "until", "units", "proposals_opened", "seconds")},
                     ensure_ascii=False, indent=1, default=str))
    print(f"report: {ledger_dir / 'reports'}", file=sys.stderr)
    return 0


def _gold_meta_commands(args) -> int:
    from .gold import CURATED_DIRNAME, load_gold, write_draft

    if args.command == "gold" and args.action == "draft":
        if not args.item:
            print("gold draft needs --item repo#N", file=sys.stderr)
            return 2
        path = write_draft(Path(args.gt_dir), args.item)
        print(json.dumps({"drafted": str(path)}))
        return 0
    if args.command == "gold":
        problems = {}
        curated = Path(args.gt_dir) / CURATED_DIRNAME
        for path in sorted(curated.glob("*.gold.json")):
            try:
                gold = load_gold(path)
                problems[path.name] = "ok" if gold.status == "curated" else "draft (not used)"
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                problems[path.name] = f"INVALID: {exc}"
        print(json.dumps(problems, ensure_ascii=False, indent=1))
        return 0 if not any(v.startswith("INVALID") for v in problems.values()) else 1
    from ..trace_store import TraceStore
    from .lints import Baseline, run_lints
    from .meta import lint_samples

    report = {}
    ok = True
    for lint_id, units in lint_samples(Path(args.meta_dir)).items():
        for unit in units:
            found = {f.lint for f in run_lints(unit, TraceStore(Path(args.meta_dir) / "lints" / lint_id), Baseline())}
            hit = lint_id in found
            ok &= hit
            report[f"{lint_id}/{unit.unit_id}"] = "ok" if hit else f"MISSED (found {sorted(found)})"
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
