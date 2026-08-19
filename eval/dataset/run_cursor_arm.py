#!/usr/bin/env python3
"""Cursor Composer arm: headless `cursor-agent` on the pinned PR-time tree.

Same measurement contract as `run_baseline_pinned.py` — pinned worktree,
frozen sanitized snapshot (byte-identical to what every other arm received),
no PR-discussion access — with one structural difference that is disclosed
rather than hidden: `cursor-agent` has no tool allowlist, so where the
Claude baseline PREVENTS discussion access (allowlist), this arm DETECTS it
(post-run audit over the full stream-json tool log) and fails the item on
any violation. Plan mode was probed and rejected: it disables the shell,
which would strip `git diff`/grep and cripple the arm relative to the
baseline it is compared against.

gh auth is stripped for the subprocess (empty GH_CONFIG_DIR, tokens
removed); the repo is public, so unauthenticated fetches remain *possible*
— which is exactly why the audit, not the environment, is the gate.

Usage: run_cursor_arm.py [splits] [only_stem]
Env:   ARM_OUT (default cursor_composer25), ARM_MODEL (default composer-2.5),
       ARM_JOBS (default 3), CURSOR_TIMEOUT_S (default 1800)
Outputs: arms/<ARM_OUT>/pr<N>.{md,cost.json,events.jsonl} + manifest.json
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

import cc_arm_common as cc
from run_ocr_arm import _prepare_worktree, _write_atomic, EXPECTED_HEADS, JUDGE_CAP

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
OUT = HERE / "arms" / os.environ.get("ARM_OUT", "cursor_composer25")
MODEL = os.environ.get("ARM_MODEL", "composer-2.5")
TIMEOUT = int(os.environ.get("CURSOR_TIMEOUT_S", "1800"))
ARM = f"cursor_{MODEL.replace('-', '')}"

# Discussion-access signatures. `git fetch pull/N/head` is CODE and allowed;
# what must never be reachable is the human review thread the ground truth is
# made of. Case-insensitive, matched against every shell command the agent ran.
_FORBIDDEN = re.compile(
    r"(?i)\bgh\s+(pr|issue|api)\b"
    r"|api\.github\.com/repos/[^ ]*/(pulls|issues)/\d+/(comments|reviews)"
    r"|github\.com/[^ ]*/pull/\d+([^0-9]|$)(?![^ ]*\.diff)"
    r"|(curl|wget)[^|;&]*github\.com[^|;&]*(comment|review|discussion)")


def prompt(pr: int, snap: str, base: str, head: str) -> str:
    return (
        f"Review pull request #{pr} of {cc.REPO} as an expert reviewer.\n\n"
        f"Your working directory IS a read-only checkout of the repository at this "
        f"PR's exact head commit ({head[:12]}) — the merge-base with main is "
        f"{base[:12]}, so `git diff {base} HEAD` is precisely this PR's change. The "
        f"code around it is the code as it stood when the PR was opened.\n\n"
        f"Frozen PR context (this is all of it — there is no PR discussion available, "
        f"deliberately; do NOT try to fetch any):\n\n{snap}\n\n"
        f"Investigate the code before concluding: read the changed files and the code "
        f"that calls into them. Do not modify any file, and do not read ANY file "
        f"outside this working directory (no home-directory configs, no other "
        f"checkouts) — reviews that do are disqualified.\n\n"
        f"Budget: spend at most two thirds of your effort investigating and then "
        f"WRITE THE REVIEW — an unwritten review scores as silence no matter how "
        f"good the investigation behind it was.\n\n"
        f"IMPORTANT: do not post anything to GitHub. Output the complete review as "
        f"your final message — an overall verdict, then specific comments with "
        f"file:line references and what to change."
    )


def _run_cursor(text: str, cwd: str, gh_empty: Path) -> list[dict]:
    env = {k: v for k, v in os.environ.items()
           if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    env["GH_CONFIG_DIR"] = str(gh_empty)
    p = subprocess.run(
        ["cursor-agent", "--print", "--trust", "--force",
         "--output-format", "stream-json", "--model", MODEL, text],
        cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=TIMEOUT)
    events = []
    for line in (p.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _audit(events: list[dict], worktree: str) -> tuple[list[str], int, int]:
    """(violations, shell_commands, reads). Reads outside the worktree and any
    discussion-access command are violations — same policy the baseline's
    audit enforces, applied detectively instead of preventively."""
    violations: list[str] = []
    n_shell = n_read = 0
    wt_real = os.path.realpath(worktree)
    for e in events:
        tc = (e.get("tool_call") or {}) if e.get("type") == "tool_call" else {}
        shell = tc.get("shellToolCall")
        if shell and "result" not in shell:
            cmd = str((shell.get("args") or {}).get("command") or "")
            n_shell += 1
            if _FORBIDDEN.search(cmd):
                violations.append(f"shell: forbidden discussion access: "
                                  f"{cmd[:160]}")
        read = tc.get("readToolCall")
        if read and "result" not in read:
            path = str((read.get("args") or {}).get("path") or "")
            n_read += 1
            # realpath both sides: the machine reaches the same worktree via
            # /home and /data prefixes, and a symlinked HOME must not read as
            # an out-of-tree violation
            if path and not (os.path.realpath(path) + "/").startswith(
                    wt_real + "/"):
                violations.append(f"read outside worktree: {path[:160]}")
        write = tc.get("writeToolCall") or tc.get("editToolCall")
        if write:
            violations.append("write attempted in read-only review")
    return violations, n_shell, n_read


def _final_text(events: list[dict]) -> str:
    for e in reversed(events):
        if e.get("type") == "result":
            return str(e.get("result") or "").strip()
    return ""


def main() -> int:
    splits = set((sys.argv[1] if len(sys.argv) > 1 else "holdout").split(","))
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    ds = yaml.safe_load(DATASET.read_text(encoding="utf-8"))
    heads = json.loads(EXPECTED_HEADS.read_text(encoding="utf-8"))
    items = [i for i in ds["pr_review"] + (ds.get("pr_review_wave2") or [])
             + (ds.get("pr_review_wave3") or [])
             + (ds.get("pr_review_wave4") or [])
             + (ds.get("pr_review_wave5") or [])
             if i.get("split") in splits]
    if only:
        items = [i for i in items if f"pr{i['pr']}" == only]
    OUT.mkdir(parents=True, exist_ok=True)
    gh_empty = Path(tempfile.mkdtemp(prefix="cursor-arm-gh-"))

    failures: list[str] = []
    done = 0
    lock = threading.Lock()

    pending = []
    for item in items:                      # serial: worktree lock
        pr = int(item["pr"])
        stem = f"pr{pr}"
        expected_head = heads.get(str(pr))
        if not expected_head:
            failures.append(f"{stem}: no pinned head")
            continue
        if (OUT / f"{stem}.md").is_file() and (OUT / f"{stem}.md").stat().st_size:
            done += 1
            print(f"  {stem}: already done, skipping")
            continue
        try:
            wt, base = _prepare_worktree(str(pr), expected_head,
                                         int(item["size"]["files"]))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{stem}: {exc}")
            continue
        pending.append((item, str(wt), str(base), expected_head))

    def _review(job) -> None:
        nonlocal done
        item, wt, base, expected_head = job
        pr = int(item["pr"])
        stem = f"pr{pr}"
        snap, snap_sha = cc.snapshot(pr)
        t0 = time.time()
        events = _run_cursor(prompt(pr, snap, base, expected_head), wt, gh_empty)
        wall = round(time.time() - t0, 1)
        body = _final_text(events)
        violations, n_shell, n_read = _audit(events, wt)
        cost = {"arm": ARM, "model_requested": MODEL, "head": expected_head,
                "base": base, "snapshot_sha256": snap_sha, "wall_s": wall,
                "shell_commands": n_shell, "file_reads": n_read,
                "cost_usd": None,  # cursor does not expose per-run billing
                "audit_ok": not violations, "audit_violations": violations,
                "artifact_chars": len(body), "split": item.get("split")}
        _write_atomic(OUT / f"{stem}.cost.json",
                      json.dumps(cost, indent=2) + "\n")
        _write_atomic(OUT / f"{stem}.events.jsonl",
                      "\n".join(json.dumps(e, ensure_ascii=False)
                                for e in events) + "\n")
        _write_atomic(OUT / f"{stem}.md", (body or "(no output)") + "\n")
        with lock:
            if violations:
                failures.append(f"{stem}: audit violations {violations[:2]}")
                print(f"  {stem}: AUDIT FAILED — {violations[:2]}")
                return
            if not body:
                failures.append(f"{stem}: empty review")
                print(f"  {stem}: EMPTY REVIEW")
                return
            done += 1
            print(f"  {stem}: wall={wall}s shell={n_shell} reads={n_read} "
                  f"chars={len(body)}", flush=True)

    jobs = max(1, int(os.environ.get("ARM_JOBS", "3")))
    try:
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_review, j) for j in pending]
            for f in as_completed(futs):
                if f.exception():
                    with lock:
                        failures.append(f"worker crashed: {f.exception()}")
        _write_atomic(OUT / "manifest.json", json.dumps({
            "arm": OUT.name, "model_requested": MODEL,
            "harness": "cursor-agent --print --trust --force stream-json",
            "leakage_control": "DETECTIVE, not preventive: gh auth stripped "
                               "(empty GH_CONFIG_DIR, tokens removed) and every "
                               "shell command/read audited post-run; items with "
                               "violations are failed. cursor-agent has no tool "
                               "allowlist, so prevention equivalent to the "
                               "claude baseline is not available.",
            "pr_context": "frozen snapshot (no_discussion), byte-identical to "
                          "the other arms",
            "dataset": DATASET.name, "splits": sorted(splits),
            "n_items": done, "concurrency": jobs,
        }, indent=2) + "\n")
    finally:
        shutil.rmtree(gh_empty, ignore_errors=True)
    print(f"\n{done}/{len(items)} items written to {OUT}")
    for f in failures:
        print(f"  FAILED {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
