import subprocess
from pathlib import Path

import pytest

from omni_copilot.config import Settings
from omni_copilot.run_trace import RunTrace


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        run_root=tmp_path / "runs",
        playbooks_dir=tmp_path / "playbooks",
        plugins_dir=tmp_path / "plugins",
        repo_paths={},
        allow_push=False,
    )


@pytest.fixture()
def trace(tmp_path: Path) -> RunTrace:
    return RunTrace(tmp_path / "trace" / "run_trace.jsonl")


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
