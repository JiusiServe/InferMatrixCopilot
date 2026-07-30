import sys
from pathlib import Path
from types import ModuleType

import pytest

import infermatrix_copilot.thin_mcp_server as thin_mcp_server
from infermatrix_copilot.knowledge_docs import KnowledgeDocsError
from infermatrix_copilot.thin_mcp_server import (
    build_mcp,
    _docs,
    _normalize_repo,
    _review_delivery,
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


def _advance_to_verify(mcp, *, post: bool) -> tuple[str, dict]:
    started = mcp.tools["review"](
        target="https://github.com/owner/repo/pull/7",
        repo="vllm-project/vllm-omni",
        mode="strict",
        post=post,
    )
    run_id = started["run_id"]
    evidence = {
        "head": "a" * 40,
        "base": "b" * 40,
        "changed_files": ["a.py", "b.py"],
        "diff_summary": "two files changed",
    }
    if post:
        evidence["diff_hunks"] = [{
            "path": "a.py", "right_start": 10, "right_count": 3,
        }]
    out = mcp.tools["submit_review_stage"](run_id, "evidence", evidence)
    assert out["stage"] == "gates"
    out = mcp.tools["submit_review_stage"](run_id, "gates", {
        "merge_state": "OPEN",
        "ci_status": "passing",
        "risk_areas": ["API compatibility"],
    })
    assert out["stage"] == "review"
    out = mcp.tools["submit_review_stage"](run_id, "review", {
        "coverage": ["a.py", "b.py"],
        "findings": [],
    })
    assert out["stage"] == "verify"
    return run_id, out


def test_strict_completion_preserves_structured_findings(monkeypatch, tmp_path):
    monkeypatch.setattr(thin_mcp_server, "_RUN_ROOT", tmp_path)
    mcp = _fake_mcp(monkeypatch)
    run_id, _ = _advance_to_verify(mcp, post=False)

    completed = mcp.tools["submit_review_stage"](run_id, "verify", {
        "verified_findings": [{
            "title": "Wrong fallback",
            "location": "a.py:11",
            "severity": "major",
            "body": "The fallback returns stale state.",
        }],
        "discarded_findings": [],
    })

    assert completed["stage"] == "complete"
    assert completed["verified_findings"] == [{
        "path": "a.py",
        "line": 11,
        "severity": "major",
        "title": "Wrong fallback",
        "body": "The fallback returns stale state.",
    }]
    assert "github_review" not in completed
    resumed = mcp.tools["get_review_status"](run_id)
    assert resumed["verified_findings"] == completed["verified_findings"]


def test_strict_post_builds_inline_review_and_requires_proof(
        monkeypatch, tmp_path):
    monkeypatch.setattr(thin_mcp_server, "_RUN_ROOT", tmp_path)
    mcp = _fake_mcp(monkeypatch)
    run_id, _ = _advance_to_verify(mcp, post=True)

    publish = mcp.tools["submit_review_stage"](run_id, "verify", {
        "verified_findings": [{
            "title": "Broken branch",
            "path": "a.py",
            "line": 11,
            "severity": "major",
            "body": "This branch drops the request.",
        }, {
            "title": "Stale location",
            "path": "b.py",
            "line": 5,
            "severity": "minor",
            "body": "The finding is valid but no current hunk contains line 5.",
        }],
        "discarded_findings": [],
    })

    assert publish["stage"] == "publish"
    payload = publish["next_action"]["github_review"]
    expected = publish["next_action"]["expected_publication"]
    assert payload["event"] == "REQUEST_CHANGES"
    assert set(payload) == {"commit_id", "body", "event", "comments"}
    assert expected["inline_count"] == 1
    assert expected["fallback_count"] == 1
    assert payload["comments"][0]["path"] == "a.py"
    assert payload["comments"][0]["side"] == "RIGHT"
    assert "b.py:5" in payload["body"]

    rejected = mcp.tools["submit_review_stage"](run_id, "publish", {
        "review_url": (
            "https://github.com/owner/repo/pull/7#pullrequestreview-99"),
        "event": "REQUEST_CHANGES",
        "inline_count": 0,
        "fallback_count": 1,
    })
    assert "does not match github_review" in rejected["error"]
    assert mcp.tools["get_review_status"](run_id)["stage"] == "publish"

    completed = mcp.tools["submit_review_stage"](run_id, "publish", {
        "review_url": (
            "https://github.com/owner/repo/pull/7#pullrequestreview-99"),
        "event": "REQUEST_CHANGES",
        "inline_count": 1,
        "fallback_count": 1,
    })
    assert completed["stage"] == "complete"
    assert completed["publication"]["review_url"].endswith(
        "#pullrequestreview-99")
    assert len(completed["verified_findings"]) == 2


def test_strict_post_requires_diff_hunks_and_direct_rejects_post(
        monkeypatch, tmp_path):
    monkeypatch.setattr(thin_mcp_server, "_RUN_ROOT", tmp_path)
    mcp = _fake_mcp(monkeypatch)
    direct = mcp.tools["review"]("PR 7", mode="direct", post=True)
    assert direct["error"] == "post=true requires strict mode"

    started = mcp.tools["review"]("PR 7", mode="strict", post=True)
    rejected = mcp.tools["submit_review_stage"](
        started["run_id"], "evidence", {
            "head": "a" * 40,
            "base": "b" * 40,
            "changed_files": ["a.py"],
            "diff_summary": "one file",
        })
    assert "diff_hunks" in rejected["error"]


@pytest.mark.parametrize(
    ("findings", "merge_state", "event"),
    [
        ([], "OPEN", "APPROVE"),
        ([{
            "path": "a.py", "line": 1, "severity": "minor",
            "title": "Small issue", "body": "Non-blocking.",
        }], "OPEN", "COMMENT"),
        ([{
            "path": "a.py", "line": 1, "severity": "major",
            "title": "Shipped issue", "body": "Already merged.",
        }], "MERGED", "COMMENT"),
    ],
)
def test_strict_github_review_event_mapping(findings, merge_state, event):
    run = {
        "artifacts": {
            "evidence": {
                "head": "a" * 40,
                "diff_hunks": [{
                    "path": "a.py", "right_start": 1, "right_count": 1,
                }],
            },
            "gates": {"merge_state": merge_state},
            "verify": {"verified_findings": findings},
        },
    }
    assert _review_delivery(run)["github_review"]["event"] == event
