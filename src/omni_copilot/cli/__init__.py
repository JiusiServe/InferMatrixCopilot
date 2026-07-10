"""omni-copilot — conversational CLI (design §3.Y, phases A+B).

REPL + one-shot (-p). NL -> intent -> TaskSpec(s) (echoed; write/push tasks
need confirmation) -> inline plan review for adapted/generated plans ->
planner (reuse > adapt > generate) -> executor. Compound commands ("rebase
pr 12, then review it") become an ordered task queue. Built-ins: /status
/logs /playbooks /resume /quit. Blocked runs exit 3.

This was one 406-line module; it is now a package — `copilot` (the Copilot
orchestrator), `entry` (argparse + REPL wiring, exposes `main`), and `utils`
(pure formatters). The public surface (`Copilot`, `main`) is re-exported so
the `omni_copilot.cli:main` entry point and `from omni_copilot.cli import
Copilot` importers are unchanged.
"""

from __future__ import annotations

from .copilot import Copilot
from .entry import main

__all__ = ["Copilot", "main"]


if __name__ == "__main__":
    import sys

    sys.exit(main())
