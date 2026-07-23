#!/usr/bin/env python3
"""Cross-run cost/latency aggregation (design W7): mean/median/p95 of wall,
attempt-inclusive USD, tokens, and per-phase durations over an arm directory's
cost.json files; cost-per-successful-task = TOTAL attempt-inclusive USD ÷
successful items. Usage: aggregate_costs.py <arm_dir> [<arm_dir> ...]"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def _pctl(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    idx = min(len(vs) - 1, max(0, round(q * (len(vs) - 1))))
    return vs[idx]


def _stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {"n": len(values), "mean": round(statistics.fmean(values), 3),
            "median": round(statistics.median(values), 3),
            "p95": round(_pctl(values, 0.95), 3)}


VAL_STEMS = ("pr4893", "pr4810", "pr4825", "pr4837", "pr4816",
             "issue4793", "issue4827", "issue4905", "issue4891", "issue4842")


def _campaign_stems(split: str) -> tuple[str, ...]:
    """The exact stems a split must find in the baseline dir. `val` keeps its
    frozen tuple; `all_pr` (the 20-case PR campaign) reads the dataset manifest
    so the list cannot drift from it. EVAL_STEMS overrides for ad-hoc slices."""
    import os

    env = tuple(s for s in (os.environ.get("EVAL_STEMS") or "").split(",") if s)
    if env:
        return env
    if split == "val":
        return VAL_STEMS
    if split == "all_pr":
        import yaml

        d = yaml.safe_load(
            (Path(__file__).parent / "vllm_omni_dataset.yaml").read_text())
        return tuple(f"pr{i['pr']}" for i in d["pr_review"])
    raise SystemExit(f"unknown --split {split!r} (val | all_pr)")


def aggregate_baseline(base_dir: Path, split: str) -> dict:
    """Recorded-baseline aggregation (plan round-3 fix): REQUIRES a split and
    validates the exact expected item stems — the baseline dir mixes
    val/train/test artifacts; wrong/missing items are a hard error."""
    stems = _campaign_stems(split)
    walls, usds, tins, touts = [], [], [], []
    for stem in stems:
        cj = base_dir / f"{stem}.cost.json"
        if not cj.exists():
            raise SystemExit(f"baseline missing expected item: {stem}")
        c = json.loads(cj.read_text())
        usds.append(float(c.get("cost_usd") or 0.0))   # real CLI-billed
        walls.append(float(c.get("wall_s") or 0.0))
        tins.append(float(c.get("input_tokens") or 0.0))
        touts.append(float(c.get("output_tokens") or 0.0))
    return {"arm": f"baseline:{base_dir.name}", "split": split,
            "items": len(stems), "basis": "real_billed_final_attempt",
            "wall_s": _stats(walls), "usd": _stats(usds),
            "input_tokens": _stats(tins), "output_tokens": _stats(touts),
            "total_usd": round(sum(usds), 4)}


def _attempt_service_totals(arm_dir: Path) -> dict:
    """Attempt-inclusive tokens/USD/by_role summed over EVERY attempt's spans
    (incl. `.invalid` sibling dirs — their spend counts even though their
    quality never does). These are SERVICE totals (span sums), never latency."""
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from infermatrix_copilot.metrics import cost_from_spans

    tot = {"usd": 0.0, "input_tokens": 0, "output_tokens": 0, "by_role": {}}
    roots = [arm_dir / "runs"]
    inv = arm_dir.with_name(arm_dir.name + ".invalid")
    if inv.exists():
        roots.append(inv / "runs")
    for root in roots:
        if not root.exists():
            continue
        for run in root.glob("*/run-*"):
            span = cost_from_spans(run / "trace.jsonl")
            if not span:
                continue
            tot["usd"] += span["usd"]
            tot["input_tokens"] += span["input_tokens"]
            tot["output_tokens"] += span["output_tokens"]
            for role, r in (span.get("by_role") or {}).items():
                agg = tot["by_role"].setdefault(
                    role, {"usd": 0.0, "calls": 0})
                agg["usd"] += r["usd"]
                agg["calls"] += r["calls"]
    tot["usd"] = round(tot["usd"], 4)
    tot["by_role"] = {k: {"usd": round(v["usd"], 4), "calls": v["calls"]}
                      for k, v in tot["by_role"].items()}
    return tot


def aggregate(arm_dir: Path) -> dict:
    walls, usds, tins, touts = [], [], [], []
    phases: dict[str, list[float]] = {}
    ttfrs: list[float] = []
    successes = 0
    items = 0
    for cj in sorted(arm_dir.glob("*.cost.json")):
        try:
            c = json.loads(cj.read_text())
        except Exception:
            continue
        items += 1
        walls.append(float(c.get("wall_s") or 0.0))
        # attempt-inclusive USD (every paid attempt, incl. clarifies/blocked)
        usd = c.get("attempt_usd_total")
        if usd is None:  # older cost.json: fall back to the run's own usd
            usd = c.get("usd") or (c.get("metrics") or {}).get("cost", {}).get("usd", 0)
        usds.append(float(usd or 0.0))
        tins.append(float(c.get("input_tokens") or 0.0))
        touts.append(float(c.get("output_tokens") or 0.0))
        rc = c.get("rc")
        if rc is not None and int(rc) == 0:   # rc=0 is success, not missing
            successes += 1
        m = c.get("metrics") or {}
        for step, dur in ((m.get("timings") or {}).get("steps") or {}).items():
            phases.setdefault(step, []).append(float(dur))
        ttfr = (m.get("timings") or {}).get("time_to_first_result_s")
        if isinstance(ttfr, (int, float)):
            ttfrs.append(float(ttfr))
    total_usd = sum(usds)
    return {
        "arm": arm_dir.name,
        "items": items,
        "successes": successes,
        # wall_s is the ONLY latency metric; span sums below are service totals
        "attempt_service_totals": _attempt_service_totals(arm_dir),
        "wall_s": _stats(walls),
        "usd_attempt_inclusive": _stats(usds),
        "input_tokens": _stats(tins),
        "output_tokens": _stats(touts),
        "time_to_first_result_s": _stats(ttfrs),
        "phase_dur_s": {k: _stats(v) for k, v in sorted(phases.items())},
        "total_usd": round(total_usd, 4),
        "cost_per_successful_task": (round(total_usd / successes, 4)
                                     if successes else None),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if "--baseline" in sys.argv:
        if "--split" not in sys.argv:
            raise SystemExit("--baseline REQUIRES --split (val)")
        split = sys.argv[sys.argv.index("--split") + 1]
        base = Path(sys.argv[sys.argv.index("--baseline") + 1])
        print(json.dumps(aggregate_baseline(base, split), indent=1))
        return 0
    for arg in sys.argv[1:]:
        print(json.dumps(aggregate(Path(arg)), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
