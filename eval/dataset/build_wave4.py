#!/usr/bin/env python3
"""Build wave 4 of the PR-review dataset: the clean promotion gate after wave 3
was spent.

Wave 3 hosted two disclosed gate attempts of the v14 pipeline (machinery
failures invalidated attempt 1; attempt 2 measured a real recall gap), after
which its GT and judge rationales were opened for tuning forensics — so it can
no longer serve as an unbiased gate. Wave 4 mirrors build_wave3.py exactly,
excluding waves 1-3 and the tainted never-drawn extras.

Usage: build_wave4.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import build_wave2 as w2  # audited machinery
from build_wave3 import TAINTED_POOL_EXTRAS

SEED = "vllm-omni-wave4-2026-08-15"
N_TARGET = 10
PROV = HERE / "goal-eval" / "provenance_wave4.json"


def main() -> int:
    dry = "--dry-run" in sys.argv
    import yaml
    ds = yaml.safe_load((HERE / "vllm_omni_dataset.yaml").read_text(encoding="utf-8"))
    exclude = ({int(i["pr"]) for i in ds["pr_review"]}
               | {int(i["pr"]) for i in (ds.get("pr_review_wave2") or [])}
               | {int(i["pr"]) for i in (ds.get("pr_review_wave3") or [])}
               | TAINTED_POOL_EXTRAS)

    print(f"[wave4] pool: merged >= {w2.MERGED_SINCE}, "
          f">= {w2.MIN_HUMAN_COMMENTS} human inline, excluding {len(exclude)}")
    pool = w2.eligible_pool(exclude)
    print(f"[wave4] eligible: {len(pool)}")
    w2.SEED = SEED
    picked, draw_meta = w2.stratified_draw(pool, N_TARGET)
    print(f"[wave4] band quotas: {draw_meta['quota']}; rejections: "
          f"{[r['pr'] for r in draw_meta['rejected']]}")
    for p in picked:
        print(f"    #{p['pr']} {p['merged']} {p['band']:>5} files={p['files']:<3} "
              f"human={p['human_inline']:<3} {p['title'][:46]}")
    if dry:
        print("\n[wave4] --dry-run: nothing written")
        return 0

    ypath = HERE / "vllm_omni_dataset.yaml"
    text = ypath.read_text(encoding="utf-8")
    marker = "\n# ============================================================\n# wave 4"
    if marker in text:
        prev = yaml.safe_load(text).get("pr_review_wave4") or []
        ypath.write_text(text[:text.index(marker)] + "\n", encoding="utf-8")
        stale = {str(i["pr"]) for i in prev}
        print(f"[wave4] replacing previous block ({len(stale)} items)")
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
        print(f"    gt pr{n}: inline={len(g['inline'])} head={g['head'][:12]}")

    w2.HEADS.write_text(json.dumps(heads, indent=2) + "\n", encoding="utf-8")

    lines = [
        "",
        "# ============================================================",
        "# wave 4 — 10 PRs, ALL frozen holdout (added 2026-08-15)",
        "#",
        "# Wave 3 is SPENT (two disclosed v14 gate attempts, then opened for",
        "# forensics). Wave 4 is the clean promotion gate; same machinery",
        "# (build_wave4.py), exclusions cover waves 1-3 + tainted extras.",
        "pr_review_wave4:",
    ]
    for p, g in rows:
        mods = w2.modules_of(g["diff"])
        lines += [
            f"  - {{pr: {p['pr']}, split: holdout4, wave: \"2026-08w4\", "
            f"title: {w2.y(p['title'])},",
            f"     author: {p['author']}, merged: {w2.y(p['merged'])}, "
            f"modules: [{', '.join(mods) if mods else 'misc'}],",
            f"     size: {{files: {p['files']}, add: {p['add']}, del: {p['del']}}}, "
            f"review_comments: {len(g['inline'])},",
            f"     class: {w2.class_of(p['title'])}}}",
        ]
    with ypath.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    PROV.write_text(json.dumps({
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "purpose": "wave-4 frozen holdout; clean gate after wave-3 was spent",
        "eligibility": {"merged_since": w2.MERGED_SINCE,
                        "min_human_inline_comments": w2.MIN_HUMAN_COMMENTS,
                        "excludes": sorted(exclude)},
        "seed": SEED, "n_target": N_TARGET,
        "band_quotas": draw_meta["quota"],
        "range_gate_rejected": [{"pr": r["pr"], "declared_files": r["files"],
                                 "range_files": r.get("range_files")}
                                for r in draw_meta["rejected"]],
        "eligible_pool_size": len(pool),
        "eligible_pool": pool,
        "selected": [p["pr"] for p, _ in rows],
        "gt": gt_stats,
        "gt_policy": "human-only, same filter as waves 2-3",
        "caveats": ["no arm has been run against these items yet"],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n[wave4] wrote {len(rows)} items; provenance -> "
          f"{PROV.relative_to(HERE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
