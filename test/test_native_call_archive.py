"""Durable native call journals: offline transports and local fake CLI only."""

import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole, ModelUnavailable
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.providers.zcode import ZCodeTransport
from infermatrix_copilot.trace_store import REDACTED, TraceStore, trace_context

ROLE = ModelRole("generator", "zcode", "GLM-5.3")


def _attempts(store):
    return [json.loads(path.read_text()) for path in store.root.glob("attempts/*/attempt.json")]


@pytest.mark.parametrize("failure", [RuntimeError("native failed"), KeyboardInterrupt()])
def test_inputs_precede_dispatch_and_partial_events_survive_failure(tmp_path, failure):
    store = TraceStore(tmp_path / "traces", environ={})

    class Transport:
        supports_native_events = True
        native_snapshot = ZCodeTransport.native_snapshot

        def complete(self, *, native_event_sink, **_):
            (pending,) = _attempts(store)
            assert pending["status"] == "inflight"
            assert store.blob(pending["inputs"]["system"]) == "system instructions"
            assert store.blob(pending["inputs"]["prompt"]) == "full input"
            native_event_sink({"type": "session.updated", "payload": {"sessionId": "native-123", "modelId": "GLM-5.3"}})
            native_event_sink({"type": "model.streaming", "payload": {"delta": "partial answer"}})
            raise failure

    gateway = ModelGateway(None, transport_factory=lambda _: Transport(), recorder=trace_recorder(store))
    with trace_context(run_id="archive-test"), pytest.raises(KeyboardInterrupt if isinstance(failure, KeyboardInterrupt) else ModelUnavailable):
        gateway.call_json(ROLE, system="system instructions", prompt="full input")
    (attempt,) = _attempts(store)
    (record,) = store.query(kind="model_call")
    assert attempt["status"] == ("interrupted" if isinstance(failure, KeyboardInterrupt) else "failed")
    assert attempt["trace_id"] == record["id"]
    assert attempt["served_model"] == "GLM-5.3" and attempt["native_session_ids"] == ["native-123"]
    assert attempt["usage"] == {} and attempt["cost_usd"] is None
    assert "partial answer" in store.blob(attempt["native_events_sha256"])
    assert store.blob(record["outputs"]["native_events"]) == store.blob(attempt["native_events_sha256"])
    assert record["context"]["run_id"] == "archive-test"


def test_pending_archive_is_readable_by_a_fresh_store_and_secrets_are_redacted(tmp_path):
    store = TraceStore(tmp_path, environ={"API_KEY": "secret-value-12345"})
    archive = store.begin_call({"system": "secret-value-12345", "prompt": "input", "provider": "zcode"})
    archive.event({"type": "native.debug", "payload": {"apiKey": "short-key", "accessToken": "short-token", "inputTokens": 5}})
    fresh = TraceStore(tmp_path, environ={})
    (attempt,) = _attempts(fresh)
    assert attempt["status"] == "inflight" and fresh.blob(attempt["inputs"]["system"]) == REDACTED
    text = (archive.path / "native-events.jsonl").read_text()
    assert "short-key" not in text and "short-token" not in text and '"inputTokens": 5' in text
    assert not fresh.query(kind="model_call")  # a pending attempt is not a second billed call


def test_thirteen_isolated_workers_never_overwrite_native_attempts(tmp_path):
    ids = set()
    for number in range(13):
        store = TraceStore(tmp_path / f"worker-{number}" / "init/traces", environ={})
        archive = store.begin_call({"system": "s", "prompt": str(number), "provider": "zcode"})
        archive.event({"type": "session.updated", "payload": {"sessionId": str(number)}})
        ids.add(archive.id)
    assert len(ids) == 13
    assert len(list(tmp_path.glob("worker-*/init/traces/attempts/*/attempt.json"))) == 13


def _cli_transport(tmp_path, *, mode="ok", timeout=5):
    cli = tmp_path / "zcode"
    cli.write_text("#!/usr/bin/env python3\n" + "\n".join([
        "import json, sys, time",
        "def emit(value): print(json.dumps(value), flush=True)",
        "emit({'type':'session.updated','payload':{'modelId':'GLM-5.3','sessionId':'cli-native'}})",
        "emit({'type':'model.streaming','payload':{'delta':'partial'}})",
        "emit({'type':'native.debug','payload':{'apiKey':'secret-short'}})",
        "time.sleep(5)" if mode == "timeout" else "pass",
        "sys.exit(3)" if mode == "fail" else "pass",
        "emit({'type':'result','response':'{\\\"ok\\\": true}','usage':{'inputTokens':7}})",
    ]) + "\n")
    cli.chmod(0o700)
    return ZCodeTransport(Settings(_env_file=None, strict_backend="zcode", strict_backend_cli=str(cli), strict_backend_timeout_s=timeout))


