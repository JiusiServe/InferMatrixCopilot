import subprocess
from pathlib import Path

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.run_trace import RunTrace


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        run_root=tmp_path / "runs",
        playbooks_dir=tmp_path / "playbooks",
        adapters_dir=tmp_path / "adapters",
        repo_paths={},
        allow_push=False,
        rebase_agent_root=tmp_path / "agent_root",  # never the real one in tests
        rebase_poll_interval=1,
        skills_dir=tmp_path / "skills",  # never the shipped skills in tests
        memory_db=tmp_path / "memory.db",
        review_ensemble=False,  # ensemble tests opt in explicitly
        ensemble_parallel=False,  # ordered ScriptedLLM fakes need determinism;
                                  # the parallel path has its own keyed-fake test
        ensemble_samples_per_lens=1,  # sampling tests opt in explicitly
        ensemble_stagger_seconds=0,  # tests never sleep for cache warm-up
        ensemble_zero_yield_retry=False,  # scripted fakes opt in explicitly
        review_verify_comments=False,  # verify-pass tests opt in explicitly
        review_deep_engine=False,  # deep-pass tests opt in explicitly; the
                                   # legacy scripted fakes assume 4 lenses
        review_second_round=False,  # second-round tests opt in explicitly —
                                    # scripted fakes budget exact call counts
    )


@pytest.fixture()
def trace(tmp_path: Path) -> RunTrace:
    return RunTrace(tmp_path / "trace" / "run_trace.jsonl")




MINI_REBASE_PLAYBOOK = """\
# test-only minimal LOCKED repo_rebase playbook (the deleted v2's shape
# minus the external delegation, retired in the 2026-08-25 PR7 purge):
# generic steps only, so planner/CLI/queue/chat flows stay exercised
# without the heavy repo-rebase-v3 pipeline.
name: repo-rebase-mini
version: 1
status: locked
provenance:
  created_by: human
  source: test fixture (post-PR7 cutover)
task_kinds: [repo_rebase]
repos: [vllm-omni]
requires: []
params:
  report_only: {type: bool, default: true}
steps:
  - {id: guard, step: workspace.guard_clean}
  - {id: report, step: report.final_summary}
success: guard + report complete
"""


def install_mini_rebase_playbook(playbooks_dir):
    """Write the minimal locked repo_rebase playbook into a sandbox store."""
    from pathlib import Path
    d = Path(playbooks_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / "repo-rebase-mini.yaml").write_text(MINI_REBASE_PLAYBOOK)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """A tiny real git repo with one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    (repo / "mod_a.py").write_text("A = 1\n")
    (repo / "mod_b.py").write_text("B = 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "init")
    return repo
