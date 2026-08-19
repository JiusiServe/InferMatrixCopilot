#!/usr/bin/env python3
"""Pipelined campaign: generation and judging overlap per item.

The serial shape (generate every review, then judge every review) costs
wall-clock equal to the SUM of the two phases. Generation and judging use
disjoint capacity (the arm burns the copilot's LLM endpoint; the judge burns
the judge backend), so the phases can overlap: the moment one item's review
lands on disk, its verdicts can start while sibling items are still
generating. Wall-clock collapses to ~max(generation) + one item's judging.

Usage:
  run_campaign_pipelined.py <splits> <arm_out>

  splits    comma list over BOTH dataset blocks (train,val,test,holdout)
  arm_out   arm directory name under arms/ (also the generation ARM_OUT)

Env (forwarded):
  generation — KINDS (forced pr_review here), MOA_WHEN, ARM_JOBS, OMNI_CLI
  judging    — ARM_B_DIR (default baselines/claudecode_opus5), JUDGE_OUT
               (default judgments/<arm_out>_pipelined), REPLICATES,
               JUDGE_BACKEND, JUDGE_MODEL
  JUDGE_ITEM_JOBS  concurrent per-item judge processes (default 3)
  GEN_CMD          override the generation command (testing)
  JUDGE_CMD        override the per-item judge command (testing; receives
                   the PR number appended as its last argument)

Judging per item is one `judge_val.py` invocation with ONLY_ITEMS=<pr>
(resumable, so a crashed pipeline rerun skips finished verdicts). A judge
failure is retried up to 3 times, then reported — never silently averaged
over. The pipeline exits non-zero if any item failed to generate or judge.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import yaml

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"


def expected_prs(splits: set[str]) -> list[int]:
    ds = yaml.safe_load(DATASET.read_text(encoding="utf-8"))
    items = (ds["pr_review"] + (ds.get("pr_review_wave2") or [])
             + (ds.get("pr_review_wave3") or [])
             + (ds.get("pr_review_wave4") or [])
             + (ds.get("pr_review_wave5") or []))
    return [int(i["pr"]) for i in items if i.get("split") in splits]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip().splitlines()[0])
        print("usage: run_campaign_pipelined.py <splits> <arm_out>")
        return 2
    splits = set(sys.argv[1].split(","))
    arm_out = sys.argv[2]
    prs = expected_prs(splits)
    if not prs:
        print(f"no pr_review items in splits {sorted(splits)}")
        return 2
    arm_dir = HERE / "arms" / arm_out
    judge_out = os.environ.get("JUDGE_OUT", f"judgments/{arm_out}_pipelined")
    reps = int(os.environ.get("REPLICATES", "3"))
    item_jobs = int(os.environ.get("JUDGE_ITEM_JOBS", "3"))

    gen_cmd = os.environ.get("GEN_CMD")
    gen_argv = (gen_cmd.split() if gen_cmd else
                [sys.executable, str(HERE / "run_copilot_arm.py"),
                 ",".join(sorted(splits))])
    gen_env = dict(os.environ, KINDS="pr_review", ARM_OUT=arm_out)
    print(f"[pipeline] generating {len(prs)} item(s) -> {arm_dir.name}; "
          f"judging {reps}x each -> {judge_out} as they land", flush=True)
    gen = subprocess.Popen(gen_argv, env=gen_env, cwd=str(HERE))

    sem = threading.Semaphore(item_jobs)
    failures: list[str] = []
    lock = threading.Lock()

    def judge_item(pr: int) -> None:
        with sem:
            judge_cmd = os.environ.get("JUDGE_CMD")
            argv = (judge_cmd.split() + [str(pr)] if judge_cmd else
                    [sys.executable, str(HERE / "judge_val.py")])
            env = dict(os.environ,
                       SPLIT=("holdout5" if "holdout5" in splits else
                              "holdout4" if "holdout4" in splits else
                              "holdout3" if "holdout3" in splits else
                              "holdout" if "holdout" in splits else "all_pr"),
                       ONLY_ITEMS=str(pr),
                       ARM_A_DIR=f"arms/{arm_out}",
                       JUDGE_OUT=judge_out, REPLICATES=str(reps))
            for attempt in range(1, 4):
                rc = subprocess.run(argv, env=env, cwd=str(HERE)).returncode
                if rc == 0:
                    print(f"[pipeline] judged pr{pr}", flush=True)
                    return
                print(f"[pipeline] judge pr{pr} attempt {attempt} rc={rc}", flush=True)
                time.sleep(5 * attempt)
            with lock:
                failures.append(f"pr{pr}: judging failed after 3 attempts")

    threads: list[threading.Thread] = []
    pending = set(prs)
    while pending:
        for pr in sorted(pending):
            md = arm_dir / f"pr{pr}.md"
            if md.is_file() and md.stat().st_size > 0:
                pending.discard(pr)
                t = threading.Thread(target=judge_item, args=(pr,), daemon=True)
                t.start()
                threads.append(t)
                break
        else:
            if gen.poll() is not None and pending:
                # generation exited with items missing: report, do not spin
                with lock:
                    failures.extend(f"pr{p}: never generated"
                                    for p in sorted(pending))
                pending.clear()
            time.sleep(5)
    try:
        gen.wait(timeout=300)
    except subprocess.TimeoutExpired:
        # every expected item is on disk; a generator that lingers past its
        # grace (or a never-exiting GEN_CMD stub) must not hang the campaign
        gen.terminate()
    for t in threads:
        t.join()
    print(f"[pipeline] complete: {len(prs) - len(failures)}/{len(prs)} ok",
          flush=True)
    for f in failures:
        print(f"  FAILED {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
