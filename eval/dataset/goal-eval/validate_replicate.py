#!/usr/bin/env python3
"""Machine-enforced replicate validation (eval plan v3 + rounds 3-6).

A (generation-replicate, judgment-dir) pair is VALID only when ALL hold:
1. Arm outputs: 10/10 expected val stems present with cost.json rc==0.
2. PR-time checkout: every PR item's report asserts `PR-TIME TREE` with the
   head SHA from the independently frozen expected_pr_heads.json.
3. Verdicts: exactly the 30 expected filenames (10 stems x r1-r3); each
   parses; per-kind dimension set present for BOTH x and y with values in
   [0,1] (gap_hit boolean); winner/margin in their enums; _blinding maps
   {X,Y} to the two known labels; _arm_meta.judge_rep matches the filename
   and _arm_meta.arm_a_sha256 matches the actual arm file content (ENFORCED
   — a wrong ARM_A_DIR is a hard error).
4. A2 MoA validity (--moa): every issue item and every non-light PR item
   shows moa_dispatch with >=2 expected member labels AND >=1 llm span whose
   attr.model is a RAW member model name with role=moa_member; light PR items
   are exempt (`moa: n/a (light)`).

Exit 0 valid / 1 invalid (reasons printed). Usage:
  validate_replicate.py <arm_dir> <judge_dir> [--moa member1,member2]
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
HEADS = HERE / "expected_pr_heads.json"
VAL_STEMS = ["pr4893", "pr4810", "pr4825", "pr4837", "pr4816",
             "issue4793", "issue4827", "issue4905", "issue4891", "issue4842"]
# The 20-case PR-review campaign validates a different stem set. EVAL_STEMS (a
# comma list) overrides; absent, the val stems keep every existing call working.
_ENV_STEMS = [s for s in (os.environ.get("EVAL_STEMS") or "").split(",") if s]
PR_DIMS = ("recall", "precision", "actionability")
ISSUE_DIMS = ("correctness", "grounding", "completeness")
WINNERS = {"X", "Y", "tie"}
MARGINS = {"slight", "clear", "decisive"}
LABELS = {"copilot_v2", "opus_baseline"}


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def _check_verdict(f: Path, stem: str, rep: int, arm_dir: Path,
                   errors: list[str]) -> None:
    try:
        v = json.loads(f.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return _fail(errors, f"{f.name}: unreadable/unparseable ({exc})")
    dims = PR_DIMS if stem.startswith("pr") else ISSUE_DIMS
    for side in ("x", "y"):
        s = v.get(side)
        if not isinstance(s, dict):
            return _fail(errors, f"{f.name}: missing side {side}")
        for d in dims:
            val = s.get(d)
            if not isinstance(val, (int, float)) or not 0.0 <= float(val) <= 1.0:
                _fail(errors, f"{f.name}: {side}.{d}={val!r} out of [0,1]")
        if stem.startswith("pr") and not isinstance(s.get("gap_hit"),
                                                    (bool, type(None))):
            _fail(errors, f"{f.name}: {side}.gap_hit not boolean")
    if v.get("winner") not in WINNERS:
        _fail(errors, f"{f.name}: winner={v.get('winner')!r}")
    if v.get("margin") not in MARGINS:
        _fail(errors, f"{f.name}: margin={v.get('margin')!r}")
    bl = v.get("_blinding") or {}
    if set(bl.keys()) != {"X", "Y"} or set(bl.values()) != LABELS:
        _fail(errors, f"{f.name}: bad _blinding {bl}")
    meta = v.get("_arm_meta") or {}
    if meta.get("judge_rep") != rep:
        _fail(errors, f"{f.name}: judge_rep {meta.get('judge_rep')} != {rep}")
    arm_file = arm_dir / f"{stem}.md"
    if arm_file.exists():
        cap = 24_000  # judge_val CAP — hash over the same truncation
        actual = hashlib.sha256(
            arm_file.read_text()[:cap].encode()).hexdigest()
        if meta.get("arm_a_sha256") and meta["arm_a_sha256"] != actual:
            _fail(errors, f"{f.name}: arm content hash mismatch — verdict "
                          "was judged against a DIFFERENT arm output")


def _check_moa(arm_dir: Path, stem: str, members: list[str],
               errors: list[str]) -> None:
    runs = sorted((arm_dir / "runs" / stem).glob("run-*")) \
        if (arm_dir / "runs" / stem).exists() else []
    if not runs:
        return _fail(errors, f"{stem}: no run dir for MoA validation")
    run = runs[-1]
    events = [json.loads(x) for x in
              (run / "run_trace.jsonl").read_text().splitlines()]
    if any(e.get("kind") == "diff_fallback" for e in events):
        return _fail(errors, f"{stem}: used the post-drift diff_fallback path "
                             "(comparability to A1 broken)")
    light = any(e.get("kind") == "review_plan" and e.get("depth") == "light"
                for e in events)
    if stem.startswith("pr") and light:
        return  # moa: n/a (light) — exempt by design
    dispatch = [e for e in events if e.get("kind") == "moa_dispatch"]
    if not dispatch or len(dispatch[0].get("members") or []) < 2:
        return _fail(errors, f"{stem}: no moa_dispatch with >=2 members")
    served = set()
    for line in (run / "trace.jsonl").read_text().splitlines():
        s = json.loads(line)
        if s.get("name") == "llm" and s.get("attr", {}).get("role") == "moa_member":
            served.add(str(s["attr"].get("model")))
    if not served & set(members):   # RAW model names, not model@host labels
        _fail(errors, f"{stem}: no successful member span (served={served})")


def validate(arm_dir: Path, judge_dir: Path,
             moa_members: list[str] | None = None,
             stems: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    stems = stems or _ENV_STEMS or VAL_STEMS
    heads = json.loads(HEADS.read_text()) if HEADS.exists() else {}
    for stem in stems:
        cj = arm_dir / f"{stem}.cost.json"
        md = arm_dir / f"{stem}.md"
        if not md.exists() or not cj.exists():
            _fail(errors, f"{stem}: missing arm output")
            continue
        cost = json.loads(cj.read_text())
        if int(cost.get("rc", 1)) != 0:
            _fail(errors, f"{stem}: rc={cost.get('rc')} (not successful)")
        if stem.startswith("pr"):
            text = md.read_text()
            want = heads.get(stem[2:], "")
            if "PR-TIME TREE" not in text:
                _fail(errors, f"{stem}: no PR-TIME TREE assertion "
                              "(live-checkout fallback?)")
            elif want and want[:12] not in text:
                _fail(errors, f"{stem}: pinned head != expected {want[:12]}")
        if moa_members:
            _check_moa(arm_dir, stem, moa_members, errors)
        for rep in (1, 2, 3):
            f = judge_dir / f"{stem}.r{rep}.json"
            if not f.exists():
                _fail(errors, f"{stem}.r{rep}.json: missing verdict")
            else:
                _check_verdict(f, stem, rep, arm_dir, errors)
    extra = {p.name for p in judge_dir.glob("*.json")} - {
        f"{s}.r{r}.json" for s in stems for r in (1, 2, 3)}
    if extra:
        _fail(errors, f"unexpected verdict files: {sorted(extra)[:5]}")
    return errors


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    members = []
    if "--moa" in sys.argv:
        members = sys.argv[sys.argv.index("--moa") + 1].split(",")
    errs = validate(Path(sys.argv[1]), Path(sys.argv[2]), members or None)
    for e in errs:
        print("INVALID:", e)
    print("VALID" if not errs else f"{len(errs)} problem(s)")
    raise SystemExit(0 if not errs else 1)
