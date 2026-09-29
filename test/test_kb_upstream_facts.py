"""Upstream fact attestations: the service signs them, the publisher observes them again."""

from __future__ import annotations

import subprocess

import pytest

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.gate import changes_between, run_gate
from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver
from infermatrix_copilot.knowledge_service.facts import (
    Claim, FactsError, attest, claims_in, defines, recheck,
)
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from test_kb_intake_gate import JUDGE, PAGE, ScriptedGateway, _judge_all, _rule, _tree

UP = "org/upstream"
SHA = "a" * 40


class FakeUpstream:
    """An upstream the test controls: files at one SHA and PR states."""

    def __init__(self, files=None, pulls=None, *, sha=SHA, down=False):
        self.repository = UP
        self.sha = sha
        self.files = dict(files or {"pkg/queue.py": "class Queue:\n    def put(self):\n        pass\n",
                                    "README.md": "x\n"})
        self.pulls = dict(pulls or {10: {"merged": True, "merge_commit_sha": "c" * 40}})
        self.down = down

    def _up(self):
        if self.down:
            raise FactsError("upstream unreachable")

    def head(self):
        self._up()
        return self.sha

    def _known(self, sha):
        self._up()
        if sha != self.sha:
            raise FactsError(f"no commit {sha[:12]}")

    def top_level(self, sha):
        self._known(sha)
        return {p.split("/", 1)[0] for p in self.files}

    def path_exists(self, sha, path):
        self._known(sha)
        return path in self.files or any(p.startswith(path + "/") for p in self.files)

    def file_text(self, sha, path):
        self._known(sha)
        return self.files.get(path)

    def pull(self, number):
        self._up()
        return self.pulls.get(number, {"merged": False})


# -- claims ------------------------------------------------------------------------

def test_only_resolvable_tokens_are_claims():
    text = ("见 `pkg/queue.py`、`pkg/queue.py::Queue.put`、`pkg/`、`config/x.py`、`/v1/chat`、"
            "`pkg/../etc/passwd`、`pkg/...`、`origin/main`。 ^[PR #10] ^[PR #11]")
    claims = claims_in(text, {"pkg", "README.md"}, active=True)
    assert {(c.kind, c.pr, c.path, c.symbol) for c in claims} == {
        ("pr", 10, "", ""), ("pr", 11, "", ""), ("path", 0, "pkg/queue.py", ""),
        ("symbol", 0, "pkg/queue.py", "Queue.put"), ("path", 0, "pkg", "")}
    assert all(c.must_hold for c in claims)


def test_a_retired_rule_records_its_claims_but_must_cite_merged_evidence():
    claims = claims_in("`pkg/gone.py` ^[PR #10]", {"pkg"}, active=False, evidence="PR #12")
    assert {(c.kind, c.pr, c.path, c.must_hold) for c in claims} == {
        ("pr", 10, "", False), ("path", 0, "pkg/gone.py", False), ("pr", 12, "", True)}


def test_symbol_definitions():
    text = "class Queue:\n    async def put(self):\n        pass\nLIMIT: int = 3\n"
    for path in ("pkg/queue.py", "pkg/queue.txt"):              # parsed, and the line-pattern fallback
        assert defines(text, "Queue.put", path) and defines(text, "LIMIT", path)
        assert not defines(text, "Queue.get", path) and not defines(text, "Que", path)


def test_definitions_inside_strings_do_not_count():
    text = 'DOC = """\nclass Removed:\n    pass\n"""\n# def gone(): pass\ndef kept():\n    x = 1\n'
    assert not defines(text, "Removed", "pkg/m.py") and not defines(text, "gone", "pkg/m.py")
    assert defines(text, "kept", "pkg/m.py") and defines(text, "DOC", "pkg/m.py")
    assert not defines(text, "kept.y", "pkg/m.py")
    reads = "registry[Missing] = 1\nobj.Attr = 2\na, (b, *c) = 1, (2, 3)\n"
    assert not defines(reads, "Missing", "pkg/m.py") and not defines(reads, "Attr", "pkg/m.py")
    assert not defines(reads, "obj", "pkg/m.py") and not defines(reads, "registry", "pkg/m.py")
    assert all(defines(reads, n, "pkg/m.py") for n in ("a", "b", "c"))
    exports = "from .engine import Engine as Public, Other\nimport os.path\nfrom x import *\n"
    assert all(defines(exports, n, "pkg/__init__.py") for n in ("Public", "Other", "os"))
    assert not defines(exports, "Engine", "pkg/__init__.py")
    _, facts, problems = attest(claims_in("`pkg/m.py::Removed`", {"pkg"}, active=True),
                                FakeUpstream(files={"pkg/m.py": text}))
    assert facts[0]["defined"] is False and problems


