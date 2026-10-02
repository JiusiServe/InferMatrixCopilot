"""Playbook stage handoffs survive plain-JSON state and model outages."""
import asyncio
import json
from types import SimpleNamespace

from infermatrix_copilot.engine.step import FailureKind
from infermatrix_copilot.engine.steps import knowledge
from infermatrix_copilot.kb_service.runtime import collect_events
from test_kb_intake_gate import ScriptedGateway, _generator_then_judge, _runtime


def test_intake_steps_handoff_only_plain_state_and_resume_without_new_draft(tmp_path, monkeypatch):
    gateway = ScriptedGateway(_generator_then_judge())
    rt, lifecycle = _runtime(tmp_path, gateway)
    monkeypatch.setattr(knowledge, "_RUNTIME", rt)
    collect_events(rt, lifecycle)
    ctx = SimpleNamespace(params={"repo": "demo"}, state={"kb_changeset": "old"})
    prepared = asyncio.run(knowledge.prepare_intake(ctx))
    assert prepared.ok
    ctx.state.update(json.loads(json.dumps(prepared.outputs["state_updates"])))
    assert ctx.state["kb_intake_batch"] and ctx.state["kb_changeset"] == ""
    assert asyncio.run(knowledge.draft_intake(ctx)).ok
    calls = len(gateway.calls)
    # Engine resume uses the same checkpoint ID; no Python objects in state.
    assert asyncio.run(knowledge.draft_intake(ctx)).ok
    assert len(gateway.calls) == calls
    gated = asyncio.run(knowledge.gate_intake(ctx))
    assert gated.ok
    ctx.state.update(json.loads(json.dumps(gated.outputs["state_updates"])))
    assert ctx.state["kb_changeset_status"] == "gated"
    assert asyncio.run(knowledge.publish(ctx)).ok
    assert rt.ledger.changeset(ctx.state["kb_changeset"])["status"] == "shadow_recorded"


def test_source_failure_cannot_appear_as_successful_empty_intake(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service.sources import SourceError

    rt, lifecycle = _runtime(tmp_path, ScriptedGateway(_generator_then_judge()))
    monkeypatch.setattr(knowledge, "_RUNTIME", rt)
    collect_events(rt, lifecycle)
    monkeypatch.setattr(rt.github, "history_evidence", lambda *args, **kwargs:
                        (_ for _ in ()).throw(SourceError("incomplete PR files")))
    result = asyncio.run(knowledge.prepare_intake(SimpleNamespace(params={"repo": "demo"}, state={})))
    assert not result.ok and result.failure == FailureKind.BLOCKED
    assert "incomplete PR files" in rt.ledger.events("demo", "pending")[0]["detail"]
    assert not rt.gateway.calls


def test_failed_or_uncertain_gate_is_a_blocked_playbook_with_durable_decision(tmp_path, monkeypatch):
    for verdict in ("no", "unsure"):
        rt, lifecycle = _runtime(tmp_path / verdict, ScriptedGateway(_generator_then_judge(verdict)))
        monkeypatch.setattr(knowledge, "_RUNTIME", rt)
        collect_events(rt, lifecycle)
        ctx = SimpleNamespace(params={"repo": "demo"}, state={})
        prepared = asyncio.run(knowledge.prepare_intake(ctx))
        ctx.state.update(prepared.outputs["state_updates"])
        assert asyncio.run(knowledge.draft_intake(ctx)).ok
        result = asyncio.run(knowledge.gate_intake(ctx))
        assert not result.ok and result.failure == FailureKind.BLOCKED
        updates = result.outputs["state_updates"]
        assert updates["kb_changeset_status"] == {"no": "failed", "unsure": "human"}[verdict]
        assert rt.ledger.changeset(updates["kb_changeset"])["status"] == updates["kb_changeset_status"]
        # Resuming the validation step returns the recorded rejection, not another model call.
        calls = len(rt.gateway.calls)
        assert asyncio.run(knowledge.gate_intake(ctx)).outputs == result.outputs
        assert len(rt.gateway.calls) == calls
