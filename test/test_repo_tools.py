"""Change-archaeology + calc tools for review steps (review/repo_tools.py)."""

import subprocess
from pathlib import Path

import pytest

from infermatrix_copilot.engine.steps.review.repo_tools import (
    _calc,
    _safe_rel_path,
    review_repo_tools,
)


@pytest.fixture()
def pr_repo(tmp_path: Path) -> Path:
    """A repo shaped like a PR worktree: origin/main at the base commit,
    HEAD one commit ahead."""
    repo = tmp_path / "pr_repo"
    repo.mkdir()

    def git(*args: str) -> str:
        out = subprocess.run(["git", *args], cwd=repo, check=True,
                             capture_output=True, text=True)
        return out.stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (repo / "old.py").write_text("VALUE = 'before'\n")
    git("add", "-A")
    git("commit", "-qm", "base commit")
    base = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", base)
    (repo / "old.py").write_text("VALUE = 'after'\n")
    (repo / "new.py").write_text("ADDED = True\n")
    git("add", "-A")
    git("commit", "-qm", "pr head commit")
    return repo


def test_diff_stat_lists_changed_files(pr_repo):
    tools = review_repo_tools(pr_repo)
    out = tools["diff_stat"].handler()
    assert out.startswith("merge-base ")
    assert "old.py" in out and "new.py" in out


def test_file_at_base_reads_pre_pr_content(pr_repo):
    tools = review_repo_tools(pr_repo)
    assert "before" in tools["file_at_base"].handler(path="old.py")
    assert tools["file_at_base"].handler(path="new.py").startswith(
        "(absent at base")


def test_show_commit_validates_sha_and_shows_patch(pr_repo):
    tools = review_repo_tools(pr_repo)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=pr_repo,
                          capture_output=True, text=True).stdout.strip()
    out = tools["show_commit"].handler(sha=head)
    assert "pr head commit" in out and "after" in out
    with pytest.raises(ValueError):
        tools["show_commit"].handler(sha="HEAD")        # not hex
    with pytest.raises(ValueError):
        tools["show_commit"].handler(sha="--all")       # option smuggling


def test_search_history_finds_introducing_commit(pr_repo):
    tools = review_repo_tools(pr_repo)
    out = tools["search_history"].handler(term="ADDED")
    assert "pr head commit" in out
    assert "(no commits touch this term)" in tools["search_history"].handler(
        term="never-was-here")


def test_no_repo_yields_no_tools():
    assert review_repo_tools(None) == {}


def test_safe_rel_path_rejects_escapes():
    for bad in ("-rf", "/etc/passwd", "../secrets", "a/../../b", ""):
        with pytest.raises(ValueError):
            _safe_rel_path(bad)
    assert _safe_rel_path("docs/a.md") == "docs/a.md"


def test_calc_evaluates_arithmetic():
    assert _calc("55.4 + 22.1/8") == repr(55.4 + 22.1 / 8)
    assert _calc("sum([1, 2, 3]) >= 6") == "True"
    assert _calc("round(24000/44100, 3)") == repr(round(24000 / 44100, 3))
    assert _calc("min(sqrt(16), 5)") == "4.0"


def test_calc_rejects_everything_but_arithmetic():
    for bad in ("__import__('os')", "().__class__", "open('/etc/passwd')",
                "x + 1", "'a' * 9", "2 ** 100000", "[i for i in range(3)]"):
        with pytest.raises(ValueError):
            _calc(bad)
