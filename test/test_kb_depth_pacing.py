"""Shared native request timing and cooldown, entirely offline."""

import argparse
import json
import multiprocessing
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.depth_pacing import SharedZcodePacer, PacingStopped, is_native_rate_limit
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole, ModelUnavailable
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.trace_store import TraceStore


class Clock:
    def __init__(self): self.now = 100.0
    def __call__(self): return self.now
    def sleep(self, seconds): self.now += seconds


def _pacer(tmp_path, clock=None, **kwargs):
    clock = clock or Clock()
    return SharedZcodePacer(tmp_path / "pacing.json", clock=clock, sleep=clock.sleep, **kwargs), clock


def test_starts_are_shared_persistent_and_waiting_is_outside_file_lock(tmp_path):
    pacer, clock = _pacer(tmp_path)
    events = []
    first = pacer.acquire(events.append)
    other, _ = _pacer(tmp_path, clock)
    second = other.acquire(events.append)
    assert second.started_at - first.started_at == 15
    assert json.loads(pacer.path.read_text())["starts"] == 2
    assert any(event["type"] == "native.throttle.wait" for event in events)
    with pytest.raises(ValueError, match="configuration"):
        SharedZcodePacer(pacer.path, start_interval=20).prepare()


def test_native_429_extends_shared_cooldown_but_doubles_only_once_per_turn(tmp_path):
    pacer, clock = _pacer(tmp_path)
    events = []
    ticket = pacer.acquire(events.append)
    event = {"type": "native.stderr", "text": "Status:429 [1302][您的账户已达到速率限制，请您控制请求频率]"}
    pacer.observe(ticket, event, events.append)
    clock.now += 20
    pacer.observe(ticket, event, events.append)
    state = json.loads(pacer.path.read_text())
    assert state["interval_s"] == 30 and state["cooldown_until"] == 210
    assert state["rate_limited_calls"] == 1
    next_ticket = pacer.acquire(events.append)
    assert next_ticket.started_at == 210
    pacer.observe(next_ticket, event, events.append)
    assert json.loads(pacer.path.read_text())["interval_s"] == 60
    for _ in range(3): pacer.observe(next_ticket, event, events.append)
    assert json.loads(pacer.path.read_text())["interval_s"] == 60
    assert any(event["type"] == "native.throttle.cooldown" for event in events)


def test_success_recovery_is_gradual_and_old_inflight_success_cannot_undo_429(tmp_path):
    pacer, clock = _pacer(tmp_path)
    sink = lambda _event: None
    old = pacer.acquire(sink)
    limited = pacer.acquire(sink)
    pacer.observe(limited, {"type":"native.stderr", "text":"Status:429"}, sink)
    clock.now += 90
    pacer.finish(old, success=True, sink=sink)
    assert json.loads(pacer.path.read_text())["recovery_successes"] == 0
    for _ in range(4):
        ticket = pacer.acquire(sink)
        pacer.finish(ticket, success=True, sink=sink)
    assert json.loads(pacer.path.read_text())["interval_s"] == 25


def test_stop_while_waiting_prevents_dispatch_and_preserves_reservation(tmp_path):
    stop = tmp_path / "STOP"
    pacer, clock = _pacer(tmp_path, stop_file=stop)
    pacer.acquire(lambda _: None)
    before = pacer.path.read_bytes()

    def stopped_sleep(seconds):
        clock.now += seconds
        stop.write_text("stop")

    pacer.sleep = stopped_sleep
    with pytest.raises(PacingStopped): pacer.acquire(lambda _: None)
    assert pacer.path.read_bytes() == before


@pytest.mark.parametrize("event", [
    {"type":"result", "response":"source code checks Status:429"},
    {"type":"model.streaming", "payload":{"delta":"rate limit exceeded"}},
    {"type":"native.stderr", "text":"ordinary diagnostic 429 examples"},
])
def test_generated_text_and_bare_numbers_never_trigger_cooldown(event):
    assert not is_native_rate_limit(event)


