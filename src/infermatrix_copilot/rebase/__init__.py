"""Rebase subsystem: read-only observability over the external parent
rebase-agent pipeline. Re-exports the public surface (`build_command`,
`build_escalation`, `classify_failure`, `diff_progress`, `parse_parent_state`,
`summarize_progress`) so callers import from the package, not its modules."""

from .monitor import (  # noqa: F401
    build_command,
    build_escalation,
    classify_failure,
    diff_progress,
    parse_parent_state,
    summarize_progress,
)
