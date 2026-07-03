"""Unified agent-step runtime (修正方案 P0): dispatch context, evidence pack,
skills, output contract, failure mapping, and the all-agent-steps-unified rule."""

import asyncio
import json

import pytest

from omni_copilot.engine.agent_runtime import (
    BASE_OUTPUT_SCHEMA,
    run_agent_step,
)
from omni_copilot.engine.builtin_steps import register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import FailureKind, StepContext
from omni_copilot.llm import Block, Reply
from omni_copilot.memory.skills import SkillStore


class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None):
        self.calls.append({"system": system, "messages": [*messages],
                           "tools": tools})
        return self._replies.pop(0)


def contract(status="success", **extra):
    base = {k: ([] if "list" in v else "x") for k, v in BASE_OUTPUT_SCHEMA.items()}
    base.update(status=status, summary="did the thing", confidence="high",
                next_action="none")
    base["failure_kind"] = None
    base.update(extra)
    return Reply(blocks=[Block(type="text", text=json.dumps(base))])


def _ctx(settings, trace, tmp_path, state=None, llm=None):
    return StepContext(settings=settings, state=state or {"task_spec": {"pr": 1}},
                       params={}, run_dir=tmp_path / "run", trace=trace, llm=llm)


def _run(ctx, **kw):
    defaults = dict(step_name="t.step", purpose="test", evidence={"e": "small"})
    defaults.update(kw)
    return asyncio.run(run_agent_step(ctx, **defaults))


def test_evidence_capped_and_archived(settings, trace, tmp_path):
    settings.evidence_item_chars = 100
    llm = ScriptedLLM([contract()])
    ctx = _ctx(settings, trace, tmp_path, llm=llm)
    big = "x" * 500 + "TAIL_MARKER"
    result, output = _run(ctx, evidence={"big_item": big})
    assert result.ok
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "chars omitted" in prompt and "TAIL_MARKER" in prompt
    archived = tmp_path / "run" / "evidence" / "big_item.txt"
    assert archived.exists() and archived.read_text() == big
    assert str(archived) in prompt  # agent told where the full text lives


def test_skills_retrieved_and_injected(settings, trace, tmp_path):
    store = SkillStore(settings.skills_dir)
    store.propose(name="test-skill", description="guidance for t.step testing",
                  body="## Fix\ndo the thing")
    store.promote("test-skill")
    llm = ScriptedLLM([contract()])
    ctx = _ctx(settings, trace, tmp_path, llm=llm)
    _run(ctx, step_name="t.step testing")
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "RELEVANT SKILLS" in prompt and "test-skill" in prompt
    ev = next(trace.events("agent_dispatch"))
    assert "test-skill" in ev["skills"]


def test_skill_candidate_tool_is_gated(settings, trace, tmp_path):
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="tool_use", id="t1", name="skill_update_candidate",
                            input={"name": "new-lesson", "description": "d",
                                   "body": "b"})]),
        contract(),
    ])
    ctx = _ctx(settings, trace, tmp_path, llm=llm)
    result, _ = _run(ctx)
    assert result.ok
    store = SkillStore(settings.skills_dir)
    assert "new-lesson" in store.candidates()   # candidate recorded
    assert store.load_all() == []               # no active skill created
    assert any(True for _ in trace.events("skill_candidate_proposed"))


def test_status_and_failure_kind_mapping(settings, trace, tmp_path):
    cases = [
        ("blocked", None, FailureKind.BLOCKED),
        ("needs_review", None, FailureKind.ESCALATE),
        ("failed", "retryable", FailureKind.RETRYABLE),
        ("failed", "test_failure", FailureKind.TEST_FAILURE),
        ("failed", "bogus-kind", FailureKind.ESCALATE),
    ]
    for status, kind, expected in cases:
        llm = ScriptedLLM([contract(status=status, failure_kind=kind)])
        result, _ = _run(_ctx(settings, trace, tmp_path, llm=llm))
        assert not result.ok and result.failure is expected, (status, kind)


def test_unparseable_after_repair_is_retryable(settings, trace, tmp_path):
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="text", text="prose")]),
        Reply(blocks=[Block(type="text", text="still prose")]),  # repair fails
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert not result.ok and result.failure is FailureKind.RETRYABLE
    assert output == {}


def test_files_modified_flow_into_changed_files(settings, trace, tmp_path):
    llm = ScriptedLLM([contract(files_modified=["a.py", "b.py"])])
    result, _ = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.changed_files == ["a.py", "b.py"]


@pytest.mark.parametrize("step_name,state", [
    ("agent.review_diff", {"task_spec": {"pr": 1}, "diff_text": "diff"}),
    ("agent.draft_issue_answer", {"task_spec": {"issue": 2}, "issue_text": "help"}),
    ("agent.triage_issues", {"task_spec": {"kind": "issue_filter"},
                             "issue_text": "[]"}),
    ("agent.debug_group", {"task_spec": {"pr": 3}, "repo_path": "/tmp"}),
])
def test_every_agent_step_goes_through_the_runtime(settings, trace, tmp_path,
                                                   step_name, state):
    """修正方案 acceptance #1: agent-kind steps share the unified entry —
    proven by the agent_dispatch trace event each must emit."""
    registry = register_builtin_steps(StepRegistry())
    llm = ScriptedLLM([contract(review_comments=[], answer_draft="a",
                                triage_table=[], root_cause="r",
                                fix_summary="f", verification="v")])
    ctx = StepContext(settings=settings, state=state, params={},
                      run_dir=tmp_path / "run", trace=trace, llm=llm)
    ctx.item = {"signature": "sig", "jobs": []}  # for debug_group
    result = asyncio.run(registry.get(step_name).handler(ctx))
    assert result.ok, f"{step_name}: {result.summary}"
    ev = next(trace.events("agent_dispatch"))
    assert ev["permissions"]["tools"], step_name
