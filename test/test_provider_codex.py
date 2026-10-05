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


def test_subscription_requires_chatgpt_login_and_default_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    transport = _transport(tmp_path)
    assert not transport.subscription_billing
    (tmp_path / "bin" / "logged-in").touch()
    assert transport.subscription_billing
    config = tmp_path / "home" / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('model_provider = "custom"\n')
    assert not transport.subscription_billing
    config.write_text('profile = "custom"\n[profiles.custom]\nmodel_provider = "api-provider"\n')
    assert not transport.subscription_billing
    config.write_text('[model_providers.openai]\nbase_url = "https://example.invalid"\n')
    assert not transport.subscription_billing
    config.write_text('malformed = [\n')
    assert not transport.subscription_billing


def test_api_login_and_base_url_do_not_establish_subscription(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    transport = _transport(tmp_path)
    cli = tmp_path / "bin" / "codex"
    cli.write_text('#!/usr/bin/env python3\nprint("Logged in using an API key")\n')
    assert not transport.subscription_billing
    cli.write_text('#!/usr/bin/env python3\nprint("Logged in using ChatGPT")\n')
    assert transport.subscription_billing
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid")
    assert not transport.subscription_billing


@pytest.mark.parametrize("default_mode,custom_mode,approved", [
    ("apikey", "chatgpt", False),
    ("chatgpt", "apikey", True),
])
def test_subscription_probe_and_exec_use_same_sanitized_home(
        tmp_path, monkeypatch, default_mode, custom_mode, approved):
    """An inherited CODEX_HOME cannot approve a different execution login."""
    home = tmp_path / "home"
    default = home / ".codex"
    custom = tmp_path / "custom-codex"
    for directory, mode in ((default, default_mode), (custom, custom_mode)):
        directory.mkdir(parents=True)
        (directory / "auth-mode").write_text(mode)
        (directory / "config.toml").write_text('model_provider = "openai"\n')
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(custom))
    monkeypatch.setenv("OPENAI_API_KEY", "must-be-dropped")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    transport = _transport(tmp_path)
    cli = tmp_path / "bin" / "codex"
    cli.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
here = Path(__file__).parent
kind = "login" if sys.argv[1:3] == ["login", "status"] else "exec"
(here / (kind + "-context.json")).write_text(json.dumps({
    "home": str(home), "custom_home": os.environ.get("CODEX_HOME"),
    "api_key_present": bool(os.environ.get("OPENAI_API_KEY"))}))
if kind == "login":
    mode = (home / "auth-mode").read_text()
    print("Logged in using ChatGPT" if mode == "chatgpt" else "Logged in using an API key")
else:
    sys.stdin.read()
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "fixture"}}))
''')
    assert transport.subscription_billing is approved
    assert transport.auth_gap() is None  # either login is authenticated
    transport._run("offline fixture", cwd=str(tmp_path), timeout_s=5)
    login = json.loads((tmp_path / "bin/login-context.json").read_text())
    execution = json.loads((tmp_path / "bin/exec-context.json").read_text())
    assert login == execution == {"home": str(default), "custom_home": None, "api_key_present": False}


@pytest.mark.parametrize("config", [
    'model_provider = "custom"\n',
    'profile = "api"\n[profiles.api]\nmodel_provider = "custom"\n',
    '[model_providers.openai]\nbase_url = "https://example.invalid"\n',
])
def test_custom_subscription_home_cannot_hide_api_execution_config(tmp_path, monkeypatch, config):
    home = tmp_path / "home"
    default = home / ".codex"
    custom = tmp_path / "custom-codex"
    default.mkdir(parents=True)
    custom.mkdir()
    (default / "config.toml").write_text(config)
    (custom / "config.toml").write_text('model_provider = "openai"\n')
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(custom))
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    transport = _transport(tmp_path)
    (tmp_path / "bin/logged-in").touch()
    assert not transport.subscription_billing
    assert not (tmp_path / "bin/capture.json").exists()


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


def test_run_session_timeout_is_truncated(tmp_path):
    transport = _transport(tmp_path)
    req = _request(tmp_path, with_bridge=False)
    req.timeout_s = 0.8
    (tmp_path / "bin" / "sleep").write_text("", encoding="utf-8")

    outcome = transport.run_session(req)

    assert outcome.truncated is True and outcome.text == ""


def test_complete_runs_in_scratch(tmp_path):
    transport = _transport(tmp_path)

    reply = transport.complete(
        system="CLASSIFY", messages=[{"role": "user", "content": "hi"}])

    assert reply.text == "REVIEW"
    capture = json.loads(
        (tmp_path / "bin" / "capture.json").read_text(encoding="utf-8"))
    assert "imc-codex-oneshot-" in capture["cwd"]
    assert "CLASSIFY" in capture["stdin"] and "[USER]\nhi" in capture["stdin"]


def test_complete_archives_all_buffered_native_events_without_changing_reply(tmp_path):
    transport = _transport(tmp_path)
    events = []

    reply = transport.complete(
        system="CLASSIFY", messages=[{"role": "user", "content": "hi"}],
        native_event_sink=events.append)

    assert transport.supports_native_events
    assert [event["type"] for event in events] == ["native.codex.event"] * 5
    assert [event["payload"]["type"] for event in events] == [
        "thread.started", "item.completed", "item.completed",
        "item.completed", "turn.completed"]
    assert events[1]["payload"]["item"] == {
        "item_type": "command_execution", "command": "ls"}
    assert events[3]["payload"]["item"]["text"] == reply.text == "REVIEW"
    assert reply.stop_reason == "end_turn"
    assert reply.usage["input_tokens"] == 50
    assert reply.usage["output_tokens"] == 9
