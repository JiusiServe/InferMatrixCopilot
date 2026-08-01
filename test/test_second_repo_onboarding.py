"""Second-repo onboarding proof (2026-08-01 GPT neutrality audit).

The acceptance bar for the repo-neutrality invariant: a SECOND repo
onboards purely via `adapters/<repo>/` + configuration — ZERO commits to
`src/`. This suite builds a synthetic "widgetlib" adapter that differs
from adapter zero in every axis the audit flagged as a hidden
assumption:

- default branch `master` on remote `upstream` (not origin/main)
- CI yaml under `ci/pipelines/` (not .buildkite/cuda)
- test changes under `checks/` (not tests/)
- NO wheel workflow, NO runtime venv, NO precommit declared
- its own module names and routing

and drives the PRODUCTION pipeline over it: manifest build with change
classification against the adapter's baseline ref, and the v3 playbook
report_only + local_ci runs end-to-end through the real executor."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.rebase_engine.modes import resolve_effective_mode
from infermatrix_copilot.rebase_engine.substate import Substate
from infermatrix_copilot.rebase_engine.test_manifest import (ManifestSpec,
                                                             build_manifest)

REPO_ROOT = Path(__file__).resolve().parents[1]

WIDGET_MANIFEST = {
    "name": "widgetlib",
    "status": "active",
    "created_by": "human",
    "schema_version": 1,
    "repo": {"path": "${WIDGETLIB_REPO}", "default_branch": "master",
             "remote": "upstream", "language": "go"},
    "upstream": {"kind": "fork_tracking",
                 "repo_path": "${WIDGETLIB_UPSTREAM}", "remote": "origin"},
    "modules": {
        "parser": {"local_paths": ["widget/parser/"],
                   "upstream_paths": ["lib/parser/"],
                   "test_paths": ["checks/parser/"], "wave": 1},
        "renderer": {"local_paths": ["widget/render/"],
                     "upstream_paths": ["lib/render/"],
                     "test_paths": ["checks/render/"], "wave": 2},
    },
    "rebase": {
        "lock_name": "widgetlib",
        "test_manifest": {
            "yaml_dir": "ci/pipelines",
            "pipelines": {"merge.yml": "merge", "ready.yml": "ready"},
            "queue_map": {"cpu_queue": [0, "any"]},
            "default_queue": "cpu_queue",
            "file_ref_prefixes": ["checks", "widget"],
            "file_tree_roots": ["checks", "widget"],
            "test_change_roots": ["checks/"],
        },
    },
}


def _git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def widget_env(settings, tmp_path, monkeypatch):
    import shutil
    from infermatrix_copilot.engine.executor import Executor
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.playbooks.store import PlaybookStore
    from infermatrix_copilot.run_trace import RunTrace

    # a bare "upstream" the baseline ref points at, then the working clone
    origin = tmp_path / "widget-origin"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "master")
    (origin / "ci" / "pipelines").mkdir(parents=True)
    (origin / "checks" / "parser").mkdir(parents=True)
    (origin / "widget" / "parser").mkdir(parents=True)
    (origin / "ci" / "pipelines" / "merge.yml").write_text(yaml.safe_dump({
        "steps": [{"label": "Parser Checks", "timeout_in_minutes": 1,
                   "commands": ["export WIDGET_MODE=fast",
                                "echo checks/parser/run_check.sh"]}]}))
    (origin / "checks" / "parser" / "baseline.txt").write_text("v1\n")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-qm", "seed")
    repo = tmp_path / "widgetlib"
    subprocess.run(["git", "clone", "-q", "--origin", "upstream",
                    str(origin), str(repo)], check=True)
    # a NEW test change relative to upstream/master, under checks/
    (repo / "checks" / "parser" / "new_check.txt").write_text("n\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add check")

    adir = Path(settings.adapters_dir) / "widgetlib"
    adir.mkdir(parents=True, exist_ok=True)
    (adir / "manifest.yaml").write_text(yaml.safe_dump(WIDGET_MANIFEST))
    monkeypatch.setenv("WIDGETLIB_REPO", str(repo))
    monkeypatch.setenv("WIDGETLIB_UPSTREAM", str(origin))
    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "playbooks" / "repo-rebase-v3.yaml",
                settings.playbooks_dir / "repo-rebase-v3.yaml")
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(settings.playbooks_dir, registry)

    def make_run(name):
        run_dir = tmp_path / name
        run_dir.mkdir()
        return Executor(registry, settings, run_dir=run_dir,
                        trace=RunTrace(run_dir / "trace.jsonl")), run_dir

    return SimpleNamespace(repo=repo, origin=origin,
                           playbook=store.get("repo-rebase-v3"),
                           make_run=make_run)


def _state_for(env, run_dir, mode):
    spec = SimpleNamespace(params={"rebase_mode": mode}, report_only=False)
    resolve_effective_mode(spec)
    return {"task_spec": {"kind": "repo_rebase", "repo": "widgetlib",
                          "mode": "eco", "params": spec.params},
            "repo_path": str(env.repo), "run_id": run_dir.name}


def test_widgetlib_manifest_builds_with_adapter_baseline(widget_env):
    """Change classification diffs against the ADAPTER's baseline
    (upstream/master) over the adapter's test roots (checks/) — the
    audit's hardcoded origin/main + tests/ would have found nothing."""
    spec = ManifestSpec.from_manifest(WIDGET_MANIFEST)
    assert spec.baseline_ref == "upstream/master"
    assert spec.test_change_roots == ("checks/",)
    built = build_manifest(widget_env.repo, spec)
    assert [j.slug for j in built.jobs] == ["parser_checks"]
    job = built.jobs[0]
    assert job.env == "WIDGET_MODE=fast"
    assert job.min_gpus == 0                       # cpu queue, no GPUs
    # the committed new check under checks/ is CLASSIFIED as a change
    assert [(c.path, c.change_type) for c in built.changes] == [
        ("checks/parser/new_check.txt", "added")]
    # routing falls back to test_paths (no assignment flavor declared)
    assert job.module == "parser"


def test_widgetlib_report_only_end_to_end(widget_env, settings):
    executor, run_dir = widget_env.make_run("run-widget-ro")
    outcome = asyncio.run(executor.run(
        widget_env.playbook, _state_for(widget_env, run_dir, "report_only")))
    assert outcome.status == "done", getattr(outcome, "blocked_reason", "")
    assert (run_dir / "test_manifest.json").exists()


def test_widgetlib_local_ci_end_to_end(widget_env, settings):
    """A COMPLETE local_ci run for the venv-less, wheel-less,
    precommit-less adapter: the pin precondition is data-gated off, test
    jobs run with the inherited environment (capability note traced),
    precommit records not_declared — done/exit-0 with ZERO src/
    changes."""
    from infermatrix_copilot.engine import lifecycle
    executor, run_dir = widget_env.make_run("run-widget-lci")
    outcome = asyncio.run(executor.run(
        widget_env.playbook, _state_for(widget_env, run_dir, "local_ci")))
    assert outcome.status == "done", getattr(outcome, "blocked_reason", "")
    data = Substate(run_dir, run_dir.name).read()
    assert data["tests"]["pipeline"]["passed"] == 1
    assert data["tests"]["precommit"]["result"] == "not_declared"
    assert data["phase"] == "done"
    asyncio.run(lifecycle.finalize(run_dir, outcome))
    # the adapter-named lock was used and released
    assert (widget_env.repo / "locks" / "widgetlib.lock").exists()