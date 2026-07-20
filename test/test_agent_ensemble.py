"""Ensemble agent steps: perspective-diverse fan-out + verify-and-merge
(run_agent_step_ensemble) and its wiring into agent.review_diff."""

import asyncio
import json

from omni_copilot.engine.agent_runtime import (
    BASE_OUTPUT_SCHEMA,
    run_agent_step_ensemble,
)
from omni_copilot.engine.steps import register_builtin_steps
from omni_copilot.engine.steps.review import _REVIEW_LENSES
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import FailureKind, StepContext
from omni_copilot.llm import Block, Reply


class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None, role=""):
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


def verdicts_reply(*vs, summary="merged", **extra):
    """A reducer reply in the per-candidate verdict contract."""
    return Reply(blocks=[Block(type="text", text=json.dumps(
        {"verdicts": list(vs), "summary": summary, **extra}))])


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
        contract(items=[{"name": "shared"}, {"name": "only-b"}]),   # lens b
        verdicts_reply({"i": 0, "action": "keep"},
                       {"i": 1, "action": "keep"},
                       {"i": 2, "action": "keep"}),                 # reduce
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["shared", "only-a",
                                                    "only-b"]
    assert "lenses" not in output["items"][0]  # tags stripped from the result
    assert result.summary.startswith("[ensemble x2]")

    # each lens got its focus (at the prompt tail — static-system invariant);
    # the merger got the numbered candidates + evidence
    assert "look at A" in llm.calls[0]["messages"][0]["content"]
    assert "look at B" in llm.calls[1]["messages"][0]["content"]
    merge = llm.calls[2]
    assert "verify-and-merge" in merge["system"]
    body = merge["messages"][0]["content"]
    # "shared" collapsed to ONE candidate carrying cross-lens consensus
    assert '"consensus": 2' in body and '"only-a"' in body
    assert "the evidence" in body

    ev = next(trace.events("agent_ensemble"))
    assert ev["lenses"] == ["a", "b"] and ev["candidates"] == 3
    assert ev["merged"] == 3 and ev["verified"] is True


def test_ensemble_small_union_skips_reduction(settings, trace, tmp_path):
    """A small union whose every item has cross-lens consensus needs no
    arbitration — the reducer is never called (its latency was ~25% of
    ensemble wall-clock on small PRs)."""
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),   # lens a
        contract(items=[{"name": "x"}]),   # lens b — same item, consensus 2
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x"]
    assert "lenses" not in output["items"][0]
    assert len(llm.calls) == 2  # no reducer call
    ev = next(trace.events("agent_ensemble"))
    assert ev["candidates"] == 1 and ev["merged"] == 1


def test_ensemble_singleton_without_consensus_still_verified(settings, trace,
                                                             tmp_path):
    """An unreplicated single-lens claim must face the reducer — a
    hallucinated blocker once skipped verification via the small-union fast
    path and became the entire review."""
    llm = ScriptedLLM([
        contract(items=[{"name": "maybe-hallucinated"}]),  # lens a only
        contract(items=[]),                                # lens b: nothing
        verdicts_reply({"i": 0, "action": "drop",
                        "why": "not grounded in the evidence"}),
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert output["items"] == []
    assert len(llm.calls) == 3  # reducer WAS called
    ev = next(trace.events("agent_ensemble"))
    assert ev["dropped"] == 1 and ev["verified"] is True


def test_ensemble_merge_failure_falls_open_to_union(settings, trace, tmp_path):
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}, {"name": "x2"}]),
        contract(items=[{"name": "y"}]),
        Reply(blocks=[Block(type="text", text="prose")]),   # merge unparseable
        Reply(blocks=[Block(type="text", text="still prose")]),  # repair fails
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x", "x2", "y"]
    assert "lenses" not in output["items"][0]
    assert "unverified union" in output["summary"]
    assert next(trace.events("agent_ensemble"))["verified"] is False


