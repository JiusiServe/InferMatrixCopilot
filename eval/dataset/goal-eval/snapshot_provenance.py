#!/usr/bin/env python3
"""Provenance snapshot for the eval campaign (plan v3 step 0 + round-5/6
fixes): captured BEFORE any val generation; asserted unchanged before every
later stage.

- Content digest covers tracked changes (`git diff --binary HEAD`) + HEAD sha
  + NUL-safe digest of untracked SOURCE files only (src, playbooks,
  eval/dataset/*.py|sh) — generated campaign artifacts (arms/, judgments/,
  invocations, ledger, provenance/manifest files) are excluded so the campaign
  cannot self-invalidate.
- NO raw env values: an allowlist of NON-SECRET knobs + member model@host
  labels only; LLM_MIXTURE's raw value (may contain api_key) is never written.
- Also freezes `expected_pr_heads.json` (val PR -> head SHA via gh) for the
  independent PR-time checkout validation.

Usage: snapshot_provenance.py [--assert]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent.parent          # repo root
OUT = HERE / "provenance_val.json"
HEADS = HERE / "expected_pr_heads.json"
VAL_PRS = [4893, 4810, 4825, 4837, 4816]

_KNOB_ALLOWLIST = (
    "MOA_WHEN", "PR_CONTEXT_MODE", "REVIEW_DEPTH", "ECO_MODEL",
    "PERFORMANCE_MODEL", "AGENT_MODEL", "INTENT_MODEL", "MOA_MAX_USD",
    "MOA_MAX_MEMBERS", "REVIEW_ENSEMBLE",
)


def _run(cmd: list[str], cwd: Path = ROOT) -> bytes:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                          timeout=120).stdout


def _digest() -> dict:
    head = _run(["git", "rev-parse", "HEAD"]).decode().strip()
    diff_sha = hashlib.sha256(_run(["git", "diff", "--binary", "HEAD"])).hexdigest()
    # NUL-safe untracked-source digest: zero-terminated all the way, sorted
    names = _run(["git", "ls-files", "-zo", "--exclude-standard", "--",
                  "src", "playbooks"]).split(b"\x00")
    names += [p.encode() for p in sorted(
        str(f.relative_to(ROOT)) for pat in ("*.py", "*.sh")
        for f in (ROOT / "eval" / "dataset").glob(pat))]
    h = hashlib.sha256()
    for n in sorted(x for x in names if x):
        p = ROOT / n.decode()
        if not p.is_file():
            continue
        rel = str(n.decode())
        if "/goal-eval/" in rel or rel.endswith((".invalid",)):
            continue  # campaign artifacts never affect their own provenance
        h.update(n + b"\x00" + hashlib.sha256(p.read_bytes()).digest())
    return {"head": head, "tracked_diff_sha256": diff_sha,
            "untracked_source_sha256": h.hexdigest()}


def _settings_view() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from omni_copilot.config import Settings
    from omni_copilot.engine.agent_runtime.moa import resolve_members
    from omni_copilot.metrics import MODEL_PRICES

    s = Settings()
    import os
    return {
        "tier_models": {"eco": s.model_for("eco"),
                        "performance": s.model_for("performance")},
        "moa_members": [m.label() for m in resolve_members(s)],  # no keys ever
        "model_prices": json.loads(json.dumps(MODEL_PRICES)),  # tuple->list normalize
        "knobs": {k: os.environ.get(k, "(default)") for k in _KNOB_ALLOWLIST},
        "pip_freeze_sha256": hashlib.sha256(_run(
            [str(ROOT / ".venv" / "bin" / "pip") if (ROOT / ".venv").exists()
             else "pip", "freeze"])).hexdigest(),
    }


def snapshot() -> dict:
    prov = {**_digest(), **_settings_view()}
    OUT.write_text(json.dumps(prov, indent=1))
    if not HEADS.exists():
        heads = {}
        for pr in VAL_PRS:
            out = _run(["gh", "pr", "view", str(pr), "--json", "commits"],
                       cwd=Path("/rebase/vllm-omni"))
            try:
                commits = json.loads(out or b"{}").get("commits") or []
                heads[str(pr)] = str(commits[-1].get("oid", "")) if commits else ""
            except (json.JSONDecodeError, AttributeError, IndexError):
                heads[str(pr)] = ""
        HEADS.write_text(json.dumps(heads, indent=1))
    return prov


def check() -> bool:
    if not OUT.exists():
        print("no snapshot yet")
        return False
    old = json.loads(OUT.read_text())
    cur = {**_digest(), **_settings_view()}
    drift = [k for k in cur if old.get(k) != cur[k]]
    if drift:
        print("PROVENANCE DRIFT in:", drift)
        return False
    print("provenance unchanged")
    return True


if __name__ == "__main__":
    if "--assert" in sys.argv:
        raise SystemExit(0 if check() else 1)
    p = snapshot()
    print(json.dumps({k: p[k] for k in ("head", "tracked_diff_sha256",
                                        "untracked_source_sha256")}, indent=1))
