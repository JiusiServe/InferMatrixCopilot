"""Dual-path (双路径) model-tier routing: the split happens after intent — eco by
default, performance only on an explicit user claim — and the chosen tier selects
the agent-reasoning model. All offline."""

from __future__ import annotations

import asyncio
import json

from infermatrix_copilot.config import Settings
from infermatrix_copilot.engine.agent_runtime import BASE_OUTPUT_SCHEMA, run_agent_step
from infermatrix_copilot.engine.step import StepContext
from infermatrix_copilot.intent import _wants_performance, parse_intent, parse_intents
from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.task_spec import TaskSpec

_PR = {"kind": "pr_review", "pr": 1, "confidence": 0.9}


class FakeLLM:
    """Returns a fixed intent payload regardless of the input text (so the
    deterministic phrase detector, which reads the raw text, is exercised
    independently of the LLM's own `performance` flag)."""
    available = True

    def __init__(self, payload):
        self.payload = payload

    def create(self, **kw):
        text = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return Reply(blocks=[Block(type="text", text=text)])


# ── TaskSpec + Settings tiers ─────────────────────────────────────────────────
def test_taskspec_mode_defaults_eco_and_describe():
    assert TaskSpec(kind="pr_review").mode == "eco"
    assert "performance" not in TaskSpec(kind="pr_review").describe()
    assert "performance" in TaskSpec(kind="pr_review", mode="performance").describe()


def test_model_for_tiers_and_fallbacks():
    import pytest as _pytest

    from infermatrix_copilot.config import TierNotConfiguredError

    base = Settings(_env_file=None, agent_model="base")
    assert base.model_for("eco") == "base"          # eco unset -> agent_model
    # perf unset now FAILS UPFRONT (plan v2) — the silent agent_model fallback
    # is how a run once carried a high-capability label on the eco-class model
    with _pytest.raises(TierNotConfiguredError):
        base.model_for("performance")
    cfg = Settings(_env_file=None, agent_model="base",
                   eco_model="cheap", performance_model="strong")
    assert cfg.model_for("eco") == "cheap"
    assert cfg.model_for("performance") == "strong"
    assert cfg.model_for("anything") == "cheap"     # default path is eco


# ── intent routing (the split point) ──────────────────────────────────────────
def test_intent_defaults_to_eco():
    assert parse_intent("review pr 1", llm=FakeLLM(_PR)).spec.mode == "eco"


def test_intent_llm_performance_flag_upgrades():
    r = parse_intent("review pr 1", llm=FakeLLM({**_PR, "performance": True}))
    assert r.spec.mode == "performance"


def test_intent_explicit_phrase_upgrades_even_when_llm_missed():
    # payload carries NO performance flag; the deterministic phrase forces it
    r = parse_intent("review pr 1 with the high performance model", llm=FakeLLM(_PR))
    assert r.spec.mode == "performance"


def test_intent_chinese_phrase_upgrades():
    assert parse_intent("用高性能模型评审 pr 1", llm=FakeLLM(_PR)).spec.mode == "performance"


def test_wants_performance_detector():
    assert _wants_performance("use the best model")
    assert _wants_performance("强模型")
    assert not _wants_performance("just review this pr, thanks")


def test_compound_global_performance_applies_to_all_segments():
    results = parse_intents("review pr 1, then review pr 2 with the strongest model",
                            llm=FakeLLM(_PR))
    assert len(results) == 2
    assert all(r.spec.mode == "performance" for r in results)


# ── the runner threads the tier's model into run_agent ────────────────────────
class CaptureLLM:
    """Records the `model` of every create call and returns a contract-valid
    final answer (no tool calls)."""
    available = True

    def __init__(self):
        self.models: list[str | None] = []

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None, role=""):
        self.models.append(model)
        base = {k: ([] if "list" in v else "x") for k, v in BASE_OUTPUT_SCHEMA.items()}
        base.update(status="success", summary="s", confidence="high",
                    next_action="none", failure_kind=None)
        return Reply(blocks=[Block(type="text", text=json.dumps(base))])


def _run_step(settings, trace, tmp_path, mode):
    settings.agent_model = "eco-base"
    settings.performance_model = "strong-model"
    llm = CaptureLLM()
    spec = {"kind": "pr_review", "pr": 1}
    if mode:
        spec["mode"] = mode
    ctx = StepContext(settings=settings, state={"task_spec": spec}, params={},
                      run_dir=tmp_path / "run", trace=trace, llm=llm)
    asyncio.run(run_agent_step(ctx, step_name="t.step", purpose="p", evidence={"e": "x"}))
    return llm.models


def test_runner_uses_performance_model_for_performance_tier(settings, trace, tmp_path):
    models = _run_step(settings, trace, tmp_path, mode="performance")
    assert models and all(m == "strong-model" for m in models)


def test_runner_uses_eco_model_by_default(settings, trace, tmp_path):
    models = _run_step(settings, trace, tmp_path, mode=None)  # no mode -> eco
    assert models and all(m == "eco-base" for m in models)


# ── the ensemble reducer rides the tier too (live perf-run regression: lenses
# ran on the performance model while the merge/repair calls silently fell back
# to agent_model) ──────────────────────────────────────────────────────────────
def test_ensemble_reducer_uses_tier_model(settings, trace, tmp_path):
    from infermatrix_copilot.engine.agent_runtime.ensemble import run_agent_step_ensemble

    class EnsembleLLM(CaptureLLM):
        def create(self, *, system, messages, tools=None, model=None,
                   max_tokens=None, on_text=None):
            self.models.append(model)
            base = {k: ([] if "list" in v else "x")
                    for k, v in BASE_OUTPUT_SCHEMA.items()}
            base.update(status="success", summary="s", confidence="high",
                        next_action="none", failure_kind=None,
                        review_comments=[{"file": "a.py", "line": 1,
                                          "severity": "minor", "comment": "c",
                                          "evidence": "e"}])
            return Reply(blocks=[Block(type="text", text=json.dumps(base))])

    settings.agent_model = "eco-base"
    settings.performance_model = "strong-model"
    settings.ensemble_stagger_seconds = 0.0
    llm = EnsembleLLM()
    ctx = StepContext(settings=settings,
                      state={"task_spec": {"kind": "pr_review", "pr": 1,
                                           "mode": "performance"}},
                      params={}, run_dir=tmp_path / "run", trace=trace, llm=llm)
    asyncio.run(run_agent_step_ensemble(
        ctx, step_name="t.step", purpose="p", evidence={"e": "x"},
        lenses=[{"name": "l1", "focus": "f1"}, {"name": "l2", "focus": "f2"}],
        merge_key="review_comments",
        output_extension={"review_comments": "list"}))
    # every LLM call in the ensemble — lenses, merge, repair — uses the tier
    assert llm.models and all(m == "strong-model" for m in llm.models)
