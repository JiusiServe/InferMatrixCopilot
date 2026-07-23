#!/usr/bin/env python3
"""Aggregate the 20-case PR-review campaign into doc/EVAL-PR20-report.md.

Scoring rule (unchanged from the val campaign): a configuration's score is the
mean over GENERATION replicates of each replicate's own mean over
{items x judge replicates} — never a pooled mean over all verdicts, which would
let a replicate with more surviving verdicts weigh more. Spread is the sd
ACROSS replicate means, the quantity `eval/ANALYSIS.md` measures at ~±0.1 for
single runs.

Splits are reported separately and never pooled into a headline: train is the
adaptation stream, val the promotion gate, test the frozen holdout. gap_hit is
a 1-item measurement inside each split (the three GOLD latent-gap PRs) and is
labelled as such rather than presented as a rate.

Usage: make_pr20_report.py [out.md]
"""

from __future__ import annotations

import json
import statistics as st
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DS = HERE.parent
ROOT = DS.parent.parent
PY = sys.executable

ARM = "copilot_v4_pr20"
PREFIX = "pr20"
REPS = (1, 2, 3)
DIMS = ("recall", "precision", "actionability")
GOLD = {"pr4870": "train", "pr4810": "val", "pr4834": "test"}
# A1 = the arm whose val numbers doc/EVAL-goal-report.md records (MoA off),
# scored on the SAME rubric by the same judge model. PR dims only.
A1_VAL = {"recall": (0.520, 0.021), "precision": (0.800, 0.034),
          "actionability": (0.731, 0.062)}


def splits() -> dict[str, str]:
    import yaml

    d = yaml.safe_load((DS / "vllm_omni_dataset.yaml").read_text())
    return {f"pr{i['pr']}": i["split"] for i in d["pr_review"]}


def collect() -> tuple[dict, dict]:
    """(rep -> split -> dim -> [values], rep -> stem -> gap_hit mean)."""
    sp = splits()
    per: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    gap: dict = defaultdict(lambda: defaultdict(list))
    for k in REPS:
        jdir = DS / "judgments" / f"{PREFIX}_{ARM}_r{k}"
        if not jdir.exists():
            continue
        for f in sorted(jdir.glob("*.r*.json")):
            v = json.loads(f.read_text())
            stem = f.name.split(".r")[0]
            side = "x" if v["_blinding"]["X"] == "copilot_v2" else "y"
            s = v[side]
            for dim in DIMS:
                val = float(s.get(dim) or 0.0)
                per[k][sp[stem]][dim].append(val)
                per[k]["all"][dim].append(val)
            if stem in GOLD:
                gap[k][stem].append(1.0 if s.get("gap_hit") else 0.0)
    return per, gap


def rep_means(per: dict, split: str, dim: str) -> list[float]:
    return [st.mean(per[k][split][dim]) for k in sorted(per)
            if per[k][split].get(dim)]


def _fmt(vals: list[float]) -> str:
    if not vals:
        return "-"
    m = st.mean(vals)
    sd = st.stdev(vals) if len(vals) > 1 else 0.0
    return f"{m:.3f} ± {sd:.3f}"


def cost_block() -> tuple[list[dict], dict]:
    arms = []
    for k in REPS:
        d = DS / "arms" / f"{ARM}_r{k}"
        if not d.exists():
            continue
        out = subprocess.run([PY, str(DS / "aggregate_costs.py"), str(d)],
                             capture_output=True, text=True).stdout
        try:
            arms.append(json.loads(out))
        except json.JSONDecodeError:
            pass
    out = subprocess.run(
        [PY, str(DS / "aggregate_costs.py"), "--baseline",
         str(DS / "baselines" / "claudecode_opus48"), "--split", "all_pr"],
        capture_output=True, text=True).stdout
    try:
        base = json.loads(out)
    except json.JSONDecodeError:
        base = {}
    return arms, base


