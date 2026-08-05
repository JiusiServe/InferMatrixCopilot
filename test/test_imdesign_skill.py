from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "infermatrix-copilot" / "skills" / "imdesign" / "SKILL.md"
AGENT = SKILL.parent / "agents" / "openai.yaml"


def test_imdesign_skill_defines_co_design_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "name: imdesign" in text
    assert "/imdesign <goal-or-issue-or-pr>" in text
    assert "$imdesign <goal-or-issue-or-pr>" in text
    assert "co-design packet" in text
    for section in (
        "Problem statement",
        "Proposed design",
        "Implementation plan",
        "Validation plan",
    ):
        assert section in text
    assert "Do not implement" in text


def test_imdesign_agent_metadata_exists() -> None:
    text = AGENT.read_text(encoding="utf-8")

    assert "InferMatrix Design" in text
    assert "$imdesign" in text
