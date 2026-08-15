#!/usr/bin/env python3
"""Build wave 3 of the PR-review dataset: a fresh frozen holdout for the post-wave-2
pipeline iteration.

Wave 2 (10 items, merged 2026-07-11..08-12) was one-shot holdout material and is now
SPENT for gating: its judge rationales and GT were opened for tuning forensics after
the cursor-model campaign concluded (see model_comparison.md). Any further claim of
"beats the baseline" needs items no tuning decision has ever seen. That is wave 3.

Selection mirrors build_wave2.py exactly (same eligibility predicate, seeded
stratified draw over size bands, human-only GT, range gate), with three deltas:

* The exclusion set is wave 1 + the wave-2 SELECTED 10 + the 6 extra pool items whose
  GT was already materialized under gt/ during the wave-2 build (pr5472/5636/5647/
  5737/5790/5887): those files sat on disk during tuning sessions, so they are not
  provably unseen. Exclusion is cheap; certainty is not.
* MERGED_SINCE stays 2026-07-11 (the pool window that produced 55 eligible PRs) but
  the pool is re-fetched live, so PRs merged after the wave-2 build enter it.
* New seed. The draw is fixed BEFORE the current pipeline iteration's changes are
  validated, and this script is committed with the provenance, so nobody picks items
  after seeing reviews.

Items land under `pr_review_wave3:` with split `holdout3` (kept distinct from wave 2's
`holdout` so existing judgment sets stay unambiguous). Runners/judge need the split
registered: judge_val.py `_SPLITS` and run_copilot_arm's split filter accept it.

Usage: build_wave3.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import build_wave2 as w2  # reuse the audited machinery verbatim

SEED = "vllm-omni-wave3-2026-08-15"
N_TARGET = 10
PROV = HERE / "goal-eval" / "provenance_wave3.json"
# GT materialized during the wave-2 build for items the draw did not select; present
# on disk throughout the tuning window, therefore excluded from wave 3.
TAINTED_POOL_EXTRAS = {5472, 5636, 5647, 5737, 5790, 5887}


def main() -> int:
    dry = "--dry-run" in sys.argv
    import yaml
    ds = yaml.safe_load((HERE / "vllm_omni_dataset.yaml").read_text(encoding="utf-8"))
    wave1 = {int(i["pr"]) for i in ds["pr_review"]}
    wave2 = {int(i["pr"]) for i in (ds.get("pr_review_wave2") or [])}
    exclude = wave1 | wave2 | TAINTED_POOL_EXTRAS

    print(f"[wave3] building pool: merged >= {w2.MERGED_SINCE}, "
          f">= {w2.MIN_HUMAN_COMMENTS} human inline comments, no self-review, "
          f"excluding {len(exclude)} prior/tainted items")
    pool = w2.eligible_pool(exclude)
    print(f"[wave3] eligible: {len(pool)}")

    # seeded stratified draw, wave-3 seed
    w2.SEED = SEED
    picked, draw_meta = w2.stratified_draw(pool, N_TARGET)
    quota = draw_meta["quota"]
    print(f"[wave3] band quotas: {quota}; range-gate rejections: "
          f"{[r['pr'] for r in draw_meta['rejected']]}")
    for p in picked:
        print(f"    #{p['pr']} {p['merged']} {p['band']:>5} files={p['files']:<3} "
              f"human={p['human_inline']:<3} {p['title'][:46]}")
    if dry:
        print("\n[wave3] --dry-run: nothing written")
        return 0

    w2.GT.mkdir(exist_ok=True)
    ypath = HERE / "vllm_omni_dataset.yaml"
    text = ypath.read_text(encoding="utf-8")
    marker = "\n# ============================================================\n# wave 3"
    if marker in text:
        prev = yaml.safe_load(text).get("pr_review_wave3") or []
        ypath.write_text(text[:text.index(marker)] + "\n", encoding="utf-8")
        stale = {str(i["pr"]) for i in prev}
        print(f"[wave3] replacing previous block ({len(stale)} items)")
    else:
        stale = set()
    heads = json.loads(w2.HEADS.read_text(encoding="utf-8"))
    for k in stale:
        heads.pop(k, None)

    rows, gt_stats = [], []
    for p in picked:
        n = p["pr"]
        g = w2.fetch_gt(n)
        (w2.GT / f"pr{n}.diff").write_text(g["diff"], encoding="utf-8")
        (w2.GT / f"pr{n}.inline.json").write_text(
            json.dumps(g["inline"], indent=2, ensure_ascii=False), encoding="utf-8")
        (w2.GT / f"pr{n}.reviews.json").write_text(
            json.dumps(g["reviews"], indent=2, ensure_ascii=False), encoding="utf-8")
        heads[str(n)] = g["head"]
        gt_stats.append({"pr": n, "inline": len(g["inline"]),
                         "thread": len(g["reviews"]["comments"]),
                         "review_bodies": len(g["reviews"]["reviews"]),
                         "diff_bytes": len(g["diff"]), "head": g["head"]})
        rows.append((p, g))
        print(f"    gt pr{n}: inline={len(g['inline'])} "
              f"thread={len(g['reviews']['comments'])} diff={len(g['diff'])}B "
              f"head={g['head'][:12]}")

    w2.HEADS.write_text(json.dumps(heads, indent=2) + "\n", encoding="utf-8")

    lines = [
        "",
        "# ============================================================",
        "# wave 3 — 10 PRs, ALL frozen holdout (added 2026-08-15)",
        "#",
        "# Wave 2 is SPENT: opened for tuning forensics after the cursor-model campaign.",
        "# Wave 3 is the promotion gate for the post-wave-2 pipeline iteration. Same",
        "# eligibility and draw machinery as wave 2 (see build_wave3.py); exclusions",
        "# additionally cover the 6 never-drawn pool items whose GT was materialized",
        "# on disk during the wave-2 build (5472/5636/5647/5737/5790/5887).",
        "pr_review_wave3:",
    ]
    for p, g in rows:
        mods = w2.modules_of(g["diff"])
        lines += [
            f"  - {{pr: {p['pr']}, split: holdout3, wave: \"2026-08w3\", "
            f"title: {w2.y(p['title'])},",
            f"     author: {p['author']}, merged: {w2.y(p['merged'])}, "
            f"modules: [{', '.join(mods) if mods else 'misc'}],",
            f"     size: {{files: {p['files']}, add: {p['add']}, del: {p['del']}}}, "
            f"review_comments: {len(g['inline'])},",
            f"     class: {w2.class_of(p['title'])}}}",
        ]
    with (HERE / "vllm_omni_dataset.yaml").open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    PROV.write_text(json.dumps({
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "purpose": "wave-3 frozen holdout; gate for the post-wave-2 iteration",
        "eligibility": {"merged_since": w2.MERGED_SINCE,
                        "min_human_inline_comments": w2.MIN_HUMAN_COMMENTS,
                        "excludes_self_reviewed": "vllm-omni-review-bot",
                        "range_gate": "merge-base(head,origin/main)..head must yield "
                                      "exactly the declared changed-file count",
                        "excludes": sorted(exclude)},
        "seed": SEED, "n_target": N_TARGET, "band_quotas": quota,
        "range_gate_rejected": [{"pr": r["pr"], "declared_files": r["files"],
                                 "range_files": r.get("range_files")}
                                for r in draw_meta["rejected"]],
        "eligible_pool_size": len(pool),
        "eligible_pool": pool,
        "selected": [p["pr"] for p, _ in rows],
        "gt": gt_stats,
        "gt_policy": "human-only, same filter as wave 2",
        "caveats": [
            "pool window overlaps wave 2's (re-fetched live), so wave-3 items are "
            "contemporaries of wave-2 items, plus anything merged since",
            "no GOLD latent-gap items",
            "no arm has been run against these items yet",
        ],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n[wave3] wrote {len(rows)} items, {len(rows)*3} gt artifacts, "
          f"{len(rows)} head pins")
    print(f"[wave3] provenance -> {PROV.relative_to(HERE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
