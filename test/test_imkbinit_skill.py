from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "infermatrix-copilot" / "skills" / "imkbinit" / "SKILL.md"


def test_imkbinit_skill_drives_one_stage_through_the_cli() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert text.startswith("---\nname: imkbinit\n")
    assert "/imkbinit <repository>" in text and "$imkbinit <repository>" in text
    assert "{{INFERMATRIX_COPILOT_ROOT}}" in text
    # the stage order and where their records live
    assert "`skeleton` → `feature-discovery` → `modules` → `knowledge` → `deepen` →\n`pr-history` → `harvest-calibration`" in text
    assert "<state-dir>/init/<repo>/<stage>.json" in text
    assert "`$KB_STATE_DIR`" in text
    # publishing counts only merged PRs; a dry run also counts dry-run records
    assert "`MERGED`" in text and "`status: dry_run`" in text
    assert "Dry-run records don't count, so a previewed stage is published\n  next rather than skipped." in text
    # every stage runs; the skill never works around a blocked one or flips auto_merge
    assert "later PR" not in text and "not implemented" not in text
    assert "fewer than five bad cases" in text
    assert "`auto_merge` still needs `kb calibrate` and the shadow period. The skill never\nflips it." in text
    assert "Never work around it by hand." in text
    # dry run by default; publishing only on request, with the double gate
    assert "<imc> kb init <repo> --stage <next> --dry-run" in text
    # the MCP-only install puts no CLI on PATH: the skill resolves a launcher
    assert "command -v infermatrix-copilot" in text
    assert 'uvx --from "<infermatrix-root>[kb]" infermatrix-copilot' in text
    for flag in ("ALLOW_PUSH=1", "ALLOW_POST=1", "KB_INIT_GIT_AUTHOR"):
        assert flag in text
    assert "--suggest-seeds" in text
    # the skill has no logic of its own and stops after one stage
    assert "Never\nedit the generated pages" in text
    assert "Never run two stages in one invocation, and never merge a PR." in text


def test_imkbinit_matches_the_cli_contract() -> None:
    """The stage names and flags the skill tells the host to use are the
    CLI's own, so a renamed stage or flag breaks this test, not a user."""
    from infermatrix_copilot.kb_service.init_support import STAGES

    text = SKILL.read_text(encoding="utf-8")
    cli = (ROOT / "src" / "infermatrix_copilot" / "kb_service" / "cli.py").read_text(encoding="utf-8")
    assert STAGES == ("skeleton", "feature-discovery", "modules", "knowledge", "deepen", "pr-history", "harvest-calibration")
    for stage in STAGES:
        assert f"`{stage}`" in text
    for flag in ("--stage", "--dry-run", "--suggest-seeds"):
        assert f'"{flag}"' in cli and flag in text
    for flag in ("--pr-count", "--budget-usd"):
        assert f'"{flag}"' in cli and flag in text


def test_installer_and_docs_expose_imkbinit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    hosts = (ROOT / "doc" / "guide" / "hosts" / "README.md").read_text(encoding="utf-8")
    mcp = (ROOT / "doc" / "guide" / "mcp.md").read_text(encoding="utf-8")

    assert "`imkbinit`" in readme and "/imkbinit afd-plugin" in readme
    assert "`imkbinit`" in hosts
    assert "plugins/infermatrix-copilot/skills/imkbinit/SKILL.md" in mcp
