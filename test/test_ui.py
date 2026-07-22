"""UI chrome: plain fallback correctness + fancy smoke (no TTY required)."""

import shutil

from infermatrix_copilot.chat import ChatSession
from infermatrix_copilot.cli import Copilot
from infermatrix_copilot.config import _REPO_ROOT
from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.ui import FancyUI, PlainUI, make_ui, style


def test_style_is_passthrough_without_tty():
    # pytest captures stdout -> not a tty -> no ANSI escapes leak into output
    assert style("hello", "green", "bold") == "hello"


def test_make_ui_with_writer_is_plain():
    buf = []
    ui = make_ui(lambda s: buf.append(s))
    assert isinstance(ui, PlainUI)
    ui.banner({"model": "m", "repo": "r", "playbooks": "p"})
    ui.stream_delta("hi")
    ui.tool_call("run_task", "{}")
    ui.stream_end("hi")
    joined = "".join(buf)
    assert "infermatrix-copilot chat" in joined and "⚙ run_task({})" in joined
    assert "\033[" not in joined  # plain means plain


def test_fancy_ui_smoke_without_tty():
    """All FancyUI methods must run headless (rich degrades gracefully)."""
    ui = FancyUI()
    ui.console.file = open("/dev/null", "w")
    ui.banner({"model": "m", "repo": "r", "playbooks": "a[L], b[A]",
               "run_root": "/tmp/x"})
    ui.stream_start()
    ui.stream_delta("# heading\nsome **markdown** text\n")
    ui.tool_call("get_status", "{}")
    ui.tool_result("no runs yet")
    ui.stream_start()
    ui.stream_delta("final answer")
    ui.stream_end("final answer")
    ui.info("done")
    ui.error("boom")
    assert ui.prompt()  # non-empty prompt string
    ui.console.file.close()


def test_chat_session_with_fancy_ui(settings, git_repo):
    """A full scripted turn through the FancyUI path (headless console)."""
    settings.playbooks_dir.mkdir(parents=True)
    shutil.copy(_REPO_ROOT / "playbooks" / "repo-rebase.yaml",
                settings.playbooks_dir / "repo-rebase.yaml")
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    copilot = Copilot(settings)

    class OneShot:
        available = True

        def __init__(self):
            self.replies = [
                Reply(blocks=[Block(type="tool_use", id="t1", name="get_status",
                                    input={})]),
                Reply(blocks=[Block(type="text", text="**no runs yet**")]),
            ]

        def create(self, *, on_text=None, **kwargs):
            reply = self.replies.pop(0)
            if on_text:
                for b in reply.blocks:
                    if b.type == "text":
                        on_text(b.text)
            return reply

    copilot.llm = OneShot()
    ui = FancyUI()
    ui.console.file = open("/dev/null", "w")
    session = ChatSession(copilot, assume_yes=True, ui=ui)
    final = session.turn("status?")
    assert final == "**no runs yet**"
    ui.console.file.close()
