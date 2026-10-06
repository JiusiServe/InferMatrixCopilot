"""Portable CLI adapters and incremental batches on real committed sources."""
import json
import subprocess
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.git_source import GitSource
from infermatrix_copilot.kb_service.init_support import InitRecord
from infermatrix_copilot.kb_service.portable_commands import incremental_update, run_portable_init
from infermatrix_copilot.kb_service.repo_spec import RepoRegistry, RepoSpec, acceptance_receipt, propose_repository


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


def _registered(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    (root / "api.py").write_text("def api(): return 1\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "API")
    source = GitSource(root)
    spec = RepoSpec.from_dict(propose_repository(source, repo_id="api-library")["spec"])
    state = tmp_path / "state"
    RepoRegistry(state).register(spec, acceptance_receipt(spec, source, source.head(), accepted=True),
        source_path=root, knowledge_root=tmp_path / "canonical/knowledge")
    return state, source, spec


def test_knowledge_only_source_commit_does_not_start_discovery(tmp_path):
    state, source, spec = _registered(tmp_path)
    generated = source.path / ".infermatrix/knowledge/repos/api-library"
    generated.mkdir(parents=True)
    (generated / "_index.md").write_text("Generated knowledge\n")
    _git(source.path, "add", ".")
    _git(source.path, "commit", "-qm", "Knowledge mirror only")
    report = incremental_update(state, spec.repo_id, "HEAD", apply=True)
    assert report["implementation_unchanged"] is True
    assert report["effective_changed_paths"] == []
    assert not (state / "batches").exists()
    assert RepoRegistry(state).get(spec.repo_id)["spec"]["source_pin"] == spec.source_pin


def test_incremental_batch_pins_new_source_and_reports_deleted_paths(tmp_path):
    state, source, spec = _registered(tmp_path)
    (source.path / "api.py").unlink()
    (source.path / "new.langx").write_text("public function new_contract() {}\n")
    _git(source.path, "add", "-A")
    _git(source.path, "commit", "-qm", "New public contract")
    report = incremental_update(state, spec.repo_id, "HEAD", apply=True)
    assert report["changed_paths"] == ["api.py", "new.langx"]
    assert report["scan_paths"] == ["new.langx"]
    assert report["init_complete"] is False
    batch = state / "batches" / spec.repo_id / source.head()
    assert RepoRegistry(batch).get(spec.repo_id)["spec"]["source_pin"] == source.head()
    assert RepoRegistry(state).get(spec.repo_id)["spec"]["source_pin"] == spec.source_pin
    assert json.loads((batch / "incremental.json").read_text())["from_pin"] == spec.source_pin


@pytest.mark.parametrize("explicit,expected", [(False, "lightweight"), (True, "strict")])
def test_portable_defaults_do_not_override_explicit_strict_mode(tmp_path, monkeypatch, explicit, expected):
    import infermatrix_copilot.kb_service.portable_commands as commands
    import infermatrix_copilot.kb_service.init_stages as stages
    pin = "a" * 40
    runtime = SimpleNamespace(generator=SimpleNamespace(provider="zcode"),
        portable_spec=SimpleNamespace(source_pin=pin))
    monkeypatch.setattr(commands, "portable_runtime", lambda *a: (runtime, SimpleNamespace(repo="library")))
    captured = {}
    def run(*a, **kwargs):
        captured.update(kwargs)
        return InitRecord("knowledge-deepen", "library", pin=pin, status="dry_run")
    monkeypatch.setattr(stages, "run_stage", run)
    args = SimpleNamespace(repo="library", stage="knowledge-deepen", suggest_seeds=False,
        pin=None, budget_usd=None, acceptance_mode="strict", acceptance_mode_explicit=explicit,
        foundation_mode="strict", from_existing=False, retry_unfinished=False,
        subscription_generator=False, unlimited_subscription=False, pr_count=None)
    assert run_portable_init(args, tmp_path) == 0
    assert captured["acceptance_mode"] == expected
    assert captured["unlimited_subscription"] is True
    assert captured["foundation_mode"] == "partial"
