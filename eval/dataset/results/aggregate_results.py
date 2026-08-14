#!/usr/bin/env python3
"""Aggregate all model-comparison judgment sets into results/ files."""
import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path("/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset")
J = HERE / "judgments"
RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)

# judgment set -> (label, generator, route, judge-era note)
SETS = {
    "goal_v13_val":            ("v13 val (dev gate)",),
    "goal_v13_test":           ("v13 test",),
    "goal_v13_wave2":          ("DS v4-pro r1, wave-2 holdout",),
    "goal_v13_wave2_sonnet":   ("DS v4-pro r1 re-scored",),
    "goal_ds_wave2_r2_sonnet": ("DS v4-pro r2 fresh gen",),
    "goal_mimo_wave2":         ("MiMo-v2.5, wave-2",),
    "goal_mimo_wave2_sonnet":  ("MiMo-v2.5 re-scored",),
    "goal_composer_wave2_sonnet": ("Composer-2.5 harness",),
    "goal_grok45_wave2_sonnet":   ("Grok-4.5 harness",),
    "goal_cb_composer25_wave2_sonnet": ("Composer-2.5, v13 via cursor backend",),
    "goal_cb_grok45_wave2_sonnet":     ("Grok-4.5, v13 via cursor backend",),
    "goal_cb_grok46_wave2_sonnet":     ("Grok-4.6 cb r2 — TAINTED (skill leak)",),
    "goal_cb_grok46_r3_sonnet":        ("Grok-4.6, v13 via cursor backend (r3, canonical)",),
    "goal_v13moa_cgm_wave2_sonnet":    ("MoA composer+grok4.6+mimo r1, DS spine",),
    "goal_moa_cgm_wave2_sonnet":       ("MoA composer+grok4.6+mimo r2 (peer session)",),
}


def audit_map(arm_dir: Path) -> dict:
    out = {}
    if not arm_dir.is_dir():
        return out
    for f in arm_dir.glob("pr*.cost.json"):
        d = json.loads(f.read_text())
        out[f.name.split(".")[0]] = {
            "audit_ok": d.get("audit_ok", True),
            "violations": d.get("audit_violations") or [],
        }
    return out


def tally(set_dir: Path) -> dict | None:
    files = sorted(set_dir.glob("pr*.r*.json"))
    if not files:
        return None
    wins = defaultdict(int)
    rubric = defaultdict(lambda: defaultdict(list))
    verdicts = []
    arm = base = judge = None
    for f in files:
        d = json.loads(f.read_text())
        blind = d.get("_blinding") or {}
        roles = d.get("_roles") or {}
        arm = roles.get("arm") or arm
        base = roles.get("baseline") or base
        judge = d.get("_judge_resolved_model") or judge
        w = d.get("winner")
        w_arm = blind.get(w, w)  # "X"/"Y" -> arm name; ties/arm-names pass through
        wins[w_arm] += 1
        for side_key, side_arm in blind.items():
            scores = d.get(side_key.lower()) or {}
            for k, v in scores.items():
                if isinstance(v, (int, float)):
                    rubric[side_arm][k].append(v)
        stem, rep = f.name.split(".")[0], f.name.split(".")[1]
        verdicts.append({"item": stem, "rep": rep, "winner": w_arm,
                         "margin": d.get("margin")})
    mean = {a: {k: round(sum(v) / len(v), 3) for k, v in ks.items()}
            for a, ks in rubric.items()}
    items = sorted({v["item"] for v in verdicts})
    # normalized view: each metric as arm/baseline WITHIN the same verdicts,
    # cancelling judge-noise and item-subset variation in the baseline column;
    # win_share counts a tie as half a win
    normalized = {}
    ra, rb = mean.get(arm, {}), mean.get(base, {})
    for k in ra:
        if k in rb and rb[k]:
            normalized[k] = {"ratio": round(ra[k] / rb[k], 2),
                             "delta": round(ra[k] - rb[k], 3)}
    win_share = round((wins.get(arm, 0) + 0.5 * wins.get("tie", 0))
                      / len(files), 3) if files else None
    return {"arm": arm, "baseline": base, "judge": judge,
            "n_items": len(items), "n_verdicts": len(files),
            "wins": dict(wins), "mean_rubric": mean,
            "normalized": normalized, "win_share": win_share,
            "items": items, "verdicts": verdicts}


results = {}
for name in SETS:
    t = tally(J / name)
    if t is None:
        continue
    t["label"] = SETS[name][0]
    # contamination cross-reference for harness arms
    if t["arm"] and t["arm"].startswith("cursor_"):
        audits = audit_map(HERE / "arms" / t["arm"])
        bad = sorted(i for i in t["items"]
                     if not audits.get(i, {}).get("audit_ok", True))
        t["audit_failed_items"] = bad
        t["audit_violations"] = {i: audits[i]["violations"] for i in bad}
        clean = defaultdict(int)
        for v in t["verdicts"]:
            if v["item"] not in bad:
                clean[v["winner"]] += 1
        t["wins_clean_only"] = dict(clean)
        t["n_clean_items"] = t["n_items"] - len(bad)
    results[name] = t

stamp = subprocess.run(["date", "-Is"], capture_output=True,
                       text=True).stdout.strip()
out = {"generated_at": stamp, "campaign": "goal: Strict(DS) vs CC+Opus5",
       "baseline": "claudecode_opus5 (Claude Code + Opus 5, pinned worktree)",
       "sets": results}
(RESULTS / "model_comparison.json").write_text(
    json.dumps(out, indent=2) + "\n")

with (RESULTS / "model_comparison.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["judgment_set", "label", "arm", "judge", "n_items",
                "n_verdicts", "arm_wins", "baseline_wins", "ties",
                "win_share",
                "arm_recall", "base_recall", "recall_ratio",
                "arm_precision", "base_precision", "precision_ratio",
                "arm_actionability", "base_actionability",
                "audit_failed_items"])
    for name, t in results.items():
        a, b = t["arm"], t["baseline"]
        ra, rb = t["mean_rubric"].get(a, {}), t["mean_rubric"].get(b, {})
        nz = t.get("normalized", {})
        w.writerow([name, t["label"], a, t["judge"], t["n_items"],
                    t["n_verdicts"], t["wins"].get(a, 0),
                    t["wins"].get(b, 0), t["wins"].get("tie", 0),
                    t.get("win_share"),
                    ra.get("recall"), rb.get("recall"),
                    nz.get("recall", {}).get("ratio"),
                    ra.get("precision"), rb.get("precision"),
                    nz.get("precision", {}).get("ratio"),
                    ra.get("actionability"), rb.get("actionability"),
                    ";".join(t.get("audit_failed_items", []))])

for name, t in results.items():
    a, b = t["arm"], t["baseline"]
    line = (f"{name:32s} {t['label']:28s} judge={t['judge']:22s} "
            f"{t['wins'].get(a,0)}-{t['wins'].get(b,0)}"
            f" (tie {t['wins'].get('tie',0)})  items={t['n_items']}")
    if "audit_failed_items" in t:
        line += (f"  AUDIT-FAIL={len(t['audit_failed_items'])}"
                 f" clean-only={t['wins_clean_only']}")
    print(line)
print("\nwrote", RESULTS / "model_comparison.json")
print("wrote", RESULTS / "model_comparison.csv")
