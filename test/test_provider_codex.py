"""Codex transport against a fake codex CLI — fully offline (the dev
machine has no ChatGPT login, so the JSONL contract is recorded here from
codex-cli 0.145.0 event shapes and the auth-gap path is what a live
readiness check exercises)."""

import json
import stat
from pathlib import Path

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.providers.base import AgentSessionRequest
from infermatrix_copilot.providers.codex import CodexTransport
from infermatrix_copilot.scopes import read_only_scope
from infermatrix_copilot.tool_bridge import write_bridge_spec

_FAKE_CLI = """#!/usr/bin/env python3
import json, os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
if sys.argv[1:3] == ["login", "status"]:
    if os.path.exists(os.path.join(here, "logged-in")):
        print("Logged in using ChatGPT"); sys.exit(0)
    print("Not logged in"); sys.exit(1)
text = sys.stdin.read()
with open(os.path.join(here, "capture.json"), "w") as f:
    json.dump({"argv": sys.argv[1:], "stdin": text, "cwd": os.getcwd(),
               "env_key": os.environ.get("OPENAI_API_KEY", "")}, f)
if os.path.exists(os.path.join(here, "sleep")):
    time.sleep(10)
failure_path = os.path.join(here, "failure.json")
if os.path.exists(failure_path):
    with open(failure_path) as f:
        failure = json.load(f)
    for event in failure.get("events", []):
        print(json.dumps(event))
    sys.stderr.write(failure.get("stderr", ""))
    sys.exit(failure.get("exit_code", 0))
print(json.dumps({"type": "thread.started", "thread_id": "t1"}))
print(json.dumps({"type": "item.completed", "item": {
    "item_type": "command_execution", "command": "ls"}}))
print(json.dumps({"type": "item.completed", "item": {
    "item_type": "reasoning", "text": "thinking..."}}))
print(json.dumps({"type": "item.completed", "item": {
    "item_type": "agent_message", "text": "REVIEW"}}))
print(json.dumps({"type": "turn.completed", "usage": {
    "input_tokens": 50, "cached_input_tokens": 10, "output_tokens": 9}}))
"""


class FakeTrace:
    def __init__(self):
        self.events = []

    def record(self, kind, **fields):
        self.events.append({"kind": kind, **fields})


def _transport(tmp_path: Path) -> CodexTransport:
    cli = tmp_path / "bin" / "codex"
    cli.parent.mkdir(exist_ok=True)
    cli.write_text(_FAKE_CLI, encoding="utf-8")
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    return CodexTransport(Settings(
        _env_file=None, strict_backend="codex",
        strict_backend_cli=str(cli)))


def _request(tmp_path: Path, with_bridge: bool = True) -> AgentSessionRequest:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    scope = read_only_scope()
    scope = type(scope)(name=scope.name, allowed_tools=scope.allowed_tools,
                        read_only=True, root=str(worktree))
    bridge = write_bridge_spec(run_dir=run_dir, step_name="agent.review_diff",
                               scope=scope, repo="vllm-omni") \
        if with_bridge else None
    return AgentSessionRequest(
        system="SYS", prompt="PROMPT", scope=scope, model="",
        max_iters=8, timeout_s=30.0, run_dir=run_dir,
        step_name="agent.review_diff", bridge_spec_path=bridge,
        trace=FakeTrace())


def test_run_session_sandbox_mcp_and_parse(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "should-not-leak")
    transport = _transport(tmp_path)
    req = _request(tmp_path)

    outcome = transport.run_session(req)

    assert outcome.text == "REVIEW"
    assert (outcome.input_tokens, outcome.output_tokens) == (50, 9)
    assert outcome.tools_used == ["command_execution"]  # reasoning excluded
    assert outcome.tool_calls == 1 and outcome.truncated is False

    capture = json.loads(
        (tmp_path / "bin" / "capture.json").read_text(encoding="utf-8"))
    argv = capture["argv"]
    assert argv[0] == "exec" and "--json" in argv
    assert argv[argv.index("-s") + 1] == "read-only"
    assert "--skip-git-repo-check" in argv and argv[-1] == "-"
    # bridge wired purely via -c config overrides — nothing in the worktree
    overrides = [argv[i + 1] for i, a in enumerate(argv) if a == "-c"]
    assert any("mcp_servers.infermatrix-tools.command=" in o
               for o in overrides)
    assert any("tool_bridge" in o for o in overrides)
    assert capture["stdin"] == "SYS\n\nPROMPT"
    assert capture["env_key"] == ""  # sanitized env


def test_auth_gap_reports_login_fix(tmp_path):
    transport = _transport(tmp_path)
    gap = transport.auth_gap()
    assert gap and "codex login" in gap

    (tmp_path / "bin" / "logged-in").write_text("", encoding="utf-8")
    assert transport.auth_gap() is None