def test_ensemble_empty_merge_reply_falls_open_without_repair(settings, trace,
                                                              tmp_path):
    """An empty reducer reply must NOT go through the repair round (which would
    hallucinate a contract from nothing — live bug on PR 4678)."""
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}, {"name": "x2"}]),
        contract(items=[{"name": "y"}]),
        Reply(blocks=[Block(type="text", text="")]),   # reducer returns nothing
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x", "x2", "y"]  # union
    assert len(llm.calls) == 3  # no repair call happened


def test_ensemble_status_comes_from_samples_not_reducer(settings, trace,
                                                        tmp_path):
    """Reducers conflate step status with the reviewed artifact's verdict
    (live bug: merge said needs_review about the PR, step got escalated)."""
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),
        contract(items=[{"name": "x"}]),
        verdicts_reply({"i": 0, "action": "keep"}, status="needs_review"),
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok and output["status"] == "success"


def test_ensemble_reducer_losing_payload_falls_open(settings, trace, tmp_path):
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}, {"name": "x2"}]),
        contract(items=[{"name": "y"}]),
        contract(),  # contract-shaped but no verdicts key
        contract(),  # ...and the repair round loses it again
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x", "x2", "y"]
    assert next(trace.events("agent_ensemble"))["verified"] is False


def test_ensemble_survives_one_failed_lens(settings, trace, tmp_path):
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="text", text="prose")]),    # lens a: no contract
        Reply(blocks=[Block(type="text", text="prose")]),    # ...repair fails too
        contract(items=[{"name": "y"}]),                     # lens b ok
        verdicts_reply({"i": 0, "action": "keep"}),          # merge
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    # T4 salvage: the failed lens still contributes a (candidate-less) sample,
    # so it appears in the lens list; its salvaged text adds no items.
    assert next(trace.events("agent_ensemble"))["lenses"] == ["a", "b"]


def test_ensemble_all_lenses_failed(settings, trace, tmp_path):
    """T4 salvage: unparseable lens finals wrap as needs_review, so an
    all-failed ensemble ESCALATES (raw texts preserved) instead of RETRY."""
    llm = ScriptedLLM([Reply(blocks=[Block(type="text", text="prose")])] * 4)
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert not result.ok and result.failure is FailureKind.ESCALATE


class KeyedLLM:
    """Thread-safe fake for the PARALLEL ensemble path: picks the reply by a
    key found in the system prompt, so lens completion order doesn't matter."""

    def __init__(self, by_key: dict):
        import threading
        self._by_key = by_key
        self._lock = threading.Lock()
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None, role=""):
        with self._lock:
            self.calls.append({"system": system, "messages": [*messages]})
        # lens markers ride the user prompt now (static-system invariant);
        # match on system + first-message content so either placement keys.
        haystack = system + "\n" + str(messages[0].get("content", ""))
        for key, reply in self._by_key.items():
            if key in haystack:
                return reply
        raise AssertionError(f"no scripted reply matches: {haystack[:80]}")


def test_ensemble_parallel_lenses_merge(settings, trace, tmp_path):
    """ensemble_parallel=True runs lenses concurrently; the merge must still
    see every lens's candidates and samples keep lens order."""
    settings.ensemble_parallel = True
    llm = KeyedLLM({
        "Your assigned lens: a": contract(items=[{"name": "from-a"},
                                                 {"name": "from-a2"}]),
        "Your assigned lens: b": contract(items=[{"name": "from-b"}]),
        "verify-and-merge": verdicts_reply({"i": 0, "action": "keep"},
                                           {"i": 1, "action": "keep"},
                                           {"i": 2, "action": "keep"}),
    })
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["from-a", "from-a2",
                                                    "from-b"]
    ev = next(trace.events("agent_ensemble"))
    assert ev["lenses"] == ["a", "b"] and ev["candidates"] == 3
    merge_call = next(c for c in llm.calls if "verify-and-merge" in c["system"])
    body = merge_call["messages"][0]["content"]
    assert '"from-a"' in body and '"from-b"' in body


