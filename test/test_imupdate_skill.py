from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "infermatrix-copilot" / "skills" / "imupdate" / "SKILL.md"


def test_imupdate_skill_supports_three_input_modes() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "/imupdate <path-or-repository> [target-tag-or-sha]" in text
    assert "### Local Git path" in text
    assert "### Repository name, alias, or URL" in text
    for alias in ("`vllm-omni`", "`vllmomni`", "`vllm omni`"):
        assert alias in text
    assert "temporary clone" in text
    assert "Never call that result `CLEAN`" in text
    assert "Never silently downgrade" in text

    assert "upstream.audited_sha" in text
    assert "tools/audit_vllm_omni_release.py" in text
    for argument in ("--from", "--to", "--repo", "--mode report-only"):
        assert argument in text
    assert "--mode enforce" in text
    assert "generate or rewrite owner rules automatically" in text


def test_installer_and_docs_expose_imupdate() -> None:
    installer = (ROOT / "scripts" / "install_mcp.py").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "SKILLS_SOURCE" in installer
    assert '_install_skills(config_root / ".agents" / "skills")' in installer
    assert '_install_skills(config_root / ".claude" / "skills")' in installer
    assert '_install_skills(cursor_root / "skills")' in installer
    assert "/imupdate /path/to/vllm-omni" in readme
    assert "$imupdate vllm-omni" in readme
    assert "$imdesign" in readme
    assert "/imdesign 给 scheduler 加抢占开关" in readme
