#!/usr/bin/env python3
"""Recompute the audit verdict for already-recorded items from their saved events.

The audit rule is the thing that changed, not the runs. Every item here already
completed with `terminal_reason: completed` and a written review; what was wrong was
my classification of reading installed dependencies as a leak. Re-running 20 Opus
items to fix a post-hoc classifier would cost ~$70 and produce *different* reviews,
which would quietly mix two populations in one arm — strictly worse evidence than
re-scoring the recorded events.

This only ever relaxes: it re-derives `audit_violations` under the current rule and
leaves the artifact, the events and every cost figure untouched. An item that still
has violations stays failed.

Usage: reaudit_arm.py <arm_or_baseline_dir> [--knowledge]
  --knowledge  also allow the copilot's knowledge tree (the Direct arm follows its
               routes there; the baseline has no business in it)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cc_arm_common as cc

HERE = Path(__file__).parent
CHECKOUT = Path(__file__).resolve().parents[2]
WORKTREES = Path.home() / ".infermatrix-copilot" / "worktrees"


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = Path(sys.argv[1])
    if not d.is_absolute():
        d = HERE / d
    extra = (CHECKOUT / "knowledge",) if "--knowledge" in sys.argv else ()
    if not d.is_dir():
        sys.exit(f"not a directory: {d}")

    changed = still_bad = 0
    for cj in sorted(d.glob("pr*.cost.json")):
        stem = cj.name.split(".")[0]
        evf = d / f"{stem}.events.jsonl"
        if not evf.is_file():
            print(f"  {stem}: no events retained — cannot re-audit, leaving as is")
            continue
        cost = json.loads(cj.read_text(encoding="utf-8"))
        events = [json.loads(l) for l in evf.read_text(encoding="utf-8").splitlines()
                  if l.strip().startswith("{")]
        wt = WORKTREES / f"vllm-omni-{stem}"
        violations, blocked = cc.audit_events(events, wt, extra_read_roots=extra)
        was = cost.get("audit_ok")
        cost.update({"audit_ok": not violations, "audit_violations": violations,
                     "audit_blocked_attempts": blocked,
                     "audit_rule": "worktree + installed dependencies"
                                   + (" + copilot knowledge" if extra else "")})
        cc._write_atomic(cj, json.dumps(cost, indent=2) + "\n")
        if was is False and not violations:
            changed += 1
            print(f"  {stem}: cleared (was flagged for dependency reads)")
        elif violations:
            still_bad += 1
            print(f"  {stem}: STILL FLAGGED — {violations[0][:140]}")
    print(f"\n{changed} cleared, {still_bad} still flagged in {d.name}")
    return 1 if still_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
