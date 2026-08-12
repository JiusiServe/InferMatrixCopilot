#!/usr/bin/env python3
"""Compare N arms against the single reference baseline they were all judged against.

Every arm is judged in the ARM_A slot against the same ARM_B baseline, so their scores
are commensurable without touching `judge_val.py` — proposer/judge independence is the
property that makes these numbers worth anything, and it is not worth risking to save a
post-processing script.

Four things this is careful about:

* **Arm identity.** Older verdicts label the ARM_A slot `copilot_v2` whatever arm
  actually ran (a generic label from when there was only one). The real identity lives
  in `_arm_meta.arm_a_dir`, which is what this reads. Trusting the label would silently
  mix arms.

* **One campaign at a time.** With two baselines and two judges now on disk, verdicts
  from different campaigns are averageable-looking and meaningless. Mixed baseline dir
  or mixed judge model is a hard refusal, not a warning: the gpt-5.6 / Opus 5 numbers
  are internally consistent and *not* comparable to the sonnet-5 / Opus 4.8 ones.

* **Completeness.** A campaign that silently lost verdicts reports a wrong denominator.
  Set EXPECT_ITEMS / EXPECT_VERDICTS to make short input a refusal — the earlier
  campaign nearly reported on 179 verdicts instead of 180 because nothing checked.

* **Structural skips.** OCR cannot review Markdown, so a docs-only PR returns zero
  findings in ~100ms. That is a real capability result and the primary number includes
  it. A secondary number excludes those PRs from ALL arms — excluding them from one
  side only would be dishonest, and reporting only the primary would hide *why* OCR
  scores where it does.

Usage: compare_ocr_vs_copilot.py <judgments_dir> [<judgments_dir> ...]
Env:   EXPECT_ITEMS (per arm), EXPECT_VERDICTS (total) — refuse if not met exactly
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ARMS = HERE / "arms"
RUBRIC = ("recall", "precision", "actionability")


def _structurally_skipped(arm_dir: Path) -> set[str]:
    """PR stems the arm could not review at all (capability boundary, not a verdict)."""
    out = set()
    for cost in arm_dir.glob("pr*.cost.json"):
        try:
            if json.loads(cost.read_text(encoding="utf-8")).get("structural_skip"):
                out.add(cost.name.split(".")[0])
        except Exception:
            continue
    return out


def _load(jdir: Path) -> tuple[str, dict[str, list[dict]], str, str]:
    """(arm_dir_name, {stem: [verdict, ...]}, baseline_dir, judge_model), keyed on
    what each verdict RECORDED rather than on the directory name."""
    by_stem: dict[str, list[dict]] = defaultdict(list)
    arm_dirs: set[str] = set()
    base_dirs: set[str] = set()
    judges: set[str] = set()
    unparseable = []
    for f in sorted(jdir.glob("pr*.r*.json")):
        try:
            v = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            # silently skipping these is how a campaign reports a wrong denominator
            unparseable.append(f"{f.name}: {exc}")
            continue
        meta = v.get("_arm_meta") or {}
        if meta.get("arm_a_dir"):
            arm_dirs.add(Path(str(meta["arm_a_dir"]).rstrip("/")).name)
        # legacy verdicts predate arm_b_dir/judge_model: they were all Opus 4.8 + sonnet
        base_dirs.add(Path(str(meta.get("arm_b_dir")
                               or "baselines/claudecode_opus48").rstrip("/")).name)
        judges.add(str(meta.get("judge_model") or "claude-sonnet-5"))
        by_stem[f.name.split(".")[0]].append(v)
    if unparseable:
        sys.exit(f"{jdir.name}: {len(unparseable)} unreadable verdict(s) — refusing to "
                 f"score a partial campaign:\n  " + "\n  ".join(unparseable))
    if len(arm_dirs) > 1:
        sys.exit(f"{jdir.name}: verdicts mix arms {sorted(arm_dirs)} — refusing to score")
    if len(base_dirs) > 1:
        sys.exit(f"{jdir.name}: verdicts mix baselines {sorted(base_dirs)} — refusing "
                 "to score (arms judged against different references are not "
                 "comparable)")
    if len(judges) > 1:
        sys.exit(f"{jdir.name}: verdicts mix judges {sorted(judges)} — refusing to score")
    return ((arm_dirs.pop() if arm_dirs else jdir.name), by_stem,
            base_dirs.pop(), judges.pop())


def _score(verdicts: dict[str, list[dict]], exclude: set[str]) -> dict:
    """Mean rubric for the ARM_A side, plus win rate against the baseline."""
    scores = {k: [] for k in RUBRIC}
    wins = {"arm": 0, "baseline": 0, "tie": 0}
    n_items = 0
    for stem, vs in verdicts.items():
        if stem in exclude:
            continue
        n_items += 1
        for v in vs:
            blind = v.get("_blinding") or {}
            # Which label sat in the baseline slot, as recorded. Older verdicts have no
            # _roles and always used the literal "opus_baseline"; new ones name the real
            # directory, so string-matching that literal would mis-assign every verdict
            # in the gpt-5.6 campaign — silently, and in the arm's favour half the time.
            base_label = (v.get("_roles") or {}).get("baseline", "opus_baseline")
            side = "x" if blind.get("X") != base_label else "y"
            rub = v.get(side) or {}
            for k in RUBRIC:
                if isinstance(rub.get(k), (int, float)):
                    scores[k].append(float(rub[k]))
            w = v.get("winner")
            if w == "tie" or w not in ("X", "Y"):
                wins["tie"] += 1
            elif blind.get(w) == base_label:
                wins["baseline"] += 1
            else:
                wins["arm"] += 1
    total = sum(wins.values()) or 1
    return {
        "items": n_items, "verdicts": sum(wins.values()),
        "win_rate": round(wins["arm"] / total, 3),
        "wins": wins,
        **{k: round(statistics.fmean(v), 3) if v else None for k, v in scores.items()},
    }


def _pm(values: list[float]) -> str:
    """mean ± half-range across repeats — the spread is the point, not the mean."""
    vs = [v for v in values if v is not None]
    if not vs:
        return "n/a"
    if len(vs) == 1:
        return f"{vs[0]:.3f} (1 repeat)"
    return f"{statistics.fmean(vs):.3f} ±{(max(vs) - min(vs)) / 2:.3f}"


def main() -> int:
    dirs = [Path(a) for a in sys.argv[1:]]
    if not dirs:
        sys.exit(__doc__)

    loaded = []
    skipped_union: set[str] = set()
    baselines: set[str] = set()
    judges: set[str] = set()
    for d in dirs:
        if not d.is_dir():
            sys.exit(f"not a directory: {d}")
        arm, verdicts, base, judge = _load(d)
        baselines.add(base)
        judges.add(judge)
        skipped_union |= _structurally_skipped(ARMS / arm)
        loaded.append((d.name, arm, verdicts))

    # The cross-directory version of the same refusal: each dir can be internally
    # consistent while the set spans two campaigns.
    if len(baselines) > 1:
        sys.exit(f"inputs mix baselines {sorted(baselines)} — refusing to score arms "
                 "judged against different references")
    if len(judges) > 1:
        sys.exit(f"inputs mix judges {sorted(judges)} — refusing to score")

    expect_items = int(os.environ.get("EXPECT_ITEMS", "0"))
    expect_verdicts = int(os.environ.get("EXPECT_VERDICTS", "0"))
    if expect_items or expect_verdicts:
        short = [f"{jn} ({arm}): {len(vd)} items, "
                 f"{sum(len(v) for v in vd.values())} verdicts"
                 for jn, arm, vd in loaded
                 if expect_items and len(vd) != expect_items]
        total = sum(sum(len(v) for v in vd.values()) for _, _, vd in loaded)
        if short or (expect_verdicts and total != expect_verdicts):
            sys.exit("COMPLETENESS GATE FAILED — refusing to report on a partial "
                     f"campaign.\n  expected {expect_items} items/arm and "
                     f"{expect_verdicts} verdicts total; got {total} verdicts"
                     + ("\n  " + "\n  ".join(short) if short else ""))

    base_name = baselines.pop()
    print(f"# {len(loaded)} arm(s) judged against baselines/{base_name} "
          f"by {judges.pop()}\n")
    print(f"Structurally skipped by at least one arm (excluded from the secondary "
          f"number on BOTH sides): {sorted(skipped_union) or 'none'}\n")

    for label, exclude in (("PRIMARY — all items", set()),
                           ("SECONDARY — supported-only", skipped_union)):
        print(f"\n## {label}\n")
        print(f"{'judgments':38} {'arm':24} {'n':>3} {'win%':>6} "
              f"{'recall':>7} {'prec':>7} {'action':>7}")
        print("-" * 100)
        groups: dict[str, list[dict]] = defaultdict(list)
        for jname, arm, verdicts in loaded:
            s = _score(verdicts, exclude)
            groups[arm.rsplit("_r", 1)[0]].append(s)
            print(f"{jname:38} {arm:24} {s['items']:>3} {s['win_rate']*100:>5.1f}% "
                  f"{str(s['recall']):>7} {str(s['precision']):>7} "
                  f"{str(s['actionability']):>7}")
        print()
        for family, runs in sorted(groups.items()):
            print(f"  {family:30} over {len(runs)} repeat(s): "
                  f"win% {_pm([r['win_rate'] * 100 for r in runs])} | "
                  f"recall {_pm([r['recall'] for r in runs])} | "
                  f"precision {_pm([r['precision'] for r in runs])} | "
                  f"actionability {_pm([r['actionability'] for r in runs])}")
    print("\nNote: OCR emits findings only — it produces no narrative review, so a "
          "zero-finding result is a short artifact by design, not a rendering artefact.")
    print("Note: these results must NOT be used to tune the copilot; the item set "
          "includes the frozen test split, which stays valid only while no proposer "
          "adapts to it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
