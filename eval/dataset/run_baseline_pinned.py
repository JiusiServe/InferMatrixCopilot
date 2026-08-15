#!/usr/bin/env python3
"""The Opus 5 reference arm: headless Claude Code, PR-time tree, no MCP, no skills.

This replaces `baselines/claudecode_opus48` as the common reference every arm is judged
against. It is a *new* reference, not a rerun: the old one is not reproducible (its
workdir and `vllm-omni-review` project skill are both gone), and it was advantaged in a
way the arms were not — it reviewed post-merge `main`, where the fix is in history, and
its allowlist carried `Bash(gh pr view:*)`, which permits `--comments` and
`--json reviews`. The dataset's ground truth *is* that discussion. So baseline-relative
numbers from this campaign cannot be compared to the previously reported ones at all;
they are internally consistent instead.

Three things bring it down to arm-equivalent information:

* the PR-time worktree, head-pinned and range-validated (the same three gates
  `run_ocr_arm.py` uses, imported rather than re-implemented);
* `gh pr view` / `gh pr checks` dropped, replaced by the frozen sanitized snapshot that
  `run_direct_arm.py` also receives byte-for-byte;
* zero skills and an empty MCP config, asserted against the run's own init event —
  `imreview` is installed at user level, and a baseline that could invoke our skill
  would put our contribution on both sides of the contrast it exists to provide.

Usage: run_baseline_pinned.py [splits] [only_stem]
Env: BASELINE_OUT (default claudecode_opus5), ARM_JOBS (default 3), ARM_MODEL
Outputs: eval/dataset/baselines/<BASELINE_OUT>/pr<N>.{md,cost.json,events.jsonl}
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

import cc_arm_common as cc
import trace_pack
from run_ocr_arm import _prepare_worktree, _write_atomic, EXPECTED_HEADS, JUDGE_CAP

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
OUT = HERE / "baselines" / os.environ.get("BASELINE_OUT", "claudecode_opus5")

ARM = "baseline_opus5"
TOOLS = cc.BASE_TOOLS + cc.VALIDATION_TOOLS


def prompt(pr: int, snap: str, base: str, head: str) -> str:
    return (
        f"Review pull request #{pr} of {cc.REPO} as an expert reviewer.\n\n"
        f"Your working directory IS a read-only checkout of the repository at this "
        f"PR's exact head commit ({head[:12]}) — the merge-base with main is "
        f"{base[:12]}, so `git diff {base} HEAD` is precisely this PR's change. The "
        f"code around it is the code as it stood when the PR was opened.\n\n"
        f"Frozen PR context (this is all of it — there is no PR discussion available, "
        f"deliberately):\n\n{snap}\n\n"
        f"Investigate the code before concluding: read the changed files and the code "
        f"that calls into them. You may run a quick import/version preflight, targeted "
        f"tests, or low-cost static checks if they would settle a real question.\n\n"
        f"Budget: you have {cc.MAX_TURNS} turns. Spend at most two thirds of them "
        f"investigating and then WRITE THE REVIEW — an unwritten review scores as "
        f"silence no matter how good the investigation behind it was.\n\n"
        f"IMPORTANT: do not post anything to GitHub. Output the complete review as "
        f"your final message — an overall verdict, then specific comments with "
        f"file:line references and what to change."
    )


def main() -> int:
    splits = set((sys.argv[1] if len(sys.argv) > 1 else "train,val,test").split(","))
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    ds = yaml.safe_load(DATASET.read_text(encoding="utf-8"))
    heads = json.loads(EXPECTED_HEADS.read_text(encoding="utf-8"))
    items = [i for i in ds["pr_review"] + (ds.get("pr_review_wave2") or [])
             + (ds.get("pr_review_wave3") or [])
             + (ds.get("pr_review_wave4") or [])
             if i.get("split") in splits]
    if only:
        items = [i for i in items if f"pr{i['pr']}" == only]
    OUT.mkdir(parents=True, exist_ok=True)

    home = cc.provision_home()
    mcp_cfg = home / "empty-mcp.json"
    failures: list[str] = []
    oversize: list[tuple[str, int]] = []
    resolved_models: set[str] = set()
    done = 0
    lock = threading.Lock()

    # PHASE 1 — serial: every gate and every git write before any review starts,
    # because `git worktree add` takes a repository-level lock.
    pending = []
    for item in items:
        pr = int(item["pr"])
        stem = f"pr{pr}"
        expected_head = heads.get(str(pr))
        if not expected_head:
            failures.append(f"{stem}: no pinned head in expected_pr_heads.json")
            continue
        if cc.already_done(OUT, stem, expected_head):
            print(f"  {stem}: already done, skipping")
            done += 1
            continue
        try:
            wt, base = _prepare_worktree(str(pr), expected_head,
                                         int(item["size"]["files"]))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{stem}: {exc}")
            print(f"  {stem}: GATE FAILED — {exc}")
            continue
        pending.append((item, wt, base, expected_head))

    def _review(job) -> None:
        nonlocal done
        item, wt, base, expected_head = job
        pr = int(item["pr"])
        stem = f"pr{pr}"
        snap, snap_sha = cc.snapshot(pr)
        t0 = time.time()
        run = cc.run_cc(prompt(pr, snap, base, expected_head), TOOLS, home, wt,
                        mcp_cfg, disable_skills=True)
        events = run["events"]
        wall = round(time.time() - t0, 1)
        try:
            model = cc.assert_init(events, expect_skills=[], expect_mcp=[], arm=ARM)
        except Exception as exc:  # noqa: BLE001
            with lock:
                failures.append(f"{stem}: {exc}")
                print(f"  {stem}: CONFIG ASSERTION FAILED — {exc}")
            return
        body = cc.final_text(events)
        cost = cc.cost_from(events)
        violations, blocked = cc.audit_events(events, wt)
        cost = cc.stamp(cost, item=item, head=expected_head, base=base, model=model,
                        snap_sha=snap_sha, worktree=wt, events=events)
        cost.update({"arm": ARM, "wall_s": wall, "audit_ok": not violations,
                     "audit_violations": violations,
                     "audit_blocked_attempts": blocked,
                     "artifact_chars": len(body)})
        cc.write_run(OUT, stem, body or "(no output)", cost, events)
        with lock:
            resolved_models.add(model)
            if len(body) > JUDGE_CAP:
                oversize.append((stem, len(body)))
            if violations:
                failures.append(f"{stem}: audit violations {violations[:3]}")
                print(f"  {stem}: AUDIT FAILED — {violations[:2]}")
                return
            # An empty artifact is the failure mode that matters most here: it is
            # indistinguishable from "the reviewer had nothing to say" once it reaches
            # the judge, and it scores as silence.
            if not body:
                failures.append(f"{stem}: empty review "
                                f"({cost.get('terminal_reason')}, {cost['calls']} turns)")
                print(f"  {stem}: EMPTY REVIEW — {cost.get('terminal_reason')}")
                return
            if cost.get("is_error"):
                failures.append(f"{stem}: run errored ({cost.get('terminal_reason')})")
                print(f"  {stem}: RUN ERROR — {cost.get('terminal_reason')}")
                return
            done += 1
            print(f"  {stem}: wall={wall}s turns={cost['calls']} "
                  f"usd={cost.get('cost_usd')} chars={len(body)} "
                  f"bash={len(cost['validation_commands'])} "
                  f"validated={cost['ran_validation']}")

    jobs = max(1, int(os.environ.get("ARM_JOBS", "3")))
    try:
        if pending:
            print(f"  reviewing {len(pending)} item(s), {jobs} at a time")
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_review, j) for j in pending]
            for f in as_completed(futs):
                if f.exception():
                    with lock:
                        failures.append(f"worker crashed: {f.exception()}")
        _write_atomic(OUT / "manifest.json", json.dumps({
            "arm": OUT.name,
            "role": "common reference for the gpt-5.6 campaign; supersedes "
                    "claudecode_opus48 and is NOT comparable to it",
            "model_requested": cc.MODEL,
            "resolved_models": sorted(resolved_models),
            "harness": "claude -p --output-format stream-json --verbose",
            "isolation": {"setting_sources": "", "skills": "disabled "
                          "(--disable-slash-commands)", "mcp": "empty config "
                          "(--strict-mcp-config)", "home": "isolated, credentials only"},
            "allowed_tools": TOOLS,
            "pr_context": "frozen snapshot (no_discussion); gh pr view and gh pr "
                          "checks removed from the allowlist",
            "dataset": DATASET.name, "splits": sorted(splits), "n_items": done,
            "concurrency": jobs,
        }, indent=2) + "\n")
    finally:
        shutil.rmtree(home, ignore_errors=True)

    print(f"\n{done}/{len(items)} items written to {OUT}")
    # Trace gate: an arm that cannot be explained later is not a finished arm. Checked
    # here rather than trusted, because the wave-1 Strict loss was silent — nothing
    # ever asserted the traces existed until someone needed them, months too late.
    trace_problems, checked = trace_pack.verify_arm(OUT)
    print(f"trace gate: {checked} packed trace(s) verified")
    failures += [f"trace: {p}" for p in trace_problems]
    if oversize:
        print("OVER JUDGE CAP (would be silently truncated before scoring):")
        for stem, n in oversize:
            print(f"  {stem}: {n} chars > {JUDGE_CAP}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
