import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_mcp.py"


def _load_installer():
    spec = importlib.util.spec_from_file_location("install_mcp", INSTALLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_detected_agent_writes_generic_config(monkeypatch, tmp_path):
    installer = _load_installer()
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(installer, "_detect_agents", lambda root: [])

    assert installer.main(["--config-root", str(tmp_path)]) == 0

    generated = tmp_path / "infermatrix-copilot.mcp.json"
    config = json.loads(generated.read_text(encoding="utf-8"))
    server = config["mcpServers"]["infermatrix-copilot"]
    assert server["command"] == "uvx"
    assert "infermatrix-copilot-mcp" in server["args"]


def test_cursor_install_preserves_existing_config(tmp_path):
    installer = _load_installer()
    cursor_root = tmp_path / ".cursor"
    cursor_root.mkdir()
    config_path = cursor_root / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "other": "kept",
                "mcpServers": {"existing": {"command": "existing"}},
            }
        ),
        encoding="utf-8",
    )

    installer._install_cursor(tmp_path)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["other"] == "kept"
    assert config["mcpServers"]["existing"]["command"] == "existing"
    assert config["mcpServers"]["infermatrix-copilot"]["command"] == "uvx"
    assert list(cursor_root.glob("mcp.json.*.bak"))
    assert (cursor_root / "skills" / "imreview" / "SKILL.md").is_file()
    update_skill = cursor_root / "skills" / "imupdate" / "SKILL.md"
    assert update_skill.is_file()
    text = update_skill.read_text(encoding="utf-8")
    assert "{{INFERMATRIX_COPILOT_ROOT}}" not in text
    assert str(ROOT) in text
