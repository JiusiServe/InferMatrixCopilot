"""pr-review on the unified agent runtime: gate check + governed review step."""

import asyncio
import json

from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import FailureKind, StepContext
from infermatrix_copilot.llm import Block, Reply


class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None, max_tokens=None,
               on_text=None):
        self.calls.append({"system": system, "messages": [*messages],
                           "tools": tools})
        return self._replies.pop(0)


def _ctx(settings, trace, tmp_path, state, llm=None):
    return StepContext(settings=settings, state=state, params={},
                       run_dir=tmp_path / "run", trace=trace, llm=llm)


def _registry():
    return register_builtin_steps(StepRegistry())


def _contract_reply(comments, status="success"):
    return Reply(blocks=[Block(type="text", text=json.dumps({
        "status": status, "summary": "reviewed", "findings": [],
        "files_read": [], "files_modified": [], "tests_requested": [],
        "tests_run": [], "assumptions": [], "blockers": [],
        "confidence": "high", "failure_kind": None, "next_action": "post",
        "review_comments": comments,
    }))])


def test_gate_check_injected_and_missing_pr(settings, trace, tmp_path):
    gate = _registry().get("pr.gate_check")
    ctx = _ctx(settings, trace, tmp_path, {"gate_report": "gates clean"})
    assert asyncio.run(gate.handler(ctx)).ok

    ctx = _ctx(settings, trace, tmp_path, {"task_spec": {}})
    result = asyncio.run(gate.handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_review_runtime_flow(settings, trace, tmp_path, git_repo):
    llm = ScriptedLLM([
        # investigation: one evidence lookup, then the contract JSON
        Reply(blocks=[Block(type="tool_use", id="t1", name="read_file",
                            input={"path": str(git_repo / "mod_a.py")})]),
        _contract_reply([
            {"file": "mod_a.py", "line": 1, "severity": "nit",
             "comment": "rename A for clarity", "evidence": "read mod_a.py"},
            {"file": "mod_b.py", "line": 1, "severity": "major",
             "comment": "B breaks consumers", "evidence": "grep"},
        ]),
    ])
    state = {"diff_text": "diff --git a/mod_a.py b/mod_a.py\n+A = 1",
             "gate_report": "MERGE STATE: DIRTY", "task_spec": {"pr": 9},
             "repo_path": str(git_repo)}
    result = asyncio.run(_registry().get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary

    # rendered markdown: severity-ordered, verdict from major finding
    review = state["review_text"]
    assert review.index("mod_b.py") < review.index("mod_a.py")
    assert review.endswith("**Verdict:** REQUEST CHANGES")

    # dispatch context reached the model: evidence fenced, gate report included,
    # checklist guidance at the prompt TAIL (the system prompt stays static so
    # sibling lenses share one cached prefix), contract demanded
    first = llm.calls[0]
    prompt = first["messages"][0]["content"]
    assert "MERGE STATE: DIRTY" in prompt and "OUTPUT CONTRACT" in prompt
    assert "PERMISSIONS" in prompt and "<untrusted_data>" in prompt
    assert "Breaking behavior" in prompt
    assert "Breaking behavior" not in first["system"]  # static-system invariant
    # knowledge tools offered alongside scoped read tools
    tool_names = {t["name"] for t in first["tools"]}
    assert {"read_file", "skill_search", "gh_pr_view"} <= tool_names
    assert "write_file" not in tool_names  # read-only scope enforced

    # RunTrace: unified-runtime events present
    assert any(True for _ in trace.events("agent_dispatch"))
    out_ev = next(trace.events("agent_output"))
    assert out_ev["status"] == "success" and out_ev["tool_calls"] == 1


def test_review_contract_repair_round(settings, trace, tmp_path, git_repo):
    """Prose final output triggers exactly one repair call that must yield JSON."""
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="text", text="here is my review in prose")]),
        _contract_reply([]),  # the repair call converts it
    ])
    state = {"diff_text": "diff", "task_spec": {"pr": 9},
             "repo_path": str(git_repo)}
    result = asyncio.run(_registry().get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok
    assert state["review_text"].endswith("**Verdict:** APPROVE")
    assert "Convert the agent's draft output" in llm.calls[-1]["system"]


def test_review_blocked_without_diff(settings, trace, tmp_path):
    result = asyncio.run(_registry().get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, {"task_spec": {"pr": 1}},
             llm=ScriptedLLM([]))))
    assert not result.ok and "no diff_text" in result.summary


def test_pr_review_playbook_shape():
    from infermatrix_copilot.config import _REPO_ROOT
    from infermatrix_copilot.playbooks.store import PlaybookStore

    store = PlaybookStore(_REPO_ROOT / "playbooks", _registry())
    pb = store.get("pr-review")
    assert pb.version == 6  # v6 = declared review_depth param (adaptive depth)
    assert [s.step for s in pb.steps] == [
        "pr.fetch_diff", "pr.gate_check", "agent.review_diff",
        "pr.post_review", "report.final_summary"]
    assert "review_depth" in pb.params  # reuse (L0) with the depth override


def test_review_salvaged_when_agent_escalates_with_comments(settings, trace,
                                                            tmp_path, git_repo):
    """A review carrying comments ships as success even when the agent sets an
    escalating status — finding a blocking defect IS a successful review."""
    reply = json.dumps({
        "status": "needs_review", "summary": "found a blocking survivor",
        "findings": [], "files_read": [], "files_modified": [],
        "tests_requested": [], "tests_run": [], "assumptions": [],
        "blockers": [], "confidence": "high", "failure_kind": "escalate",
        "next_action": "block merge",
        "review_comments": [{"file": "a.py", "line": 1, "severity": "major",
                             "comment": "removed-API survivor", "evidence": "grep"}],
    })
    llm = ScriptedLLM([Reply(blocks=[Block(type="text", text=reply)])])
    state = {"task_spec": {"kind": "pr_review", "pr": 9, "repo": "r"},
             "repo_path": str(git_repo), "diff_text": "+++ b/a.py\n@@ +1\n+x=1"}
    result = asyncio.run(_registry().get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary
    assert "salvaged" in result.summary
    assert "removed-API survivor" in state["review_text"]
    assert state["review_text"].rstrip().endswith("**Verdict:** REQUEST CHANGES")
