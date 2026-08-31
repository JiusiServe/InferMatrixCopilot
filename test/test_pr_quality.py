from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import FailureKind, StepContext
from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.llm import Block, Reply


class QualityLLM:
    available = True

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def for_target(self, _target):
        return self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return Reply(blocks=[Block(type="text", text=json.dumps(self.payload))])


def _run(settings, trace, tmp_path, payload):
    llm = QualityLLM(payload)
    state = {
        "diff_text": "diff --git a/a.py b/a.py\n+value = 1\n",
        "pr_context": "Title: add value\nBody: validates the new value",
        "task_spec": {
            "kind": "pr_quality", "pr": 7, "mode": "eco",
            "params": {"deterministic_signals": ["Q2: no test changes"]},
        },
    }
    ctx = StepContext(
        settings=settings, state=state, params={},
        run_dir=tmp_path / "run", trace=trace, llm=llm,
    )
    step = register_builtin_steps(StepRegistry()).get(
        "agent.assess_pr_quality")
    return asyncio.run(step.handler(ctx)), llm


def test_quality_step_returns_grounded_needs_rework(settings, trace, tmp_path):
    result, llm = _run(settings, trace, tmp_path, {
        "verdict": "needs_rework",
        "confidence": "high",
        "summary": "The change is not ready.",
        "reasons": [
            {"criterion": "validation", "evidence": "No failure-path test",
             "path": "a.py", "line": 1},
            {"criterion": "scope", "evidence": "Public behavior is unexplained",
             "path": "", "line": None},
        ],
    })
    assert result.ok
    updates = result.outputs["state_updates"]
    assert updates["quality_verdict"] == "needs_rework"
    assert updates["quality_confidence"] == "high"
    assert len(updates["quality_reasons"]) == 2
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "FALLIBLE DETERMINISTIC HINTS" in prompt
    assert "<untrusted_data>" in prompt


def test_quality_step_downgrades_unsupported_rejection(settings, trace,
                                                       tmp_path):
    result, _ = _run(settings, trace, tmp_path, {
        "verdict": "needs_rework", "confidence": "high", "summary": "x",
        "reasons": [{"criterion": "size", "evidence": "large diff"}],
    })
    assert result.ok
    updates = result.outputs["state_updates"]
    assert updates["quality_verdict"] == "concerns"
    assert updates["quality_confidence"] == "low"


def test_quality_step_fails_closed_on_invalid_output(settings, trace, tmp_path):
    result, _ = _run(settings, trace, tmp_path, {
        "verdict": "reject", "confidence": "certain", "reasons": [],
    })
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_pr_quality_playbook_is_packaged():
    from infermatrix_copilot.config import _REPO_ROOT
    from infermatrix_copilot.playbooks.store import PlaybookStore

    registry = register_builtin_steps(StepRegistry())
    playbook = PlaybookStore(_REPO_ROOT / "playbooks", registry).get(
        "pr-quality")
    assert playbook.task_kinds == ["pr_quality"]
    assert [item.step for item in playbook.steps] == [
        "pr.fetch_diff", "agent.assess_pr_quality", "report.final_summary",
    ]


def test_quality_readiness_checks_the_dedicated_playbook(settings, tmp_path):
    from infermatrix_copilot.mcp_server import CopilotMCP

    repo = tmp_path / "vllm-omni"
    (repo / ".git").mkdir(parents=True)
    settings.repo_paths = {"vllm-omni": str(repo)}
    settings.anthropic_api_key = "test-key"
    settings.strict_backend = "api"
    settings.playbooks_dir.mkdir(parents=True)
    shutil.copy2(
        Path(__file__).resolve().parents[1] / "playbooks" / "pr-quality.yaml",
        settings.playbooks_dir / "pr-quality.yaml",
    )
    core = CopilotMCP(settings)
    try:
        assert core.quality_readiness("vllm-omni") == []
    finally:
        core.close()
