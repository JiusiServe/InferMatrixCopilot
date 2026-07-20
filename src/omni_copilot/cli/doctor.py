"""`omni-copilot doctor` — preflight diagnostics with exact fixes.

Every check prints ✓/✗ plus, on failure, the ONE command or edit that fixes it
(the hermes/cline capture-and-print pattern; Claude Code's `claude doctor` is
the UX bar). Read-only: never mutates config, never prints secret VALUES (key
names only), never makes a paid LLM call. `--json` emits machine-readable
results for CI.
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def _check_deps() -> tuple[bool, str]:
    missing = [m for m in ("pydantic", "pydantic_settings", "yaml", "anthropic")
               if importlib.util.find_spec(m) is None]
    if missing:
        return False, ("missing python deps: " + ", ".join(missing)
                       + " — fix: pip install -e . (from the repo root)")
    return True, "python dependencies import"


def _check_env(settings) -> tuple[bool, str]:
    env_file = Path(".env")
    if not env_file.exists() and not os.environ.get("ANTHROPIC_API_KEY"):
        return False, (".env missing and ANTHROPIC_API_KEY unset — fix: "
                       "cp .env.template .env && edit ANTHROPIC_API_KEY")
    if not (settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")):
        return False, ("ANTHROPIC_API_KEY is empty — fix: set it in .env "
                       "(key NAME checked only; value never printed)")
    return True, "LLM credentials configured"


def _check_gh() -> tuple[bool, str]:
    if shutil.which("gh") is None:
        return False, ("GitHub CLI not installed — fix: "
                       "https://cli.github.com (e.g. `sudo apt install gh`)")
    try:
        out = subprocess.run(["gh", "auth", "status"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace",
                             timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"gh auth status failed ({exc}) — fix: gh auth login"
    if out.returncode != 0:
        detail = (out.stderr or out.stdout).strip().splitlines()
        return False, ("gh is not authenticated — fix: gh auth login"
                       + (f"  ({detail[0]})" if detail else ""))
    return True, "gh installed and authenticated"


def _check_repos(settings) -> tuple[bool, str]:
    if not settings.repo_paths:
        return False, ("REPO_PATHS is empty — fix: set REPO_PATHS in .env, "
                       'e.g. {"my-repo": "/path/to/my-repo"}')
    missing = {a: p for a, p in settings.repo_paths.items()
               if not Path(str(p)).is_dir()}
    if missing:
        return False, ("repo path(s) missing: "
                       + "; ".join(f"{a} -> {p}" for a, p in missing.items())
                       + " — fix: clone the repo(s) or correct REPO_PATHS")
    return True, f"repo paths exist ({', '.join(sorted(settings.repo_paths))})"


def _check_playbooks(settings) -> tuple[bool, str]:
    try:
        from ..engine.registry import StepRegistry
        from ..engine.steps import register_builtin_steps
        from ..playbooks.store import PlaybookStore

        store = PlaybookStore(settings.playbooks_dir,
                              register_builtin_steps(StepRegistry()))
        names = [p for p in store.names()] if hasattr(store, "names") else \
            list(getattr(store, "_playbooks", {}))
        return True, f"playbooks load ({len(names)} registered)"
    except Exception as exc:
        return False, f"playbooks failed to load: {exc} — fix: git checkout playbooks/"


def _check_mixture(settings) -> tuple[bool, str]:
    mix = getattr(settings, "llm_mixture", {}) or {}
    members = mix.get("members") or []
    if not members:
        return True, "MoA off (LLM_MIXTURE unset/empty — optional)"
    from ..engine.agent_runtime.moa import resolve_members

    usable = resolve_members(settings)
    if len(usable) < 2:
        return False, (f"MoA configured but only {len(usable)}/{len(members)} "
                       "members usable (need >=2; unpriced models are rejected "
                       "— add a MODEL_PRICES entry or fix api_key_env)")
    return True, (f"MoA usable ({len(usable)}/{len(members)} members: "
                  + ", ".join(m.label() for m in usable)
                  + "; keys never printed)")


def run_doctor(as_json: bool = False) -> int:
    """Run every check; return 0 when all pass, 1 otherwise."""
    from ..config import Settings

    try:
        settings = Settings()
    except Exception as exc:
        msg = f"Settings failed to parse: {exc} — fix: check .env syntax"
        if as_json:
            print(json.dumps({"ok": False, "checks": [
                {"name": "settings", "ok": False, "detail": msg}]}))
        else:
            print(f"✗ settings — {msg}")
        return 1

    checks = [
        ("deps", _check_deps()),
        ("env", _check_env(settings)),
        ("gh", _check_gh()),
        ("repos", _check_repos(settings)),
        ("playbooks", _check_playbooks(settings)),
        ("moa", _check_mixture(settings)),
    ]
    ok_all = all(ok for _, (ok, _) in checks)
    if as_json:
        print(json.dumps({"ok": ok_all, "checks": [
            {"name": n, "ok": ok, "detail": d} for n, (ok, d) in checks]}))
    else:
        for name, (ok, detail) in checks:
            print(f"{'✓' if ok else '✗'} {name:9s} — {detail}")
        print("\nall good — start with: ./omni-copilot" if ok_all
              else "\nfix the ✗ items above, then re-run: omni-copilot doctor")
    return 0 if ok_all else 1
