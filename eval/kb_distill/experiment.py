"""A pre-registered, engine-adjudicated experiment on the drafting step.

The meta-improvement engine's protocol (design §8) end to end, with this
benchmark as the unit runner: register the hypothesis, the metric, the item
set and both configuration fingerprints BEFORE any arm runs; run arm and
incumbent per item and replicate; score every unit through the
``kb-intake.draft`` outcome adapter; adjudicate paired within item with the
power recomputed on the retained items; write the verdict as a
``decision(type=experiment_verdict)`` record.

What "running" means here:

* the **arm** drafts live (generator × strategy from its overrides) and is
  judged by the production gate (``Bench.judge_unit``);
* the **incumbent** is the recorded production generator: its reply to the
  byte-identical prompt, re-appended as a unit of the experiment's store and
  judged the same way. It has ONE recorded sample per item; every replicate
  of the incumbent side therefore carries that same sample (the paired delta
  per item is then arm-mean minus the incumbent sample), which the
  hypothesis text states;
* **gold** for the item is the incumbent's gate-passing rules (written by
  ``gold`` from the judged incumbent arm), so ``recall_gold`` says how much
  of what the production generator got through the gate the arm covers.

Usage (after ``harness.py replay`` + ``judge`` of the incumbent arm)::

    experiment.py --bench DIR --items items.json --git REPO --mirror M --state-dir SNAP \\
        gold --incumbent opus-recorded --gold-dir DIR/gold
    experiment.py ... register --metric net_pass_review --arm KB_GENERATOR=zcode:GLM-5.3-Flash \\
        --arm KB_DRAFT_STRATEGY=v2 --incumbent KB_GENERATOR=claude-code:claude-opus-5-5 \\
        --incumbent KB_DRAFT_STRATEGY=v1 --replicates 2 --min-effect 0.25
    experiment.py ... run EXP-ID
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from infermatrix_copilot.config import Settings
from infermatrix_copilot.improve import experiments
from infermatrix_copilot.improve.adapters.kb_intake import gold_from_incumbent, write_gold
from infermatrix_copilot.improve.budget import Governor
from infermatrix_copilot.improve.reader import units_between
from infermatrix_copilot.trace_store import TraceStore

from .harness import INCUMBENT_GENERATOR, WORKFLOW, Bench, _environ


def _settings(bench_dir: Path, judge: str) -> Settings:
    return Settings(_env_file=None, improve_judge=judge, improve_ledger_dir=str(bench_dir / "improve"),
                    improve_budget_usd_week=50.0, improve_budget_judge_calls_week=100_000,
                    trace_store_root=str(bench_dir / "traces"))


def build_gold(bench: Bench, incumbent: str, gold_dir: Path) -> dict[str, int]:
    units = units_between(bench.store, 0.0, float("inf"), grace=0.0, lookback=0.0)
    counts: dict[str, int] = {}
    for unit_id, unit in units.items():
        if not unit_id.startswith(f"{incumbent}:") or unit.workflow != WORKFLOW:
            continue
        entries = gold_from_incumbent(bench.store, unit)
        write_gold(gold_dir, unit.item, entries, source=f"gate:{bench.judge.label()}:{incumbent}")
        counts[unit.item] = len(entries)
    return counts


def make_stage(bench: Bench):
    def stage(settings, item: str, *, shadow_root: Path, run_dir: Path) -> dict:
        data = bench.items[item]
        shadow_dir = shadow_root / re.sub(r"[^A-Za-z0-9._-]+", "_", item)
        shadow_dir.mkdir(parents=True, exist_ok=True)
        snapshots = run_dir / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshots / (re.sub(r"[^A-Za-z0-9._-]+", "_", item) + ".json")
        snapshot_path.write_text(json.dumps({"item": item, "base_sha": data["base_sha"], "evidence": data["evidence"],
                                             "release": data["release"], "today": data["today"]},
                                            ensure_ascii=False), encoding="utf-8")
        return {"repo": bench.repo, "pr": data["pr"], "shadow_dir": str(shadow_dir), "snapshot_path": str(snapshot_path)}
    return stage


def make_run_unit(bench: Bench, experiment_id: str, reuse: dict[str, str] | None = None):
    """``reuse`` maps a side to a benchmark arm whose judged units may stand
    in for that side: a unit of the same item, replicate and fingerprint is
    tagged for the experiment instead of being drafted and judged again (the
    engine still checks its fingerprint and scores it from its outcomes)."""
    reuse = reuse or {}

    def run_unit(*, side: str, item: str, replicate: int, env: dict, snapshot_path: Path, shadow_dir: Path,
                 run_root: Path, playbook: str, repo: str, pr: int, timeout: int = 3600) -> dict:
        generator = env.get("KB_GENERATOR") or (INCUMBENT_GENERATOR if side == "incumbent" else "")
        strategy = env.get("KB_DRAFT_STRATEGY") or "v1"
        tag = env.get("IMPROVE_UNIT_TAG", "")
        arm = f"{experiment_id}:{side}"
        candidate = bench.units.get(f"{reuse.get(side, '')}:{item}:{replicate}") if reuse.get(side) else None
        if candidate and candidate.get("status") == "judged" \
                and candidate["fingerprint"] == bench.fingerprint(generator, strategy):
            bench.retag(candidate["unit_id"], tag, experiment_id=experiment_id, side=side)
            return {"rc": 0, "stderr": "", "tag": tag, "reused": candidate["unit_id"]}
        with _environ(IMPROVE_UNIT_TAG=tag):
            if side == "incumbent" and generator == INCUMBENT_GENERATOR and strategy == "v1":
                unit_ids = bench.replay(arm, [item], strategy=strategy, replicate=replicate)
            else:
                unit_ids = bench.run(arm, [item], generator=generator, strategy=strategy, replicates=replicate,
                                     workers=1, only_replicate=replicate)
        for unit_id in unit_ids:
            bench.judge_unit(unit_id)
        return {"rc": 0 if unit_ids else 1, "stderr": "" if unit_ids else "no unit produced", "tag": tag}
    return run_unit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--bench", required=True)
    parser.add_argument("--items", required=True)
    parser.add_argument("--git", required=True)
    parser.add_argument("--mirror", default="")
    parser.add_argument("--state-dir", default="")
    parser.add_argument("--judge", default="", help="gate judge role (default KB_JUDGE)")
    parser.add_argument("--gold-judge", default="cli:codex:gpt-6-sol", help="engine judge spec for gold_match")
    parser.add_argument("--gold-dir", default="")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("gold")
    p.add_argument("--incumbent", default="opus-recorded")
    p = sub.add_parser("register")
    p.add_argument("--hypothesis", default="")
    p.add_argument("--metric", default="net_pass_review")
    p.add_argument("--arm", action="append", default=[], help="KEY=VALUE overrides of the arm")
    p.add_argument("--incumbent", action="append", default=[], help="KEY=VALUE overrides of the incumbent")
    p.add_argument("--items-only", default="")
    p.add_argument("--replicates", type=int, default=2)
    p.add_argument("--min-effect", type=float, default=0.25)
    p.add_argument("--direction", default="higher")
    p.add_argument("--sd-item", type=float, default=None)
    p = sub.add_parser("run")
    p.add_argument("experiment_id")
    p.add_argument("--reuse-arm", default="", help="benchmark arm whose judged units stand in for the arm side")
    p.add_argument("--reuse-incumbent", default="", help="benchmark arm whose judged units stand in for the incumbent")
    p = sub.add_parser("list")
    args = parser.parse_args(argv)

    bench_dir = Path(args.bench)
    gold_dir = Path(args.gold_dir or bench_dir / "gold")
    os.environ["KB_INTAKE_GOLD_DIR"] = str(gold_dir)
    settings = _settings(bench_dir, args.gold_judge)
    bench = Bench(bench_dir, args.items, args.git, mirror_dir=args.mirror or None, state_dir=args.state_dir or None,
                  settings=settings, judge=args.judge or "")
    ledger_dir = bench_dir / "improve"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    if args.command == "gold":
        counts = build_gold(bench, args.incumbent, gold_dir)
        print(f"gold written for {len(counts)} items; entries: {sum(counts.values())}")
        for item, n in sorted(counts.items()):
            print(f"  {item}: {n}")
        return 0
    if args.command == "register":
        items = bench.select(args.items_only.split(",")) if args.items_only else list(bench.items)
        arm = dict(kv.split("=", 1) for kv in args.arm)
        incumbent = dict(kv.split("=", 1) for kv in args.incumbent)
        hypothesis = args.hypothesis or (
            f"Drafting with {arm} reaches the gate quality of the recorded incumbent {incumbent} on the "
            f"same intake events; the incumbent side re-uses its one recorded sample per item for every replicate.")
        governor = Governor(ledger_dir, usd_week=settings.improve_budget_usd_week,
                            judge_calls_week=settings.improve_budget_judge_calls_week, settings=settings)
        exp = experiments.register(bench.store, settings, ledger_dir, workflow=WORKFLOW, hypothesis=hypothesis,
                                   metric=args.metric, items=items, arm_overrides=arm, incumbent_overrides=incumbent,
                                   direction=args.direction, min_effect=args.min_effect, replicates=args.replicates,
                                   cost_per_unit_usd=0.0, governor=governor, registered_by="owner",
                                   sd_item=args.sd_item)
        print(json.dumps({k: v for k, v in exp.__dict__.items() if k not in ("item_set", "fingerprint_diff")},
                         ensure_ascii=False, indent=1, default=str))
        print("fingerprint_diff:", json.dumps(exp.fingerprint_diff, ensure_ascii=False, default=str)[:800])
        return 0
    if args.command == "run":
        reuse = {k: v for k, v in (("arm", args.reuse_arm), ("incumbent", args.reuse_incumbent)) if v}
        exp = experiments.run(bench.store, settings, ledger_dir, args.experiment_id,
                              run_unit=make_run_unit(bench, args.experiment_id, reuse), stage=make_stage(bench),
                              shadow_store=bench.store)
        print(json.dumps(exp.result, ensure_ascii=False, indent=1, default=str))
        print("STATE:", exp.state)
        return 0
    if args.command == "list":
        for exp in experiments.list_experiments(ledger_dir):
            print(exp.experiment_id, exp.state, exp.metric, exp.n_available, "items", exp.result.get("label", ""))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
