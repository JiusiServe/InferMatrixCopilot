from pathlib import Path

from infermatrix_copilot.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_wheel_declares_all_strict_runtime_resources() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"knowledge" = "infermatrix_copilot/knowledge"' in text
    assert (
        '"playbooks" = "infermatrix_copilot/_runtime/playbooks"'
        in text
    )
    assert (
        '"adapters" = "infermatrix_copilot/_runtime/adapters"'
        in text
    )
    assert '"skills" = "infermatrix_copilot/_runtime/skills"' in text


def test_source_runtime_defaults_have_strict_resources() -> None:
    settings = Settings(_env_file=None)

    assert (settings.knowledge_dir / "AGENTS.md").is_file()
    assert (settings.playbooks_dir / "pr-review.yaml").is_file()
    assert (
        settings.adapters_dir / "vllm_omni" / "manifest.yaml"
    ).is_file()
    assert (settings.adapters_dir / "afd_plugin" / "manifest.yaml").is_file()
    assert (
        settings.skills_dir / "code-quality-review" / "SKILL.md"
    ).is_file()
