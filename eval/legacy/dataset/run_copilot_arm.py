#!/usr/bin/env python3
"""Run the copilot arm (the real omni-copilot product CLI) over dataset items.

Unlike the in-process copilot_v2 arm of eval/run_eval.py, this drives the full
shipped pipeline end-to-end: LLM intent parse -> planner (vetted playbook) ->
executor (pr-review@4 with the 4-lens ensemble / issue-answer with gated post
off) -> RUN_REPORT.md. LLM per .env (DeepSeek-routed); ALLOW_POST/ALLOW_PUSH
stay off, so nothing touches the live repo.

Usage: run_copilot_arm.py [splits] [only_stem]
  splits: comma list, default "val,train" (test is frozen — untouched by default)
  only_stem: e.g. pr4816 to run a single item

Outputs (resumable — existing non-empty .md files are skipped):
  eval/dataset/arms/copilot_v2/{pr|issue}<N>.md        (RUN_REPORT.md)
  eval/dataset/arms/copilot_v2/{pr|issue}<N>.cost.json (metrics.json + trace tokens)
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# omni-copilot names run dirs run-<YYYYmmdd-HHMMSS>: two runs whose STARTUP
# reaches run-dir naming in the same second COLLIDE and overwrite each other's
# artifacts (observed live twice: pr4810+pr4893, then issue4827+issue4793 even
# with staggered Popen — import latency varies). Bulletproof fix: every
# invocation gets its own private RUN_ROOT (env-overridable Settings field),
# so collisions are structurally impossible. A small start stagger remains to
# avoid thundering-herd startup.
_START_LOCK = threading.Lock()
_last_start = [0.0]

import yaml

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
# ARM_OUT selects the arm directory (default T0). For the post-learning T1 pass:
#   ARM_OUT=copilot_v2_t1 run_copilot_arm.py val
import os as _os

OUT = HERE / "arms" / _os.environ.get("ARM_OUT", "copilot_v2")
RUN_ROOT = Path.home() / ".omni-copilot" / "runs"
CLI = "/rebase/.venv/bin/omni-copilot"
CWD = HERE.parent.parent  # repo root, where .env lives
SPLIT_ORDER = {"val": 0, "train": 1, "test": 2}


def _find_run_dir(private_root: Path, kind: str, n: int) -> Path | None:
    """The newest run dir under this item's PRIVATE run root (spec verified)."""
    best = None
    for d in private_root.glob("run-*"):
        try:
            task = json.loads((d / "task.json").read_text())
        except Exception:
            continue
        spec = task.get("spec") or task  # task.json nests the TaskSpec under "spec"
        key = "pr" if kind == "pr_review" else "issue"
        if spec.get(key) == n and spec.get("kind") == kind:
            if best is None or d.stat().st_mtime > best.stat().st_mtime:
                best = d
    return best


def _trace_tokens(run_dir: Path) -> dict:
    tin = tout = calls = 0
    try:
        for line in (run_dir / "run_trace.jsonl").read_text().splitlines():
            ev = json.loads(line)
            u = ev.get("usage") or ev.get("llm_usage") or {}
            if u:
                calls += 1
                tin += u.get("input_tokens", 0)
                tout += u.get("output_tokens", 0)
    except Exception:
        pass
    return {"llm_calls": calls, "input_tokens": tin, "output_tokens": tout}


