import subprocess

import pytest
import yaml

from omni_copilot.plugins import (
    PluginError,
    PluginRegistry,
    draft_plugin,
    fingerprint_repo,
    load_plugin,
    update_manifest,
)

PLUGIN_YAML = """\
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
def plugin_dir(settings, git_repo):
    d = settings.plugins_dir / "vllm_omni"
    d.mkdir(parents=True)
    (d / "plugin.yaml").write_text(PLUGIN_YAML.format(repo_path=git_repo))
    return d


def test_load_and_accessors(plugin_dir, git_repo):
    p = load_plugin(plugin_dir)
    assert p.name == "vllm_omni" and p.status == "active"
    assert p.protected_branches == ["main"]
    assert p.module_for_path("vllm_omni/core/sched.py") == "scheduler"
    assert p.module_for_path("docs/readme.md") is None


def test_registry_resolution(settings, plugin_dir, git_repo):
    reg = PluginRegistry(settings.plugins_dir)
    assert reg.resolve(name="vllm_omni").name == "vllm_omni"
    assert reg.resolve(repo_path=str(git_repo)).name == "vllm_omni"
    assert reg.resolve(repo_path="/nonexistent") is None
    with pytest.raises(PluginError):
        reg.resolve(name="missing")


def test_high_risk_sections_are_human_only(plugin_dir):
    p = load_plugin(plugin_dir)
    with pytest.raises(PluginError, match="high-risk"):
        update_manifest(p, "push", {"protected_branches": []}, actor="agent")
    # human may
    update_manifest(p, "push", {"protected_branches": ["main", "release"]}, actor="human")
    assert load_plugin(plugin_dir).protected_branches == ["main", "release"]
    # agent may update low-risk sections
    update_manifest(p, "modules", {"platform": {"local_paths": ["vllm_omni/platforms/"]}},
                    actor="agent")
    assert "platform" in load_plugin(plugin_dir).modules


def test_bootstrap_draft_stops_and_never_touches_repo(settings, git_repo):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=git_repo,
                            capture_output=True, text=True).stdout
    fp = fingerprint_repo(git_repo)
    assert fp["language"] == "python" and fp["default_branch"] == "main"

    root = draft_plugin(fp, settings.plugins_dir)
    manifest = yaml.safe_load((root / "plugin.yaml").read_text())
    assert manifest["status"] == "draft"
    assert manifest["push"]["allowed"] is False
    assert (root / "BOOTSTRAP_REPORT.md").exists()

    after = subprocess.run(["git", "status", "--porcelain"], cwd=git_repo,
                           capture_output=True, text=True).stdout
    assert before == after  # target repo untouched


def test_shipped_plugin_zero_parses():
    from omni_copilot.config import _REPO_ROOT

    p = load_plugin(_REPO_ROOT / "plugins" / "vllm_omni")
    assert p.name == "vllm_omni"
    assert p.manifest["push"]["allowed"] is False
    assert "main" in p.protected_branches
    assert p.module_for_path("vllm_omni/core/scheduler.py") == "scheduler"
