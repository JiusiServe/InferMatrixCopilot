"""Offline producers exercise lossless native stdout spooling and cleanup."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import time

import pytest

from infermatrix_copilot.providers import zcode
from infermatrix_copilot.trace_store import TraceStore


pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="native process-group and /tmp checks are Linux-specific")


@pytest.fixture
def session():
    # The producer's spool must stay on local temporary storage, rather than
    # inherit a network-backed working tree or test --basetemp.
    with tempfile.TemporaryDirectory(prefix="imc-zcode-spool-test-", dir="/tmp") as raw:
        path = Path(raw)
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
        yield path


@pytest.fixture
def spools(monkeypatch, session):
    original = zcode.subprocess.Popen
    observed = []

    def checked_popen(*args, **kwargs):
        if kwargs.get("cwd") != str(session) or not kwargs.get("start_new_session"):
            return original(*args, **kwargs)
        handles = [kwargs["stdout"], kwargs["stderr"]]
        for handle in handles:
            # A regular file makes Node's writes synchronous, including the
            # producer's final process.exit(). It must not contain public data.
            info = os.fstat(handle.fileno())
            assert stat.S_ISREG(info.st_mode)
            assert stat.S_IMODE(info.st_mode) == 0o600
            target = os.readlink(f"/proc/self/fd/{handle.fileno()}")
            assert target.startswith(str(session) + "/")
        proc = original(*args, **kwargs)
        observed.append((proc, handles))
        return proc

    monkeypatch.setattr(zcode.subprocess, "Popen", checked_popen)
    return observed


def run_python(script, session, sink, *, timeout=5):
    return zcode.ZCodeTransport._stream_run(
        [sys.executable, "-c", script], session, os.environ.copy(), timeout, sink)


def assert_spools_closed(observed, session):
    assert len(observed) == 1
    proc, handles = observed[0]
    assert proc.poll() is not None
    assert all(handle.closed for handle in handles)
    assert list(session.iterdir()) == []


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is needed to reproduce forced-exit stdout loss")
def test_forced_node_exit_keeps_every_reasoning_delta_and_exact_result_with_slow_journal(session, spools, tmp_path):
    count = 3000
    response = json.dumps({"operations": [], "rationale": "complete answer 完整"}, ensure_ascii=False)
    script = "\n".join([
        "const count = 3000;",
        "for (let i=0; i<count; i++) process.stdout.write(JSON.stringify({type:'model.streaming',seq:i,payload:{kind:'reasoning_delta',delta:'x'.repeat(220)}})+'\\n');",
        f"process.stdout.write(JSON.stringify({{type:'result',response:{json.dumps(response)}}})+'\\n');",
        "setTimeout(() => process.exit(0), 1000);",
    ])
    store = TraceStore(tmp_path / "traces", environ={})
    archive = store.begin_call({"provider": "zcode", "model": "fixture", "system": "s", "prompt": "p"})

    def slow_journal(event):
        archive.event(event)
        time.sleep(0.002)

    events, timed_out = zcode.ZCodeTransport._stream_run(
        [shutil.which("node"), "-e", script], session, os.environ.copy(), 20, slow_journal)

    assert not timed_out
    assert len(events) == count + 1
    assert [event["seq"] for event in events[:-1]] == list(range(count))
    assert events[-1] == {"type": "result", "response": response}
    journal = [json.loads(line) for line in archive.events_path.read_text().splitlines()]
    assert journal == events
    assert_spools_closed(spools, session)


def test_completed_producer_is_not_timed_out_while_its_durable_sink_drains(session, spools):
    count = 50
    script = "\n".join([
        "import json,os",
        f"events=[{{'type':'model.streaming','seq':i,'payload':{{'kind':'reasoning_delta','delta':'partial'}}}} for i in range({count})]",
        "events.append({'type':'result','response':'exact final answer'})",
        "os.write(1, ('\\n'.join(json.dumps(e) for e in events)+'\\n').encode())",
    ])
    received = []

    def slow_sink(event):
        received.append(event)
        time.sleep(0.04)

    started = time.monotonic()
    events, timed_out = run_python(script, session, slow_sink, timeout=1.0)

    assert time.monotonic() - started > 1.0
    assert not timed_out
    assert events == received
    assert len(events) == count + 1
    assert events[-1]["response"] == "exact final answer"
    assert_spools_closed(spools, session)


def test_real_timeout_kills_owned_group_and_retains_received_partial_events(session, spools):
    script = "\n".join([
        "import json,os,subprocess,sys,time",
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])",
        "events=[{'type':'session.updated','payload':{'child_pid':child.pid}}, {'type':'model.streaming','payload':{'kind':'reasoning_delta','delta':'retained partial'}}]",
        "os.write(1, ('\\n'.join(json.dumps(e) for e in events)+'\\n').encode())",
        "time.sleep(30)",
    ])
    received = []
    events, timed_out = run_python(script, session, received.append, timeout=0.5)

    assert timed_out
    assert events == received
    assert events[-1]["payload"]["delta"] == "retained partial"
    child_pid = events[0]["payload"]["child_pid"]
    state = Path(f"/proc/{child_pid}/stat")
    deadline = time.monotonic() + 2
    while state.exists() and state.read_text().split(") ", 1)[1].split()[0] != "Z" and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not state.exists() or state.read_text().split(") ", 1)[1].split()[0] == "Z"
    assert_spools_closed(spools, session)


def test_producer_deadline_still_kills_cli_while_event_sink_is_blocked(session, spools):
    script = "\n".join([
        "import json,os,time",
        "os.write(1, (json.dumps({'type':'model.streaming','payload':{'delta':'before blocked sink'}})+'\\n').encode())",
        "time.sleep(30)",
    ])
    received = []

    def blocked_sink(event):
        received.append(event)
        time.sleep(0.9)
        # The reader cannot check its deadline while this callback runs. The
        # independent deadline guard must already have reaped the producer.
        assert spools[0][0].poll() is not None

    events, timed_out = run_python(script, session, blocked_sink, timeout=0.3)

    assert timed_out
    assert events == received
    assert len(events) == 1
    assert events[0]["payload"]["delta"] == "before blocked sink"
    assert_spools_closed(spools, session)


@pytest.mark.parametrize("returncode,with_result", [(3, True), (0, False)])
def test_nonzero_or_missing_result_fails_closed_and_preserves_unterminated_tails(session, spools, returncode, with_result):
    stdout_tail = '{"type":"model.streaming","payload":'
    stderr_tail = "diagnostic without newline"
    script = "\n".join([
        "import json,os",
        "os.write(1,(json.dumps({'type':'model.streaming','payload':{'delta':'before tail'}})+'\\n').encode())",
        *(["os.write(1,(json.dumps({'type':'result','response':'must reject nonzero exit'})+'\\n').encode())"] if with_result else []),
        f"os.write(1,{stdout_tail.encode()!r})",
        f"os.write(2,{stderr_tail.encode()!r})",
        f"os._exit({returncode})",
    ])
    received = []

    with pytest.raises(RuntimeError, match=f"zcode exited {returncode} without a result event"):
        run_python(script, session, received.append)

    assert {"type": "native.stdout", "text": stdout_tail} in received
    assert {"type": "native.stderr", "text": stderr_tail} in received
    assert received[0]["type"] == "model.streaming"
    assert_spools_closed(spools, session)


def test_sink_interrupt_reaps_producer_drains_already_spooled_tails_and_closes_spools(session, spools):
    tail = "received stderr tail"
    script = "\n".join([
        "import json,os,time",
        "events=[{'type':'model.streaming','seq':i,'payload':{'delta':'partial'}} for i in range(3)]",
        f"os.write(2,{tail.encode()!r})",
        "os.write(1, ('\\n'.join(json.dumps(e) for e in events)+'\\n').encode())",
        "time.sleep(30)",
    ])
    received = []
    interruption = KeyboardInterrupt("original sink interruption")

    def interrupted_sink(event):
        received.append(event)
        if len(received) == 1:
            raise interruption

    with pytest.raises(KeyboardInterrupt) as caught:
        run_python(script, session, interrupted_sink)

    assert caught.value is interruption
    assert [event["seq"] for event in received if event["type"] == "model.streaming"] == [0, 1, 2]
    assert {"type": "native.stderr", "text": tail} in received
    assert_spools_closed(spools, session)