@pytest.mark.parametrize("mode", ["ok", "fail", "timeout"])
def test_zcode_stream_is_archived_on_success_failure_and_timeout(tmp_path, mode):
    transport = _cli_transport(tmp_path, mode=mode, timeout=0.15 if mode == "timeout" else 5)
    store = TraceStore(tmp_path / "traces", environ={})
    gateway = ModelGateway(None, transport_factory=lambda _: transport, recorder=trace_recorder(store))
    if mode == "ok":
        reply = gateway.call_json(ROLE, system="system", prompt="input")
        assert reply.data == {"ok": True} and reply.usage == {"input_tokens": 7}
        assert reply.cost_usd is None
    else:
        with pytest.raises(ModelUnavailable):
            gateway.call_json(ROLE, system="system", prompt="input")
    (attempt,) = _attempts(store)
    assert attempt["status"] == ("complete" if mode == "ok" else "failed")
    assert attempt["served_model"] == "GLM-5.3" and attempt["native_session_ids"] == ["cli-native"]
    events = store.blob(attempt["native_events_sha256"])
    assert "partial" in events and "secret-short" not in events
    if mode != "ok":
        assert attempt["usage"] == {} and attempt["cost_usd"] is None


def test_zcode_event_sink_interruption_reaps_cli_and_preserves_flushed_events(tmp_path):
    transport = _cli_transport(tmp_path)
    events = []

    def sink(event):
        events.append(event)
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        transport.complete(system="s", messages=[], model="GLM-5.3", native_event_sink=sink)
    assert events[0]["payload"]["sessionId"] == "cli-native"


def test_reported_usage_and_actual_model_survive_a_post_response_failure(tmp_path):
    store = TraceStore(tmp_path, environ={})

    class Transport:
        supports_native_events = True
        native_snapshot = ZCodeTransport.native_snapshot

        def complete(self, *, native_event_sink, **_):
            native_event_sink({"type": "session.updated", "payload": {"modelId": "GLM-5.3-Flash"}})
            native_event_sink({"type": "result", "response": '{"ok":true}', "usage": {"inputTokens": 4, "costUsd": 0.02}})
            raise RuntimeError("model mismatch")

    gateway = ModelGateway(None, transport_factory=lambda _: Transport(), recorder=trace_recorder(store))
    with pytest.raises(ModelUnavailable):
        gateway.call_json(ROLE, system="s", prompt="p")
    (attempt,) = _attempts(store)
    assert attempt["served_model"] == "GLM-5.3-Flash"
    assert attempt["usage"] == {"input_tokens": 4, "cost_usd": 0.02} and attempt["cost_usd"] == 0.02
    assert store.blob(attempt["outputs"]["reply"]) == '{"ok":true}'


def test_pending_native_identity_is_persisted_before_final_receipt(tmp_path):
    store = TraceStore(tmp_path, environ={})
    archive = store.begin_call({"system": "s", "prompt": "p"})
    archive.event({"type": "session.updated", "payload": {"sessionId": "pending-native", "modelId": "GLM-5.3"}})
    (attempt,) = _attempts(store)
    assert attempt["status"] == "inflight" and attempt["served_model"] == "GLM-5.3"
    assert attempt["native_session_ids"] == ["pending-native"]
    assert attempt["cost_usd"] is None and attempt["usage"] == {}


def test_final_payload_survives_missing_standard_receipt(tmp_path):
    store = TraceStore(tmp_path, environ={})
    archive = store.begin_call({"system": "s", "prompt": "p"})
    archive.finish(None, {"reply": "final output", "usage": {}, "cost_usd": None}, status="complete")
    (attempt,) = _attempts(store)
    assert attempt["trace_id"] == "" and store.blob(attempt["outputs"]["reply"]) == "final output"


def test_interrupted_validation_keeps_the_completed_response_and_usage(tmp_path):
    store = TraceStore(tmp_path, environ={})

    class Transport:
        def complete(self, **_):
            return SimpleNamespace(blocks=[SimpleNamespace(text='{"ok":true}')], model="GLM-5.3",
                                   usage={"input_tokens": 3}, stop_reason="end_turn")

    gateway = ModelGateway(None, transport_factory=lambda _: Transport(), recorder=trace_recorder(store))

    def validate(_):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        gateway.call_json(ROLE, system="s", prompt="p", validate=validate)
    (attempt,) = _attempts(store)
    (record,) = store.query(kind="model_call")
    assert attempt["status"] == "interrupted" and attempt["usage"] == {"input_tokens": 3}
    assert attempt["trace_id"] == record["id"] and record["error"] == "KeyboardInterrupt"
    assert store.blob(attempt["outputs"]["reply"]) == '{"ok":true}'


@pytest.mark.parametrize("channel", ["stdout", "stderr"])
def test_interrupted_stream_keeps_already_read_tail_without_newline(tmp_path, channel):
    import sys
    other = "stderr" if channel == "stdout" else "stdout"
    script = (f"import sys,time; sys.{channel}.write('partial diagnostic'); sys.{channel}.flush(); "
              f"time.sleep(0.15); sys.{other}.write('interrupt\\n'); sys.{other}.flush(); time.sleep(5)")
    events = []

    def sink(event):
        events.append(event)
        if event.get("text") == "interrupt":
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        ZCodeTransport._stream_run([sys.executable, "-c", script], tmp_path, {}, 5, sink)
    assert {"type": "native." + channel, "text": "partial diagnostic"} in events