def test_ensemble_reducer_verdicts_drop_dup_and_failopen(settings, trace,
                                                         tmp_path):
    """Per-candidate reduction: drops need a why, dups consolidate into the
    survivor, and any candidate the reducer does not mention is KEPT (the
    fail-open is per item — free-form reducers silently lost findings)."""
    llm = ScriptedLLM([
        contract(items=[{"name": "real", "comment": "c1"},
                        {"name": "misread", "comment": "c2"},
                        {"name": "same-as-real", "comment": "c3"}]),  # lens a
        contract(items=[{"name": "unjudged", "comment": "c4"}]),      # lens b
        verdicts_reply({"i": 0, "action": "keep", "comment": "rewritten"},
                       {"i": 1, "action": "drop", "why": "misreads evidence"},
                       {"i": 2, "action": "dup", "of": 0}),
        # candidate 3 (unjudged) is never mentioned -> kept unchanged
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["real", "unjudged"]
    assert output["items"][0]["comment"] == "rewritten"
    assert output["items"][1]["comment"] == "c4"
    ev = next(trace.events("agent_ensemble"))
    assert ev["candidates"] == 4 and ev["merged"] == 2 and ev["dropped"] == 1
    assert ev["verified"] is True


def test_ensemble_samples_per_lens_union(settings, trace, tmp_path):
    """Repeat samples per lens: identical items collapse with a consensus
    count; the union across samples is what reaches the reducer."""
    settings.ensemble_samples_per_lens = 2
    llm = ScriptedLLM([
        contract(items=[{"name": "x"}]),   # a/1
        contract(items=[{"name": "x"}]),   # a/2 — identical -> consensus 2
        contract(items=[{"name": "y"}]),   # b/1
        contract(items=[{"name": "z"}]),   # b/2
        verdicts_reply({"i": 0, "action": "keep"}, {"i": 1, "action": "keep"},
                       {"i": 2, "action": "keep"}),
    ])
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert [i["name"] for i in output["items"]] == ["x", "y", "z"]
    assert result.summary.startswith("[ensemble x4]")
    assert '"consensus": 2' in llm.calls[4]["messages"][0]["content"]
    dispatches = [e["step"] for e in trace.events("agent_dispatch")]
    assert dispatches == ["t.step#a/1", "t.step#a/2",
                          "t.step#b/1", "t.step#b/2"]


def test_review_step_caps_comments_deterministically(settings, trace, tmp_path,
                                                     git_repo):
    """The comment budget is enforced in code (severity-ordered, cap 5) — the
    low-signal nit tail goes first. Reducers ignored a prompted cap."""
    settings.review_ensemble = True
    settings.review_depth = "full"  # pin: this test exercises ensemble mechanics
    many = ([{"file": "m.py", "line": i, "severity": "nit",
              "comment": f"n{i}", "evidence": "hunk"} for i in range(4)]
            + [{"file": "m.py", "line": 9, "severity": "major",
                "comment": "big", "evidence": "hunk"}]
            + [{"file": "m.py", "line": 20 + i, "severity": "minor",
                "comment": f"m{i}", "evidence": "hunk"} for i in range(3)])
    from omni_copilot.engine.steps import register_builtin_steps
    llm = ScriptedLLM(
        [contract(review_comments=many)]
        + [contract(review_comments=[])] * (len(_REVIEW_LENSES) - 1)
        + [verdicts_reply()])   # reducer silent -> all 8 kept, then capped
    state = {"diff_text": "diff --git a/m.py b/m.py\n+A = 1",
             "task_spec": {"pr": 9}, "repo_path": str(git_repo)}
    registry = register_builtin_steps(StepRegistry())
    result = asyncio.run(registry.get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary
    kept = result.outputs["review_comments"]
    assert len(kept) == 5
    sevs = [c["severity"] for c in kept]
    assert sevs == ["major", "minor", "minor", "minor", "nit"]
    assert state["review_text"].endswith("**Verdict:** REQUEST CHANGES")


def test_render_verdict_calibration():
    """T4 calibration: only verified blocker/major block; other comments are
    COMMENT (mergeable with asks); none -> APPROVE. Self-declared-uncertain
    majors never block (T3 forensics: 14/15 human-approved PRs got REQUEST
    CHANGES under the old minor-blocks rule). [validated] findings render."""
    from omni_copilot.engine.steps.review import _render_review_md

    major = {"review_comments": [{"file": "a.py", "line": 1, "severity":
                                  "major", "comment": "breaks X", "evidence": "hunk"}]}
    assert _render_review_md(major).endswith("**Verdict:** REQUEST CHANGES")
    minor = {"review_comments": [{"file": "a.py", "line": 1, "severity":
                                  "minor", "comment": "simplify", "evidence": "hunk"}]}
    assert _render_review_md(minor).endswith("**Verdict:** COMMENT")
    uncertain_major = {"review_comments": [
        {"file": "a.py", "line": 1, "severity": "major",
         "comment": "potential gap; comment is uncertain", "evidence": "hunk"}]}
    assert _render_review_md(uncertain_major).endswith("**Verdict:** COMMENT")
    assert _render_review_md({"summary": "clean"}).endswith(
        "**Verdict:** APPROVE")
    validated = {"summary": "clean",
                 "findings": ["[upstream-verify] vllm/x.py:12 — API confirmed"]}
    out = _render_review_md(validated)
    assert "**Validated:**" in out and "x.py:12" in out


def test_review_step_uses_ensemble_when_enabled(settings, trace, tmp_path,
                                                git_repo):
    settings.review_ensemble = True
    settings.review_depth = "full"  # pin: tiny diff would auto-plan light
    comments = [{"file": "mod_a.py", "line": 1, "severity": "major",
                 "comment": "the diff sets A=1 which breaks B — guard it",
                 "evidence": "hunk"}]
    llm = ScriptedLLM(
        [contract(review_comments=comments)] * len(_REVIEW_LENSES)
        + [verdicts_reply({"i": 0, "action": "keep"})]     # merge
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
    plan_ev = next(trace.events("review_plan"))
    assert plan_ev["depth"] == "full" and plan_ev["planner"] == "override"


def test_review_step_auto_plans_light_for_tiny_diff(settings, trace, tmp_path,
                                                    git_repo):
    """A tiny low-risk diff under review_depth=auto runs ONE full-checklist
    pass — no ensemble, no reducer (the Codex-measured 1.1M-token 4-lens run
    on a 2-file/+60-line PR is the regime this removes)."""
    settings.review_ensemble = True
    comments = [{"file": "mod_a.py", "line": 1, "severity": "minor",
                 "comment": "tighten the guard", "evidence": "hunk"}]
    llm = ScriptedLLM([contract(review_comments=comments)])  # exactly one pass
    state = {"diff_text": "diff --git a/mod_a.py b/mod_a.py\n"
                          "--- a/mod_a.py\n+++ b/mod_a.py\n+x = 1",
             "task_spec": {"pr": 9}, "repo_path": str(git_repo)}
    registry = register_builtin_steps(StepRegistry())
    result = asyncio.run(registry.get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary
    plan_ev = next(trace.events("review_plan"))
    assert plan_ev["depth"] == "light" and plan_ev["planner"] == "rules"
    assert len(list(trace.events("agent_dispatch"))) == 1
    assert not list(trace.events("agent_ensemble"))
    assert result.outputs["review_plan"]["depth"] == "light"
    assert "depth=light via rules" in result.summary


def test_review_step_invalid_override_blocks_before_any_llm(settings, trace,
                                                            tmp_path, git_repo):
    """A typo like review_depth=ful must fail fast, never silently downgrade
    an explicitly requested full review."""
    settings.review_ensemble = True
    llm = ScriptedLLM([])   # any LLM call would pop from an empty script
    state = {"diff_text": "diff --git a/m.py b/m.py\n+x = 1",
             "task_spec": {"pr": 9, "params": {"review_depth": "ful"}},
             "repo_path": str(git_repo)}
    registry = register_builtin_steps(StepRegistry())
    result = asyncio.run(registry.get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert not result.ok and result.failure is FailureKind.BLOCKED
    assert "invalid review_depth" in result.summary
    assert not llm.calls


def test_review_step_gray_zone_falls_back_to_standard(settings, trace,
                                                      tmp_path, git_repo):
    """Mid-size diff + unparseable planner reply → deterministic standard
    (logic+behavior): 1 garbage planner call, 2 lens passes, 1 reducer."""
    settings.review_ensemble = True
    body = "\n".join(f"+line {i}" for i in range(60))
    state = {"diff_text": "\n".join(
        f"diff --git a/src/f{i}.py b/src/f{i}.py\n"
        f"--- a/src/f{i}.py\n+++ b/src/f{i}.py\n{body}" for i in range(4)),
        "task_spec": {"pr": 9}, "repo_path": str(git_repo)}
    c1 = [{"file": "src/f0.py", "line": 1, "severity": "major",
           "comment": "breaks the consumer contract", "evidence": "hunk"}]
    c2 = [{"file": "src/f1.py", "line": 2, "severity": "minor",
           "comment": "stale docstring", "evidence": "hunk"}]
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="text", text="prose, not json")]),  # planner
        contract(review_comments=c1),                                # lens 1
        contract(review_comments=c2),                                # lens 2
        verdicts_reply({"i": 0, "action": "keep"},                   # reducer
                       {"i": 1, "action": "keep"}),
    ])
    registry = register_builtin_steps(StepRegistry())
    result = asyncio.run(registry.get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary
    plan_ev = next(trace.events("review_plan"))
    assert plan_ev["planner"] == "llm-fallback"
    assert plan_ev["lenses"] == ["logic", "behavior"]
    assert len(list(trace.events("agent_dispatch"))) == 2
    assert not llm._replies  # the whole script was consumed


def test_review_step_cap_applies_to_light_path(settings, trace, tmp_path,
                                               git_repo):
    """The 5-comment severity-ordered budget is a product cap, not ensemble
    mechanics — it applies to the light single pass too."""
    settings.review_ensemble = True
    many = ([{"file": "m.py", "line": i, "severity": "nit", "comment": f"n{i}",
              "evidence": "hunk"} for i in range(6)]
            + [{"file": "m.py", "line": 9, "severity": "major",
                "comment": "big", "evidence": "hunk"}])
    llm = ScriptedLLM([contract(review_comments=many)])
    state = {"diff_text": "diff --git a/mod_a.py b/mod_a.py\n"
                          "--- a/mod_a.py\n+++ b/mod_a.py\n+x = 1",
             "task_spec": {"pr": 9}, "repo_path": str(git_repo)}
    registry = register_builtin_steps(StepRegistry())
    result = asyncio.run(registry.get("agent.review_diff").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok, result.summary
    kept = result.outputs["review_comments"]
    assert len(kept) == 5 and kept[0]["severity"] == "major"


def test_zero_yield_lens_gets_one_retry(settings, trace, tmp_path):
    """A lens whose candidate list is empty is re-asked once (single lens, not
    a full ensemble re-run); the retry's candidates flow into the merge."""
    settings.ensemble_parallel = False
    settings.ensemble_zero_yield_retry = True
    llm = KeyedLLM({
        "first pass yielded zero": contract(items=[{"name": "late-find"}]),
        "Your assigned lens: a": contract(items=[]),
        "Your assigned lens: b": contract(items=[{"name": "from-b"}]),
        "verify-and-merge": verdicts_reply({"i": 0, "action": "keep"},
                                           {"i": 1, "action": "keep"}),
    })
    result, output = _run(_ctx(settings, trace, tmp_path, llm=llm))
    assert result.ok
    assert any(True for _ in trace.events("lens_zero_yield_retry"))
    assert {i["name"] for i in output["items"]} == {"late-find", "from-b"}
