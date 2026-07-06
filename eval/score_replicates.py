#!/usr/bin/env python3
"""Score archived copilot_v2 replicate runs: per-run RQS3/RQS3e + the
replicate mean (the config's official score — single runs are ±0.1 noise).

Usage: python score_replicates.py <tag> [<tag2> ...]
Reads raw/copilot_v2_samples/<tag>_run*/RESULTS_V3.md snapshots.
"""

from __future__ import annotations

import re
import statistics
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
SAMPLES = EVAL_DIR / "raw" / "copilot_v2_samples"

sys.path.insert(0, str(EVAL_DIR))
from run_eval_v3 import rqs3e  # noqa: E402


def parse_snapshot(path: Path) -> dict | None:
    """Pull copilot_v2's aggregate + efficiency row out of a RESULTS_V3.md."""
    text = path.read_text()
    m = re.search(
        r"^\| copilot_v2 \| [\d.]+ \| [\d.]+ \| [\d.]+ \| [\d.]+ \| "
        r"\*\*([\d.]+)\*\* \| ([\d,]+) \|$",
        text, re.MULTILINE)
    e = re.search(
        r"^\| copilot_v2 \| ([\d.]+) \| \$([\d.]+) \| ([\d.]+) \| "
        r"\*\*([\d.]+)\*\*", text, re.MULTILINE)
    if not e:
        return None
    return {"rqs3": float(e.group(1)), "usd": float(e.group(2)),
            "minutes": float(e.group(3)), "rqs3e": float(e.group(4))}


def main() -> int:
    tags = sys.argv[1:] or ["final13"]
    runs = []
    for tag in tags:
        for d in sorted(SAMPLES.glob(f"{tag}_run*")):
            snap = d / "RESULTS_V3.md"
            if snap.exists():
                row = parse_snapshot(snap)
                if row:
                    runs.append((d.name, row))
    if not runs:
        print("no scored replicates found")
        return 1
    for name, r in runs:
        print(f"{name}: RQS3={r['rqs3']:.3f} RQS3e={r['rqs3e']:.3f} "
              f"(${r['usd']:.2f}, {r['minutes']:.1f} min)")
    q = [r["rqs3"] for _, r in runs]
    usd = [r["usd"] for _, r in runs]
    mins = [r["minutes"] for _, r in runs]
    mq, musd, mmin = (statistics.mean(x) for x in (q, usd, mins))
    sd = statistics.stdev(q) if len(q) > 1 else 0.0
    me = rqs3e(mq, musd, mmin)
    print(f"\nREPLICATE MEAN over {len(runs)} runs: "
          f"RQS3={mq:.4f} (sd {sd:.3f})  RQS3e={me:.4f} "
          f"(${musd:.2f}, {mmin:.1f} min)")
    print(f"targets: RQS3>0.6 {'MET' if mq > 0.6 else 'NOT MET'}; "
          f"RQS3e>0.5 {'MET' if me > 0.5 else 'NOT MET'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
