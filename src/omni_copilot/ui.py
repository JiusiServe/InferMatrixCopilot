"""Terminal chrome for the chat interface.

FancyUI (rich): banner, spinner while thinking, live streaming tail, final
replies rendered as markdown, styled tool-call lines. PlainUI: byte-boring
passthrough used for pipes, tests, and --no-chat — every FancyUI feature
degrades to it, so nothing depends on a TTY.
"""

from __future__ import annotations

import os
import sys
from typing import Callable

ANSI = {
    "reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
    "green": "\033[32m", "red": "\033[31m", "cyan": "\033[36m",
    "yellow": "\033[33m", "magenta": "\033[35m",
}


def tty() -> bool:
    return sys.stdout.isatty() or bool(os.environ.get("COPILOT_FORCE_FANCY"))


def style(text: str, *names: str) -> str:
    """ANSI-colorize only when attached to a terminal (safe for tests/pipes)."""
    if not tty():
        return text
    return "".join(ANSI[n] for n in names) + text + ANSI["reset"]


class PlainUI:
    """No-frills sink; `writer` lets tests capture the stream."""

    def __init__(self, writer: Callable[[str], None] | None = None):
        self.write = writer or (lambda s: print(s, end="", flush=True))

    def banner(self, info: dict) -> None:
        self.write("omni-copilot chat — talk to me about the repo, or ask me to "
                   "run tasks.\n")
        self.write(f"model={info.get('model')} repo={info.get('repo')} "
                   f"playbooks={info.get('playbooks')}\n")
        self.write("(/status /logs /playbooks /resume /quit; Ctrl+C stops a turn)\n")

    def prompt(self) -> str:
        return "copilot> "

    def stream_start(self) -> None:
        pass

    def stream_delta(self, delta: str) -> None:
        self.write(delta)

    def stream_end(self, full_text: str) -> None:
        self.write("\n")

    def tool_call(self, name: str, args: str) -> None:
        self.write(f"\n⚙ {name}({args})\n")

    def tool_result(self, brief: str) -> None:
        pass

    def info(self, text: str) -> None:
        self.write(text + "\n")

    def error(self, text: str) -> None:
        self.write(f"⚠ {text}\n")


class FancyUI:
    """rich-powered chrome. Construct only when rich imports and we have a TTY."""

    _TAIL_LINES = 10

    def __init__(self):
        from rich.console import Console

        self.console = Console(highlight=False)
        self._buf = ""
        self._live = None

    # -- session banner ---------------------------------------------------------
    def banner(self, info: dict) -> None:
        from rich.panel import Panel
        from rich.table import Table

        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim")
        table.add_column()
        table.add_row("model", str(info.get("model", "-")))
        table.add_row("repo", str(info.get("repo", "-")))
        table.add_row("playbooks", str(info.get("playbooks", "-")))
        table.add_row("runs", str(info.get("run_root", "-")))
        self.console.print(Panel(
            table, title="[bold cyan]omni-copilot[/] · conversational repo maintenance",
            subtitle="[dim]/status /logs /playbooks /resume /quit · Ctrl+C stops a turn[/]",
            border_style="cyan", expand=False,
        ))

    def prompt(self) -> str:
        # \001/\002 mark zero-width sequences so readline keeps column math right
        return "\001\033[1;36m\002❯\001\033[0m\002 "

    # -- streaming reply: spinner -> live tail -> final markdown ---------------
    def stream_start(self) -> None:
        from rich.live import Live
        from rich.spinner import Spinner

        self._buf = ""
        self._live = Live(Spinner("dots", text="[dim]thinking…[/]"),
                          console=self.console, refresh_per_second=8,
                          transient=True)
        self._live.start()

    def stream_delta(self, delta: str) -> None:
        from rich.text import Text

        self._buf += delta
        if self._live is not None:
            tail = "\n".join(self._buf.splitlines()[-self._TAIL_LINES:])
            self._live.update(Text(tail, style="dim"))

    def stream_end(self, full_text: str) -> None:
        from rich.markdown import Markdown

        if self._live is not None:
            self._live.stop()  # transient: the dim tail disappears...
            self._live = None
        if full_text.strip():
            self.console.print(Markdown(full_text))  # ...replaced by rendered md
        self.console.print()

    # -- tool activity -----------------------------------------------------------
    def tool_call(self, name: str, args: str) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        if self._buf.strip():  # keep any preamble text the model wrote
            from rich.markdown import Markdown

            self.console.print(Markdown(self._buf))
            self._buf = ""
        self.console.print(f"[bold cyan]⚙ {name}[/][dim]({args})[/]")

    def tool_result(self, brief: str) -> None:
        if brief:
            self.console.print(f"  [dim]{brief}[/]")

    def info(self, text: str) -> None:
        self.console.print(text)

    def error(self, text: str) -> None:
        self.console.print(f"[bold red]⚠ {text}[/]")


def make_ui(writer: Callable[[str], None] | None = None):
    """FancyUI on a real terminal, PlainUI otherwise (or when rich is absent)."""
    if writer is None and tty():
        try:
            return FancyUI()
        except ImportError:
            pass
    return PlainUI(writer)
