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
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).parent
GT = HERE / "gt"
# ARM_A_DIR/JUDGE_OUT select the copilot arm + output dir (default T0). T1:
#   ARM_A_DIR=arms/copilot_v2_t1 JUDGE_OUT=judgments/val_t1 judge_val.py
ARM_A = HERE / os.environ.get("ARM_A_DIR", "arms/copilot_v2")
# ARM_B_DIR selects the reference. Default is the historical Opus 4.8 baseline so
# existing judgments stay reproducible; the gpt-5.6 campaign points it at
# baselines/claudecode_opus5, which is a NEW reference and not comparable to it.
ARM_B = HERE / os.environ.get("ARM_B_DIR", "baselines/claudecode_opus48")
OUT = HERE / os.environ.get("JUDGE_OUT", "judgments/val")
# Backend/model/replicates default to what every existing verdict on disk was produced
# with, so re-running this script over old judgment dirs reproduces them rather than
# silently re-scoring them under a different judge.
JUDGE_BACKEND = os.environ.get("JUDGE_BACKEND", "claude")   # claude | cursor
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-sonnet-5")
REPLICATES = int(os.environ.get("REPLICATES", "3"))
CAP = 24_000  # chars per candidate / per GT block

# Provenance labels. The blinding map used to carry the literal `copilot_v2` whatever
# arm actually ran; with three arms and two possible baselines in play that is no
# longer a harmless generic label, it is a way to average two campaigns together
# without noticing. Both sides are now named for real, and `_roles` records which
# label held which slot so scoring never has to guess from the name.
ARM_A_LABEL = ARM_A.name
ARM_B_LABEL = ARM_B.name

# SPLIT=val (default) or test — selects items; test items stay untouched
# until the frozen final evaluation.
_SPLITS = {
    "val": {"prs": [4893, 4810, 4825, 4837, 4816],
            "issues": [4793, 4827, 4905, 4891, 4842]},
    "test": {"prs": [4762, 4834, 4849, 4954, 4777],
             "issues": [4957, 4962, 4815, 4826, 4802]},
    # PR-only sweep over every split (the 20-case pr_review campaign). Issues
    # are empty on purpose: this split scores review quality alone, and the
    # per-split breakdown is reconstructed at scoring time from the stem list.
    "all_pr": {"prs": [5009, 4923, 4804, 4870, 4817, 4977, 4926, 4859, 4970,
                       4950,                                    # train
                       4893, 4810, 4825, 4837, 4816,            # val
                       4762, 4834, 4849, 4954, 4777],           # test
               "issues": []},
    # Wave 2 (build_wave2.py): 10 recent PRs, pure frozen holdout — human-only
    # GT, no GOLD gap items (recent PRs lack the history to prove one).
    "holdout": {"prs": [5509, 5550, 5610, 5703, 5715, 5840, 5863, 5884,
                        5957, 5976],
                "issues": []},
}
_SPLIT = os.environ.get("SPLIT", "val")
PR_ITEMS = _SPLITS[_SPLIT]["prs"]
ISSUE_ITEMS = _SPLITS[_SPLIT]["issues"]
# ONLY_ITEMS=4762,4834 restricts the run to those numbers — for smoke-testing a judge
# backend on two items before committing a whole campaign to it.
if os.environ.get("ONLY_ITEMS"):
    _only = {int(x) for x in os.environ["ONLY_ITEMS"].split(",") if x.strip()}
    PR_ITEMS = [n for n in PR_ITEMS if n in _only]
    ISSUE_ITEMS = [n for n in ISSUE_ITEMS if n in _only]
GAP_NOTES = {
    4870: ("LATENT GAP CHECK: history proves human review missed a dual-batch-"
           "axis case in this PR's payload splitting, fixed later by follow-up "
           "PR #4910. gap_hit = does the candidate question the splitting "
           "logic's handling of more than one batch axis (or demand a test "
           "covering the multi-axis case)?"),
    4810: ("LATENT GAP CHECK: history proves human review missed that one more "
           "caller of the removed get_cache_scale API existed (the HunyuanImage3 "
           "diffusion loader, later issue #4891). gap_hit = does the candidate "
           "flag other/unswept callers of the removed API or demand a "
           "repo-wide sweep?"),
    4834: ("LATENT GAP CHECK: history proves this PR's own strict "
           "NotImplementedError safeguard broke merge CI after landing "
           "(issue #4905, relaxed by #4912) — human review missed the "
           "over-strictness. gap_hit = does the candidate question whether "
           "existing tests/CI exercise the newly guarded path, or flag the "
           "guard as potentially too strict for existing callers?"),
}

PR_SCHEMA = ('{"x": {"recall": 0.0, "precision": 0.0, "actionability": 0.0, '
             '"gap_hit": false}, "y": {...same...}, '
             '"winner": "X|Y|tie", "margin": "slight|clear|decisive", '
             '"rationale": "2-4 sentences"}')
