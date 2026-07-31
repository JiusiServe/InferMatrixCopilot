"""`RebaseHooks` — the narrow BEHAVIORAL surface an adapter may customize
(plan §1.2: behavioral policies are adapter code, loaded only for declared
and active adapters; everything else is data). The neutral base has working
defaults, so a repo with no hooks file runs the stock pipeline.

Loading is fail-closed and human-gated: the manifest must declare
`rebase.hooks` explicitly (the file's mere existence activates nothing), the
adapter must be `status: active`, and the manifest's `rebase` section is
HIGH-RISK (agent writes rejected) — an agent cannot self-install hooks."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Mapping


class RebaseHooks:
    """Neutral defaults. Adapters subclass in `<adapter>/rebase/hooks.py`
    and export HOOKS (an instance)."""

    def adaptive_guidance(self, module: str) -> str:
        """Knowledge-layer block injected into the module prompt's
        {ADAPTIVE_GUIDANCE} slot. Default: none (the template's neutral
        placeholder is used). Must never raise — a broken knowledge layer
        must not block a rebase."""
        return ""

    def commit_message(self, upstream_short: str) -> str | None:
        """Override the rebase commit message; None keeps the adapter
        manifest's template."""
        return None

    def on_module_result(self, module: str, result: Mapping) -> None:
        """Observation hook after each module agent finishes (metrics,
        notifications). Must never raise."""


class HooksError(RuntimeError):
    """Declared hooks failed to load — fail closed, never silently stock."""


def load_hooks(adapter_dir: Path, manifest: Mapping) -> RebaseHooks:
    """The adapter's declared hooks, or the neutral defaults.

    Absent declaration ⇒ defaults. A DECLARED hooks file that is missing,
    unloadable, or exports no `HOOKS: RebaseHooks` raises — the operator
    asked for behavior the run cannot provide, and running stock silently
    would misrepresent what executed."""
    rel = ((manifest.get("rebase") or {}).get("hooks") or "")
    if not rel:
        return RebaseHooks()
    if manifest.get("status") != "active":
        raise HooksError("hooks declared but the adapter is not active")
    path = Path(adapter_dir) / rel
    if not path.is_file():
        raise HooksError(f"declared hooks file missing: {path}")
    spec = importlib.util.spec_from_file_location(
        f"_adapter_hooks_{Path(adapter_dir).name}", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 - surface, never run stock silently
        raise HooksError(f"hooks failed to load: {path}: {e}") from e
    hooks = getattr(mod, "HOOKS", None)
    if not isinstance(hooks, RebaseHooks):
        raise HooksError(f"{path} must export HOOKS, a RebaseHooks instance")
    return hooks
