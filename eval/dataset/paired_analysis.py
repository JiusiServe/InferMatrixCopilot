#!/usr/bin/env python3
"""Paired, item-clustered effect sizes for arm-vs-baseline judgment sets.

Why this exists. Reporting each side's raw rubric MEAN and comparing them
across judgment sets is the wrong statistic for this campaign, and it
overstated a result: the baseline's own recall mean read .335 / .338 / .416
across three wave-4 sets scoring the SAME baseline reviews, i.e. ±.08 of
pure judge drift — larger than the arm-vs-baseline differences under study.

Two corrections, both applied here:

1. **Pair within the verdict.** Every judge call scores BOTH candidates, so
   `arm - baseline` inside one verdict cancels that call's leniency. The
   drift above is a between-call effect; it disappears under pairing.
2. **Cluster by item.** Three replicates of the same PR are not three
   independent observations — they share the item's difficulty and the two
   fixed review texts. Averaging replicates per item and taking the CI over
   items (t with n_items-1 df) is the honest interval; treating 30 verdicts
   as independent understates the standard error roughly two-fold.

A win/loss count is a third statistic and is kept, but it is the least
informative: it discards margin, and a "slight" 0.02 loss counts the same as
a decisive one.

Usage:
  paired_analysis.py <judgment_set> [<judgment_set> ...]
  paired_analysis.py --pool <set> <set> ...   # per-item mean across sets
Sets are directory names under `judgments/` (or paths).
"""
from __future__ import annotations

import glob
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
# two-sided 95% t quantiles by df (n_items - 1); n<=2 is not summarized
_T95 = {2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
        14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 24: 2.064, 29: 2.045, 39: 2.023, 59: 2.001}


def _t95(df: int) -> float:
    if df in _T95:
        return _T95[df]
    for k in sorted(_T95):
        if df <= k:
            return _T95[k]
    return 1.96


def deltas(setname: str) -> dict[str, dict[str, list[float]]]:
    """Per-item lists of per-verdict (arm - baseline) deltas."""
    root = Path(setname)
    if not root.exists():
        root = HERE / "judgments" / setname
    out: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"recall": [], "precision": [], "actionability": [],
                 "wins": []})
    for f in sorted(glob.glob(str(root / "pr*.r*.json"))):
        v = json.load(open(f, encoding="utf-8"))
        stem = os.path.basename(f).split(".")[0]
        roles, blind = v.get("_roles") or {}, v.get("_blinding") or {}
        if not roles or not blind:
            continue
        a = "x" if blind.get("X") == roles.get("arm") else "y"
        b = "y" if a == "x" else "x"
        for key in ("recall", "precision", "actionability"):
            if key in v.get(a, {}) and key in v.get(b, {}):
                out[stem][key].append(float(v[a][key]) - float(v[b][key]))
        winner = blind.get(v.get("winner"), "tie")
        out[stem]["wins"].append(1.0 if winner == roles.get("arm")
                                 else 0.0 if winner == roles.get("baseline")
                                 else 0.5)
    return out


def summarize(per_item: dict[str, dict[str, list[float]]], label: str) -> dict:
    """Item-clustered mean and 95% CI per metric."""
    items = sorted(per_item)
    row = {"label": label, "n_items": len(items),
           "n_verdicts": sum(len(per_item[i]["recall"]) for i in items)}
    for key in ("recall", "precision", "actionability", "wins"):
        vals = [st.mean(per_item[i][key]) for i in items if per_item[i][key]]
        if len(vals) < 2:
            continue
        m = st.mean(vals)
        se = st.stdev(vals) / math.sqrt(len(vals))
        h = _t95(len(vals) - 1) * se
        row[key] = {"mean": m, "lo": m - h, "hi": m + h, "sd": st.stdev(vals)}
    return row


def render(rows: list[dict], per_item_last: dict | None = None) -> str:
    out = ["", f"{'config':22}{'items':>6}{'verd':>6}  "
               f"{'Δrecall [95% CI]':<26}{'Δprecision [95% CI]':<26}win share",
           "-" * 96]
    for r in rows:
        def cell(key):
            d = r.get(key)
            if not d:
                return " " * 26
            star = "*" if d["hi"] < 0 or d["lo"] > 0 else " "
            return f"{d['mean']:+.3f} [{d['lo']:+.3f},{d['hi']:+.3f}]{star}  "
        ws = r.get("wins", {}).get("mean")
        out.append(f"{r['label']:22}{r['n_items']:>6}{r['n_verdicts']:>6}  "
                   f"{cell('recall')}{cell('precision')}"
                   f"{'' if ws is None else f'{ws:.2f}'}")
    out += ["", "* = 95% CI excludes zero (a difference the data supports).",
            "Δ = arm − baseline, paired inside each verdict, clustered by item."]
    if per_item_last:
        out.append("\nper-item Δrecall (last row):")
        for k in sorted(per_item_last):
            vals = per_item_last[k]["recall"]
            if vals:
                out.append(f"   {k}: {st.mean(vals):+.3f}")
    return "\n".join(out)


def power_note(rows: list[dict]) -> str:
    """How many ITEMS a future gate needs to resolve the observed effect."""
    last = rows[-1]
    d = last.get("recall")
    if not d or not d["sd"]:
        return ""
    eff = abs(d["mean"]) or 0.05
    n = ((_t95(last["n_items"] - 1) + 0.84) * d["sd"] / eff) ** 2
    return (f"\nPower: at the observed item-level sd ({d['sd']:.3f}), "
            f"resolving a {eff:.3f} difference at 95%/80% needs ~{math.ceil(n)} "
            f"items ({last['n_items']} in this set).")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--pool"]
    pool = "--pool" in sys.argv
    if not args:
        print(__doc__.strip().splitlines()[0])
        print("usage: paired_analysis.py [--pool] <judgment_set> ...")
        return 2
    rows, last = [], None
    if pool:
        merged: dict = defaultdict(
            lambda: {"recall": [], "precision": [], "actionability": [],
                     "wins": []})
        for s in args:
            for item, d in deltas(s).items():
                for k, v in d.items():
                    merged[item][k].extend(v)
        rows.append(summarize(merged, "POOLED " + "+".join(
            os.path.basename(a) for a in args)[:40]))
        last = merged
    else:
        for s in args:
            per_item = deltas(s)
            rows.append(summarize(per_item, os.path.basename(s)[:22]))
            last = per_item
    print(render(rows, last))
    print(power_note(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
