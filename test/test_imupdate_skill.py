from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugin" / "skills" / "imupdate" / "SKILL.md"


def test_imupdate_skill_wraps_the_low_level_release_audit() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "/imupdate <upstream-repo> [target-tag-or-sha]" in text
    assert "upstream.audited_sha" in text
    assert "checkout's `HEAD`" in text
    assert "tools/audit_vllm_omni_release.py" in text
    for argument in ("--from", "--to", "--repo", "--mode report-only"):
        assert argument in text
    assert "--mode enforce" in text
    assert "Never" in text
    assert "generate or rewrite owner rules automatically" in text


def test_installers_expose_imupdate_for_supported_agents() -> None:
    installer = (ROOT / "install-mcp.ps1").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    cursor = (ROOT / "integrations" / "cursor" / "imupdate.md").read_text(
        encoding="utf-8"
    )

    assert 'Install-AgentSkills (Join-Path $ConfigRoot ".codex\\skills")' in installer
    assert 'Install-AgentSkills (Join-Path $ConfigRoot ".claude\\skills")' in installer
    assert "imupdate.md" in installer
    assert "/imupdate D:\\path\\to\\vllm-omni" in readme
    assert "plugin/skills/imupdate/SKILL.md" in cursor
