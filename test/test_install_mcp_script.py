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
    strict_config = tmp_path / ".infermatrix-copilot" / ".env"
    assert strict_config.is_file()
    assert "REPO_FULL_NAMES=" in strict_config.read_text(encoding="utf-8")


def test_repo_path_is_saved_for_strict_without_overwriting_secret(
    monkeypatch, tmp_path
):
    installer = _load_installer()
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(installer, "_detect_agents", lambda root: [])
    repo = tmp_path / "vllm-omni"
    (repo / ".git").mkdir(parents=True)
    strict_config = tmp_path / ".infermatrix-copilot" / ".env"
    strict_config.parent.mkdir()
    strict_config.write_text(
        "ANTHROPIC_API_KEY=keep-me\nREPO_PATHS={}\n",
        encoding="utf-8",
    )

    assert installer.main([
        "--config-root",
        str(tmp_path),
        "--repo-path",
        str(repo),
    ]) == 0

    text = strict_config.read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY=keep-me" in text
    assert "OPENAI_API_KEY=" in text
    assert "OPENAI_BASE_URL=" in text
    assert "LLM_PROVIDER=auto" in text
    repo_paths_line = next(
        line for line in text.splitlines()
        if line.startswith("REPO_PATHS=")
    )
    assert json.loads(repo_paths_line.partition("=")[2]) == {
        "vllm-omni": str(repo)
    }
    assert (
        'REPO_FULL_NAMES={"vllm-omni": "vllm-project/vllm-omni"}'
        in text
    )


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


def test_codex_install_sets_timeout_and_installs_current_skill_location(
    monkeypatch, tmp_path
):
    installer = _load_installer()
    monkeypatch.delenv("CODEX_HOME", raising=False)
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        "[mcp_servers.infermatrix-copilot]\n"
        'command = "uvx"\n'
        "startup_timeout_sec = 30\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(installer.shutil, "which", lambda command: command)
    monkeypatch.setattr(installer, "_run", lambda command, message: None)
    monkeypatch.setattr(installer, "_run_quiet", lambda command: None)

    installer._install_codex(tmp_path)

    text = config_path.read_text(encoding="utf-8")
    assert "startup_timeout_sec = 120" in text
    assert text.count("startup_timeout_") == 1
    assert (tmp_path / ".agents" / "skills" / "imreview" / "SKILL.md").is_file()


def test_codex_timeout_supports_quoted_server_table(tmp_path):
    installer = _load_installer()
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[mcp_servers."infermatrix-copilot"]\ncommand = "uvx"\n',
        encoding="utf-8",
    )

    installer._set_codex_startup_timeout(config_path)

    text = config_path.read_text(encoding="utf-8")
    assert "startup_timeout_sec = 120" in text


def test_codex_config_path_honors_codex_home(monkeypatch, tmp_path):
    installer = _load_installer()
    custom_home = tmp_path / "custom-codex"
    monkeypatch.setenv("CODEX_HOME", str(custom_home))

    assert installer._codex_config_path(tmp_path) == custom_home / "config.toml"