def test_gateway_preserves_native_failure_and_fsynced_throttle_receipt(tmp_path):
    store = TraceStore(tmp_path / "traces", environ={})
    pacer, _ = _pacer(tmp_path)

    class Transport:
        supports_native_events = True
        def complete(self, *, native_event_sink, **kwargs):
            native_event_sink({"type":"native.stderr", "text":"Status:429"})
            raise RuntimeError("native turn failed")

    gateway = ModelGateway(None, transport_factory=lambda _:Transport(), recorder=trace_recorder(store), zcode_pacer=pacer)
    with pytest.raises(ModelUnavailable, match="native turn failed"):
        gateway.call_json(ModelRole("generator","zcode","GLM-5.3"),system="s",prompt="p")
    attempt = json.loads(next((store.root / "attempts").glob("*/attempt.json")).read_text())
    assert attempt["status"] == "failed" and attempt["cost_usd"] is None and attempt["usage"] == {}
    native = store.blob(attempt["native_events_sha256"])
    assert "native.throttle.started" in native and "native.throttle.cooldown" in native
    assert len(store.query(kind="model_call")) == 1


@pytest.mark.parametrize("provider", ["zcode", "codex"])
def test_campaign_stop_has_canceled_status_and_no_backend_call(tmp_path, provider):
    store = TraceStore(tmp_path / "traces", environ={})
    stop = tmp_path / "STOP"; stop.write_text("requested")
    pacer, _ = _pacer(tmp_path, stop_file=stop)
    gateway = ModelGateway(None, transport_factory=lambda _:pytest.fail("transport called"), recorder=trace_recorder(store), zcode_pacer=pacer)
    with pytest.raises(ModelUnavailable) as exc:
        gateway.call_json(ModelRole("generator",provider,"model"),system="s",prompt="p")
    assert exc.value.pre_dispatch_cancelled
    attempt = json.loads(next((store.root / "attempts").glob("*/attempt.json")).read_text())
    assert attempt["status"] == "canceled_before_dispatch" and attempt["cost_usd"] is None


def _process_start(path, queue):
    ticket = SharedZcodePacer(Path(path), start_interval=.025, rate_cooldown=.1, max_interval=.1).acquire(lambda _:None)
    queue.put(ticket.started_at)


def test_real_processes_share_one_start_schedule(tmp_path):
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    children = [context.Process(target=_process_start,args=(str(tmp_path/'shared.json'),queue)) for _ in range(4)]
    for child in children: child.start()
    times = sorted(queue.get(timeout=5) for _ in children)
    for child in children:
        child.join(timeout=5)
        assert child.exitcode == 0
    assert all(right-left >= .024 for left,right in zip(times,times[1:]))


def test_stale_checkpoint_and_attempt_read_isolated_from_live_workers(runner, campaign_args, monkeypatch):
    from test_kb_depth_campaign import _offline_processes
    from infermatrix_copilot.kb_service.init_support import InitRecord

    processes, signals = _offline_processes(runner, monkeypatch, codes=(None,0))
    checkpoint = InitRecord(stage="knowledge-deepen",repo=campaign_args.repo,status="running")
    checkpoint.save(campaign_args.state/'worker-0')
    archive = TraceStore(campaign_args.state/'worker-0/init/traces').begin_call({"system":"s","prompt":"p"})
    original = Path.read_bytes

    def stale(path):
        if path.name in {"knowledge-deepen.json", "attempt.json"}:
            raise OSError(116,"Stale file handle")
        return original(path)

    monkeypatch.setattr(Path,"read_bytes",stale)
    sleeps=[]

    def sleep(_seconds):
        assert not signals
        sleeps.append(_seconds)
        if len(sleeps) == 1:
            (campaign_args.state / "STOP").write_text("requested")
        else:
            report = json.loads((campaign_args.state / "drain.json").read_text())
            assert report["progress"][0]["snapshot_error"]["errno"] == 116
            assert report["inflight"][0]["read_error"]["errno"] == 116
            assert report["running_workers"] == [0]
            processes[0].returncode=0

    monkeypatch.setattr(runner.time,"sleep",sleep)
    assert runner.campaign(campaign_args,argparse.ArgumentParser()) == 0
    assert all(child.waited for child in processes)
    assert sleeps == [20, 2]


from test_kb_depth_campaign import runner, campaign_args  # reusable offline fixtures
