"""Conditional Patch-Review trigger rules (框架层改进建议 §3): review the diff
only in high-risk situations — cost stays near zero on clean runs.
"""

from __future__ import annotations

from ..config import Settings
from .diff_summary import DiffSummary

ALL_RULES = (
    "out_of_scope_edits",
    "high_risk_modules",
    "large_diff",
    "tests_unavailable",
    "full_file_fallback",
    "before_push",
    "knowledge_edit",
)


def evaluate_triggers(
    summary: DiffSummary,
    settings: Settings,
    *,
    touched_modules: tuple[str, ...] = (),
    pre_push: bool = False,
    knowledge_edit: bool = False,
) -> list[str]:
    fired: list[str] = []
    if summary.out_of_scope_files:
        fired.append("out_of_scope_edits")
    if any(m in settings.high_risk_modules for m in touched_modules):
        fired.append("high_risk_modules")
    if (summary.total_lines > settings.large_diff_lines
            or len(summary.changed_files) > settings.large_diff_files):
        fired.append("large_diff")
    if summary.changed_files and not summary.tests_run:
        fired.append("tests_unavailable")
    if summary.full_file_writes:
        fired.append("full_file_fallback")
    if pre_push or summary.push_requested:
        fired.append("before_push")
    if knowledge_edit:
        fired.append("knowledge_edit")
    return fired
