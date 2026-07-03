import shutil

import pytest

from omni_copilot.cli import Copilot
from omni_copilot.config import _REPO_ROOT
from omni_copilot.task_spec import TaskSpec


@pytest.fixture()
def copilot(settings, git_repo):
    # ship the real playbooks into the sandbox store
    settings.playbooks_dir.mkdir(parents=True)
    shutil.copy(_REPO_ROOT / "playbooks" / "repo-rebase.yaml",
                settings.playbooks_dir / "repo-rebase.yaml")
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    return Copilot(settings)


def test_shipped_repo_rebase_playbook_resolves_L0(copilot):
    res = copilot.resolve(TaskSpec(kind="repo_rebase"))
    assert res.mode == "reuse" and res.tier == "L0" and res.playbook.locked


def test_plan_only_never_executes(copilot, capsys):
    code = copilot.run_task(TaskSpec(kind="repo_rebase"), plan_only=True)
    assert code == 0
    out = capsys.readouterr().out
    assert "reuse repo-rebase@2 (locked)" in out
    assert not (copilot.settings.run_root.exists()
                and list(copilot.settings.run_root.iterdir()))


def test_end_to_end_locked_run(copilot, capsys, monkeypatch):
    # make the external orchestrator a harmless echo for the test
    copilot.settings.rebase_orchestrator_cmd = "echo dry-run-rebase-ok"
    code = copilot.run_task(TaskSpec(kind="repo_rebase"), assume_yes=True)
    assert code == 0
    out = capsys.readouterr().out
    assert "✓ guard" in out and "✓ rebase" in out and "✓ report" in out
    run_dirs = list(copilot.settings.run_root.iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "RUN_REPORT.md").exists()
    assert (run_dirs[0] / "run_trace.jsonl").exists()
    assert copilot.status().startswith(run_dirs[0].name)


def test_blocked_run_exits_3_and_escalates(copilot, git_repo):
    (git_repo / "dirty.txt").write_text("x")  # guard_clean will block
    code = copilot.run_task(TaskSpec(kind="repo_rebase"), assume_yes=True)
    assert code == 3
    run_dir = list(copilot.settings.run_root.iterdir())[0]
    assert (run_dir / "ESCALATION.md").exists()
    assert "workspace dirty" in (run_dir / "ESCALATION.md").read_text()