def trace_block() -> dict:
    tot = {"runs": 0, "incomplete": 0, "llm_calls": 0, "events_bytes": 0,
           "spans_bytes": 0, "in": 0, "out": 0, "retries": {}}
    for k in REPS:
        p = HERE / f"trace_inventory_r{k}.json"
        if not p.exists():
            continue
        recs = json.loads(p.read_text())["arms"][f"{ARM}_r{k}"]
        seen: dict[str, int] = {}
        for r in recs:
            tot["runs"] += 1
            tot["incomplete"] += 1 if r["errors"] else 0
            tot["llm_calls"] += r.get("llm_spans", 0)
            tot["events_bytes"] += r["bytes"].get("events.jsonl", 0)
            tot["spans_bytes"] += r["bytes"].get("trace.jsonl", 0)
            tot["in"] += r["tokens"]["spans"]["in"]
            tot["out"] += r["tokens"]["spans"]["out"]
            seen[r["stem"]] = seen.get(r["stem"], 0) + 1
        extra = {s: n for s, n in seen.items() if n > 1}
        if extra:
            tot["retries"][f"r{k}"] = extra
    return tot


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        ROOT / "doc" / "EVAL-PR20-report.md"
    per, gap = collect()
    n_reps = len(per)
    arms, base = cost_block()
    tr = trace_block()

    L: list[str] = []
    A = L.append
    A("# 20-case PR-review evaluation — full rerun with complete traces")
    A("")
    A(f"{n_reps} generation replicates x 20 `pr_review` items (10 train / 5 val "
      "/ 5 test) x 3 judge replicates = "
      f"{n_reps * 60} blind pairwise verdicts against the recorded "
      "`claudecode_opus48` baseline (never rerun). Judge: `claude-sonnet-5`, "
      "tool-less, randomized X/Y order — a third model, distinct from both "
      "arms. Metric definitions reused unchanged from "
      "`eval/dataset/judge_val.py`.")
    A("")
    A("**Configuration**: `MOA_WHEN=off`, `PR_CONTEXT_MODE=no_discussion`, "
      "`REVIEW_DEPTH=auto`, `ALLOW_POST=0`/`ALLOW_PUSH=0`, full trace capture "
      "(`AGENT_TRACE_IO_FULL=1`). MoA off matches the A1 arm in "
      "`doc/EVAL-goal-report.md`, so the val slice stays comparable.")
    A("")
    A("## Leakage controls (asserted per item, not assumed)")
    A("")
    A("1. `PR_CONTEXT_MODE=no_discussion` — the human review discussion IS the "
      "ground truth, so it is excluded from the prompt.")
    A("2. PR-time checkout — every PR item's report asserts `PR-TIME TREE` with "
      "the head SHA from `expected_pr_heads.json`, frozen independently before "
      "generation. `pr.fetch_diff`'s live-checkout fallback returns success, so "
      "rc=0 alone would not catch a contaminated tree.")
    A("3. Head SHAs were re-resolved for all 20 PRs before the campaign: "
      "**zero drift** on the 5 val PRs carried over from the val campaign.")
    A("4. `pr_review` is a read-only kind, so no skill/profile/debug-memory "
      "writeback; skill-candidate files were digest-snapshotted before and "
      "after.")
    A("")
    A("## Quality — replicate means ± sd across replicates")
    A("")
    A("Per split, never pooled: train is the adaptation stream, val the "
      "promotion gate, test the frozen holdout.")
    A("")
    A("| slice | n | " + " | ".join(DIMS) + " |")
    A("|---|---|" + "---|" * len(DIMS))
    for split, n in (("all", 20), ("train", 10), ("val", 5), ("test", 5)):
        row = f"| {split} | {n} | "
        row += " | ".join(_fmt(rep_means(per, split, d)) for d in DIMS)
        A(row + " |")
    A("")
    A("### vs the recorded A1 val numbers (`doc/EVAL-goal-report.md`)")
    A("")
    A("| dim | this campaign (val) | A1 (val) | Δ |")
    A("|---|---|---|---|")
    for d in DIMS:
        vals = rep_means(per, "val", d)
        if not vals:
            continue
        m = st.mean(vals)
        a1, a1sd = A1_VAL[d]
        A(f"| {d} | {_fmt(vals)} | {a1:.3f} ± {a1sd:.3f} | {m - a1:+.3f} |")
    A("")
    A("Both sides are 5-item slices with replicate sds of 0.02-0.07, so "
      "differences under ~0.1 sit inside judge+generation noise "
      "(`eval/ANALYSIS.md`: ±0.1 per single run).")
    A("")
    A("### gap_hit — the three GOLD latent-gap items")
    A("")
    A("History proves human review missed something in each. **One item per "
      "split**, so each cell is a 1-item measurement, not a rate.")
    A("")
    A("| item | split | hit rate over replicates |")
    A("|---|---|---|")
    for stem, sp in GOLD.items():
        vals = [st.mean(gap[k][stem]) for k in sorted(gap) if gap[k].get(stem)]
        A(f"| {stem} | {sp} | {_fmt(vals)} |")
    A("")
    A("## Cost and latency")
    A("")
    A("| arm | items | rc=0 | USD (attempt-incl.) | wall s mean/median/p95 |")
    A("|---|---|---|---|---|")
    for a in arms:
        w = a["wall_s"]
        A(f"| {a['arm']} | {a['items']} | {a['successes']} | "
          f"${a['total_usd']:.3f} | {w['mean']:.0f} / {w['median']:.0f} / "
          f"{w['p95']:.0f} |")
    if base:
        w = base["wall_s"]
        A(f"| {base['arm']} (recorded) | {base['items']} | - | "
          f"${base['total_usd']:.3f} | {w['mean']:.0f} / {w['median']:.0f} / "
          f"{w['p95']:.0f} |")
    A("")
    if arms and base:
        mean_arm = st.mean([a["total_usd"] for a in arms])
        A(f"Generation costs **${mean_arm:.2f} per 20-item replicate** vs the "
          f"baseline's **${base['total_usd']:.2f}** for the same 20 PRs — "
          f"**{base['total_usd'] / mean_arm:.1f}x cheaper**. Judging costs more "
          "than generating: ~$11 per replicate at $0.185/verdict.")
    A("")
    A("Wall-clock is the only latency metric here; per-role span sums are "
      "service time and are never summed into it (concurrent lenses would "
      "double-count).")
    A("")
    A("## Trace corpus")
    A("")
    A(f"- **{tr['runs']} run dirs, {tr['incomplete']} incomplete** — every run "
      "carries `trace.jsonl` (spans + `run_meta` header), `run_trace.jsonl` "
      "(RunTrace events) and `events.jsonl` (full request/response payloads).")
    A(f"- {tr['llm_calls']:,} LLM calls · {tr['in']:,} input / {tr['out']:,} "
      "output tokens.")
    A(f"- **{tr['events_bytes'] / 1e6:.0f} MB** of payloads + "
      f"{tr['spans_bytes'] / 1e6:.1f} MB of spans.")
    A("- Gate (`goal-eval/verify_traces.py`): per run, "
      "`llm.request == llm.response == llm` span count, and token totals agree "
      "across events.jsonl / trace.jsonl / metrics.json.")
    if tr["retries"]:
        A(f"- Retried items (one extra run dir each, cost counted): "
          f"{tr['retries']}.")
    A("- `eval/dataset/arms/*/runs/` is gitignored: the corpus is local-only.")
    A("")
    A("## Caveats")
    A("")
    A("- **Retrospective synthesis under thread visibility**, not blind "
      "pre-resolution maintenance — same framing as the val campaign.")
    A("- Evidence is asymmetric and not claimed otherwise: the baseline ran "
      "against post-merge `main` with the discussion reachable; these arms run "
      "PR-time trees with the discussion excluded.")
    A("- Same-family judge for neither arm (Sonnet-5 vs DeepSeek arm / Opus "
      "baseline), but the baseline is cross-family to the judge's own lineage.")
    A("- Test-split items were scored and reported as aggregates only; item "
      "content and judge rationales were not read, so the holdout stays usable "
      "for future error analysis.")
    A("- Cost/latency are NOT comparable to `EVAL-goal-report.md`'s: different "
      "item mix (20 PRs vs 5 PRs + 5 issues) and payload-write overhead.")
    A("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print("\n".join(L[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