def one(kind: str, n: int, split: str) -> str:
    stem = ("pr" if kind == "pr_review" else "issue") + str(n)
    md, cj = OUT / f"{stem}.md", OUT / f"{stem}.cost.json"
    if md.exists() and md.stat().st_size > 50:
        return f"skip {stem} (done)"
    # "do not post" pins post=false at intent parse (the LLM parser once
    # hallucinated post=true); ALLOW_POST=0 already dry-runs posting regardless.
    prompt = (f"review pr {n}, do not post" if kind == "pr_review"
              else f"answer issue {n}, do not post")
    import os

    private_root = OUT / "runs" / stem
    private_root.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, RUN_ROOT=str(private_root))
    t0 = time.time()
    blocked_retries = 0
    for attempt in range(4):
        with _START_LOCK:
            gap = time.time() - _last_start[0]
            if gap < 0.5:
                time.sleep(0.5 - gap)
            _last_start[0] = time.time()
        proc = subprocess.run([CLI, "-p", prompt, "--yes"], capture_output=True,
                              text=True, timeout=3000, cwd=str(CWD), env=env)
        # the LLM-only intent parser occasionally returns a clarify instead of
        # a TaskSpec ("I couldn't parse that") — nondeterministic; retry.
        if "couldn't parse" in proc.stdout:
            print(f"[copilot-arm] retry {stem} (intent clarify, "
                  f"attempt {attempt + 1})", flush=True)
            continue
        # rc=3 (blocked/escalated) is usually a bad roll (T3: $0.017/attempt,
        # the same item answered fine in a sibling replicate) — one retry.
        if proc.returncode == 3 and blocked_retries < 1:
            blocked_retries += 1
            print(f"[copilot-arm] retry {stem} (blocked rc=3)", flush=True)
            continue
        break
    wall = round(time.time() - t0, 1)
    run_dir = _find_run_dir(private_root, kind, n)
    report = ""
    if run_dir and (run_dir / "RUN_REPORT.md").exists():
        report = (run_dir / "RUN_REPORT.md").read_text()
    if not report.strip():
        # fall back to CLI stdout so failures stay diagnosable
        report = (f"(no RUN_REPORT.md — rc={proc.returncode})\n\n"
                  f"## stdout\n{proc.stdout[-8000:]}\n\n## stderr\n{proc.stderr[-4000:]}")
    cost = {"wall_s": wall, "split": split, "rc": proc.returncode,
            "run_dir": str(run_dir) if run_dir else None,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if run_dir:
        cost.update(_trace_tokens(run_dir))
        mfile = run_dir / "metrics.json"
        if mfile.exists():
            try:
                cost["metrics"] = json.loads(mfile.read_text())
            except Exception:
                pass
    md.write_text(report, encoding="utf-8")
    cj.write_text(json.dumps(cost, indent=2))
    status = "done" if run_dir and proc.returncode == 0 else "DONE-WITH-ISSUES"
    return (f"{status} {stem} [{split}] {wall}s rc={proc.returncode} "
            f"tok_out={cost.get('output_tokens', '?')}")


def main() -> None:
    d = yaml.safe_load(DATASET.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    want = (sys.argv[1] if len(sys.argv) > 1 else "val,train").split(",")
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    items = ([("pr_review", i["pr"], i["split"]) for i in d["pr_review"]]
             + [("issue_answer", i["issue"], i["split"]) for i in d["issue_answer"]])
    items = [t for t in items if t[2] in want]
    if only:
        items = [t for t in items
                 if ("pr" if t[0] == "pr_review" else "issue") + str(t[1]) == only]
    items.sort(key=lambda t: SPLIT_ORDER[t[2]])
    (OUT / "manifest.json").write_text(json.dumps({
        "arm": "copilot_v2", "engine": "omni-copilot CLI (shipped pipeline, "
        "pr-review@4 ensemble; issue-answer dry-run)",
        "llm": "per .env (DeepSeek-routed)", "dataset": DATASET.name,
        "splits": want, "n_items": len(items)}, indent=2))
    print(f"[copilot-arm] {len(items)} items -> {OUT}", flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(one, *t): t for t in items}
        for f in as_completed(futs):
            try:
                print(f"[copilot-arm] {f.result()}", flush=True)
            except Exception as e:  # noqa: BLE001 — keep the sweep going
                print(f"[copilot-arm] FAIL {futs[f]}: {e}", flush=True)
    print("[copilot-arm] sweep complete", flush=True)


if __name__ == "__main__":
    main()
