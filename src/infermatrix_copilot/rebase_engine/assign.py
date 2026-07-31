"""Commit → module assignment — the deterministic core of `40_assign_commits.sh`.

Path-based classification: for each module, the commits in
``baseline..head`` touching its upstream paths (adapter data). Modules with
zero commits are marked skippable. The agent double-check pass (parent's
"Pass 2") is an agent step wired in the assembly PR; this module deliberately
contains only the deterministic passes and the report rendering.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence


def _log(msg: str) -> None:
    print(f"[assign] {msg}", flush=True)


def _git(repo: Path, *args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=str(repo), check=False,
                          text=True, capture_output=True, errors="replace")


def check_path_drift(repo: Path, module_paths: Mapping[str, Sequence[str]],
                     ) -> list[tuple[str, str]]:
    """Upstream may rename/move directories between rebases: report every
    configured module path that no longer exists in the tree as
    ``(module, path)`` (trailing slash ignored for the existence test)."""
    repo = Path(repo)
    missing: list[tuple[str, str]] = []
    for module, paths in module_paths.items():
        for entry in paths:
            if not (repo / entry.rstrip("/")).exists():
                missing.append((module, entry))
    return missing


def render_drift_report(head_short: str,
                        missing: Sequence[tuple[str, str]]) -> str:
    lines = [
        "# Path Mapping Drift Check",
        "",
        f"Checking module upstream paths against current tree at `{head_short}`.",
        "",
    ]
    if not missing:
        lines.append("All paths valid.")
    else:
        lines += [f"- **MISSING**: `{path}` (module: {module})"
                  for module, path in missing]
    return "\n".join(lines) + "\n"


@dataclass
class Assignment:
    """Path-based commit classification over ``baseline..head``."""

    baseline: str
    head: str
    target_branch: str
    total_commits: int
    commits_by_module: dict[str, list[str]] = field(default_factory=dict)
    skip: dict[str, bool] = field(default_factory=dict)
    missing_paths: list[tuple[str, str]] = field(default_factory=list)
    base_class_commits: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {m: len(c) for m, c in self.commits_by_module.items()}


def assign_commits(repo: Path, baseline: str,
                   module_paths: Mapping[str, Sequence[str]], *,
                   target_branch: str = "",
                   base_class_watch_paths: Sequence[str] = (),
                   log: Callable[[str], None] = _log) -> Assignment:
    """Classify every commit in ``baseline..HEAD`` into modules by the paths
    it touches (one commit may land in several modules — that is deliberate:
    each module's rebase wave needs to see it)."""
    repo = Path(repo)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    range_spec = f"{baseline}..HEAD"
    total_out = _git(repo, "log", "--oneline", range_spec).stdout
    total = len([ln for ln in total_out.splitlines() if ln.strip()])
    log(f"Analyzing {total} commits from {baseline[:12]}..{head[:12]}")

    result = Assignment(baseline=baseline, head=head,
                        target_branch=target_branch, total_commits=total,
                        missing_paths=check_path_drift(repo, module_paths))
    for module, path in result.missing_paths:
        log(f"  WARNING: path '{path}' for module '{module}' does not exist in tree")

    for module, paths in module_paths.items():
        r = _git(repo, "log", "--oneline", range_spec, "--", *paths)
        commits = [ln for ln in r.stdout.splitlines() if ln.strip()]
        result.commits_by_module[module] = commits
        result.skip[module] = not commits
        log(f"  {module}: {len(commits)} commits"
            + (" (will skip)" if not commits else ""))

    if base_class_watch_paths:
        r = _git(repo, "log", "--oneline", range_spec, "--",
                 *base_class_watch_paths)
        result.base_class_commits = [ln for ln in r.stdout.splitlines()
                                     if ln.strip()]
    return result


def render_assignment_report(assignment: Assignment, *,
                             repo_label: str = "Upstream",
                             path_sync_report: str = "") -> str:
    """Markdown report, structure-parity with the parent's
    commits_assignment.md (module sections in map order, base-class section
    last, optional embedded path-sync snapshot)."""
    a = assignment
    lines = [
        f"# {repo_label} Commits Assignment Report",
        "",
        f"- Last rebase commit: `{a.baseline}`",
        f"- Current HEAD: `{a.head}`",
        f"- Target branch: `{a.target_branch}`",
        f"- Total commits: {a.total_commits}",
    ]
    if a.missing_paths:
        lines.append(f"- **WARNING**: {len(a.missing_paths)} path mapping(s) "
                     "missing — see path_drift_check.md")
    lines += ["", "## Module Path Sync Snapshot", ""]
    if path_sync_report:
        lines += ["Path mappings were finalized in Phase 1.", "",
                  path_sync_report.rstrip(), ""]
    else:
        lines += ["_No path sync report found for this run._", ""]

    for module, commits in a.commits_by_module.items():
        lines += [f"## {module} ({len(commits)} commits)", ""]
        if commits:
            lines += ["```", *commits, "```"]
        else:
            lines.append("(no relevant commits)")
        lines.append("")

    lines += ["## Base Class Inheritance Changes", "", "```"]
    lines += a.base_class_commits if a.base_class_commits else ["(none)"]
    lines += ["```", ""]
    return "\n".join(lines)
