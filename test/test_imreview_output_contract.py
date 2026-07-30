from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
IMREVIEW_PROMPTS = (
    ROOT / "plugin" / "skills" / "imreview" / "SKILL.md",
    ROOT / "integrations" / "cursor" / "imreview.md",
)


@pytest.mark.parametrize("prompt_path", IMREVIEW_PROMPTS)
def test_imreview_returns_github_style_findings(prompt_path: Path) -> None:
    prompt = " ".join(prompt_path.read_text(encoding="utf-8").split())

    assert "normal GitHub inline review comment" in prompt
    assert "exact path and line/hunk" in prompt
    assert "do not expose rule IDs, coverage tables, matrices" in prompt
    assert "unless the user explicitly asks for the full audit artifact" in prompt
