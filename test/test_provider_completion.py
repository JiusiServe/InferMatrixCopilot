"""Native completion preserves evidence and records the final schema verdict."""

import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole, ModelUnavailable
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.providers.completion import complete_native
from infermatrix_copilot.trace_store import TraceStore


@pytest.mark.parametrize("provider", ["cursor", "codex", "claude-code"])
@pytest.mark.parametrize("event", [
    {"type": "tool_call", "tool_call": {"readToolCall": {"args": {"path": "source.py"}}}},
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}]}},
    {"type": "assistant", "message": {"content": [{"type": "future_unknown_block"}]}},
    {"type": "item.completed", "item": {"type": "future_unknown_item"}},
])
def test_native_tool_less_contract_rejects_read_tools_and_unknown_blocks(provider, event, monkeypatch):
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.providers.registry import transport_for_id

    transport = transport_for_id(Settings(_env_file=None), provider)
    data = event if provider == "claude-code" else [event]
    monkeypatch.setattr(transport, "_run", lambda *args, **kwargs: (data, False))
    with pytest.raises(RuntimeError, match="tool calls"):
        transport.complete(system="blind judge", messages=[])


def test_native_completion_budget_receives_paid_usage_after_validation_failure():
    from infermatrix_copilot.budgeting import bind_call_budget

    observed = []
    paid = reply()
    paid.usage = {"input_tokens": 8, "output_tokens": 2}
    transport = SimpleNamespace(complete=lambda **kwargs: paid)
    def reject(_):
        raise ValueError("invalid conclusion")
    with bind_call_budget("domain", lambda request: "ticket", lambda ticket, facts: observed.append(dict(facts))):
        with pytest.raises(ValueError):
            complete_native(lambda: transport, request={"system": "s", "messages": [], "model": "pinned-model"},
                            validate=reject)
    assert observed == [{"sent": True, "reply": paid, "usage": paid.usage, "outcome": "failed"}]


def reply(text='{"ok":true}'):
    return SimpleNamespace(blocks=[SimpleNamespace(text=text)], model="pinned-model",
                           stop_reason="end_turn", usage={})


def test_standalone_completion_keeps_unknown_events_and_pinned_request(tmp_path):
    store, requests = TraceStore(tmp_path, environ={}), []
    event = {"type": "future.native.event", "payload": {"opaque": ["retained"]}}

    class Transport:
        supports_native_events = True

        def complete(self, native_event_sink, **request):
            requests.append(request)
            native_event_sink(event)
            return reply()

    result, value, record, receipt = complete_native(
        Transport, request={"system": "s", "messages": [], "model": "pinned-model", "effort": "high"},
        payload={"system": "s", "prompt": ""}, recorder=trace_recorder(store),
        identity={"provider": "codex"}, validate=lambda _: {"accepted": True})
    assert requests[0]["model"] == "pinned-model" and requests[0]["effort"] == "high"
    assert value == {"accepted": True} and record["cost_usd"] is None
    attempt = json.loads(next((store.root / "attempts").glob("*/attempt.json")).read_text())
    assert event == json.loads(store.blob(attempt["native_events_sha256"]).strip())
    assert attempt["status"] == "complete" and attempt["trace_id"] == receipt["id"]


def test_schema_failure_finalizes_one_failed_receipt_after_native_success(tmp_path):
    store = TraceStore(tmp_path, environ={})

    class Transport:
        def complete(self, **_):
            return reply()

    gateway = ModelGateway(None, transport_factory=lambda _: Transport(), recorder=trace_recorder(store))

    def reject(_):
        raise ValueError("source does not support conclusion")

    with pytest.raises(ModelUnavailable, match="does not support"):
        gateway.call_json(ModelRole("judge", "codex", "pinned-model", "high"),
                          system="s", prompt="evidence", validate=reject)
    attempts = list((store.root / "attempts").glob("*/attempt.json"))
    records = store.query(kind="model_call")
    assert len(attempts) == len(records) == 1
    assert json.loads(attempts[0].read_text())["status"] == "failed"
    assert records[0]["error"] and records[0]["usage"] == {}


def test_omitting_archived_payload_keeps_returned_reply_and_unknown_cost():
    records = []
    gateway = ModelGateway(None, transport_factory=lambda _: SimpleNamespace(complete=lambda **_: reply()),
                           recorder=records.append)
    result = gateway.call_json(ModelRole("generator", "codex", "pinned-model"),
                               system="private", prompt="source", record_payload=False)
    assert result.text == '{"ok":true}' and result.data == {"ok": True} and result.cost_usd is None
    assert len(records) == 1 and records[0]["system"] == records[0]["prompt"] == records[0]["reply"] == ""
