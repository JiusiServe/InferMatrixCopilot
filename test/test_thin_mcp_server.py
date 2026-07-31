import sys
from pathlib import Path
from types import ModuleType

import pytest

from infermatrix_copilot.knowledge_docs import KnowledgeDocsError
from infermatrix_copilot.thin_mcp_server import (
    build_mcp,
    _direct_completion_result,
    _docs,
    _normalize_repo,
)
from infermatrix_copilot.config import Settings


def _fake_mcp(monkeypatch):
    fastmcp_module = ModuleType("mcp.server.fastmcp")

    class FakeMCP:
        def __init__(self, *_args, **_kwargs):
            self.tools = {}

        def tool(self):
            def register(fn):
                self.tools[fn.__name__] = fn
                return fn

            return register

    fastmcp_module.FastMCP = FakeMCP
    mcp_module = ModuleType("mcp")
    mcp_module.__path__ = []
    server_module = ModuleType("mcp.server")
    server_module.__path__ = []
    mcp_module.server = server_module
    server_module.fastmcp = fastmcp_module
    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)

    class FakeCore:
        def __init__(self):
            self.settings = Settings(
                repo_full_names={"vllm-omni": "vllm-project/vllm-omni"})
            self.requests = []

        def start_strict_review(self, request):
            self.requests.append(request)
            return "run-20260730-120000-abc123"

        def get_result(self, run_id, offset=0):
            return {"run_id": run_id, "state": "done", "offset": offset}

        def get_status(self, run_id):
            return {"run_id": run_id, "status": {"state": "running"}}

    core = FakeCore()
    return build_mcp(core=core), core


def test_direct_entrypoints_do_not_resolve_repo(monkeypatch):
    mcp, core = _fake_mcp(monkeypatch)
    assert set(mcp.tools) == {
        "review",
        "validate_direct_review",
        "get_review_result",
        "get_review_status",
        "update_knowledge",
        "doc_search",
        "doc_read",
    }

    review = mcp.tools["review"](
        target="https://github.com/owner/repo/pull/1",
        repo="owner/repo",
        mode="direct",
        post=True,
    )
    assert set(review) == {
        "mode",
        "knowledge_entry",
        "first_review_checklist",
        "completion_gate",
    }
    assert review["mode"] == "direct"
    assert core.requests == []
    assert Path(review["knowledge_entry"]).parts[-2:] == ("knowledge", "AGENTS.md")
    assert any(
        "subtraction" in item
        for item in review["first_review_checklist"]
    )
    assert review["completion_gate"] == {
        "tool": "validate_direct_review",
        "require_one_of": [
            "subtraction[{anchor, action, risk}]",
            "minimality_proof{scope_ledger, abstraction_census, why_no_safe_deletion}",
        ],
        "final_comment_count": 1,
        "if_missing": "partial_review",
    }

    update = mcp.tools["update_knowledge"](repo="owner/repo")
    assert set(update) == {"knowledge_entry"}
    assert Path(update["knowledge_entry"]).parts[-2:] == (
        "knowledge",
        "CONTRIBUTING.md",
    )


def test_direct_completion_requires_subtraction_or_minimality_proof():
    result = _direct_completion_result()

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False
    assert result["missing"]


def test_issue_24_direct_completion_accepts_single_comment_with_subtractions():
    result = _direct_completion_result(subtraction=[
        {
            "anchor": "examples/offline_inference/text_to_image/text_to_image.py:358",
            "action": "DELETE the unproven tokenizer fallback compatibility path",
            "risk": "low: default fail-fast behavior remains unchanged",
        },
        {
            "anchor": "examples/offline_inference/image_to_image/image_edit.py:116",
            "action": "MERGE the duplicated AR-stage application helper into one owner",
            "risk": "medium: preserve both public CLI call paths",
        },
    ])

    assert result["status"] == "complete"
    assert result["publish_ready"] is True
    assert result["subtraction_items"] == 2
    assert result["final_comment_count"] == 1


def test_direct_completion_accepts_concrete_minimality_proof():
    result = _direct_completion_result(minimality_proof={
        "scope_ledger": "Every changed production file maps to the requested API fix.",
        "abstraction_census": "No new helper, class, projection, fallback, or compatibility branch.",
        "why_no_safe_deletion": "Deleting any changed branch removes the only validated consumer path.",
    })

    assert result["status"] == "complete"
    assert result["publish_ready"] is True
    assert result["minimality_proof"] is True


def test_direct_completion_rejects_malformed_subtraction_and_two_comments():
    result = _direct_completion_result(
        subtraction=[{
            "anchor": "examples/task.py:120",
            "action": "",
            "risk": "low",
        }],
        final_comment_count=2,
    )

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False
    assert len(result["missing"]) == 3


def test_direct_completion_does_not_count_bug_fixes_as_subtraction():
    result = _direct_completion_result(subtraction=[{
        "anchor": "src/adapter.py:42",
        "action": "FIX the incorrect default value",
        "risk": "low",
    }])

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False


def test_full_github_repo_name_maps_to_knowledge_repo():
    assert _normalize_repo("vllm-project/vllm-omni") == "vllm-omni"
    docs = _docs("vllm-project/vllm-omni")
    assert docs.read("repos/vllm-omni/_index.md")["path"] == (
        "repos/vllm-omni/_index.md"
    )


def test_same_repo_name_under_another_owner_is_rejected():
    with pytest.raises(KnowledgeDocsError, match="unsupported knowledge repo"):
        _docs("another-owner/vllm-omni")


def test_strict_maps_to_old_eco_request_and_preserves_explicit_post(monkeypatch):
    mcp, core = _fake_mcp(monkeypatch)

    result = mcp.tools["review"](
        target="https://github.com/vllm-project/vllm-omni/pull/5172",
        mode="strict",
        post=True,
        review_depth="full",
    )

    assert result == {
        "run_id": "run-20260730-120000-abc123",
        "mode": "strict",
        "execution_mode": "eco",
        "post": True,
    }
    assert core.requests == [{
        "kind": "pr_review",
        "repo": "vllm-omni",
        "pr": 5172,
        "mode": "eco",
        "post": True,
        "params": {"review_depth": "full"},
    }]


def test_strict_does_not_post_by_default(monkeypatch):
    mcp, core = _fake_mcp(monkeypatch)

    result = mcp.tools["review"](target="PR #6", mode="strict")

    assert result["post"] is False
    assert core.requests[0]["mode"] == "eco"
    assert core.requests[0]["post"] is False
