from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
IMREVIEW_PROMPTS = (
    ROOT / "plugins" / "infermatrix-copilot" / "skills" / "imreview" / "SKILL.md",
    ROOT / "integrations" / "cursor" / "imreview.md",
)


@pytest.mark.parametrize("prompt_path", IMREVIEW_PROMPTS)
def test_imreview_returns_github_style_findings(prompt_path: Path) -> None:
    prompt = " ".join(prompt_path.read_text(encoding="utf-8").split())

    assert "normal GitHub inline review comment" in prompt
    assert "exact path and line/hunk" in prompt
    assert "do not expose rule IDs, coverage tables, matrices" in prompt
    assert "unless the user explicitly asks for the full audit artifact" in prompt
    assert "Within 60 seconds" in prompt
    assert "pinned head SHA" in prompt
    assert "current CI status, mergeability, and any early findings" in prompt
    assert "not a GitHub comment" in prompt
    assert "do not post an interim review" in prompt
    assert "classify `subtraction_signal`" in prompt
    assert "Use `none` without a minimality proof" in prompt
    assert "Use `triggered` for those changes" in prompt
    assert (
        "After the progress update, run independent knowledge/source and "
        "validation tracks concurrently"
    ) in prompt
    assert "Use the embedded `quick_map`" in prompt
    assert "Do not open the full route file" in prompt
    assert "before reading knowledge, searching source, or running tests" in prompt
    assert "bounded `rg` searches" in prompt
    assert "import/version compatibility preflight" in prompt
    assert "head SHA and an environment fingerprint" in prompt
