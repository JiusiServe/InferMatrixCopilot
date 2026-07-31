import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_mcp.py"


def _load_installer_module():
    spec = importlib.util.spec_from_file_location("install_mcp", INSTALLER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_is_cross_platform_entrypoint(tmp_path):
    if sys.version_info < (3, 11):
        pytest.skip("The installer requires Python 3.11 or newer.")

    result = subprocess.run(
        [
            sys.executable,
            str(INSTALLER),
            "claude",
            "--config-root",
            str(tmp_path),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Would install InferMatrixCopilot for claude." in result.stdout
    assert f"Config root: {tmp_path.resolve()}" in result.stdout
    assert not (tmp_path / ".claude").exists()


def test_cursor_install_preserves_existing_config(tmp_path):
    installer = _load_installer_module()
    cursor_root = tmp_path / ".cursor"
    cursor_root.mkdir()
    config_path = cursor_root / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "other": "kept",
                "mcpServers": {"existing": {"command": "existing-command"}},
            }
        ),
        encoding="utf-8",
    )

    venv_python = tmp_path / ".venv" / "bin" / "python"
    installer._install_cursor(tmp_path, venv_python, ROOT)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["other"] == "kept"
    assert config["mcpServers"]["existing"]["command"] == "existing-command"
    server = config["mcpServers"]["infermatrix_copilot"]
    assert server["command"] == str(venv_python)
    assert server["args"] == [
        "-m",
        "infermatrix_copilot.thin_mcp_server",
    ]
    assert list(cursor_root.glob("mcp.json.*.bak"))
    assert (cursor_root / "commands" / "imreview.md").is_file()


def test_claude_install_uses_user_scope(monkeypatch, tmp_path):
    installer = _load_installer_module()
    quiet_commands = []
    checked_commands = []
    skill_destinations = []
    monkeypatch.setattr(
        installer,
        "_require_command",
        lambda name, display_name: "claude",
    )
    monkeypatch.setattr(
        installer,
        "_run_quiet",
        lambda command: quiet_commands.append(command),
    )
    monkeypatch.setattr(
        installer,
        "_run_checked",
        lambda command, message: checked_commands.append(command),
    )
    monkeypatch.setattr(
        installer,
        "_install_imreview_skill",
        lambda destination: skill_destinations.append(destination),
    )

    venv_python = tmp_path / ".venv" / "bin" / "python"
    installer._install_claude(tmp_path, venv_python)

    assert quiet_commands == [[
        "claude",
        "mcp",
        "remove",
        "--scope",
        "user",
        "infermatrix_copilot",
    ]]
    assert checked_commands[0][:9] == [
        "claude",
        "mcp",
        "add",
        "--transport",
        "stdio",
        "--scope",
        "user",
        "--env",
        f"PYTHONPATH={installer.PYTHON_PATH}",
    ]
    assert checked_commands[0][-3:] == [
        str(venv_python),
        "-m",
        "infermatrix_copilot.thin_mcp_server",
    ]
    assert skill_destinations == [
        tmp_path / ".claude" / "skills" / "imreview"
    ]
