"""Merged owner maps can seed breadth reruns without synthetic stage records."""

import hashlib
import json
import subprocess
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.init_stages import run_stage
from infermatrix_copilot.kb_service.init_support import InitRecord

from test_kb_feature_discovery_integration import _artifacts, _record, _stage
from test_kb_init_knowledge import KnowledgeGateway
from test_kb_init_modules import CardGateway, _modules_lifecycle, _skeleton, _tree_at, _world_with_tools
from test_kb_init_skeleton import FakeGh, _commit, _runtime, _tree, world  # noqa: F401


ENV = {"ALLOW_PUSH": "1", "ALLOW_POST": "1", "KB_INIT_GIT_AUTHOR": "t <t@example.com>"}


def _merged_baseline(world):
    _world_with_tools(world)
    skeleton = _skeleton(world)
    files, report, path = _artifacts(skeleton.pin)
    policy = yaml.safe_load(files["adapters/toy/knowledge-coverage.yaml"])
    policy["core"]["roots"] = ["pkg/", "tools/"]
    files["adapters/toy/knowledge-coverage.yaml"] = yaml.safe_dump(policy)
    report["catalog_sha256"] = hashlib.sha256(files["adapters/toy/knowledge-coverage.yaml"].encode()).hexdigest()
    files[path] = json.dumps(report)
    _commit(world["origin"], {**_tree(skeleton), **files}, "merged skeleton and discovered catalog")
    return skeleton.pin, files, report, path


def test_explicit_existing_modules_uses_merged_catalog_without_local_skeleton(world):
    pin, _, report, _ = _merged_baseline(world)
    state = world["tmp"] / "existing"
    rt = _runtime(world, CardGateway(), state_dir=state)
    lifecycle = _modules_lifecycle(feature_discovery_required=True)
    legacy = run_stage(rt, lifecycle, "modules", dry_run=True, pin=pin)
    assert legacy.status == "blocked" and "run the skeleton stage first" in legacy.problems
    record = run_stage(rt, lifecycle, "modules", dry_run=True, pin=pin, from_existing=True)
    assert record.status == "dry_run", record.problems
    assert record.coverage["modules"]["after"] == 1
    assert record.discovery["catalog_binding"]["catalog_sha256"] == report["catalog_sha256"]
    assert not InitRecord.path(state, "toy", "skeleton").exists()


def test_existing_modules_cannot_replace_missing_merged_owner_map(world):
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "modules",
                       dry_run=True, from_existing=True)
    assert record.status == "blocked" and any("merged repository index" in p for p in record.problems)
    assert not gateway.calls
    assert not InitRecord.path(world["tmp"] / "state", "toy", "skeleton").exists()


@pytest.mark.parametrize("status", ["blocked", "dry_run"])
def test_existing_modules_preserves_local_skeleton_status_gate(world, status):
    pin, _, _, _ = _merged_baseline(world)
    state = world["tmp"] / "existing"
    InitRecord(stage="skeleton", repo="toy", pin=pin, status=status).save(state)
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway, state_dir=state, environ=ENV),
                       _modules_lifecycle(feature_discovery_required=True), "modules",
                       dry_run=False, pin=pin, from_existing=True)
    assert record.status == "blocked"
    assert any("skeleton" in p and ("blocked" in p or "dry run" in p) for p in record.problems)
    assert not gateway.calls


def test_existing_modules_preserves_unmerged_discovery_gate(world):
    pin, files, report, path = _merged_baseline(world)
    state = world["tmp"] / "existing"
    stage = _stage(world)
    stage.rt.state_dir = state
    discovery = _record(stage, files, report, path, status="published")
    discovery.pr = {"number": 42}
    discovery.save(state)
    gateway = CardGateway()
    rt = _runtime(world, gateway, state_dir=state,
                  gh_run=lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, b'{"state":"OPEN"}', b""))
    record = run_stage(rt, _modules_lifecycle(feature_discovery_required=True), "modules",
                       dry_run=True, pin=pin, from_existing=True)
    assert record.status == "blocked" and "merge the feature-discovery PR before continuing" in record.problems
    assert not gateway.calls
    assert not InitRecord.path(state, "toy", "skeleton").exists()


def test_knowledge_after_existing_modules_keeps_module_merge_gate_without_skeleton(world):
    pin, _, _, _ = _merged_baseline(world)
    state = world["tmp"] / "existing"
    lifecycle = _modules_lifecycle(feature_discovery_required=True)
    modules = run_stage(_runtime(world, CardGateway(), state_dir=state, environ=ENV, gh_run=FakeGh()),
                        lifecycle, "modules", dry_run=False, pin=pin, from_existing=True)
    assert modules.status == "published", modules.problems

    def pr_state(value):
        return lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, ('{"state":"' + value + '"}').encode(), b"")

    gateway = KnowledgeGateway()
    rt = _runtime(world, gateway, state_dir=state, gh_run=pr_state("OPEN"))
    modules.status = "blocked"
    modules.save(state)
    unfinished = run_stage(rt, lifecycle, "knowledge", dry_run=True, pin=pin, from_existing=True)
    assert unfinished.status == "blocked" and "the modules stage is blocked; finish it first" in unfinished.problems
    modules.status = "published"
    modules.save(state)
    waiting = run_stage(rt, lifecycle, "knowledge", dry_run=True, pin=pin, from_existing=True)
    assert waiting.status == "blocked" and any("merge the modules PR" in p for p in waiting.problems)
    assert not gateway.calls
    _commit(world["origin"], _tree_at(world, modules.pr["head_sha"]), "merge breadth rerun")
    rt.gh_run = pr_state("MERGED")
    record = run_stage(rt, lifecycle, "knowledge", dry_run=True, pin=pin, from_existing=True)
    assert record.status == "dry_run", record.problems
    assert record.coverage["knowledge"]["total_owners"] == 2
    assert record.discovery["catalog_binding"] == modules.discovery["catalog_binding"]
    assert not InitRecord.path(state, "toy", "skeleton").exists()


def test_modules_cli_forwards_existing_baseline_flag(monkeypatch, tmp_path):
    from infermatrix_copilot.kb_service.cli import main
    from infermatrix_copilot.kb_service import runner

    calls = []

    def run(*args, **kwargs):
        calls.append(kwargs["params"])
        return SimpleNamespace(status="done"), tmp_path

    monkeypatch.setattr(runner, "run_playbook", run)
    assert main(["--state-dir", str(tmp_path), "init", "toy", "--stage", "modules",
                 "--from-existing", "--pin", "a" * 40, "--dry-run"]) == 0
    assert calls == [{"stage": "modules", "dry_run": "true", "pin": "a" * 40, "from_existing": "true"}]
