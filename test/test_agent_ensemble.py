"""Ensemble agent steps: perspective-diverse fan-out + verify-and-merge
(run_agent_step_ensemble) and its wiring into agent.review_diff."""

import asyncio
import json

from omni_copilot.engine.agent_runtime import (
    BASE_OUTPUT_SCHEMA,
    run_agent_step_ensemble,
)
from omni_copilot.engine.builtin_steps import _REVIEW_LENSES, register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import FailureKind, StepContext
from omni_copilot.llm import Block, Reply


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


LENSES = [{"name": "a", "focus": "look at A"}, {"name": "b", "focus": "look at B"}]


def _run(ctx, **kw):
    defaults = dict(step_name="t.step", purpose="test",
                    evidence={"e": "the evidence"}, lenses=LENSES,
                    merge_key="items",
                    output_extension={"items": "list of {name}"})
    defaults.update(kw)
    return asyncio.run(run_agent_step_ensemble(ctx, **defaults))


def test_ensemble_fans_out_and_merges(settings, trace, tmp_path):
    llm = ScriptedLLM([
        contract(items=[{"name": "shared"}, {"name": "only-a"}]),   # lens a
        contract(items=[{"name": "shared"}]),                       # lens b
        contract(items=[{"name": "shared"}, {"name": "only-a"}],    # merge
                 summary="merged"),
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["shared", "only-a"]
    assert result.summary.startswith("[ensemble x2]")

    # each lens got its focus; the merger got the tagged candidates + evidence
    assert "look at A" in llm.calls[0]["system"]
    assert "look at B" in llm.calls[1]["system"]
    merge = llm.calls[2]
    assert "verify-and-merge" in merge["system"]
    body = merge["messages"][0]["content"]
    assert body.count('"lens": "a"') == 2 and body.count('"lens": "b"') == 1
    assert "the evidence" in body

    ev = next(trace.events("agent_ensemble"))
    assert ev["lenses"] == ["a", "b"] and ev["candidates"] == 3
    assert ev["merged"] == 2 and ev["verified"] is True


def test_ensemble_merge_failure_falls_open_to_union(settings, trace, tmp_path):
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),
        contract(items=[{"name": "y"}]),
        Reply(blocks=[Block(type="text", text="prose")]),   # merge unparseable
        Reply(blocks=[Block(type="text", text="still prose")]),  # repair fails
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x", "y"]
    assert "lens" not in output["items"][0]
    assert "unverified union" in output["summary"]
    assert next(trace.events("agent_ensemble"))["verified"] is False


def test_ensemble_empty_merge_reply_falls_open_without_repair(settings, trace,
                                                              tmp_path):
    """An empty reducer reply must NOT go through the repair round (which would
    hallucinate a contract from nothing — live bug on PR 4678)."""
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),
        contract(items=[{"name": "x"}]),
        Reply(blocks=[Block(type="text", text="")]),   # reducer returns nothing
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x"]  # deduped union
    assert len(llm.calls) == 3  # no repair call happened


def test_ensemble_status_comes_from_samples_not_reducer(settings, trace,
                                                        tmp_path):
    """Reducers conflate step status with the reviewed artifact's verdict
    (live bug: merge said needs_review about the PR, step got escalated)."""
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),
        contract(items=[{"name": "x"}]),
        contract(status="needs_review", items=[{"name": "x"}]),
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok and output["status"] == "success"


def test_ensemble_reducer_losing_payload_falls_open(settings, trace, tmp_path):
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),
        contract(items=[{"name": "y"}]),
        contract(),  # contract-shaped but the items key vanished
        contract(),  # ...and the repair round loses it again
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x", "y"]
    assert next(trace.events("agent_ensemble"))["verified"] is False


def test_ensemble_survives_one_failed_lens(settings, trace, tmp_path):
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="text", text="prose")]),    # lens a: no contract
        Reply(blocks=[Block(type="text", text="prose")]),    # ...repair fails too
        contract(items=[{"name": "y"}]),                     # lens b ok
        contract(items=[{"name": "y"}]),                     # merge
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert next(trace.events("agent_ensemble"))["lenses"] == ["b"]


def test_ensemble_all_lenses_failed(settings, trace, tmp_path):
    llm = ScriptedLLM([Reply(blocks=[Block(type="text", text="prose")])] * 4)
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert not result.ok and result.failure is FailureKind.RETRYABLE
    assert output == {}


def test_review_step_uses_ensemble_when_enabled(settings, trace, tmp_path,
                                                git_repo):
    settings.review_ensemble = True
    comments = [{"file": "mod_a.py", "line": 1, "severity": "major",
                 "comment": "the diff sets A=1 which breaks B — guard it",
                 "evidence": "hunk"}]
    llm = ScriptedLLM(
        [contract(review_comments=comments)] * len(_REVIEW_LENSES)
        + [contract(review_comments=comments)]     # merge
    )
    state = {"diff_text": "diff --git a/mod_a.py b/mod_a.py\n+A = 1",
             "task_spec": {"pr": 9}, "repo_path": str(git_repo)}
    registry = register_builtin_steps(StepRegistry())
    result = asyncio.run(registry.get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary
    assert state["review_text"].endswith("**Verdict:** REQUEST CHANGES")
    ev = next(trace.events("agent_ensemble"))
    assert ev["lenses"] == [lens["name"] for lens in _REVIEW_LENSES]
    # every lens sample went through the unified runtime (agent_dispatch each)
    dispatches = list(trace.events("agent_dispatch"))
    assert len(dispatches) == len(_REVIEW_LENSES)
