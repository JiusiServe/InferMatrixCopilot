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
    """True when stdout is a real terminal (or COPILOT_FORCE_FANCY is set) —
    the switch that selects fancy chrome over plain passthrough."""
    return sys.stdout.isatty() or bool(os.environ.get("COPILOT_FORCE_FANCY"))


def style(text: str, *names: str) -> str:
    """ANSI-colorize only when attached to a terminal (safe for tests/pipes)."""
    if not tty():
        return text
    return "".join(ANSI[n] for n in names) + text + ANSI["reset"]


class PlainUI:
    """No-frills sink; `writer` lets tests capture the stream."""

    def __init__(self, writer: Callable[[str], None] | None = None):
        """Use `writer` as the output sink, defaulting to unbuffered stdout
        print; tests pass a capture callable."""
        self.write = writer or (lambda s: print(s, end="", flush=True))

    def banner(self, info: dict) -> None:
        """Print the plain session header (model/repo/playbooks + command hint)."""
        self.write("infermatrix-copilot chat — talk to me about the repo, or ask me to "
                   "run tasks.\n")
        self.write(f"model={info.get('model')} repo={info.get('repo')} "
                   f"playbooks={info.get('playbooks')}\n")
        self.write("(/status /logs /playbooks /resume /quit; Ctrl+C stops a turn)\n")

    def prompt(self) -> str:
        """Return the plain input prompt string."""
        return "copilot> "

    def stream_start(self) -> None:
        """No-op: plain output has no spinner/live region to open."""
        pass

    def stream_delta(self, delta: str) -> None:
        """Write a streamed text chunk straight through."""
        self.write(delta)

    def stream_end(self, full_text: str) -> None:
        """End the reply with a newline (the deltas were already written)."""
        self.write("\n")

    def tool_call(self, name: str, args: str) -> None:
        """Print a one-line notice that tool `name` was called with `args`."""
        self.write(f"\n⚙ {name}({args})\n")

    def tool_result(self, brief: str) -> None:
        """No-op: plain mode omits the tool-result preview line."""
        pass

    def info(self, text: str) -> None:
        """Print an informational line."""
        self.write(text + "\n")

    def error(self, text: str) -> None:
        """Print an error line."""
        self.write(f"⚠ {text}\n")


class FancyUI:
    """rich-powered chrome. Construct only when rich imports and we have a TTY."""

    _TAIL_LINES = 10

    def __init__(self):
        """Create the rich Console and reset the stream buffer / live-region
        handle. Imports rich lazily so PlainUI stays usable when rich is absent."""
        from rich.console import Console

        self.console = Console(highlight=False)
        self._buf = ""
        self._live = None

    # -- session banner ---------------------------------------------------------
    def banner(self, info: dict) -> None:
        """Render the session header as a bordered panel (model/repo/playbooks/
        runs) with a command-hint subtitle."""
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
            table, title="[bold cyan]infermatrix-copilot[/] · conversational repo maintenance",
            subtitle="[dim]/status /logs /playbooks /resume /quit · Ctrl+C stops a turn[/]",
            border_style="cyan", expand=False,
        ))

    def prompt(self) -> str:
        """Return the styled cyan ❯ prompt, wrapping ANSI in \\001/\\002 so
        readline's column math stays correct."""
        # \001/\002 mark zero-width sequences so readline keeps column math right
        return "\001\033[1;36m\002❯\001\033[0m\002 "

    # -- streaming reply: spinner -> live tail -> final markdown ---------------
    def stream_start(self) -> None:
        """Open a transient live region showing a "thinking…" spinner and reset
        the accumulation buffer."""
        from rich.live import Live
        from rich.spinner import Spinner

        self._buf = ""
        self._live = Live(Spinner("dots", text="[dim]thinking…[/]"),
                          console=self.console, refresh_per_second=8,
                          transient=True)
        self._live.start()

    def stream_delta(self, delta: str) -> None:
        """Accumulate `delta` and refresh the live region with a dimmed tail of
        the last `_TAIL_LINES` lines (a rolling preview while the model writes)."""
        from rich.text import Text

        self._buf += delta
        if self._live is not None:
            tail = "\n".join(self._buf.splitlines()[-self._TAIL_LINES:])
            self._live.update(Text(tail, style="dim"))

    def stream_end(self, full_text: str) -> None:
        """Close the live region (the transient tail vanishes) and re-render the
        reply as Markdown, so the final answer replaces the rolling preview."""
        from rich.markdown import Markdown

        if self._live is not None:
            self._live.stop()  # transient: the dim tail disappears...
            self._live = None
        if full_text.strip():
            self.console.print(Markdown(full_text))  # ...replaced by rendered md
        self.console.print()

    # -- tool activity -----------------------------------------------------------
    def tool_call(self, name: str, args: str) -> None:
        """Announce a tool call: stop the live region, flush any preamble text
        the model wrote (as Markdown), then print the styled ⚙ name(args) line."""
        if self._live is not None:
            self._live.stop()
            self._live = None
        if self._buf.strip():  # keep any preamble text the model wrote
            from rich.markdown import Markdown

            self.console.print(Markdown(self._buf))
            self._buf = ""
        self.console.print(f"[bold cyan]⚙ {name}[/][dim]({args})[/]")

    def tool_result(self, brief: str) -> None:
        """Print a dimmed one-line preview of a tool result, when non-empty."""
        if brief:
            self.console.print(f"  [dim]{brief}[/]")

    def info(self, text: str) -> None:
        """Print an informational line to the console."""
        self.console.print(text)

    def error(self, text: str) -> None:
        """Print an error line in bold red."""
        self.console.print(f"[bold red]⚠ {text}[/]")


def make_ui(writer: Callable[[str], None] | None = None):
    """FancyUI on a real terminal, PlainUI otherwise (or when rich is absent)."""
    if writer is None and tty():
        try:
            return FancyUI()
        except ImportError:
            pass
    return PlainUI(writer)
