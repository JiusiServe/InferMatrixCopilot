"""Buffered CLI capture preserves provider-independent timeout and event data."""
import subprocess

import pytest

from infermatrix_copilot.providers.base import json_events, run_cli


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
