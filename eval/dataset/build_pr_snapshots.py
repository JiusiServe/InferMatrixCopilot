#!/usr/bin/env python3
"""Freeze one sanitized PR-context snapshot per item, shared byte-for-byte by both
Opus 5 arms (`run_baseline_pinned.py` and `run_direct_arm.py`).

Why this exists rather than letting each arm call `gh` itself:

* **Leakage.** `--allowedTools` matches by command prefix, so `Bash(gh pr view:*)`
  cannot be narrowed to exclude `--comments` / `--json reviews` — and this dataset's
  ground truth IS the human review discussion (`gt/pr<N>.inline.json`). The only safe
  move is to drop `gh pr view` from the allowlist entirely and hand the arm a snapshot
  assembled out here, where the field list is fixed in source and auditable.

* **It must be the same snapshot.** CI state is live: two arms calling `gh pr checks`
  at different wall-clock moments would silently receive different inputs, and the
  "identical information budget" claim would be false. Built once, hashed, injected
  verbatim; each arm records `snapshot_sha256` and the comparison refuses to score if
  the two arms disagree for any PR.

Content is byte-equivalent to what the copilot arms already saw, so the new arms are
neither advantaged nor starved relative to `copilot_v4_pr20_*`:

* `_pr_context_bundle` under `pr_context_mode=no_discussion` (`fetch.py:155-219`) —
  title, labels, body clipped at 4,000, and up to 2 linked issues clipped at 2,000.
  Comments, review summaries and inline review comments live behind `mode == "full"`
  and are never requested here.
* `pr.gate_check` (`fetch.py:277-330`) — draft / merge-state / failing-checks report.

Usage: build_pr_snapshots.py [splits]     # default train,val,test (the 20-PR set)
Outputs: eval/dataset/snapshots/pr<N>.json  {"text", "sha256", "pr", "built_at"}
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
OUT = HERE / "snapshots"
REPO_PATH = Path("/data/zhoutaichang/copilot/vllm-omni")

# mirrors fetch.py:124 — keep in sync if that regex changes
_LINKED_ISSUE = re.compile(r"(?:fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s*:?\s*#(\d+)",
                           re.IGNORECASE)

# Fields we are allowed to request. Anything carrying reviewer opinion — comments,
# reviews, or the pulls/<n>/comments endpoint — is absent by construction, not by
# filtering after the fact.
_VIEW_FIELDS = ("title,body,labels,headRefName,state,isDraft,mergeable,"
                "mergeStateStatus,commits")


def _gh(args: list[str]) -> tuple[int, str]:
    p = subprocess.run(["gh", *args], cwd=str(REPO_PATH), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=180)
    return p.returncode, p.stdout


def _clip(text: str, n: int = 700) -> str:
    """Identical to fetch.py:150 — the clip boundary is part of the byte-equivalence."""
    text = str(text or "").strip()
    return text if len(text) <= n else text[:n] + " …[clipped]"


def _context_bundle(pr: int, data: dict) -> str:
    """`_pr_context_bundle` under no_discussion, reproduced field for field."""
    parts: list[str] = []
    if data:
        labels = ", ".join(lb.get("name", "") for lb in data.get("labels") or [])
        parts.append(f"## PR description\n### {data.get('title', '')}"
                     + (f"  [labels: {labels}]" if labels else "")
                     + f"\n{_clip(data.get('body'), 4000)}")
    else:
        parts.append("(pr view unavailable — partial context)")
    if data:
        # commit timeline — reproduced from fetch.py `_pr_context_bundle`
        # (added there for the squashed-diff add-then-revert class); the
        # snapshot must carry it too or the copilot arm holds information
        # the reference arms were never given
        subjects = [
            f"- {str(c.get('oid') or '')[:8]} "
            f"{_clip((c.get('messageHeadline') or ''), 100)}"
            for c in (data.get("commits") or [])[-20:]]
        if subjects:
            parts.append("## Commit timeline (subjects only — the diff below "
                         "is the squashed net change)\n" + "\n".join(subjects))
    hay = f"{(data.get('body') or '')} {(data.get('headRefName') or '')}"
    for num in list(dict.fromkeys(_LINKED_ISSUE.findall(hay)))[:2]:
        code, out = _gh(["issue", "view", num, "--json", "title,body"])
        if code == 0:
            try:
                idata = json.loads(out or "{}")
            except json.JSONDecodeError:
                continue
            parts.append(f"## Linked issue #{num}: {idata.get('title', '')}\n"
                         + _clip(idata.get("body"), 2000))
    return "\n\n".join(p for p in parts if p)


def _gate_report(pr: int, data: dict) -> str:
    """`pr.gate_check`, reproduced. Returns the same one-line-clean default."""
    lines: list[str] = []
    if not data:
        return "gate check unavailable (gh failed)"
    if data.get("isDraft"):
        lines.append("PR is a DRAFT — review findings are provisional.")
    if data.get("mergeable") == "CONFLICTING" or \
            data.get("mergeStateStatus") in ("DIRTY", "BEHIND"):
        lines.append(f"MERGE STATE: {data.get('mergeStateStatus')} / "
                     f"{data.get('mergeable')} — the branch conflicts with or "
                     "trails the base; files may have moved/renamed on main. "
                     "Flag this as a blocking issue.")
    code, out = _gh(["pr", "checks", str(pr), "--json", "name,state,bucket"])
    if code == 0:
        try:
            checks = json.loads(out or "[]")
        except json.JSONDecodeError:
            checks = []
        failing = [c.get("name", "?") for c in checks
                   if c.get("bucket") == "fail"
                   or str(c.get("state", "")).upper() in ("FAILURE", "ERROR")]
        if failing:
            lines.append(f"FAILING CHECKS ({len(failing)}): {failing[:8]} — "
                         "do not re-argue what CI already reports; point at the gate.")
    return "\n".join(lines) or "gates clean (mergeable, no failing checks)"


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build(pr: int) -> tuple[str, str]:
    code, out = _gh(["pr", "view", str(pr), "--json", _VIEW_FIELDS])
    data: dict = {}
    if code == 0:
        try:
            data = json.loads(out or "{}")
        except json.JSONDecodeError:
            data = {}
    text = (f"{_context_bundle(pr, data)}\n\n"
            f"## PR state and gates\nPR state: {data.get('state') or 'UNKNOWN'}\n"
            f"{_gate_report(pr, data)}")
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    splits = set((sys.argv[1] if len(sys.argv) > 1 else "train,val,test").split(","))
    ds = yaml.safe_load(DATASET.read_text(encoding="utf-8"))
    items = [i for i in ds["pr_review"] + (ds.get("pr_review_wave2") or [])
             + (ds.get("pr_review_wave3") or [])
             + (ds.get("pr_review_wave4") or [])
             + (ds.get("pr_review_wave5") or [])
             if i.get("split") in splits]
    OUT.mkdir(parents=True, exist_ok=True)

    failures = []
    for item in items:
        pr = int(item["pr"])
        dest = OUT / f"pr{pr}.json"
        if dest.is_file():
            print(f"  pr{pr}: already frozen, keeping "
                  f"{json.loads(dest.read_text())['sha256'][:12]}")
            continue
        try:
            text, digest = build(pr)
        except Exception as exc:  # noqa: BLE001 — report every PR, fail at the end
            failures.append(f"pr{pr}: {exc}")
            print(f"  pr{pr}: FAILED — {exc}")
            continue
        # A snapshot that lost the description would silently starve both arms of
        # the same thing, which looks like a null result rather than a broken input.
        if "## PR description" not in text:
            failures.append(f"pr{pr}: snapshot has no PR description — refusing to freeze")
            print(f"  pr{pr}: FAILED — no PR description in snapshot")
            continue
        _write_atomic(dest, json.dumps(
            {"pr": pr, "sha256": digest, "text": text,
             "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "policy": "no_discussion — byte-equivalent to _pr_context_bundle "
                       "(fetch.py:155) plus pr.gate_check (fetch.py:277); comments, "
                       "reviews and inline review comments never requested"},
            indent=2, ensure_ascii=False) + "\n")
        print(f"  pr{pr}: frozen {digest[:12]} ({len(text)} chars)")

    print(f"\n{len(list(OUT.glob('pr*.json')))} snapshot(s) in {OUT}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
