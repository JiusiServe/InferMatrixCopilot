#!/usr/bin/env python3
"""Paired per-dimension results over validated judgment dirs (eval plan v3).

For each arm: score(dim) = mean over {3 generation replicates x 3 judge
replicates x items-of-that-kind} of the COPILOT side's rubric value (side
resolved via _blinding). Deltas are computed on unrounded means; item-level
paired deltas (mean over judge reps per item) give sign counts.

Usage: compute_results.py <label:arm_prefix> ...  e.g.
  compute_results.py A0:copilot_v2_t4 A1:copilot_v3
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

DS = Path(__file__).parent.parent
PR_DIMS = ("recall", "precision", "actionability", "gap_hit")
ISSUE_DIMS = ("correctness", "grounding", "completeness")
VAL_STEMS = ["pr4893", "pr4810", "pr4825", "pr4837", "pr4816",
             "issue4793", "issue4827", "issue4905", "issue4891", "issue4842"]
GAP_STEMS = {"pr4810"}   # gap_hit scored only on the GOLD latent-gap item


def collect(arm_prefix: str) -> tuple[dict, dict]:
    """dim -> [values]; and (stem, dim) -> [values] for pairing."""
    dims_all: dict[str, list[float]] = defaultdict(list)
    per_item: dict[tuple[str, str], list[float]] = defaultdict(list)
    for k in (1, 2, 3):
        jdir = DS / "judgments" / f"val_{arm_prefix}_r{k}"
        if not jdir.exists():
            continue
        for f in sorted(jdir.glob("*.json")):
            v = json.loads(f.read_text())
            stem = f.name.split(".r")[0]
            side = "x" if v["_blinding"]["X"] == "copilot_v2" else "y"
            s = v[side]
            dims = PR_DIMS if stem.startswith("pr") else ISSUE_DIMS
            for d in dims:
                if d == "gap_hit":
                    if stem not in GAP_STEMS:
                        continue
                    val = 1.0 if s.get(d) else 0.0
                else:
                    val = float(s.get(d) or 0.0)
                dims_all[d].append(val)
                per_item[(stem, d)].append(val)
    return dims_all, per_item


def main() -> None:
    arms = {}
    for arg in sys.argv[1:]:
        label, prefix = arg.split(":", 1)
        arms[label] = collect(prefix)
    labels = list(arms)
    all_dims = [*PR_DIMS, *ISSUE_DIMS]
    print(f"{'dim':14s} " + " ".join(f"{lb:>8s}" for lb in labels)
          + ("   Δ(последний−первый)" if len(labels) > 1 else ""))
    for d in all_dims:
        row = f"{d:14s} "
        means = []
        for lb in labels:
            vals = arms[lb][0].get(d) or []
            m = sum(vals) / len(vals) if vals else float("nan")
            means.append(m)
            row += f"{m:8.4f} "
        if len(means) > 1:
            row += f"  Δ={means[-1] - means[0]:+.4f}"
        print(row)
    if len(labels) == 2:
        a, b = labels
        print("\npaired per-item deltas (B−A, mean over judge reps):")
        for d in all_dims:
            deltas = []
            for stem in VAL_STEMS:
                va = arms[a][1].get((stem, d))
                vb = arms[b][1].get((stem, d))
                if va and vb:
                    deltas.append((stem, sum(vb) / len(vb) - sum(va) / len(va)))
            if not deltas:
                continue
            pos = sum(1 for _, x in deltas if x > 0.001)
            neg = sum(1 for _, x in deltas if x < -0.001)
            print(f"  {d:14s} +{pos}/-{neg}/{len(deltas)} "
                  + " ".join(f"{s}:{x:+.2f}" for s, x in deltas))


if __name__ == "__main__":
    main()
