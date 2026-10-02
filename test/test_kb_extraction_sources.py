"""Extraction scope and source completeness, using local git and synthetic REST."""

from urllib.parse import parse_qs, urlparse

import pytest

from infermatrix_copilot.kb_service.sources import GitHubReader, SourceError
from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver
from infermatrix_copilot.knowledge_service.facts import FactsError
from test_kb_judge_evidence import _commit, _git


def _reader(*, commit_count=101, file_count=101, branch="0.2.8.beta1", repository="o/up"):
    calls = []
    commits = [{"sha": f"{n:040x}", "commit": {"message": f"change {n}",
                "author": {"date": f"2026-09-30T00:{n // 60:02d}:{n % 60:02d}Z"}}}
               for n in range(101)]
    threads = [{"id": n + 1, "in_reply_to_id": 1 if n else None,
                "body": "reply" if n else "review concern", "updated_at": "2026-10-01"}
               for n in range(101)]

    def fetch(url):
        parsed = urlparse(url)
        page = int(parse_qs(parsed.query).get("page", ["1"])[0])
        calls.append((parsed.path, page))
        if parsed.path.endswith("/pulls/4"):
            return {"number": 4, "body": "complete body", "changed_files": file_count,
                    "commits": commit_count, "merge_commit_sha": "a" * 40,
                    "base": {"ref": branch, "sha": "b" * 40, "repo": {"full_name": repository}},
                    "head": {"ref": "topic", "sha": "c" * 40}}
        rows = commits if parsed.path.endswith("/commits") else (
            threads if parsed.path.endswith("/pulls/4/comments") else (
                [{"filename": f"pkg/{n}.py", "status": "modified"} for n in range(101)]
                if parsed.path.endswith("/files") else []))
        return rows[(page - 1) * 100:page * 100]

    return GitHubReader(fetch=fetch, fetch_diff=lambda url, bound: "complete diff"), calls


def test_complete_history_retains_authoritative_scope_commit_chronology_and_thread_replies():
    reader, calls = _reader()
    evidence = reader.history_evidence("o/up", 4)
    assert evidence["base"] == {"ref": "0.2.8.beta1", "sha": "b" * 40,
                                "repo": {"full_name": "o/up"}}
    assert evidence["head"] == {"ref": "topic", "sha": "c" * 40}
    assert evidence["repository"] == "o/up" and evidence["source_reference"] == "PR #4"
    assert evidence["commits"][100]["commit"]["message"] == "change 100"
    assert evidence["threads"][100]["in_reply_to_id"] == 1
    assert evidence["threads"][100]["updated_at"] == "2026-10-01"
    for endpoint in ("files", "commits", "comments"):
        assert (f"/repos/o/up/pulls/4/{endpoint}", 2) in calls
    assert len(evidence["files"]) == 101 and evidence["diff"] == "complete diff"


@pytest.mark.parametrize("counts, message", [({"commit_count": 102}, "commit evidence is incomplete"),
                                           ({"file_count": 102}, "changed-file evidence is incomplete")])
def test_terminal_page_does_not_override_declared_source_counts(counts, message):
    reader, _ = _reader(**counts)
    with pytest.raises(SourceError, match=message):
        reader.history_evidence("o/up", 4)


def test_scope_must_belong_to_the_requested_repository():
    reader, _ = _reader(repository="another/up")
    with pytest.raises(SourceError, match="base repository differs"):
        reader.history_evidence("o/up", 4)


def test_real_nondefault_branch_facts_do_not_fall_back_to_default_branch(tmp_path):
    upstream = tmp_path / "up"
    upstream.mkdir()
    _git(upstream, "init", "-q", "-b", "main")
    main = _commit(upstream, "pkg/main.py", "main\n", "main")
    _git(upstream, "checkout", "-q", "-b", "0.2.8.beta1")
    beta = _commit(upstream, "pkg/beta.py", "beta\n", "beta only")
    _git(upstream, "checkout", "-q", "main")
    path = tmp_path / "mirror.git"
    default = MirrorObserver(path, "o/up", lambda n: {}, url=str(upstream))
    scoped = MirrorObserver(path, "o/up", lambda n: {}, url=str(upstream), branch="0.2.8.beta1")
    assert default.head() == main and not default.path_exists(main, "pkg/beta.py")
    assert scoped.head() == beta and scoped.path_exists(beta, "pkg/beta.py")
    absent = MirrorObserver(path, "o/up", lambda n: {}, url=str(upstream), branch="missing")
    with pytest.raises(FactsError):
        absent.head()
    _git(upstream, "branch", "-D", "0.2.8.beta1")
    deleted = MirrorObserver(path, "o/up", lambda n: {}, url=str(upstream), branch="0.2.8.beta1")
    with pytest.raises(FactsError):
        deleted.head()


@pytest.mark.parametrize("branch", ["", "bad..branch", "@{-1}", "-main", "bad\0branch"])
def test_invalid_source_branch_is_refused_before_sync(tmp_path, branch):
    with pytest.raises(FactsError, match="invalid upstream branch"):
        MirrorObserver(tmp_path / "mirror.git", "o/up", lambda n: {}, branch=branch)
    assert not (tmp_path / "mirror.git").exists()


def test_exact_orphan_commit_is_fetchable_without_changing_observed_branch(tmp_path):
    upstream = tmp_path / "up"
    upstream.mkdir()
    _git(upstream, "init", "-q", "-b", "main")
    main = _commit(upstream, "pkg/main.py", "main\n", "main")
    observer = MirrorObserver(tmp_path / "mirror.git", "o/up", lambda n: {}, url=str(upstream))
    assert observer.head() == main
    _git(upstream, "checkout", "-q", "--orphan", "old-merge")
    orphan = _commit(upstream, "pkg/orphan.py", "orphan\n", "old merged source")
    _git(upstream, "checkout", "-q", "main")
    _git(upstream, "branch", "-D", "old-merge")
    assert observer.file_text(orphan, "pkg/orphan.py") == "orphan\n"
    assert observer.head() == main
    with pytest.raises(FactsError, match="invalid upstream commit"):
        observer.file_text("HEAD", "pkg/orphan.py")
