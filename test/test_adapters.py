import subprocess

import pytest
import yaml

from infermatrix_copilot.adapters import (
    AdapterError,
    AdapterRegistry,
    draft_adapter,
    fingerprint_repo,
    load_adapter,
    update_manifest,
)

MANIFEST_YAML = """\
name: vllm_omni
status: active
repo:
  path: {repo_path}
  default_branch: main
modules:
  scheduler:
    local_paths: [vllm_omni/core/]
push:
  default_remote: origin
  protected_branches: [main]
"""


@pytest.fixture()
def adapter_dir(settings, git_repo):
    d = settings.adapters_dir / "vllm_omni"
    d.mkdir(parents=True)
    (d / "manifest.yaml").write_text(MANIFEST_YAML.format(repo_path=git_repo))
    return d


def test_load_and_accessors(adapter_dir, git_repo):
    p = load_adapter(adapter_dir)
    assert p.name == "vllm_omni" and p.status == "active"
    assert p.protected_branches == ["main"]
    assert p.module_for_path("vllm_omni/core/sched.py") == "scheduler"
    assert p.module_for_path("docs/readme.md") is None


def test_registry_resolution(settings, adapter_dir, git_repo):
    reg = AdapterRegistry(settings.adapters_dir)
    assert reg.resolve(name="vllm_omni").name == "vllm_omni"
    assert reg.resolve(name="vllm-omni").name == "vllm_omni"
    assert reg.resolve(repo_path=str(git_repo)).name == "vllm_omni"
    assert reg.resolve(repo_path="/nonexistent") is None
    with pytest.raises(AdapterError):
        reg.resolve(name="missing")


def test_high_risk_sections_are_human_only(adapter_dir):
    p = load_adapter(adapter_dir)
    with pytest.raises(AdapterError, match="high-risk"):
        update_manifest(p, "push", {"protected_branches": []}, actor="agent")
    # human may
    update_manifest(p, "push", {"protected_branches": ["main", "release"]}, actor="human")
    assert load_adapter(adapter_dir).protected_branches == ["main", "release"]
    # agent may update low-risk sections
    update_manifest(p, "modules", {"platform": {"local_paths": ["vllm_omni/platforms/"]}},
                    actor="agent")
    assert "platform" in load_adapter(adapter_dir).modules


def test_bootstrap_draft_stops_and_never_touches_repo(settings, git_repo):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=git_repo,
                            capture_output=True, text=True, check=False).stdout
    fp = fingerprint_repo(git_repo)
    assert fp["language"] == "python" and fp["default_branch"] == "main"

    root = draft_adapter(fp, settings.adapters_dir)
    manifest = yaml.safe_load((root / "manifest.yaml").read_text())
    assert manifest["status"] == "draft"
    assert manifest["push"]["allowed"] is False
    assert (root / "BOOTSTRAP_REPORT.md").exists()

    after = subprocess.run(["git", "status", "--porcelain"], cwd=git_repo,
                           capture_output=True, text=True, check=False).stdout
    assert before == after  # target repo untouched


def test_shipped_adapter_zero_parses():
    from infermatrix_copilot.config import _REPO_ROOT

    p = load_adapter(_REPO_ROOT / "adapters" / "vllm_omni")
    assert p.name == "vllm_omni"
    assert p.manifest["push"]["allowed"] is False
    assert "main" in p.protected_branches
    assert p.module_for_path("vllm_omni/core/scheduler.py") == "scheduler"


def test_shipped_afd_adapter_parses_and_resolves_alias():
    from infermatrix_copilot.config import _REPO_ROOT

    p = load_adapter(_REPO_ROOT / "adapters" / "afd_plugin")
    assert p.name == "afd_plugin"
    assert p.manifest["repo"]["full_name"] == "vllm-project/afd-plugin"
    assert p.manifest["ci"]["provider"] == "github_actions"
    assert p.manifest["push"]["allowed"] is False
    assert p.matches_name("afd-plugin")
    assert p.matches_name("vllm-project/afd-plugin")
    assert p.module_for_path("afd_plugin/compat/patches/config_validation.py") == "compat"
    assert p.module_for_path("afd_plugin/connectors/npu/camp2p.py") == \
        "connectors_distributed"
    assert p.module_for_path("afd_plugin/v1/worker/attention_worker.py") == \
        "workers_runners"
    assert p.module_for_path("csrc/npu/a2e/op_kernel/a2e.cpp") == "native_backends"
    assert p.review_routes

    reg = AdapterRegistry(_REPO_ROOT / "adapters")
    assert reg.resolve(name="afd-plugin").name == "afd_plugin"
    assert reg.resolve(name="vllm-project/afd-plugin").name == "afd_plugin"
