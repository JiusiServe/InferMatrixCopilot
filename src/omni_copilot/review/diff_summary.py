"""Cheap deterministic diff summary — the always-on first stage of Patch Review.

The LLM review agent is only invoked when this summary trips a trigger rule.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from ..run_trace import RunTrace


@dataclass
class DiffSummary:
    changed_files: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    out_of_scope_files: list[str] = field(default_factory=list)
    full_file_writes: list[str] = field(default_factory=list)
    tests_run: list[str] = field(default_factory=list)
    push_requested: bool = False

    @property
    def total_lines(self) -> int:
        return self.insertions + self.deletions


def build_diff_summary(
    repo_path: str | Path,
    *,
    base_ref: str = "HEAD",
    primary_files: tuple[str, ...] = (),
    trace: RunTrace | None = None,
) -> DiffSummary:
    summary = DiffSummary()
    out = subprocess.run(
        ["git", "diff", "--numstat", base_ref],
        cwd=str(repo_path), capture_output=True, text=True, timeout=60,
    )
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        ins, dels, path = parts
        summary.changed_files.append(path)
        summary.insertions += int(ins) if ins.isdigit() else 0
        summary.deletions += int(dels) if dels.isdigit() else 0
        if primary_files and not any(fnmatch(path, p) for p in primary_files):
            summary.out_of_scope_files.append(path)

    if trace is not None:
        summary.out_of_scope_files.extend(
            e["path"] for e in trace.events("out_of_scope_edit")
            if e.get("path") and e["path"] not in summary.out_of_scope_files
        )
        summary.full_file_writes = [e["path"] for e in trace.events("full_file_write")]
        summary.tests_run = [e.get("command", "") for e in trace.events("test_run")]
        summary.push_requested = any(True for _ in trace.events("push_requested"))
    return summary
