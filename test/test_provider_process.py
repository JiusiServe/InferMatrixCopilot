"""Buffered CLI capture preserves provider-independent timeout and event data."""
import subprocess
import sys
import time

import pytest

from infermatrix_copilot.providers.base import json_events, run_cli, stream_cli


@pytest.mark.parametrize("partial", [b'{"result":"partial"}\n', '{"result":"partial"}\n', None])
def test_partial_stdout_survives_timeout_without_claiming_a_completed_process(monkeypatch, partial):
    def timeout(cmd, **kwargs):
        assert cmd == ["native-cli"] and kwargs["cwd"] == "/isolated"
        assert kwargs["env"] == {"HOME": "/auth-home"} and kwargs["input"] == "evidence"
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"], output=partial)

    monkeypatch.setattr(subprocess, "run", timeout)
    stdout, stderr, code, timed_out = run_cli(["native-cli"], cwd="/isolated",
        env={"HOME": "/auth-home"}, input="evidence", timeout_s=10)
    assert timed_out and code == 0 and stderr == ""
    assert json_events(stdout) == ([{"result": "partial"}] if partial else [])


def test_exit_diagnostics_and_no_stdin_policy_remain_available_to_each_provider(monkeypatch):
    def failed(cmd, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL and kwargs["input"] is None
        return subprocess.CompletedProcess(cmd, 7, 'warning\n{"type":"result"}\n', "login expired")

    monkeypatch.setattr(subprocess, "run", failed)
    stdout, stderr, code, timed_out = run_cli(["native-cli"], cwd="/isolated", env={},
                                             stdin=subprocess.DEVNULL, timeout_s=10)
    assert (stderr, code, timed_out) == ("login expired", 7, False)
    assert json_events(stdout) == [{"type": "result"}]


def test_json_events_ignore_noise_and_broken_frames_in_original_order():
    assert json_events('warning\n{broken\n  {"type":"first"}\n[]\n{"type":"last"}\n') == [
        {"type": "first"}, {"type": "last"}]


def test_stream_drains_both_pipes_and_keeps_unicode_stdin_and_unterminated_tails(tmp_path):
    code = ('import sys; text=sys.stdin.read(); '
            'sys.stderr.write("x"*200000+"\\nerror tail"); '
            'sys.stdout.write(str(len(text))+"\\noutput tail")')
    lines = []
    stdout, stderr, rc, timeout = stream_cli([sys.executable, "-u", "-c", code],
        cwd=tmp_path, env={}, deadline=time.monotonic() + 5, input="知识" * 100000,
        on_line=lambda channel, text: lines.append((channel, text)))
    assert (stdout, rc, timeout) == ("200000\noutput tail", 0, None)
    assert stderr == "x" * 200000 + "\nerror tail"
    assert ("stderr", "error tail") in lines and ("stdout", "output tail") in lines


@pytest.mark.parametrize("absolute,idle,expected", [(2, .1, None), (.2, .1, "absolute"), (2, .02, "idle")])
def test_stream_idle_tracks_non_json_stdout_and_absolute_deadline_stays_fixed(tmp_path, absolute, idle, expected):
    code = 'import time; [(print("still working", flush=True), time.sleep(.04)) for _ in range(8)]'
    stdout, _, _, timeout = stream_cli([sys.executable, "-u", "-c", code],
        cwd=tmp_path, env={}, deadline=time.monotonic() + absolute, idle_timeout_s=idle)
    assert timeout == expected
    if expected is None:
        assert stdout.count("still working") == 8


def test_interrupted_stream_preserves_already_received_tail_and_original_error(tmp_path):
    lines = []
    def fail(channel, text):
        lines.append((channel, text))
        if text == "first":
            raise OSError("journal unavailable")
    code = 'import os,time; os.write(1,b"first\\npartial tail"); time.sleep(10)'
    with pytest.raises(OSError, match="journal unavailable"):
        stream_cli([sys.executable, "-u", "-c", code], cwd=tmp_path, env={},
                   deadline=time.monotonic() + 5, on_line=fail)
    assert lines == [("stdout", "first"), ("stdout", "partial tail")]


def test_exited_leader_cannot_leave_descendant_pipes_holding_the_call_open(tmp_path):
    code = ('import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(10)"]); '
            'print("leader complete", flush=True)')
    started = time.monotonic()
    stdout, _, rc, timeout = stream_cli([sys.executable, "-u", "-c", code],
        cwd=tmp_path, env={}, deadline=started + 3)
    assert (stdout, rc, timeout) == ("leader complete\n", 0, None)
    assert time.monotonic() - started < 2


def test_stalled_stdin_writer_cannot_outlive_absolute_deadline(tmp_path):
    started = time.monotonic()
    _, _, _, timeout = stream_cli([sys.executable, "-u", "-c", "import time; time.sleep(10)"],
        cwd=tmp_path, env={}, deadline=started + .1, input="x" * 2_000_000)
    assert timeout == "absolute" and time.monotonic() - started < 2


def test_stdin_write_failure_cleans_up_and_propagates(tmp_path):
    started = time.monotonic()
    with pytest.raises(BrokenPipeError):
        stream_cli([sys.executable, "-u", "-c", "import os,time; os.close(0); time.sleep(10)"],
            cwd=tmp_path, env={}, deadline=started + 3, input="x" * 2_000_000)
    assert time.monotonic() - started < 2