def test_rebase_bridge_approval_is_server_scoped_and_native_stays_readonly(tmp_path):
    transport = _transport(tmp_path)
    req = _request(tmp_path)
    req.scope = type(req.scope)(name="rebase-module", allowed_tools=frozenset(),
                               read_only=False, root=req.scope.root)
    req.bridge_managed_writes = True

    transport.run_session(req)

    capture = json.loads((tmp_path / "bin" / "capture.json").read_text())
    argv = capture["argv"]
    overrides = [argv[i + 1] for i, arg in enumerate(argv) if arg == "-c"]
    approval_overrides = [value for value in overrides if "approval" in value.split("=", 1)[0]]
    assert approval_overrides == [
        'mcp_servers.infermatrix-tools.default_tools_approval_mode="approve"']
    assert argv[argv.index("-s") + 1] == "read-only"
    assert all(value.startswith("mcp_servers.infermatrix-tools.") for value in overrides)


def test_auth_gap_distinguishes_cli_startup_failure(tmp_path):
    transport = _transport(tmp_path)
    cli = tmp_path / "bin" / "codex"
    cli.write_text("#!/bin/sh\necho 'dyld: Library not loaded' >&2\nexit 134\n")
    gap = transport.auth_gap()
    assert "exit 134" in gap and "Library not loaded" in gap
    assert "not logged in" not in gap


def test_run_session_timeout_is_truncated(tmp_path):
    transport = _transport(tmp_path)
    req = _request(tmp_path, with_bridge=False)
    req.timeout_s = 0.8
    (tmp_path / "bin" / "sleep").write_text("", encoding="utf-8")

    outcome = transport.run_session(req)

    assert outcome.truncated is True and outcome.text == ""


def test_nonzero_cli_stderr_survives_in_trace_and_outcome(tmp_path):
    transport = _transport(tmp_path)
    req = _request(tmp_path)
    (tmp_path / "bin" / "failure.json").write_text(json.dumps({
        "events": [{"item": {"type": "agent_message", "text": '{"status":"success"}'}}],
        "stderr": "worker startup failed: missing runtime dependency", "exit_code": 42,
    }))

    outcome = transport.run_session(req)

    result = json.loads(outcome.text)
    assert result["status"] == "blocked"
    assert "code 42" in result["summary"] and "missing runtime dependency" in result["summary"]
    assert req.trace.events[-1]["exit_code"] == 42
    assert req.trace.events[-1]["stderr"] == "worker startup failed: missing runtime dependency"
    with pytest.raises(RuntimeError, match="missing runtime dependency"):
        transport.complete(system="offline", messages=[])


@pytest.mark.parametrize("event", [
    {"type": "error", "message": "model request rejected"},
    {"type": "turn.failed", "error": {"message": "model request rejected"}},
    {"type": "item.error", "error": {"message": "model request rejected"}},
    {"type": "item.completed", "item": {"type": "error", "message": "model request rejected"}},
])
def test_error_event_text_is_exposed_without_a_final_message(tmp_path, event):
    transport = _transport(tmp_path)
    req = _request(tmp_path)
    (tmp_path / "bin" / "failure.json").write_text(json.dumps({"events": [event]}))

    outcome = transport.run_session(req)

    assert json.loads(outcome.text)["status"] == "blocked"
    assert "model request rejected" in outcome.text
    assert "model request rejected" in req.trace.events[-1]["error"]
    assert req.trace.events[-1]["exit_code"] == 0


def test_error_diagnostics_are_bounded(tmp_path):
    transport = _transport(tmp_path)
    req = _request(tmp_path)
    (tmp_path / "bin" / "failure.json").write_text(json.dumps({
        "events": [{"type": "error", "message": "x" * 20000}],
        "stderr": "y" * 20000 + " final cause", "exit_code": 1,
    }))

    outcome = transport.run_session(req)

    assert "final cause" in outcome.text
    assert len(outcome.text) < 8192
    assert len(req.trace.events[-1]["stderr"]) <= 2000
    assert len(req.trace.events[-1]["error"]) <= 4000


def test_complete_runs_in_scratch(tmp_path):
    transport = _transport(tmp_path)

    reply = transport.complete(
        system="CLASSIFY", messages=[{"role": "user", "content": "hi"}])

    assert reply.text == "REVIEW"
    capture = json.loads(
        (tmp_path / "bin" / "capture.json").read_text(encoding="utf-8"))
    assert "imc-codex-oneshot-" in capture["cwd"]
    assert "CLASSIFY" in capture["stdin"] and "[USER]\nhi" in capture["stdin"]
