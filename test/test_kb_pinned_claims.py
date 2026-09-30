"""Rule claims and code evidence checked at a pinned upstream SHA (kb init §9.1)."""

from __future__ import annotations

import subprocess

import pytest

from infermatrix_copilot.knowledge_service.facts import FactsError
from infermatrix_copilot.knowledge_service.pinned_claims import (
    Evidence, PinnedObserver, check_evidence, check_rules, evidence_for,
)


def _git(repo, *args) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _commit(repo, files: dict[str, str], message: str) -> str:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def upstream(tmp_path):
    repo = tmp_path / "up"
    repo.mkdir()
    _git(repo, "init", "-q")
    first = _commit(repo, {"pkg/core.py": "class Engine:\n    def step(self):\n        return 1\n",
                           "README.md": "hello\n"}, "first")
    pin = _commit(repo, {"pkg/util.py": "def helper():\n    pass\n"}, "second")
    later = _commit(repo, {"pkg/late.py": "X = 1\n"}, "third")
    return repo, first, pin, later


def _pulls(table):
    def pull(repository, number):
        if number not in table:
            raise FactsError(f"{repository} PR #{number}: not found")
        return table[number]
    return pull


def test_observer_answers_at_the_pin(upstream):
    repo, first, pin, later = upstream
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    assert obs.head() == pin
    assert obs.top_level(pin) == {"pkg", "README.md"}
    assert obs.path_exists(pin, "pkg/util.py")
    assert not obs.path_exists(pin, "pkg/late.py")
    assert obs.file_text(pin, "pkg/late.py") is None
    assert obs.file_text(pin, "README.md") == "hello\n"
    assert obs.is_ancestor(first) and obs.is_ancestor(pin)
    assert not obs.is_ancestor(later)
    assert not obs.is_ancestor("0" * 40) and not obs.is_ancestor("nope")


def test_observer_refuses_a_bad_pin(upstream):
    repo, *_ = upstream
    with pytest.raises(FactsError):
        PinnedObserver(repo, "o/up", "abc")
    with pytest.raises(FactsError):
        PinnedObserver(repo, "o/up", "1" * 40)


def test_rule_claims_hold_or_are_reported(upstream):
    repo, first, pin, later = upstream
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({
        1: {"merged": True, "merge_commit_sha": first},
        2: {"merged": True, "merge_commit_sha": later},
        3: {"merged": False},
    }))
    ok = {"R-1": "Use `pkg/core.py::Engine.step` and `pkg/util.py` ^[PR #1]"}
    assert check_rules(ok, obs) == []
    bad = {
        "R-2": "See `pkg/late.py`",               # exists only after the pin
        "R-3": "Call `pkg/core.py::Engine.run`",  # symbol not defined
        "R-4": "Fixed in ^[PR #2]",               # merged after the pin
        "R-5": "Proposed in ^[PR #3]",            # never merged
    }
    problems = check_rules(bad, obs)
    assert len(problems) == 4
    assert problems[0].startswith("R-2:") and "pkg/late.py" in problems[0]
    assert problems[1].startswith("R-3:") and "Engine.run" in problems[1]
    assert problems[2].startswith("R-4:") and "merged after" in problems[2]
    assert problems[3].startswith("R-5:") and "not merged" in problems[3]


def test_prose_words_are_not_claims(upstream):
    repo, _, pin, _ = upstream
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    assert check_rules({"R-1": "Mention `tests` and `config/x.py` only"}, obs) == []


def test_evidence_binds_a_range_to_its_text(upstream):
    repo, _, pin, _ = upstream
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    entry = evidence_for(obs, "pkg/core.py", 2, 3)
    assert check_evidence([entry], obs) == []
    assert Evidence.from_dict(entry.to_dict()) == entry
    moved = Evidence("pkg/core.py", 1, 2, entry.sha256)
    outside = Evidence("pkg/core.py", 2, 9, entry.sha256)
    missing = Evidence("pkg/late.py", 1, 1, entry.sha256)
    backwards = Evidence("pkg/core.py", 3, 2, entry.sha256)
    problems = check_evidence([moved, outside, missing, backwards], obs)
    assert [p.split(": ", 1)[1].split(" ")[0] for p in problems] == ["content", "range", "file", "range"]
    with pytest.raises(FactsError):
        evidence_for(obs, "pkg/core.py", 0, 1)
    with pytest.raises(FactsError):
        evidence_for(obs, "pkg/late.py", 1, 1)


def test_directories_are_paths_but_not_evidence(upstream):
    repo, _, pin, _ = upstream
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    assert obs.path_exists(pin, "pkg") and obs.file_text(pin, "pkg") is None
    assert check_rules({"R-1": "Lives under `pkg/`"}, obs) == []
    with pytest.raises(FactsError):
        evidence_for(obs, "pkg", 1, 1)
    assert "file does not exist" in check_evidence([Evidence("pkg", 1, 1, "0" * 64)], obs)[0]


def test_evidence_hash_ignores_line_ending_style(tmp_path):
    repo = tmp_path / "crlf"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "core.autocrlf", "false")
    a = _commit(repo, {"f.txt": "a\nb\nc"}, "lf")
    b = _commit(repo, {"f.txt": "a\r\nb\r\nc\r\n"}, "crlf")
    lf = evidence_for(PinnedObserver(repo, "o/x", a, pull=_pulls({})), "f.txt", 1, 3)
    crlf = evidence_for(PinnedObserver(repo, "o/x", b, pull=_pulls({})), "f.txt", 1, 3)
    assert lf.sha256 == crlf.sha256


def test_an_unreadable_object_is_an_error_not_an_absence(upstream):
    repo, _, pin, _ = upstream
    blob = _git(repo, "rev-parse", f"{pin}:pkg/util.py")
    (repo / ".git" / "objects" / blob[:2] / blob[2:]).unlink()  # loose object gone
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    assert obs.path_exists(pin, "pkg/util.py")  # the tree still names it
    with pytest.raises(FactsError):
        obs.file_text(pin, "pkg/util.py")
    with pytest.raises(FactsError):
        check_rules({"R-1": "Call `pkg/util.py::helper`"}, obs)
    with pytest.raises(FactsError):
        check_evidence([Evidence("pkg/util.py", 1, 1, "0" * 64)], obs)


def test_an_unreadable_tree_is_an_error(upstream):
    repo, _, pin, _ = upstream
    tree = _git(repo, "rev-parse", f"{pin}:pkg")
    (repo / ".git" / "objects" / tree[:2] / tree[2:]).unlink()
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    with pytest.raises(FactsError):
        obs.path_exists(pin, "pkg/core.py")


def test_an_unreadable_history_is_an_error_not_a_later_merge(upstream):
    repo, first, pin, later = upstream
    (repo / ".git" / "objects" / first[:2] / first[2:]).unlink()  # the pin's parent is gone
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    with pytest.raises(FactsError):
        obs.is_ancestor(later)  # git cannot walk the pin's history: no answer, not "no"
    assert not obs.is_ancestor("0" * 40)  # an unknown commit is still simply not an ancestor


def test_a_corrupt_candidate_commit_is_an_error_not_unknown(upstream):
    repo, _, pin, later = upstream
    path = repo / ".git" / "objects" / later[:2] / later[2:]
    path.chmod(0o644)
    path.write_bytes(b"not a zlib stream")
    obs = PinnedObserver(repo, "o/up", pin, pull=_pulls({}))
    with pytest.raises(FactsError):
        obs.is_ancestor(later)
