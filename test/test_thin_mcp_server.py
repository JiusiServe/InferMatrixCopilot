import sys
from pathlib import Path
from types import ModuleType

import pytest

from infermatrix_copilot.knowledge_docs import KnowledgeDocsError
from infermatrix_copilot.thin_mcp_server import (
    build_mcp,
    _docs,
    _normalize_repo,
    _review_knowledge,
)


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
    return build_mcp()


def test_direct_entrypoints_do_not_resolve_repo(monkeypatch):
    mcp = _fake_mcp(monkeypatch)

    review = mcp.tools["review"](
        target="https://github.com/owner/repo/pull/1",
        repo="owner/repo",
        mode="direct",
    )
    assert set(review) == {"knowledge_entry"}
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


def test_full_github_repo_name_routes_review_knowledge():
    knowledge = _review_knowledge(
        "vllm-project/vllm-omni",
        ["vllm_omni/diffusion/models/t5_encoder/t5_encoder.py"],
    )
    paths = {entry["path"] for entry in knowledge}
    assert "repos/vllm-omni/rules.md" in paths
    assert "repos/vllm-omni/components/diffusion/rules.md" in paths
