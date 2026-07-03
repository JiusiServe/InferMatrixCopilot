"""Eval-informed pr-review: gate check + two-stage evidence-grounded review."""

import asyncio

from omni_copilot.engine.builtin_steps import register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import FailureKind, StepContext
from omni_copilot.llm import Block, Reply


class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None, max_tokens=None,
               on_text=None):
        self.calls.append({"system": system, "messages": [*messages]})
        return self._replies.pop(0)


def _ctx(settings, trace, tmp_path, state, llm=None):
    return StepContext(settings=settings, state=state, params={},
                       run_dir=tmp_path / "run", trace=trace, llm=llm)


def _registry():
    return register_builtin_steps(StepRegistry())


def test_gate_check_injected_and_missing_pr(settings, trace, tmp_path):
    gate = _registry().get("pr.gate_check")
    ctx = _ctx(settings, trace, tmp_path, {"gate_report": "gates clean"})
    assert asyncio.run(gate.handler(ctx)).ok

    ctx = _ctx(settings, trace, tmp_path, {"task_spec": {}})
    result = asyncio.run(gate.handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_review_two_stage_with_evidence_loop(settings, trace, tmp_path, git_repo):
    llm = ScriptedLLM([
        # stage 1 (tool loop): one evidence lookup, then the draft
        Reply(blocks=[Block(type="tool_use", id="t1", name="read_file",
                            input={"path": str(git_repo / "mod_a.py")})]),
        Reply(blocks=[Block(type="text", text="- mod_a.py:1 draft finding\n"
                                              "- praise: nice code!")]),
        # stage 2 (editor): verified, actionable rewrite
        Reply(blocks=[Block(type="text",
                            text="`mod_a.py:1` — rename A for clarity.\n\nAPPROVE")]),
    ])
    state = {"diff_text": "diff --git a/mod_a.py b/mod_a.py\n+A = 1",
             "gate_report": "MERGE STATE: DIRTY", "task_spec": {"pr": 9},
             "repo_path": str(git_repo)}
    result = asyncio.run(_registry().get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok
    assert state["review_text"].startswith("`mod_a.py:1`")
    assert result.outputs["tool_calls"] == 1
    # gate report reached the reviewer; checklist system prompt used
    assert "MERGE STATE: DIRTY" in llm.calls[0]["messages"][0]["content"]
    assert "Breaking behavior" in llm.calls[0]["system"]
    # editor pass received the draft + the diff
    assert "draft finding" in llm.calls[-1]["messages"][0]["content"]
    assert "strict review editor" in llm.calls[-1]["system"]


def test_review_single_shot_without_repo(settings, trace, tmp_path):
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="text", text="- f.py:1 draft")]),
        Reply(blocks=[Block(type="text", text="`f.py:1` — fix it.\n\nREQUEST CHANGES")]),
    ])
    state = {"diff_text": "diff", "task_spec": {"pr": 9}}  # no repo_path
    result = asyncio.run(_registry().get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok and result.outputs["tool_calls"] == 0
    assert state["review_text"].endswith("REQUEST CHANGES")
    assert len(llm.calls) == 2  # draft + editor


def test_review_blocked_without_diff_or_llm(settings, trace, tmp_path):
    step = _registry().get("agent.review_diff")
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path,
                                           {"task_spec": {"pr": 1}},
                                           llm=ScriptedLLM([]))))
    assert not result.ok and "no diff_text" in result.summary


def test_pr_review_playbook_v4_shape():
    from omni_copilot.config import _REPO_ROOT
    from omni_copilot.playbooks.store import PlaybookStore

    store = PlaybookStore(_REPO_ROOT / "playbooks", _registry())
    pb = store.get("pr-review")
    assert pb.version == 4
    assert [s.step for s in pb.steps] == [
        "pr.fetch_diff", "pr.gate_check", "agent.review_diff",
        "pr.post_review", "report.final_summary"]
