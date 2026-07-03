"""Review engine: Claude Code + skill step (mocked CLI) and its fallback."""

import asyncio
import json

import pytest

from omni_copilot.engine.builtin_steps import register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import StepContext
from omni_copilot.llm import Block, Reply


@pytest.fixture()
def skill_dir(tmp_path):
    d = tmp_path / "skills" / "vllm-omni-review"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: vllm-omni-review\n---\n# review skill")
    return d


def _ctx(settings, trace, tmp_path, state=None, llm=None):
    return StepContext(settings=settings, state=state or {}, params={},
                       run_dir=tmp_path / "run", trace=trace, llm=llm)


def _step():
    return register_builtin_steps(StepRegistry()).get("review.claudecode_skill")


def test_cc_review_happy_path(settings, trace, tmp_path, skill_dir, monkeypatch):
    settings.review_skill_dir = str(skill_dir)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")

        class Out:
            returncode = 0
            stdout = json.dumps({"result": "## Review\n- file.py:1 issue",
                                 "num_turns": 12,
                                 "usage": {"output_tokens": 500}})
            stderr = ""
        return Out()

    monkeypatch.setattr("omni_copilot.engine.cc_review.subprocess.run", fake_run)
    monkeypatch.setattr("omni_copilot.engine.cc_review.shutil.which",
                        lambda b: "/usr/local/bin/claude")

    state = {"task_spec": {"pr": 4803}, "repo_path": "/rebase/vllm-omni"}
    result = asyncio.run(_step().handler(_ctx(settings, trace, tmp_path, state)))
    assert result.ok and result.outputs["engine"] == "claudecode_skill"
    assert state["review_text"].startswith("## Review")

    # safety: allowlist has NO posting-capable tools, and the skill was staged
    allowed = captured["cmd"][captured["cmd"].index("--allowedTools") + 1]
    assert "gh pr view" in allowed and "comment" not in allowed
    assert "Write" not in allowed.split(",") and "Edit" not in allowed.split(",")
    assert (tmp_path / "run" / "cc_review" / ".claude" / "skills"
            / "vllm-omni-review" / "SKILL.md").exists()
    assert "do NOT post" in captured["cmd"][2]


def test_cc_review_falls_back_without_skill_dir(settings, trace, tmp_path):
    settings.review_skill_dir = ""  # not configured

    class FakeLLM:
        available = True

        def create(self, **kwargs):
            return Reply(blocks=[Block(type="text", text="- f.py:1 fallback finding")])

    state = {"task_spec": {"pr": 1}, "diff_text": "diff --git a b"}
    result = asyncio.run(_step().handler(_ctx(settings, trace, tmp_path, state,
                                              llm=FakeLLM())))
    assert result.ok
    assert "fallback: REVIEW_SKILL_DIR not configured" in result.summary
    assert state["review_text"] == "- f.py:1 fallback finding"


def test_cc_review_falls_back_when_cli_missing(settings, trace, tmp_path,
                                               skill_dir, monkeypatch):
    settings.review_skill_dir = str(skill_dir)
    monkeypatch.setattr("omni_copilot.engine.cc_review.shutil.which", lambda b: None)

    class FakeLLM:
        available = True

        def create(self, **kwargs):
            return Reply(blocks=[Block(type="text", text="fallback review")])

    state = {"task_spec": {"pr": 1}, "diff_text": "diff"}
    result = asyncio.run(_step().handler(_ctx(settings, trace, tmp_path, state,
                                              llm=FakeLLM())))
    assert result.ok and "claude CLI not installed" in result.summary


def test_pr_review_playbook_v2_uses_cc_engine():
    from omni_copilot.config import _REPO_ROOT
    from omni_copilot.playbooks.store import PlaybookStore

    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(_REPO_ROOT / "playbooks", registry)
    pb = store.get("pr-review")
    assert pb.version == 2
    assert [s.step for s in pb.steps] == [
        "pr.fetch_diff", "review.claudecode_skill", "pr.post_review",
        "report.final_summary"]
