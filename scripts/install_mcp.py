#!/usr/bin/env python3
"""Cross-platform MCP installer for Codex, Claude Code, and Cursor."""

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
PYTHON_PATH = PROJECT_ROOT / "src"
VENV_ROOT = PROJECT_ROOT / ".venv"
SKILL_SOURCE = PROJECT_ROOT / "plugin" / "skills" / "imreview"
SERVER_NAME = "infermatrix_copilot"


class InstallError(RuntimeError):
    """An installation error that can be shown directly to the user."""


def _run_checked(command: Sequence[str], error_message: str) -> None:
    try:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise InstallError(error_message) from exc


def _run_quiet(command: Sequence[str]) -> None:
    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def _require_command(name: str, display_name: str) -> str:
    command = shutil.which(name)
    if command is None:
        raise InstallError(f"{display_name} CLI is not on PATH.")
    return command


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_ROOT / "Scripts" / "python.exe"
    return VENV_ROOT / "bin" / "python"


def _install_runtime() -> Path:
    version = ".".join(str(part) for part in sys.version_info[:3])
    print(f"Using Python {version}")
    _run_checked(
        [sys.executable, "-m", "venv", str(VENV_ROOT)],
        "Failed to create the Python virtual environment.",
    )

    venv_python = _venv_python()
    _run_checked(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--quiet",
            "mcp>=1.2,<2",
            "PyYAML>=6.0",
        ],
        "Failed to install the MCP runtime.",
    )
    return venv_python


def _install_imreview_skill(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_SOURCE, destination, dirs_exist_ok=True)


def _install_codex(config_root: Path, venv_python: Path) -> None:
    codex = _require_command("codex", "Codex")
    _run_quiet([codex, "mcp", "remove", SERVER_NAME])
    _run_checked(
        [
            codex,
            "mcp",
            "add",
            SERVER_NAME,
            "--env",
            f"PYTHONPATH={PYTHON_PATH}",
            "--",
            str(venv_python),
            "-m",
            "infermatrix_copilot.thin_mcp_server",
        ],
        "Failed to register InferMatrixCopilot with Codex.",
    )
    _install_imreview_skill(config_root / ".codex" / "skills" / "imreview")


def _install_claude(config_root: Path, venv_python: Path) -> None:
    claude = _require_command("claude", "Claude Code")
    _run_quiet(
        [claude, "mcp", "remove", "--scope", "user", SERVER_NAME]
    )
    _run_checked(
        [
            claude,
            "mcp",
            "add",
            "--transport",
            "stdio",
            "--scope",
            "user",
            "--env",
            f"PYTHONPATH={PYTHON_PATH}",
            SERVER_NAME,
            "--",
            str(venv_python),
            "-m",
            "infermatrix_copilot.thin_mcp_server",
        ],
        "Failed to register InferMatrixCopilot with Claude Code.",
    )
    _install_imreview_skill(config_root / ".claude" / "skills" / "imreview")


def _install_cursor(
    config_root: Path,
    venv_python: Path,
    project_root: Path = PROJECT_ROOT,
) -> None:
    cursor_root = config_root / ".cursor"
    config_path = cursor_root / "mcp.json"
    cursor_root.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InstallError(
                f"Cursor config is not valid JSON and was not changed: "
                f"{config_path}"
            ) from exc
        if not isinstance(config, dict):
            raise InstallError(
                f"Cursor config must be a JSON object and was not changed: "
                f"{config_path}"
            )
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(config_path, config_path.with_name(
            f"{config_path.name}.{timestamp}.bak"
        ))
    else:
        config = {}

    mcp_servers = config.get("mcpServers")
    if mcp_servers is None:
        mcp_servers = {}
        config["mcpServers"] = mcp_servers
    if not isinstance(mcp_servers, dict):
        raise InstallError(
            f"Cursor mcpServers must be a JSON object and was not changed: "
            f"{config_path}"
        )

    mcp_servers[SERVER_NAME] = {
        "command": str(venv_python),
        "args": ["-m", "infermatrix_copilot.thin_mcp_server"],
        "env": {"PYTHONPATH": str(PYTHON_PATH)},
    }
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    command_root = cursor_root / "commands"
    command_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        project_root / "integrations" / "cursor" / "imreview.md",
        command_root / "imreview.md",
    )


def _parse_args(
    argv: Optional[Sequence[str]] = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install InferMatrixCopilot for an MCP Agent."
    )
    parser.add_argument("agent", choices=("codex", "claude", "cursor"))
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path.home(),
        help="Home directory containing the Agent configuration.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the selected paths without changing anything.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required.", file=sys.stderr)
        return 1

    config_root = args.config_root.expanduser().resolve()
    if args.dry_run:
        print(f"Would install InferMatrixCopilot for {args.agent}.")
        print(f"Project: {PROJECT_ROOT}")
        print(f"Config root: {config_root}")
        return 0

    try:
        venv_python = _install_runtime()
        if args.agent == "codex":
            _install_codex(config_root, venv_python)
        elif args.agent == "claude":
            _install_claude(config_root, venv_python)
        else:
            _install_cursor(config_root, venv_python)
    except InstallError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print()
    print(f"Installed for {args.agent}. Restart it, then run:")
    print("  /imreview <PR URL>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
