#!/usr/bin/env python3
"""Record the claudecode + Opus 4.8 baseline over vllm_omni_dataset.yaml.

Protocol is identical to eval/run_eval.py::arm_claudecode(model="claude-opus-4-8")
— the arm previously recorded as `claudecode_opus_skill`:
  real Claude Code CLI, headless (-p, --output-format json, --max-turns 60),
  native Anthropic auth (all ANTHROPIC*/CLAUDE_CODE* env stripped so no DeepSeek
  routing leaks in), the vllm-omni-review skill installed as a project skill in
  eval/raw/cc_workdir, and a read-only gh tool allowlist so nothing can be
  posted to the live repo.

Issue items use the same harness with an answer prompt (gh issue view allowed).

Outputs (resumable — existing non-empty .md files are skipped):
  eval/dataset/baselines/claudecode_opus48/pr<N>.md    + pr<N>.cost.json
  eval/dataset/baselines/claudecode_opus48/issue<N>.md + issue<N>.cost.json
  eval/dataset/baselines/claudecode_opus48/manifest.json

Run order: test -> val -> train (most scoring-critical baselines first).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
OUT = HERE / "baselines" / "claudecode_opus48"
WORKDIR = HERE.parent / "raw" / "cc_workdir"   # has .claude/skills/vllm-omni-review
MODEL = "claude-opus-4-8"
REPO = "vllm-project/vllm-omni"
SPLIT_ORDER = {"test": 0, "val": 1, "train": 2}

ALLOWED_PR = ["Skill", "Task", "Agent", "Read", "Grep", "Glob", "LS", "TodoWrite",
              "Bash(gh pr view:*)", "Bash(gh pr diff:*)", "Bash(gh pr checks:*)"]
ALLOWED_ISSUE = ["Task", "Agent", "Read", "Grep", "Glob", "LS", "TodoWrite",
                 "Bash(gh issue view:*)", "Bash(gh search:*)",
                 "Bash(gh pr view:*)", "Bash(gh pr diff:*)"]


def _env() -> dict:
    env = dict(os.environ)
    for k in [k for k in env if k.startswith(("ANTHROPIC", "CLAUDE_CODE"))]:
        env.pop(k)
    return env


def _run_cc(prompt: str, allowed: list[str]) -> tuple[str, dict]:
    out = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--max-turns", "60",
         "--allowedTools", ",".join(allowed), "--model", MODEL],
        capture_output=True, text=True, timeout=2400, env=_env(),
        cwd=str(WORKDIR))
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        data = {"result": out.stdout or out.stderr, "usage": {}, "num_turns": 0}
    usage = data.get("usage") or {}
    cost = {"calls": data.get("num_turns", 0),
            "input_tokens": usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0)}
    if data.get("total_cost_usd") is not None:
        cost["cost_usd"] = data["total_cost_usd"]
    return str(data.get("result") or "(no output)"), cost


def pr_prompt(n: int) -> str:
    return (f"Use the vllm-omni-review skill to review PR #{n} of {REPO}. "
            f"A read-only checkout of the repo (post-merge main) is at "
            f"/rebase/vllm-omni. IMPORTANT: do NOT post anything to GitHub — "
            f"output the complete review (verdict + comments with file:line) "
            f"as your final message.")


def issue_prompt(n: int) -> str:
    return (f"Answer issue #{n} of {REPO} as a knowledgeable maintainer. "
            f"A read-only checkout of the repo is at /rebase/vllm-omni — "
            f"investigate the code before answering; cite files/lines where "
            f"relevant. If the issue is a question, answer it; if a bug, give "
            f"the likely root cause and a concrete fix or workaround; if it "
            f"should be closed (invalid/duplicate/stale), say so with reasons. "
            f"IMPORTANT: do NOT post anything to GitHub — output the complete "
            f"answer as your final message.")


def one(kind: str, n: int, split: str) -> str:
    stem = ("pr" if kind == "pr_review" else "issue") + str(n)
    md, cj = OUT / f"{stem}.md", OUT / f"{stem}.cost.json"
    if md.exists() and md.stat().st_size > 50:
        return f"skip {stem} (done)"
    t0 = time.time()
    if kind == "pr_review":
        text, cost = _run_cc(pr_prompt(n), ALLOWED_PR)
    else:
        text, cost = _run_cc(issue_prompt(n), ALLOWED_ISSUE)
    cost.update({"wall_s": round(time.time() - t0, 1), "split": split,
                 "model": MODEL, "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    md.write_text(text, encoding="utf-8")
    cj.write_text(json.dumps(cost, indent=2))
    return (f"done {stem} [{split}] {cost['wall_s']}s "
            f"${cost.get('cost_usd', '?')} out={cost['output_tokens']}")


def main() -> None:
    d = yaml.safe_load(DATASET.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    items = ([("pr_review", i["pr"], i["split"]) for i in d["pr_review"]]
             + [("issue_answer", i["issue"], i["split"]) for i in d["issue_answer"]])
    items.sort(key=lambda t: SPLIT_ORDER[t[2]])
    only = sys.argv[1] if len(sys.argv) > 1 else ""   # e.g. "test" / "val" / "train"
    if only:
        items = [t for t in items if t[2] == only]
    (OUT / "manifest.json").write_text(json.dumps({
        "arm": "claudecode_opus48", "model": MODEL,
        "protocol": "eval/run_eval.py::arm_claudecode (claudecode_opus_skill arm), "
                    "issue items use the same harness with an answer prompt",
        "workdir": str(WORKDIR), "dataset": DATASET.name,
        "n_items": len(items)}, indent=2))
    print(f"[baseline] {len(items)} items -> {OUT}", flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(one, *t): t for t in items}
        for f in as_completed(futs):
            try:
                print(f"[baseline] {f.result()}", flush=True)
            except Exception as e:  # noqa: BLE001 — keep the sweep going
                print(f"[baseline] FAIL {futs[f]}: {e}", flush=True)
    print("[baseline] sweep complete", flush=True)


if __name__ == "__main__":
    main()
