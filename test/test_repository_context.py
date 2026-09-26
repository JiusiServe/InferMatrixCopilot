from pathlib import Path

import pytest

from infermatrix_copilot.app.core import Copilot
from infermatrix_copilot.app.repository_context import RepositoryContextResolver
from infermatrix_copilot.notify import BLOCKED_EXIT
from infermatrix_copilot.task_spec import TaskSpec


def _adapter(settings, checkout: Path, *, branches: str = "[main]") -> Path:
    root = settings.adapters_dir / "vllm_omni"
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "manifest.yaml"
    manifest.write_text(
        "name: vllm_omni\nstatus: active\nrepo:\n"
        f"  path: {checkout}\n"
        "modules:\n  scheduler:\n    risk: high\n"
        f"push:\n  protected_branches: {branches}\n"
    )
    return manifest


def test_planning_and_execution_context_share_checkout_and_adapter_policy(
    settings, tmp_path,
):
    ambient = tmp_path / "ambient"
    frozen = tmp_path / "frozen"
    _adapter(settings, ambient, branches="[main, release]")
    spec = TaskSpec(kind="repo_rebase", repo="vllm-omni", repo_path=str(frozen))

    context = RepositoryContextResolver(settings).for_spec(spec)

    assert context.repo_path == str(frozen)
    assert "repo.path" in context.capabilities
    assert context.protected_branches == ("main", "release")
    assert context.high_risk_modules == ("scheduler",)


@pytest.mark.parametrize("manifest", (
    "{not yaml: [",
    "name: vllm_omni\nrepo: []\n",
    "name: vllm_omni\nrepo: {}\npush: []\n",
    "name: vllm_omni\nrepo:\n  path: 123\n",
    "name: vllm_omni\nrepo: {}\ncapabilities: reviewer\n",
    "name: vllm_omni\nrepo: {}\nmodules: []\n",
    "name: vllm_omni\nrepo: {}\npush:\n  protected_branches: main\n",
))
def test_known_broken_adapter_blocks_execution_before_run_artifacts(
    settings, tmp_path, manifest,
):
    bad = settings.adapters_dir / "vllm_omni"
    bad.mkdir(parents=True)
    (bad / "manifest.yaml").write_text(manifest)
    copilot = Copilot(settings)
    run_dir = tmp_path / "run-bad-adapter"

    code = copilot._execute(None, TaskSpec(kind="repo_rebase"), run_dir)

    assert code == BLOCKED_EXIT
    assert "repository context invalid" in copilot.last_blocked_reason
    assert not run_dir.exists()
    assert copilot.run_task(TaskSpec(kind="repo_rebase")) == BLOCKED_EXIT


def test_adapter_policy_change_after_planning_blocks_execution(
    settings, tmp_path,
):
    manifest = _adapter(settings, tmp_path / "checkout")
    spec = TaskSpec(kind="repo_rebase", repo="vllm-omni")
    copilot = Copilot(settings)
    planned = copilot.repository_context.for_spec(spec)
    manifest.write_text(manifest.read_text().replace("[main]", "[main, release]"))
    run_dir = tmp_path / "run-changed-policy"

    code = copilot._execute(None, spec, run_dir, planned_context=planned)

    assert code == BLOCKED_EXIT
    assert copilot.last_blocked_reason == "repository context changed after planning"
    assert not run_dir.exists()


def test_unresolved_adapter_path_does_not_claim_checkout_capability(
    settings, tmp_path, monkeypatch,
):
    monkeypatch.delenv("IMX_TEST_MISSING_REPOSITORY_PATH", raising=False)
    _adapter(settings, tmp_path / "unused")
    manifest = settings.adapters_dir / "vllm_omni" / "manifest.yaml"
    manifest.write_text(manifest.read_text().replace(
        str(tmp_path / "unused"), "${IMX_TEST_MISSING_REPOSITORY_PATH}"))

    context = RepositoryContextResolver(settings).for_spec(
        TaskSpec(kind="repo_rebase", repo="vllm-omni"))

    assert context.repo_path == ""
    assert "repo.path" not in context.capabilities