def test_root_files_are_claims_only_with_a_symbol():
    claims = claims_in("`setup.py::missing` `setup.py` `tests`", {"setup.py", "tests"}, active=True)
    assert [(c.kind, c.path, c.symbol) for c in claims] == [("symbol", "setup.py", "missing")]
    _, _, problems = attest(claims, FakeUpstream(files={"setup.py": "def main():\n    pass\n"}))
    assert problems == [f"setup.py::missing is not defined at {UP}@{SHA[:12]}"]


# -- attest and recheck --------------------------------------------------------------

def _claims(*tokens, active=True, evidence=""):
    return claims_in(" ".join(tokens), {"pkg", "README.md"}, active=active, evidence=evidence)


def test_attest_signs_what_holds_and_fails_what_an_active_rule_gets_wrong():
    upstream, facts, problems = attest(_claims("`pkg/queue.py::Queue.put`", "^[PR #10]"), FakeUpstream())
    assert upstream == {"repository": UP, "sha": SHA} and problems == [] and len(facts) == 2
    _, _, problems = attest(_claims("`pkg/nope.py`", "`pkg/queue.py::Queue.get`", "^[PR #99]"), FakeUpstream())
    assert sorted(problems) == [f"{UP} PR #99 is not merged",
                                f"pkg/nope.py does not exist at {UP}@{SHA[:12]}",
                                f"pkg/queue.py::Queue.get is not defined at {UP}@{SHA[:12]}"]
    _, facts, problems = attest(_claims("`pkg/nope.py`", active=False, evidence="PR #10"), FakeUpstream())
    assert problems == [] and any(f["kind"] == "path" and f["exists"] is False for f in facts)


def test_recheck_agrees_only_with_the_same_upstream_state():
    upstream, facts, _ = attest(_claims("`pkg/queue.py`", "^[PR #10]"), FakeUpstream())
    assert recheck(upstream, facts, FakeUpstream()) == []
    assert recheck({}, [], FakeUpstream(down=True)) == []                   # nothing to check
    moved = FakeUpstream(pulls={10: {"merged": True, "merge_commit_sha": "d" * 40}})
    assert any("upstream disagrees" in p for p in recheck(upstream, facts, moved))
    gone = FakeUpstream(files={"README.md": "x\n"})
    assert any("upstream disagrees" in p for p in recheck(upstream, facts, gone))
    with pytest.raises(FactsError):
        recheck(upstream, facts, FakeUpstream(down=True))
    with pytest.raises(FactsError):                                         # the pinned SHA is unknown
        recheck(upstream, facts, FakeUpstream(sha="b" * 40))
    other = FakeUpstream()
    other.repository = "org/other"
    assert recheck(upstream, facts, other) == [f"facts are about {UP}, not org/other"]


def test_recheck_refuses_forged_or_false_facts():
    upstream, facts, _ = attest(_claims("`pkg/queue.py`"), FakeUpstream())
    false = [{**facts[0], "exists": False}]
    assert recheck(upstream, false, FakeUpstream())[0].startswith("signed a fact that does not hold")
    assert recheck(upstream, [{"kind": "path"}], FakeUpstream())[0].startswith("malformed fact")
    assert recheck({"repository": UP, "sha": "HEAD"}, facts, FakeUpstream()) == [
        "the verdict names no pinned upstream SHA"]


# -- the mirror ----------------------------------------------------------------------

def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def test_mirror_observer_reads_a_real_repository(tmp_path):
    work = tmp_path / "up"
    work.mkdir()
    _git(work, "init", "-q", "-b", "main")
    (work / "pkg").mkdir()
    (work / "pkg" / "queue.py").write_text("class Queue:\n    pass\n")
    _git(work, "add", "-A")
    _git(work, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "x")
    head = _git(work, "rev-parse", "HEAD")
    observer = MirrorObserver(tmp_path / "mirror.git", UP, lambda n: {"merged": n == 10}, url=str(work))
    assert observer.head() == head and observer.top_level(head) == {"pkg"}
    assert observer.path_exists(head, "pkg/queue.py") and observer.path_exists(head, "pkg")
    assert not observer.path_exists(head, "pkg/nope.py")
    assert "class Queue" in observer.file_text(head, "pkg/queue.py")
    assert observer.pull(10)["merged"] is True
    with pytest.raises(FactsError):
        observer.path_exists("f" * 40, "pkg/queue.py")
    broken = MirrorObserver(tmp_path / "m2.git", UP, lambda n: 1 / 0, url=str(tmp_path / "missing"))
    with pytest.raises(FactsError):
        broken.head()
    with pytest.raises(FactsError):
        MirrorObserver(tmp_path / "mirror.git", UP, lambda n: 1 / 0, url=str(work)).pull(1)


