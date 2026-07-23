"""`infermatrix-copilot doctor` — preflight diagnostics with exact fixes.

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
    # Mirror Settings.model_config's env_file tuple: the repo's own .env loads
    # regardless of cwd, and a cwd-local .env overrides it. Checking only the cwd
    # reported a false ✗ (and exit 1) whenever doctor ran from outside the repo,
    # even though the settings it was handed had loaded that .env correctly.
    from ..config import _REPO_ROOT

    if (not any(p.exists() for p in (_REPO_ROOT / ".env", Path(".env")))
            and not os.environ.get("ANTHROPIC_API_KEY")):
        return False, (".env missing and ANTHROPIC_API_KEY unset — fix: "
                       f"cp {_REPO_ROOT}/.env.template {_REPO_ROOT}/.env "
                       "&& edit ANTHROPIC_API_KEY")
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
    detail = f"repo paths exist ({', '.join(sorted(settings.repo_paths))})"
    # URL routing additionally needs each alias's GitHub identity; a path that
    # exists but cannot resolve one passes here yet fails the first pasted URL,
    # so warn (not fail — bare `review pr N` commands never need identity).
    from ..intent import repo_identity

    unresolved = sorted(a for a in settings.repo_paths
                        if repo_identity(a, settings) is None)
    if unresolved:
        detail += ("; ⚠ GitHub identity unknown for "
                   + ", ".join(unresolved)
                   + " — pasted-URL commands cannot route there; fix: set "
                   'REPO_FULL_NAMES={"<alias>": "<owner>/<repo>"} in .env '
                   "(or point the checkout's origin remote at GitHub)")
    return True, detail


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


# Hosts whose served-model families are KNOWN — the static (free) tier check.
# api.deepseek.com maps claude-* names to its own two models silently (verified
# 2026-07-23), which is exactly the mislabel this check exists to catch.
# Unknown gateways stay silent here; `doctor --probe` is the real check there.
_HOST_MODEL_PREFIXES: dict[str, tuple[str, ...]] = {
    "api.deepseek.com": ("deepseek-",),
    "api.anthropic.com": ("claude-",),
}


def _tier_targets(settings) -> list[tuple[str, "object"]]:
    """(label, ResolvedTarget) per configured tier; performance omitted (not
    an error) when deferred/unconfigured."""
    from ..config import TierNotConfiguredError

    out = [("eco", settings.tier_target("eco"))]
    try:
        out.append(("performance", settings.tier_target("performance")))
    except TierNotConfiguredError:
        pass
    return out


def _check_model_backends(settings) -> tuple[bool, str]:
    """Free static check: a tier model whose family a KNOWN host cannot serve
    is a config error with an exact fix — the endpoint would silently
    substitute (the fail-closed runtime guard would then kill every run)."""
    problems, oks = [], []
    for label, t in _tier_targets(settings):
        allowed = _HOST_MODEL_PREFIXES.get(t.host)
        family_ok = allowed is None or any(
            t.model.lower().startswith(p) for p in allowed)
        if not family_ok:
            problems.append(
                f"{label}: {t.host} cannot serve {t.model!r} (it silently "
                f"maps foreign names — serves only {'/'.join(allowed)}*); "
                f"fix: set a {'/'.join(allowed)}* model, or point "
                f"{label.upper()}_BASE_URL(+_API_KEY+_MODEL) at an endpoint "
                "that really serves it")
        else:
            oks.append(f"{label}={t.model}@{t.host}")
    if problems:
        return False, "; ".join(problems)
    perf_note = "" if any(lbl == "performance" for lbl, _ in
                          _tier_targets(settings)) \
        else "; performance tier unconfigured (requests will fail upfront)"
    return True, "tier backends plausible (" + ", ".join(oks) + ")" + perf_note


def _probe_tiers(settings) -> tuple[bool, str]:
    """`--probe` only: one 1-token live request per tier — the ONLY paid doctor
    check, and the strong one: prints requested→served from the response."""
    results, ok_all = [], True
    for label, t in _tier_targets(settings):
        if not t.api_key:
            results.append(f"{label}: no API key resolved")
            ok_all = False
            continue
        try:
            import anthropic

            kwargs = {"api_key": t.api_key, "timeout": 15.0, "max_retries": 0}
            if t.base_url:
                kwargs["base_url"] = t.base_url
            resp = anthropic.Anthropic(**kwargs).messages.create(
                model=t.model, max_tokens=1,
                messages=[{"role": "user", "content": "hi"}])
            served = str(getattr(resp, "model", "") or "")
        except Exception as exc:
            results.append(f"{label}: probe failed ({type(exc).__name__}: {exc})")
            ok_all = False
            continue
        from ..llm import canonical_model

        aliases = settings.model_aliases or {}
        if not served:
            results.append(f"{label}: {t.model} → (no model field: unverified)")
        elif canonical_model(served, aliases) == canonical_model(t.model, aliases):
            results.append(f"{label}: {t.model} → {served} ✓")
        else:
            results.append(
                f"{label}: {t.model} → {served} MISMATCH — {t.host} is "
                "substituting models; fix the tier backend")
            ok_all = False
    if not any(lbl == "performance" for lbl, _ in _tier_targets(settings)):
        results.append("performance: unconfigured (valid deferred state)")
    return ok_all, "; ".join(results)


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


def run_doctor(as_json: bool = False, probe: bool = False) -> int:
    """Run every check; return 0 when all pass, 1 otherwise. Doctor makes no
    paid LLM call by default; `probe=True` (`--probe`) is the one explicit
    exception — a 1-token request per tier to verify the served model."""
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
        ("backends", _check_model_backends(settings)),
        ("playbooks", _check_playbooks(settings)),
        ("moa", _check_mixture(settings)),
    ]
    if probe:
        checks.append(("probe", _probe_tiers(settings)))
    ok_all = all(ok for _, (ok, _) in checks)
    if as_json:
        print(json.dumps({"ok": ok_all, "checks": [
            {"name": n, "ok": ok, "detail": d} for n, (ok, d) in checks]}))
    else:
        for name, (ok, detail) in checks:
            print(f"{'✓' if ok else '✗'} {name:9s} — {detail}")
        print("\nall good — start with: ./infermatrix-copilot" if ok_all
              else "\nfix the ✗ items above, then re-run: infermatrix-copilot doctor")
    return 0 if ok_all else 1
