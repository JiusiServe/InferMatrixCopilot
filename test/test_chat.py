"""Conversational interface: tool round-trips, confirmation, read jail, history."""

import shutil

import pytest

from omni_copilot.chat import ChatSession, _MAX_HISTORY_MESSAGES
from omni_copilot.cli import Copilot
from omni_copilot.config import _REPO_ROOT
from omni_copilot.llm import Block, Reply


class ScriptedChatLLM:
    """Returns scripted replies in order; records what it was asked."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None):
        self.calls.append({"messages": [*messages], "tools": tools})
        reply = self._replies.pop(0)
        if on_text is not None:
            for b in reply.blocks:
                if b.type == "text" and b.text:
                    on_text(b.text)
        return reply


def text(t):
    return Reply(blocks=[Block(type="text", text=t)])


def tool_use(name, args, tid="t1", preamble=""):
    blocks = []
    if preamble:
        blocks.append(Block(type="text", text=preamble))
    blocks.append(Block(type="tool_use", id=tid, name=name, input=args))
    return Reply(blocks=blocks)


@pytest.fixture()
def copilot(settings, git_repo):
    settings.playbooks_dir.mkdir(parents=True)
    shutil.copy(_REPO_ROOT / "playbooks" / "repo-rebase.yaml",
                settings.playbooks_dir / "repo-rebase.yaml")
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    settings.rebase_orchestrator_cmd = "echo chat-rebase-ok"
    return Copilot(settings)


def _session(copilot, replies, assume_yes=True):
    copilot.llm = ScriptedChatLLM(replies)
    out_buf = []
    session = ChatSession(copilot, assume_yes=assume_yes,
                          out=lambda s: out_buf.append(s))
    return session, out_buf


def test_chat_runs_task_and_reports_result(copilot):
    session, out = _session(copilot, [
        tool_use("run_task", {"kind": "repo_rebase"},
                 preamble="I'll rebase the repo now."),
        text("Rebase finished: all steps green."),
    ])
    final = session.turn("please rebase the repo")
    assert final == "Rebase finished: all steps green."
    # the tool result fed back to the model carries the real outcome
    tool_result = session.messages[-2]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert "exit=0" in tool_result["content"]
    assert "completed_steps=['guard', 'rebase', 'report']" in tool_result["content"]
    # a real run dir exists — the task actually executed
    assert copilot.last_run_dir and (copilot.last_run_dir / "RUN_REPORT.md").exists()
    # the tool call was surfaced to the user
    assert any("run_task" in s for s in out)


def test_chat_confirmation_decline_is_respected(copilot, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a: "n")  # user declines
    session, _ = _session(copilot, [
        tool_use("run_task", {"kind": "repo_rebase"}),
        text("Understood, not running it."),
    ], assume_yes=False)  # repo_rebase (write-capable) must ask
    session.turn("rebase the repo")
    tool_result = session.messages[-2]["content"][0]
    assert "exit=1" in tool_result["content"]  # aborted, nothing ran
    assert not copilot.settings.run_root.exists() or \
        not list(copilot.settings.run_root.iterdir())


def test_chat_read_jail(copilot, git_repo, tmp_path):
    session, _ = _session(copilot, [])
    # inside the repo: allowed
    assert "A = 1" in session._dispatch_tool("repo_read",
                                             {"path": str(git_repo / "mod_a.py")})
    # relative paths resolve against the default repo root, not the cwd
    assert "A = 1" in session._dispatch_tool("repo_read", {"path": "mod_a.py"})
    # offset/limit return a numbered line range
    ranged = session._dispatch_tool("repo_read",
                                    {"path": "mod_a.py", "offset": 1, "limit": 1})
    assert ranged == "1: A = 1"
    # outside any allowed root: refused
    secret = tmp_path / "outside.txt"
    secret.write_text("nope")
    assert session._dispatch_tool("repo_read", {"path": str(secret)}).startswith("refused")
    # .env anywhere: refused
    env = git_repo / ".env"
    env.write_text("KEY=1")
    assert "secret" in session._dispatch_tool("repo_read", {"path": str(env)})


def test_chat_status_logs_playbooks_tools(copilot):
    session, _ = _session(copilot, [])
    assert "no runs yet" in session._dispatch_tool("get_status", {})
    assert "repo-rebase@2 [locked]" in session._dispatch_tool("list_playbooks", {})
    assert session._dispatch_tool("unknown_tool", {}) == "unknown tool: unknown_tool"


def test_chat_multi_round_tools_then_answer(copilot):
    session, _ = _session(copilot, [
        tool_use("list_playbooks", {}, tid="t1"),
        tool_use("get_status", {}, tid="t2"),
        text("You have the locked repo-rebase playbook; no runs yet."),
    ])
    final = session.turn("what can you do and what's the current state?")
    assert "locked repo-rebase" in final
    assert len(session.messages) == 6  # user + 2*(assistant+tool_result) + assistant


def test_chat_history_trimming_keeps_pairs(copilot):
    session, _ = _session(copilot, [])
    for i in range(_MAX_HISTORY_MESSAGES + 20):
        session.messages.append({"role": "user" if i % 2 == 0 else "assistant",
                                 "content": f"m{i}"})
    session.messages.append({"role": "user", "content": "latest"})
    session._trim_history()
    assert len(session.messages) <= _MAX_HISTORY_MESSAGES
    assert session.messages[0]["role"] == "user"
    assert isinstance(session.messages[0]["content"], str)


def test_chat_session_trace_persisted(copilot):
    session, _ = _session(copilot, [text("hello there")])
    session.turn("hi")
    events = list(session.trace.events())
    kinds = [e["kind"] for e in events]
    assert kinds == ["user", "assistant"]