# -- the gate --------------------------------------------------------------------------

def _gate(claim: str, observer):
    base = _tree()
    head = apply_operations(base, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #10", claim=claim))],
                            release="v1", today="2026-09-29").files
    head = {**base, **head}
    return run_gate(base=base, head=head, changes=changes_between(base, head), external_texts={},
                    evidence=[], gateway=ScriptedGateway(_judge_all("yes")), judge=JUDGE, release="v1",
                    repo_dir="repos/demo", retire_ratio=1.0, facts=observer)


def test_the_gate_signs_facts_and_fails_a_false_claim_before_paying_the_judge():
    decision = _gate("`pkg/queue.py::Queue.put` 满时拒绝", FakeUpstream())
    assert decision.status == "pass", decision.reasons
    assert decision.upstream == {"repository": UP, "sha": SHA}
    assert {f["kind"] for f in decision.facts} == {"pr", "symbol"}
    assert decision.to_dict()["facts"] == decision.facts
    decision = _gate("`pkg/removed.py` 满时拒绝", FakeUpstream())
    assert decision.status == "fail" and decision.blocks == []              # no L2 call was made
    assert decision.reasons == [f"upstream fact: pkg/removed.py does not exist at {UP}@{SHA[:12]}"]
    decision = _gate("`pkg/queue.py` 满时拒绝", FakeUpstream(down=True))
    assert decision.status == "human" and "could not be checked" in decision.reasons[0]
    assert _gate("`pkg/queue.py` 满时拒绝", None).facts == []                 # no upstream: nothing attested


# -- the publisher ---------------------------------------------------------------------

def _with_facts(tmp_path, observer):
    """The service's PR is open; its decision carries facts; the merge item is issued."""
    from test_kb_publisher import _collect, _setup

    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    _collect(rt)
    changeset = rt.ledger.changeset(changeset_id)
    upstream, facts, _ = attest(_claims("`pkg/queue.py`", "^[PR #10]"), FakeUpstream())
    rt.ledger.update_changeset(changeset_id, detail={**changeset["detail"], "decision": {
        **changeset["detail"]["decision"], "upstream": upstream, "facts": facts}})
    head = gh.prs[42]["headRefOid"]
    rt.github.prs[42] = {"number": 42, "state": "open", "merged": False, "head": {"sha": head}}
    assert merge.advance(rt, lifecycle) == [f"merge issued {changeset_id}"]
    rt.outbox.refresh_control()
    pub.upstreams = {lifecycle.repo: UP}
    pub.observer = lambda repo, name: observer
    return rt, lifecycle, changeset_id, pub, gh


def test_the_publisher_merges_when_the_upstream_agrees(tmp_path):
    from test_kb_publisher import _collect

    rt, lifecycle, changeset_id, pub, gh = _with_facts(tmp_path, FakeUpstream())
    assert pub.run_once()["performed"] == 1 and gh.prs[42]["state"] == "MERGED"
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["status"] == "merged"


@pytest.mark.parametrize("observer", [FakeUpstream(pulls={10: {"merged": False}}), FakeUpstream(down=True)],
                         ids=["disagrees", "unreachable"])
def test_the_publisher_does_not_merge_and_people_hear_after_a_day(tmp_path, observer):
    from test_kb_publisher import _collect

    rt, lifecycle, changeset_id, pub, gh = _with_facts(tmp_path, observer)
    assert pub.run_once()["failed"] == 1 and gh.prs[42]["state"] == "OPEN"
    assert not any(call[:2] == ["pr", "merge"] for call in gh.calls)
    _collect(rt)
    changeset = rt.ledger.changeset(changeset_id)
    assert changeset["status"] == "pr_open" and changeset["detail"]["facts_failing_since"]
    assert rt.ledger.human_queue("demo") == []                               # retried first
    now = rt.clock()
    rt.clock = rt.outbox._clock = pub.clock = lambda: now + 25 * 3600
    assert merge.advance(rt, lifecycle) == [f"merge issued {changeset_id}"]   # signed again
    rt.outbox.refresh_control()
    assert pub.run_once()["failed"] == 1
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["status"] == "gate_failed"
    assert any("upstream facts" in row["reason"] for row in rt.ledger.human_queue("demo"))


def test_facts_without_a_configured_public_upstream_never_merge(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _with_facts(tmp_path, FakeUpstream())
    pub.upstreams = {}
    assert pub.run_once()["failed"] == 1 and gh.prs[42]["state"] == "OPEN"


def test_a_claim_is_hashable_per_fact():
    assert Claim("path", True, path="a/b").key == Claim("path", False, path="a/b").key
