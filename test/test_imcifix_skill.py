from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "infermatrix-copilot" / "skills" / "imcifix" / "SKILL.md"


def test_imcifix_skill_defines_issue_fix_workflow() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "name: imcifix" in text
    assert "/imcifix <issue-or-url>" in text
    assert "$imcifix <issue-or-url>" in text
    assert "Do not claim that" in text
    assert "issue_fix" in text
    assert "Reproduce or narrow the failure" in text
    assert "Do not commit, push, open a PR, or post an issue comment" in text
    assert "fix/<issue>-<short-slug>" in text


def test_docs_expose_imcifix() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    codex = (ROOT / "doc" / "guide" / "hosts" / "codex.md").read_text(encoding="utf-8")
    cursor = (ROOT / "integrations" / "cursor" / "imcifix.md").read_text(encoding="utf-8")

    assert "$imcifix https://github.com/vllm-project/vllm-omni/issues/5023" in readme
    assert "/imcifix <issue-or-url>" in readme
    assert "$imcifix https://github.com/vllm-project/vllm-omni/issues/5023" in codex
    assert "Do not commit, push, open a PR, or post an issue comment" in cursor
