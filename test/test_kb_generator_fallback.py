"""Generator outages recover through an explicit, attributed subscription fallback."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.models import (
    ModelGateway, ModelRole, ModelUnavailable, roles_from_env,
)
from infermatrix_copilot.kb_service.replay import export_dataset
from infermatrix_copilot.kb_service.runtime import collect_events, run_intake, trace_recorder
from infermatrix_copilot.trace_store import TraceStore
from test_kb_intake_gate import GEN, JUDGE, _generator_then_judge, _runtime

FALLBACK = ModelRole("generator", "zcode", "GLM-5.3")
PRIMARY = replace(GEN, fallback=FALLBACK)


class Transport:
    stops_at_spend = True

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        answer = self.answer(kwargs) if callable(self.answer) else self.answer
        if isinstance(answer, Exception):
            raise answer
        return SimpleNamespace(
            blocks=[SimpleNamespace(text=answer)], stop_reason="end_turn",
            usage={}, model=kwargs["model"])


def gateway(primary, fallback, *, recorder=None):
    transports = {"claude-code": primary, "zcode": fallback}
    return ModelGateway(None, transport_factory=transports.__getitem__, recorder=recorder)


@pytest.fixture(autouse=True)
def clean_model_env(monkeypatch):
    for key in ("KB_GENERATOR", "KB_JUDGE", "KB_GENERATOR_FALLBACK"):
        monkeypatch.delenv(key, raising=False)


def test_fallback_is_opt_in_and_keeps_codex_judge(monkeypatch):
    generator, judge = roles_from_env()
    assert generator == GEN and generator.fallback is None
    monkeypatch.setenv("KB_GENERATOR_FALLBACK", "zcode:GLM-5.3")
    generator, judge = roles_from_env()
    assert generator == PRIMARY and judge == JUDGE


@pytest.mark.parametrize("spec,judge", [
    ("zcode", "codex:gpt-6-sol:medium"),
    (GEN.label(), "codex:gpt-6-sol:medium"),
    ("codex:gpt-6-mini:low", "codex:gpt-6-sol:medium"),
])
def test_invalid_or_same_family_fallback_is_refused(monkeypatch, spec, judge):
    monkeypatch.setenv("KB_GENERATOR_FALLBACK", spec)
    monkeypatch.setenv("KB_JUDGE", judge)
    with pytest.raises(ValueError):
        roles_from_env()


@pytest.mark.parametrize("failure", [
    RuntimeError("account restricted"),
    TimeoutError("timeout"),
    "Your account is on hold and can't use Claude Code.",
    "",
])
def test_generator_outage_uses_exact_fallback_and_records_both_attempts(failure):
    records = []
    primary, fallback = Transport(failure), Transport('{"operations": []}')
    reply = gateway(primary, fallback, recorder=records.append).call_json(
        PRIMARY, system="policy", prompt="evidence")
    assert reply.role == FALLBACK and reply.served_model == "GLM-5.3"
    assert len(primary.calls) == len(fallback.calls) == 1
    assert primary.calls[0]["messages"] == fallback.calls[0]["messages"]
    assert [r["provider"] for r in records] == ["claude-code", "zcode"]
    assert records[0]["error"] and not records[1]["error"]
    assert records[1]["fallback_from"] == GEN.label()


def test_missing_cli_is_recorded_and_uses_fallback():
    records = []
    fallback = Transport('{"ok": true}')

    def factory(provider):
        if provider == "claude-code":
            raise ModelUnavailable("claude-code CLI is not installed")
        return fallback

    g = ModelGateway(None, transport_factory=factory, recorder=records.append)
    assert g.call_json(PRIMARY, system="s", prompt="p").role == FALLBACK
    assert "not installed" in records[0]["error"] and len(fallback.calls) == 1


def test_primary_success_never_calls_fallback():
    fallback = Transport(RuntimeError("must not be called"))
    reply = gateway(Transport('{"ok": true}'), fallback).call_json(PRIMARY, system="s", prompt="p")
    assert reply.role.label() == GEN.label() and not fallback.calls


def test_schema_failure_retains_existing_primary_repair_path():
    fallback = Transport('{"ok": true}')

    def validate(data):
        if "ok" not in data:
            raise ValueError("missing ok")

    with pytest.raises(ModelUnavailable, match="failed its schema"):
        gateway(Transport('{}'), fallback).call_json(PRIMARY, system="s", prompt="p", validate=validate)
    assert not fallback.calls


def test_fallback_reply_must_pass_the_same_validation():
    def validate(data):
        raise ValueError("invalid operations")

    with pytest.raises(ModelUnavailable, match="invalid operations"):
        gateway(Transport("account restricted"), Transport('{}')).call_json(
            PRIMARY, system="s", prompt="p", validate=validate)


def test_thresholded_call_does_not_spend_a_second_reservation():
    fallback = Transport('{"ok": true}')
    with pytest.raises(ModelUnavailable):
        gateway(Transport("account restricted"), fallback).call_json(
            PRIMARY, system="s", prompt="p", max_budget_usd=1)
    assert not fallback.calls


def test_judge_never_falls_back_even_if_given_a_fallback_role():
    fallback = Transport('{"ok": true}')
    role = replace(GEN, name="judge", fallback=FALLBACK)
    with pytest.raises(ModelUnavailable):
        gateway(Transport("account restricted"), fallback).call_json(role, system="s", prompt="p")
    assert not fallback.calls


def test_payload_omission_applies_to_both_models():
    records = []
    gateway(Transport("account restricted"), Transport('{"ok": true}'), recorder=records.append).call_json(
        PRIMARY, system="private policy", prompt="private evidence", record_payload=False)
    assert len(records) == 2
    assert all(r["system"] == r["prompt"] == r["reply"] == "" for r in records)


def test_pending_event_recovers_and_change_and_trace_attribute_glm_with_codex_review(tmp_path):
    primary = Transport("Your account is on hold and can't use Claude Code.")
    unavailable = Transport(RuntimeError("zcode down"))
    g = gateway(primary, unavailable)
    rt, lifecycle = _runtime(tmp_path, g)
    rt.generator = PRIMARY
    store = TraceStore(tmp_path / "traces", environ={})
    rt.traces = store
    g._recorder = trace_recorder(store)
    collect_events(rt, lifecycle)
    assert run_intake(rt, lifecycle) is None
    assert len(rt.ledger.events("demo", "pending")) == 1
    answer = _generator_then_judge()
    fallback = Transport(lambda kw: json.dumps(answer(FALLBACK, kw["messages"][0]["content"])))
    reviewer = Transport(lambda kw: json.dumps(answer(JUDGE, kw["messages"][0]["content"])))
    transports = {"claude-code": primary, "zcode": fallback, "codex": reviewer}
    g._factory = transports.__getitem__
    changeset = rt.ledger.changeset(run_intake(rt, lifecycle))
    assert changeset["status"] == "gated"
    assert changeset["detail"]["generator"] == FALLBACK.label()
    assert changeset["detail"]["judge"] == JUDGE.label()
    assert not rt.ledger.events("demo", "pending") and reviewer.calls
    fallback_calls = [r for r in store.query(kind="model_call") if r["model"]["provider"] == "zcode"]
    assert fallback_calls[-1]["model"]["served_model"] == "GLM-5.3"
    assert fallback_calls[-1]["result"]["fallback_from"] == GEN.label()
    out = tmp_path / "dataset.jsonl"
    export_dataset(store, out, role="generator")
    generators = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(generators) == 1 and generators[0]["model"]["provider"] == "zcode"
    assert generators[0]["changeset_id"] == changeset["id"]
    assert generators[0]["decision"]["status"] == "pass"
