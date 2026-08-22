#!/usr/bin/env python3
"""knowledge_digest — standalone attestation/snapshot tool for §8 fairness.

The RUNBOOK's operational face of `rebase_engine.knowledge_attest`: the
same canonical logical digests the v3 prelude/compare steps record, usable
against ANY world (the ext checkout's parent stores included), plus the
WAL-safe snapshot/restore that replaces the old `cp -a` knowledge-snapshot
step (a bare file copy can miss committed WAL-only rows and re-attach a
stale WAL on restore — design round-5 F1).

Usage (run day, values-file shorthands):
  knowledge_digest.py digest   --db <debug_memory.db> [--skills <dir>]
  knowledge_digest.py snapshot --db <debug_memory.db> --dest <snapshot.db>
  knowledge_digest.py restore  --snapshot <snapshot.db> --target <db>

`digest` prints one line per layer (record it in the freeze table /
attestation log). `snapshot`/`restore` print the resulting digest.
`restore` must run while the world's exclusion lock (the checkout flock)
is held — the RUNBOOK's Phase-3 restore step does exactly that.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:  # runnable without an editable install
    sys.path.insert(0, str(REPO_SRC))

from infermatrix_copilot.rebase_engine import knowledge_attest as ka  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("digest", help="print logical digests")
    d.add_argument("--db", default="", help="debug store (parent or copilot)")
    d.add_argument("--skills", default="", help="skills directory")
    s = sub.add_parser("snapshot", help="WAL-safe consistent DB snapshot")
    s.add_argument("--db", required=True)
    s.add_argument("--dest", required=True)
    r = sub.add_parser("restore", help="restore a snapshot over a target "
                                       "(hold the checkout flock!)")
    r.add_argument("--snapshot", required=True)
    r.add_argument("--target", required=True)
    args = parser.parse_args(argv)

    try:
        if args.cmd == "digest":
            if not args.db and not args.skills:
                parser.error("digest needs --db and/or --skills")
            if args.db:
                print(f"debug_db {args.db} "
                      f"{ka.debug_db_digest(args.db)}")
            if args.skills:
                catalog = ka.skills_catalog(args.skills)
                print(f"skills_dir {args.skills} "
                      f"{ka.skills_catalog_digest(catalog)} "
                      f"({len(catalog)} skills)")
        elif args.cmd == "snapshot":
            digest = ka.snapshot_debug_db(args.db, args.dest)
            print(f"snapshot {args.dest} {digest}")
        elif args.cmd == "restore":
            digest = ka.restore_debug_db(args.snapshot, args.target)
            print(f"restored {args.target} {digest}")
    except Exception as exc:  # noqa: BLE001 — operators need the reason
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
