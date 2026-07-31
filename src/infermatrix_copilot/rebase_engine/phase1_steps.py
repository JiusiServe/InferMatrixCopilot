"""Phase-1 analysis composition — the deterministic PR2 modules assembled
into the units the v3 step set will wire (assembly PR). Each function is
substate-in, substate+reports-out; nothing here talks to an LLM.

Report artifacts keep the parent's filenames (`commits_assignment.md`,
`path_drift_check.md`, `path_sync_report.md`) so downstream prompts and
humans find them where they always were."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from . import assign, path_sync
from .substate import Substate


@dataclass(frozen=True)
class Phase1Config:
    upstream_repo: Path
    target_repo: Path
    log_dir: Path
    baseline_commit: str
    target_branch: str = ""
    repo_label: str = "Upstream"
    base_class_watch_paths: Sequence[str] = ()


def run_commit_assignment(config: Phase1Config,
                          module_upstream_paths: Mapping[str, Sequence[str]],
                          substate: Substate) -> assign.Assignment:
    """Task 40's deterministic passes: drift check + path-based
    classification, reports written, per-module skip flags into substate.
    The agent double-check pass layers on top in the assembly PR."""
    result = assign.assign_commits(
        config.upstream_repo, config.baseline_commit,
        module_upstream_paths, target_branch=config.target_branch,
        base_class_watch_paths=tuple(config.base_class_watch_paths))
    config.log_dir.mkdir(parents=True, exist_ok=True)
    (config.log_dir / "path_drift_check.md").write_text(
        assign.render_drift_report(result.head[:12], result.missing_paths),
        encoding="utf-8")
    sync_report = ""
    sync_path = config.log_dir / "path_sync_report.md"
    if sync_path.is_file():
        sync_report = sync_path.read_text(encoding="utf-8")
    (config.log_dir / "commits_assignment.md").write_text(
        assign.render_assignment_report(result, repo_label=config.repo_label,
                                        path_sync_report=sync_report),
        encoding="utf-8")
    substate.update({"modules": {m: {"skip": skip}
                                 for m, skip in result.skip.items()}})
    return result


def run_path_sync(config: Phase1Config, manifest_path: Path,
                  current_maps: Mapping[str, Mapping[str, Sequence[str]]],
                  curated: Mapping[str, Mapping[str, path_sync.CuratedEntry]],
                  substate: Substate) -> dict:
    """Task 35's deterministic pass: filter + curated merge per field, the
    manifest retargeted surgically, report written. The L2 final-decision
    agent pass (validated by `path_sync.apply_decision`) lands with the
    assembly PR."""
    updates: dict = {}
    for field, current in current_maps.items():
        synced = path_sync.sync_path_map(config.target_repo, current,
                                         curated.get(field))
        updates[field] = synced
    changed = path_sync.rewrite_manifest_modules(
        manifest_path,
        {module: {field: updates[field][module]
                  for field in updates if module in updates[field]}
         for module in {m for f in updates.values() for m in f}})
    config.log_dir.mkdir(parents=True, exist_ok=True)
    (config.log_dir / "path_sync_report.md").write_text(
        path_sync.render_sync_report(config.target_repo, updates,
                                     source="deterministic sync"),
        encoding="utf-8")
    substate.update({"phase1": {"path_sync": {"changed": changed}}})
    return updates
