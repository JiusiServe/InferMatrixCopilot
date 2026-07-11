#!/usr/bin/env python3
"""Blind pairwise + rubric judging: copilot_v2 arm vs claudecode_opus48 baseline
on the val split (5 pr_review + 5 issue_answer).

Judge model: claude-sonnet-5 via headless CLI (native auth) — a THIRD model,
distinct from both arms (DeepSeek copilot / Opus baseline), per the dataset
README's judge!=proposer rule. No tools; pure text judgment on a packet of
ground truth + both outputs. Arm order is randomized per call and recorded;
3 replicates per item. Scores in [0,1].

Outputs:
  eval/dataset/judgments/val/<stem>.r<k>.json   (raw verdicts + blinding map)
  eval/dataset/judgments/val/JUDGE_REPORT.md    (aggregate)
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).parent
GT = HERE / "gt"
# ARM_A_DIR/JUDGE_OUT select the copilot arm + output dir (default T0). T1:
#   ARM_A_DIR=arms/copilot_v2_t1 JUDGE_OUT=judgments/val_t1 judge_val.py
ARM_A = HERE / os.environ.get("ARM_A_DIR", "arms/copilot_v2")
ARM_B = HERE / "baselines" / "claudecode_opus48"  # Opus baseline
OUT = HERE / os.environ.get("JUDGE_OUT", "judgments/val")
JUDGE_MODEL = "claude-sonnet-5"
REPLICATES = 3
CAP = 24_000  # chars per candidate / per GT block

PR_ITEMS = [4893, 4810, 4825, 4837, 4816]
ISSUE_ITEMS = [4793, 4827, 4905, 4891, 4842]
GAP_NOTES = {
    4810: ("LATENT GAP CHECK: history proves human review missed that one more "
           "caller of the removed get_cache_scale API existed (the HunyuanImage3 "
           "diffusion loader, later issue #4891). gap_hit = does the candidate "
           "flag other/unswept callers of the removed API or demand a "
           "repo-wide sweep?"),
}

PR_SCHEMA = ('{"x": {"recall": 0.0, "precision": 0.0, "actionability": 0.0, '
             '"gap_hit": false}, "y": {...same...}, '
             '"winner": "X|Y|tie", "margin": "slight|clear|decisive", '
             '"rationale": "2-4 sentences"}')
ISSUE_SCHEMA = ('{"x": {"correctness": 0.0, "grounding": 0.0, "completeness": 0.0}, '
                '"y": {...same...}, "winner": "X|Y|tie", '
                '"margin": "slight|clear|decisive", "rationale": "2-4 sentences"}')


def _cc_judge(prompt: str) -> dict:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("ANTHROPIC", "CLAUDE_CODE"))}
    out = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--max-turns", "1",
         "--model", JUDGE_MODEL], capture_output=True, text=True, timeout=600,
        env=env, cwd=str(OUT))
    data = json.loads(out.stdout)
    text = str(data.get("result") or "")
    start, end = text.find("{"), text.rfind("}")
    verdict = json.loads(text[start:end + 1])
    verdict["_cost_usd"] = data.get("total_cost_usd")
    return verdict


def _pr_packet(n: int) -> str:
    gt_reviews = (GT / f"pr{n}.reviews.json").read_text()[:6_000]
    gt_inline = (GT / f"pr{n}.inline.json").read_text()[:6_000]
    diff = (GT / f"pr{n}.diff").read_text()[:CAP]
    gap = GAP_NOTES.get(n, "")
    return (f"## PR #{n} diff (truncated)\n```diff\n{diff}\n```\n\n"
            f"## Ground truth — human review comments\n{gt_reviews}\n\n"
            f"## Ground truth — inline review comments\n{gt_inline}\n"
            + (f"\n## {gap}\n" if gap else ""))


def _issue_packet(n: int) -> str:
    gt = json.loads((GT / f"issue{n}.json").read_text())
    return (f"## Issue #{n}: {gt['title']}\n\n### Body\n{gt['body']}\n\n"
            f"### Ground truth — actual thread resolution (maintainer comments)\n"
            f"{json.dumps(gt['comments'], ensure_ascii=False)[:8_000]}\n")


def judge_one(kind: str, n: int, rep: int) -> str:
    stem = ("pr" if kind == "pr" else "issue") + str(n)
    outf = OUT / f"{stem}.r{rep}.json"
    if outf.exists():
        return f"skip {stem}.r{rep}"
    a_text = (ARM_A / f"{stem}.md").read_text()[:CAP]
    b_text = (ARM_B / f"{stem}.md").read_text()[:CAP]
    rng = random.Random(f"{stem}.{rep}")
    x_is_a = rng.random() < 0.5
    x, y = (a_text, b_text) if x_is_a else (b_text, a_text)
    if kind == "pr":
        packet, schema = _pr_packet(n), PR_SCHEMA
        task = ("Judge two code reviews of the same PR. recall = fraction of "
                "ground-truth reviewer concerns the candidate covers; precision "
                "= fraction of the candidate's findings that are valid and "
                "grounded in the diff (not fabricated/irrelevant); "
                "actionability = are comments concrete (file/line, what to "
                "change)? gap_hit only if a LATENT GAP CHECK section exists, "
                "else set it false for both.")
    else:
        packet, schema = _issue_packet(n), ISSUE_SCHEMA
        task = ("Judge two maintainer-style answers to the same GitHub issue "
                "against the actual thread resolution. correctness = does the "
                "diagnosis/fix match what the thread established (a well-argued "
                "abstention or escalation on a genuinely uncertain issue scores "
                "0.5, a confident wrong answer scores low); grounding = cites "
                "real code/files/evidence; completeness = addresses the "
                "reporter's actual situation end-to-end.")
    prompt = (
        f"You are a blind evaluation judge. {task}\n\n{packet}\n"
        f"\n## Candidate X\n{x}\n\n## Candidate Y\n{y}\n\n"
        f"Score honestly; do not reward verbosity — reward being right, "
        f"grounded, and useful. Output ONLY minified JSON exactly matching: "
        f"{schema}")
    v = _cc_judge(prompt)
    v["_blinding"] = {"X": "copilot_v2" if x_is_a else "opus_baseline",
                      "Y": "opus_baseline" if x_is_a else "copilot_v2"}
    outf.write_text(json.dumps(v, indent=2, ensure_ascii=False))
    w = v.get("winner", "?")
    real = v["_blinding"].get(w, "tie")
    return f"done {stem}.r{rep} winner={real} ({v.get('margin','')})"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(k, n, r) for k, ns in (("pr", PR_ITEMS), ("issue", ISSUE_ITEMS))
            for n in ns for r in range(1, REPLICATES + 1)]
    print(f"[judge] {len(jobs)} judgments -> {OUT}", flush=True)
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(judge_one, *j): j for j in jobs}
        for f in as_completed(futs):
            try:
                print(f"[judge] {f.result()}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[judge] FAIL {futs[f]}: {e}", flush=True)
    aggregate()
    print("[judge] complete", flush=True)


def aggregate() -> None:
    import statistics as st
    per_arm: dict[str, dict[str, list[float]]] = {}
    wins: dict[str, float] = {"copilot_v2": 0, "opus_baseline": 0, "tie": 0}
    rows = []
    for f in sorted(OUT.glob("*.r*.json")):
        v = json.loads(f.read_text())
        bl = v["_blinding"]
        real_winner = bl.get(v.get("winner"), "tie")
        wins[real_winner] = wins.get(real_winner, 0) + 1
        for side in ("x", "y"):
            arm = bl["X" if side == "x" else "Y"]
            for dim, val in (v.get(side) or {}).items():
                if isinstance(val, bool):
                    val = 1.0 if val else 0.0
                if isinstance(val, (int, float)):
                    per_arm.setdefault(arm, {}).setdefault(dim, []).append(float(val))
        rows.append((f.stem, real_winner, v.get("margin", ""),
                     (v.get("rationale") or "")[:200]))
    lines = ["# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)",
             "", f"Judge: {JUDGE_MODEL} (blind, randomized order, "
             f"{REPLICATES} replicates x 10 items = {sum(wins.values()):.0f} verdicts)", "",
             f"## Wins\n- copilot_v2: {wins['copilot_v2']}\n"
             f"- opus_baseline: {wins['opus_baseline']}\n- tie: {wins['tie']}", "",
             "## Mean rubric scores", "",
             "| arm | " + " | ".join(sorted({d for a in per_arm.values() for d in a})) + " |",
             "|---|" + "---|" * len({d for a in per_arm.values() for d in a})]
    dims = sorted({d for a in per_arm.values() for d in a})
    for arm, ds in sorted(per_arm.items()):
        lines.append("| " + arm + " | " + " | ".join(
            f"{st.mean(ds[d]):.2f}" if d in ds else "-" for d in dims) + " |")
    lines += ["", "## Per-verdict detail", "",
              "| item.rep | winner | margin | rationale (head) |", "|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |" for r in rows]
    (OUT / "JUDGE_REPORT.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "aggregate":
        aggregate()
    else:
        main()