ISSUE_SCHEMA = ('{"x": {"correctness": 0.0, "grounding": 0.0, "completeness": 0.0}, '
                '"y": {...same...}, "winner": "X|Y|tie", '
                '"margin": "slight|clear|decisive", "rationale": "2-4 sentences"}')


def _extract(text: str) -> dict:
    """The verdict JSON out of a model's prose, by brace matching."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"no JSON object in judge output: {text[:200]!r}")
    return json.loads(text[start:end + 1])


def _cc_judge(prompt: str) -> dict:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("ANTHROPIC", "CLAUDE_CODE"))}
    # tool-less judging: without the empty allowlist the model occasionally
    # attempts a tool call and --max-turns 1 kills the run (error_max_turns,
    # no result field); --max-turns 3 is headroom for a same-turn retry.
    out = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--max-turns", "3",
         "--allowedTools", "", "--model", JUDGE_MODEL],
        capture_output=True, text=True, timeout=600, env=env, cwd=str(OUT))
    data = json.loads(out.stdout)
    verdict = _extract(str(data.get("result") or ""))
    verdict["_cost_usd"] = data.get("total_cost_usd")
    verdict["_judge_resolved_model"] = JUDGE_MODEL
    return verdict


def _cursor_judge(prompt: str) -> dict:
    """gpt-5.6 via cursor-agent, made blind by construction rather than by instruction.

    `cursor-agent` has no `--allowedTools` equivalent, and `--mode ask` buys read-only,
    not tool-less — a read-only judge can still open `gt/` and stop being blind. Both
    candidate reviews and the ground truth are already inlined in the prompt, so the
    judge has no legitimate use for a filesystem at all. Hence:

    * a **fresh empty directory** as both workspace and cwd, so there is nothing to
      read even if it tries (this is also why `--trust` is safe here — the thing being
      trusted is an empty temp dir);
    * `--mode ask` (read-only), and `--force`/`--yolo`/`--approve-mcps` never passed;
    * **any tool call in the stream fails the verdict.** That assertion is what
      actually carries the guarantee; the flags only make violations unlikely.

    `--sandbox enabled` was intended as a fourth layer and is NOT used: it needs kernel
    v6.2+ and this host runs 5.10, where passing it makes cursor-agent exit without
    producing a verdict at all. Stating that plainly rather than leaving a flag in the
    command line that silently does nothing — the empty workspace and the zero-tool
    assertion are what hold here.
    """
    ws = Path(tempfile.mkdtemp(prefix="judge-ws-"))
    ws.chmod(0o700)
    try:
        out = subprocess.run(
            ["cursor-agent", "--print", "--output-format", "stream-json",
             "--model", JUDGE_MODEL, "--mode", "ask",
             "--trust", "--workspace", str(ws), prompt],
            capture_output=True, text=True, timeout=900, cwd=str(ws))
        events = []
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        used = _judge_tool_calls(events)
        if used:
            raise RuntimeError(f"judge attempted tool calls {used} — verdict discarded "
                               "(a judge with filesystem access is not blind)")
        res = next((e for e in reversed(events) if e.get("type") == "result"), {})
        if not events:
            raise RuntimeError("cursor-agent produced no events: "
                               f"rc={out.returncode} {(out.stderr or out.stdout)[:300]}")
        if res.get("is_error"):
            raise RuntimeError(f"cursor judge errored: {str(res.get('result'))[:200]}")
        verdict = _extract(str(res.get("result") or ""))
        u = res.get("usage") or {}
        verdict["_usage"] = {"input": u.get("inputTokens"), "output": u.get("outputTokens")}
        init = next((e for e in events if e.get("subtype") == "init"), {})
        verdict["_judge_resolved_model"] = init.get("model") or JUDGE_MODEL
        return verdict
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def _judge_tool_calls(events: list[dict]) -> list[str]:
    """Any sign the judge reached outside the prompt. Deliberately over-broad: an
    unrecognised event type that mentions a tool should fail loudly, not pass."""
    used = []
    for e in events:
        if "tool" in str(e.get("type", "")).lower():
            used.append(str(e.get("type")))
            continue
        msg = e.get("message") or {}
        for b in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if isinstance(b, dict) and b.get("type") not in (None, "text"):
                used.append(str(b.get("type")))
    return sorted(set(used))


_JUDGES = {"claude": _cc_judge, "cursor": _cursor_judge}


def judge_call(prompt: str) -> dict:
    try:
        fn = _JUDGES[JUDGE_BACKEND]
    except KeyError:
        raise SystemExit(f"unknown JUDGE_BACKEND={JUDGE_BACKEND!r}; "
                         f"expected one of {sorted(_JUDGES)}")
    return fn(prompt)


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
    v = judge_call(prompt)
    v["_blinding"] = {"X": ARM_A_LABEL if x_is_a else ARM_B_LABEL,
                      "Y": ARM_B_LABEL if x_is_a else ARM_A_LABEL}
    # Which label held which slot. Scoring used to infer the baseline side by string-
    # matching the literal "opus_baseline"; with a second baseline in play that would
    # quietly mis-assign every verdict in this campaign, so the roles are recorded
    # explicitly and readers key on these rather than on the names.
    v["_roles"] = {"arm": ARM_A_LABEL, "baseline": ARM_B_LABEL}
    import hashlib as _hl
    v["_arm_meta"] = {"arm_a_dir": str(ARM_A),
                      "arm_a_sha256": _hl.sha256(a_text.encode()).hexdigest(),
                      "arm_b_dir": str(ARM_B),
                      "arm_b_sha256": _hl.sha256(b_text.encode()).hexdigest(),
                      "judge_backend": JUDGE_BACKEND,
                      "judge_model": JUDGE_MODEL,
                      "judge_resolved_model": v.get("_judge_resolved_model"),
                      "judge_rep": rep}
    outf.write_text(json.dumps(v, indent=2, ensure_ascii=False))
    w = v.get("winner", "?")
    real = v["_blinding"].get(w, "tie")
    return f"done {stem}.r{rep} winner={real} ({v.get('margin','')})"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(k, n, r) for k, ns in (("pr", PR_ITEMS), ("issue", ISSUE_ITEMS))
            for n in ns for r in range(1, REPLICATES + 1)]
    print(f"[judge] {len(jobs)} judgments -> {OUT} "
          f"(backend={JUDGE_BACKEND} model={JUDGE_MODEL}, "
          f"arm={ARM_A_LABEL} vs baseline={ARM_B_LABEL})", flush=True)
    failures = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(judge_one, *j): j for j in jobs}
        for f in as_completed(futs):
            try:
                print(f"[judge] {f.result()}", flush=True)
            except Exception as e:  # noqa: BLE001 — one bad call must not lose the rest
                failures.append(f"{futs[f]}: {e}")
                print(f"[judge] FAIL {futs[f]}: {e}", flush=True)
    aggregate()
    # A silently-short campaign is how the previous run nearly reported on 179 verdicts
    # instead of 180. Re-running is cheap and resumable; a wrong denominator is not.
    if failures:
        print(f"[judge] {len(failures)} FAILED judgment(s) — the campaign is "
              f"INCOMPLETE; re-run to fill them in:", flush=True)
        for f in failures:
            print(f"  {f}", flush=True)
        return 1
    print("[judge] complete", flush=True)
    return 0


def aggregate() -> None:
    """Report what actually ran. Every label, count and title below is derived from
    the verdicts on disk — the previous version hardcoded the arm name, the baseline
    name, the judge and a "10 items" count into the report text, which meant a report
    could describe a campaign that never happened."""
    import statistics as st
    per_arm: dict[str, dict[str, list[float]]] = {}
    wins: dict[str, float] = {"tie": 0}
    rows = []
    seen_roles: set[tuple[str, str]] = set()
    seen_judges: set[str] = set()
    for f in sorted(OUT.glob("*.r*.json")):
        v = json.loads(f.read_text())
        bl = v["_blinding"]
        roles = v.get("_roles") or {}
        # legacy verdicts predate _roles: their blinding literally said copilot_v2 /
        # opus_baseline, which is exactly the role pair they had
        seen_roles.add((roles.get("arm", "copilot_v2"),
                        roles.get("baseline", "opus_baseline")))
        seen_judges.add(str((v.get("_arm_meta") or {}).get("judge_model")
                            or "claude-sonnet-5"))
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
    if len(seen_roles) > 1:
        raise SystemExit(f"{OUT.name}: verdicts mix arm/baseline pairs "
                         f"{sorted(seen_roles)} — refusing to aggregate two campaigns "
                         "into one report")
    if len(seen_judges) > 1:
        raise SystemExit(f"{OUT.name}: verdicts mix judges {sorted(seen_judges)} — "
                         "refusing to aggregate")
    arm_label, base_label = (seen_roles.pop() if seen_roles
                             else (ARM_A_LABEL, ARM_B_LABEL))
    judge = seen_judges.pop() if seen_judges else JUDGE_MODEL
    n_items = len({r[0].split(".r")[0] for r in rows})
    n_reps = max((int(r[0].rsplit(".r", 1)[1]) for r in rows
                  if ".r" in r[0]), default=0)
    lines = [f"# Judgment: {arm_label} vs {base_label}",
             "", f"Judge: {judge} (blind, randomized order, "
             f"{n_reps} replicate(s) x {n_items} item(s) = "
             f"{sum(wins.values()):.0f} verdicts)", "",
             "## Wins", ""]
    lines += [f"- {k}: {wins.get(k, 0):.0f}"
              for k in (arm_label, base_label, "tie")]
    lines += ["", "## Mean rubric scores", "",
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
        raise SystemExit(main())
