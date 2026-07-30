import sys
from pathlib import Path
from types import ModuleType

import pytest

from infermatrix_copilot.knowledge_docs import KnowledgeDocsError
from infermatrix_copilot.thin_mcp_server import (
    build_mcp,
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
    assert set(review) == {"knowledge_entry"}
    assert core.requests == []
    assert Path(review["knowledge_entry"]).parts[-2:] == ("knowledge", "AGENTS.md")

    update = mcp.tools["update_knowledge"](repo="owner/repo")
    assert set(update) == {"knowledge_entry"}
    assert Path(update["knowledge_entry"]).parts[-2:] == (
        "knowledge",
        "CONTRIBUTING.md",
    )


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
