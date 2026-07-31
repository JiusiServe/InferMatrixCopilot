#!/usr/bin/env python3
"""Private-repository bootstrap for MCP hosts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SOURCE = PROJECT_ROOT / "plugins" / "infermatrix-copilot" / "skills"
SERVER_NAME = "infermatrix-copilot"
PACKAGE = (
    "infermatrix-copilot[mcp] @ "
    "git+https://github.com/JiusiServe/InferMatrixCopilot.git@main"
)
SERVER_COMMAND = ["uvx", "--from", PACKAGE, "infermatrix-copilot-mcp"]


class InstallError(RuntimeError):
    pass


def _run(command: Sequence[str], message: str) -> None:
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise InstallError(message) from exc


def _run_quiet(command: Sequence[str]) -> None:
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def _install_skills(destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    for source in sorted(path for path in SKILLS_SOURCE.iterdir() if path.is_dir()):
        destination = destination_root / source.name
        shutil.copytree(source, destination, dirs_exist_ok=True)
        for path in destination.rglob("*"):
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            if "{{INFERMATRIX_COPILOT_ROOT}}" in content:
                path.write_text(
                    content.replace(
                        "{{INFERMATRIX_COPILOT_ROOT}}",
                        str(PROJECT_ROOT),
                    ),
                    encoding="utf-8",
                )


def _install_codex(config_root: Path) -> None:
    codex = shutil.which("codex")
    if codex is None:
        raise InstallError("Codex CLI is not on PATH.")
    _run_quiet([codex, "mcp", "remove", SERVER_NAME])
    _run(
        [codex, "mcp", "add", SERVER_NAME, "--", *SERVER_COMMAND],
        "Codex MCP registration failed.",
    )
    _install_skills(config_root / ".codex" / "skills")


def _install_claude(config_root: Path) -> None:
    claude = shutil.which("claude")
    if claude is None:
        raise InstallError("Claude Code CLI is not on PATH.")
    _run_quiet([claude, "mcp", "remove", "--scope", "user", SERVER_NAME])
    _run(
        [
            claude,
            "mcp",
            "add",
            "--transport",
            "stdio",
            "--scope",
            "user",
            SERVER_NAME,
            "--",
            *SERVER_COMMAND,
        ],
        "Claude Code MCP registration failed.",
    )
    _install_skills(config_root / ".claude" / "skills")


def _install_cursor(config_root: Path) -> None:
    cursor_root = config_root / ".cursor"
    config_path = cursor_root / "mcp.json"
    cursor_root.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InstallError(
                f"Cursor config is invalid and was not changed: {config_path}"
            ) from exc
        if not isinstance(config, dict):
            raise InstallError(f"Cursor config must be an object: {config_path}")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(
            config_path,
            config_path.with_name(f"{config_path.name}.{timestamp}.bak"),
        )
    else:
        config = {}

    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise InstallError(f"Cursor mcpServers must be an object: {config_path}")
    servers[SERVER_NAME] = {
        "type": "stdio",
        "command": SERVER_COMMAND[0],
        "args": SERVER_COMMAND[1:],
    }
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _install_skills(cursor_root / "skills")


def _cursor_installed(config_root: Path) -> bool:
    if shutil.which("cursor") or shutil.which("cursor-agent"):
        return True
    candidates = [
        config_root / ".cursor",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "cursor" / "Cursor.exe",
        Path("/Applications/Cursor.app"),
    ]
    return any(path.exists() for path in candidates)


def _detect_agents(config_root: Path) -> list[str]:
    agents = []
    if shutil.which("codex"):
        agents.append("codex")
    if shutil.which("claude"):
        agents.append("claude")
    if _cursor_installed(config_root):
        agents.append("cursor")
    return agents


def _write_generic_config(output: Path) -> None:
    output.write_text(
        json.dumps(
            {
                "mcpServers": {
                    SERVER_NAME: {
                        "type": "stdio",
                        "command": SERVER_COMMAND[0],
                        "args": SERVER_COMMAND[1:],
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install InferMatrixCopilot.")
    parser.add_argument(
        "--agent",
        action="append",
        choices=("codex", "claude", "cursor"),
        help="Override automatic Agent detection. May be repeated.",
    )
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path.home(),
        help="Home directory containing Agent configuration.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    config_root = args.config_root.expanduser().resolve()
    agents = list(dict.fromkeys(args.agent or _detect_agents(config_root)))

    if args.dry_run:
        selected = ", ".join(agents) if agents else "generic MCP config"
        print(f"Would install: {selected}")
        print(f"Config root: {config_root}")
        return 0

    if not agents:
        output = PROJECT_ROOT / "infermatrix-copilot.mcp.json"
        _write_generic_config(output)
        print(f"No known Agent detected. MCP config written to:\n  {output}")
        print(f"Portable Skills:\n  {SKILLS_SOURCE}")
        return 0

    failures = []
    installers = {
        "codex": _install_codex,
        "claude": _install_claude,
        "cursor": _install_cursor,
    }
    for agent in agents:
        try:
            installers[agent](config_root)
            print(f"Installed for {agent}.")
        except InstallError as exc:
            failures.append(f"{agent}: {exc}")

    if failures:
        print("Installation incomplete:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print("Restart your Agent, then run: /imreview <PR URL> or /imupdate <repository>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
