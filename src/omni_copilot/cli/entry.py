"""CLI entry: argument parsing, the one-shot/REPL dispatch, and the built-in
command router. The orchestration lives in `Copilot` (copilot.py); this file is
the wiring that turns argv/stdin into calls on it.
"""

from __future__ import annotations

import argparse

from ..intent import parse_intents
from .copilot import Copilot
from .utils import parse_task_params


def _handle_line(copilot: Copilot, line: str, assume_yes: bool,
                 plan_only: bool, force_performance: bool = False) -> int | None:
    """Route one input `line`: `/`-built-ins (status/logs/playbooks/resume/quit)
    are handled inline; anything else is parsed into one-or-more TaskSpecs and
    run as a queue. `force_performance` (the --performance flag) pins every
    resolved spec to the high-performance model tier, an explicit override on top
    of intent's eco-by-default detection. Returns None when nothing runs
    (built-in or blank/clarify), -1 to signal quit, or the queue's exit code."""
    line = line.strip()
    if not line:
        return None
    if line in ("/quit", "/exit", "exit", "quit"):
        return -1
    if line == "/status":
        print(copilot.status())
        return None
    if line.startswith("/logs"):
        parts = line.split()
        print(copilot.logs(int(parts[1]) if len(parts) > 1 else 20))
        return None
    if line == "/playbooks":
        print(copilot.playbooks())
        return None
    if line == "/resume":
        return copilot.resume_last()

    results = parse_intents(line, llm=copilot.llm,
                            default_repo=copilot.settings.default_repo,
                            model=copilot.settings.intent)
    unclear = [r for r in results if r.needs_clarification]
    if unclear:
        print(f"? {unclear[0].clarify}")
        return None
    specs = [r.spec for r in results]
    if force_performance:  # explicit --performance overrides eco-by-default
        for s in specs:
            s.mode = "performance"
    return copilot.run_queue(specs, assume_yes=assume_yes, plan_only=plan_only)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Parses argv and dispatches: --resume / --playbook /
    --prompt run one-shot and return their exit code; otherwise start the
    interactive interface — the conversational chat REPL when an LLM is
    configured (and not --no-chat), else the plain command REPL. `argv` defaults
    to sys.argv. Returns the process exit code."""
    parser = argparse.ArgumentParser(prog="omni-copilot",
                                     description="Conversational repo-maintenance copilot")
    parser.add_argument("-p", "--prompt", help="one-shot natural-language command")
    parser.add_argument("--yes", action="store_true",
                        help="skip confirmation prompts (headless)")
    parser.add_argument("--plan-only", action="store_true",
                        help="resolve and print the plan without executing")
    parser.add_argument("--resume", action="store_true",
                        help="resume the most recent run at its first incomplete step")
    parser.add_argument("--playbook",
                        help="run a specific playbook by name (incl. candidates, "
                             "e.g. repo-rebase-native for validation)")
    parser.add_argument("--report-only", action="store_true",
                        help="with --playbook: read-only variant of the task")
    parser.add_argument("--task-param", action="append", default=[],
                        metavar="KEY=VALUE",
                        help="with --playbook: task param (repeatable), "
                             "e.g. --task-param local_ci_only=true")
    parser.add_argument("--no-chat", action="store_true",
                        help="use the plain command REPL instead of the "
                             "conversational interface")
    parser.add_argument("--performance", action="store_true",
                        help="use the high-performance model tier for this run "
                             "(default: eco / cost-effective)")
    # MCP-only internal entry: execute a run previously reserved by the MCP
    # server, in this fresh subprocess. Hidden from --help.
    parser.add_argument("--execute-reserved", metavar="RUN_ID",
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    copilot = Copilot()

    if args.execute_reserved:
        return copilot.execute_reserved(args.execute_reserved)
    if args.resume:
        return copilot.resume_last()
    if args.playbook:
        params = parse_task_params(args.task_param)
        return copilot.run_playbook(args.playbook, params=params,
                                    report_only=args.report_only,
                                    assume_yes=args.yes, plan_only=args.plan_only)
    if args.prompt:
        code = _handle_line(copilot, args.prompt, args.yes, args.plan_only,
                            force_performance=args.performance)
        return int(code) if code not in (None, -1) else 0

    # Interactive: conversational chat (Claude-Code-style) when an LLM is
    # configured; plain command REPL otherwise / with --no-chat.
    if copilot.llm.available and not args.no_chat:
        from ..chat import chat_repl

        return chat_repl(
            copilot, assume_yes=args.yes,
            handle_builtin=lambda line: _handle_line(copilot, line, args.yes,
                                                     args.plan_only,
                                                     force_performance=args.performance),
        )

    print("omni-copilot — natural-language repo maintenance. "
          "/status /logs /playbooks /resume /quit")
    while True:
        try:
            line = input("copilot> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        code = _handle_line(copilot, line, args.yes, args.plan_only,
                            force_performance=args.performance)
        if code == -1:
            return 0
