"""Dating rules in tools/check_spec_freshness.py.

The check compares a SPEC page's declared `verified-against:` date against the
date its source last changed, so getting that date right is the whole check.
Two git shapes make it subtle, and they pull in opposite directions:

- a `pull_request` checkout is `refs/pull/N/merge`, the branch merged into the
  base, a commit that exists nowhere else. A file edited on BOTH sides differs
  from both parents there, so git reports that merge as the last commit
  touching it and the file dates to merge time — forever. The same SHA passes
  its push run and fails its pull_request run.
- a real merge can edit source while resolving a conflict, and that edit must
  keep counting or an outdated page slips through.

So the tool cannot key on "is HEAD a merge": that fixes the first and breaks
the second. It keys on the event instead. Both shapes are pinned below,
including the resolving merge left AT the tip, which is the case a shape-based
rule would silently swallow.
"""

import datetime
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

_TOOL = Path(__file__).resolve().parent.parent / "tools" / "check_spec_freshness.py"
_spec = importlib.util.spec_from_file_location("check_spec_freshness", _TOOL)
freshness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(freshness)

_IDENT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
          "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def _git(repo: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                          env={**os.environ, **_IDENT, **env})


def _commit(repo: Path, name: str, body: str, when: str) -> None:
    (repo / name).write_text(body, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-m", f"{name}@{when}",
         GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)


def _ts(y: int, m: int, d: int) -> int:
    return int(datetime.datetime(y, m, d).timestamp())


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    return r


def _two_sided_merge(repo: Path) -> None:
    """Both branches edit src.py in non-overlapping places, then merge cleanly.

    The merged file differs from BOTH parents, which is precisely when git stops
    simplifying the merge away and reports it as the commit that touched the
    file. A one-sided change would be dated correctly by any implementation and
    would not exercise anything.
    """
    _commit(repo, "src.py", "top\n\n\n\n\n\n\n\n\n\nbottom\n", "2026-01-01T00:00:00")
    _git(repo, "checkout", "-q", "-b", "feature")
    _commit(repo, "src.py", "top-FEATURE\n\n\n\n\n\n\n\n\n\nbottom\n",
            "2026-01-02T00:00:00")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, "src.py", "top\n\n\n\n\n\n\n\n\n\nbottom-MAIN\n",
            "2026-01-03T00:00:00")
    merged = _git(repo, "merge", "-q", "--no-ff", "feature", "-m", "synthetic merge",
                  GIT_AUTHOR_DATE="2026-06-01T00:00:00",
                  GIT_COMMITTER_DATE="2026-06-01T00:00:00")
    assert merged.returncode == 0, f"fixture merge should be clean: {merged.stderr}"


def test_two_sided_merge_dates_the_file_to_the_merge_by_default(repo, monkeypatch):
    """The problem being fixed, pinned so it cannot be misdescribed.

    Outside a pull_request run the merge legitimately IS the last commit that
    produced this file's content, and the tool says so.
    """
    _two_sided_merge(repo)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setattr(freshness, "REPO", repo)
    assert freshness.last_commit(repo / "src.py") == _ts(2026, 6, 1)


def test_synthetic_pr_merge_is_skipped_under_a_pull_request_event(repo, monkeypatch):
    """Under `pull_request` the tip is GitHub's merge, so date from its parents.

    Without this the file dates to merge time and its page can never be fresh.
    """
    _two_sided_merge(repo)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setattr(freshness, "REPO", repo)
    # newest parent-side change to src.py is the main-side commit on 2026-01-03
    assert freshness.last_commit(repo / "src.py") == _ts(2026, 1, 3)


def test_resolving_merge_at_the_tip_still_counts(repo, monkeypatch):
    """A conflict resolution AT HEAD edits source and must not be skipped.

    This is the case a "tip is a merge" rule would swallow, and the reason the
    tool keys on the event instead of the shape of HEAD. Nothing follows the
    merge here on purpose — an unrelated later commit would mask the bug.
    """
    _commit(repo, "src.py", "base\n", "2026-01-01T00:00:00")
    _git(repo, "checkout", "-q", "-b", "feature")
    _commit(repo, "src.py", "base\nfeature\n", "2026-01-02T00:00:00")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, "src.py", "base\nmain\n", "2026-01-03T00:00:00")
    conflict = _git(repo, "merge", "--no-ff", "feature")
    assert conflict.returncode != 0, "fixture should conflict so the merge edits source"
    (repo / "src.py").write_text("base\nresolved\n", encoding="utf-8")
    _git(repo, "add", "src.py")
    _git(repo, "commit", "-m", "resolve",
         GIT_AUTHOR_DATE="2026-02-01T00:00:00",
         GIT_COMMITTER_DATE="2026-02-01T00:00:00")

    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setattr(freshness, "REPO", repo)
    assert freshness.last_commit(repo / "src.py") == _ts(2026, 2, 1), (
        "the resolving merge changed src.py and must date it")


def test_untracked_file_reads_as_fresh(repo, monkeypatch):
    """0 means 'not in history yet', which callers treat as fresh."""
    _commit(repo, "src.py", "base\n", "2026-01-01T00:00:00")
    monkeypatch.setattr(freshness, "REPO", repo)
    assert freshness.last_commit(repo / "nope.py") == 0
