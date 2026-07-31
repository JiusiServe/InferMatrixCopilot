"""Rebase-mode governance — Rev 8 §2.1, the ONE authority for what a
`repo_rebase` run may do.

`params.rebase_mode` is the only authoritative mode source; **`full` (and
every mutating mode) can only ever be selected explicitly** — no omission or
boolean widens permissions. `spec.report_only=True` (explicit phrasing) is a
narrowing veto: combined with any mutating mode it BLOCKS rather than
guessing which of the two the operator meant.

Truth table (spec.report_only × params.rebase_mode), pinned row-by-row:

| report_only | unset        | report_only | full    | local_ci | remote_ci |
|-------------|--------------|-------------|---------|----------|-----------|
| False       | report_only  | report_only | full    | local_ci | remote_ci |
| True        | report_only  | report_only | BLOCKED | BLOCKED  | BLOCKED   |

`resolve_effective_mode` also WRITES BACK: the canonical mode lands in
`spec.params["rebase_mode"]` and `spec.report_only` is set to
`(mode == report_only)`, so every existing TaskSpec-derived consumer
(read_only/confirm gates, tracing, push policy, finalization) sees the same
truth with no second authority.
"""

from __future__ import annotations

from typing import Mapping

MODES = ("report_only", "full", "local_ci", "remote_ci")
MUTATING_MODES = ("full", "local_ci", "remote_ci")


class ModeConflictError(ValueError):
    """Narrowing (`report_only=True`) combined with a mutating mode —
    conflicting intent is refused, never resolved by guessing."""


def resolve_effective_mode(spec) -> str:
    """Resolve and WRITE BACK the canonical mode on `spec` (a TaskSpec-like
    object with `.params: dict` and `.report_only: bool`). Raises
    `ModeConflictError` on the BLOCKED rows and on an unknown mode string."""
    raw = (spec.params.get("rebase_mode") or "").strip()
    if raw and raw not in MODES:
        raise ModeConflictError(
            f"unknown rebase_mode {raw!r} — one of {', '.join(MODES)}")
    mode = raw or "report_only"
    if spec.report_only and mode in MUTATING_MODES:
        raise ModeConflictError(
            f"report_only=true conflicts with rebase_mode={mode} — narrowing "
            "beats widening; drop one of the two")
    spec.params["rebase_mode"] = mode
    spec.report_only = (mode == "report_only")
    return mode


def mode_state_flags(mode: str) -> Mapping[str, bool]:
    """The `mode_*` flags seeded into run state — playbook `when:` gates use
    ONLY these (never raw params), pinned by the when-key hygiene test."""
    return {f"mode_{m}": (m == mode) for m in MODES}


def resolve_push_gate_conflict(params: Mapping) -> None:
    """Rev 8 Decision 3: `strict_push_gate=true` + `push_with_failures=true`
    is conflicting intent — BLOCKED with an explanation, narrowing wins."""
    if params.get("strict_push_gate") and params.get("push_with_failures"):
        raise ModeConflictError(
            "strict_push_gate=true and push_with_failures=true conflict — "
            "narrowing beats widening; drop one of the two")
