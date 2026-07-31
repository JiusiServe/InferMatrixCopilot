import sys
from pathlib import Path
from types import ModuleType

import pytest

from infermatrix_copilot.knowledge_docs import KnowledgeDocsError
from infermatrix_copilot.thin_mcp_server import (
    build_mcp,
    _direct_completion_result,
    _direct_knowledge_routes,
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
            self.repo_configurations = []

        def start_strict_review(self, request):
            self.requests.append(request)
            return "run-20260730-120000-abc123"

        def configure_strict_repo(self, repo, repo_path=""):
            self.repo_configurations.append((repo, repo_path))

        def strict_readiness(self, repo):
            return []

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
        "knowledge_routes",
        "routing",
        "navigation_policy",
        "execution_budget",
        "first_review_checklist",
        "progress_update",
        "completion_gate",
    }
    assert review["mode"] == "direct"
    assert core.requests == []
    assert Path(review["knowledge_entry"]).parts[-2:] == ("knowledge", "AGENTS.md")
    assert review["knowledge_routes"] == []
    assert review["routing"]["status"] == "needs_pr_context"
    assert review["navigation_policy"]["progress_before_knowledge"] is True
    assert review["navigation_policy"]["use_embedded_quick_maps"] is True
    assert review["navigation_policy"]["stop_after_routes"] is True
    assert review["execution_budget"]["profile"] == "code"
    assert review["execution_budget"]["total_command_calls"] == 20
    assert review["execution_budget"]["hard_ceiling"] is True
    assert review["execution_budget"]["extension_command_calls"] == 4
    assert any(
        "subtraction" in item
        for item in review["first_review_checklist"]
    )
    assert any(
        "before reading knowledge, searching source, or running tests"
        in item
        for item in review["first_review_checklist"]
    )
    assert any(
        "bounded rg searches" in item
        for item in review["first_review_checklist"]
    )
    assert any(
        "compatibility preflight" in item
        and "environment fingerprint" in item
        for item in review["first_review_checklist"]
    )
    assert review["progress_update"] == {
        "deadline_seconds": 60,
        "channel": "host_conversation",
        "required_fields": [
            "head_sha",
            "ci_status",
            "mergeability",
            "early_findings",
        ],
        "early_findings_status": "preliminary",
        "continue_review": True,
        "github_comment": False,
        "emit_before": [
            "knowledge_read",
            "source_search",
            "tests",
        ],
        "do_not_wait_for": [
            "ci_completion",
            "mergeability_resolution",
        ],
    }
    assert review["completion_gate"] == {
        "tool": "validate_direct_review",
        "subtraction_signal": {
            "none": "No helper/class/fallback/compatibility/public-behavior expansion; no subtraction evidence required.",
            "triggered": "Require subtraction items or minimality_proof.",
        },
        "triggered_require_one_of": [
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


def test_direct_routes_title_body_before_changed_files(monkeypatch):
    mcp, _core = _fake_mcp(monkeypatch)
    review = mcp.tools["review"](
        target="https://github.com/vllm-project/vllm-omni/pull/4762",
        repo="vllm-project/vllm-omni",
        mode="direct",
        title="[Core / Bugfix] Add Mechanism for Endpoint Rejection",
        body=(
            "Add pipeline config endpoint restrictions and return a 400 from "
            "the OpenAI serving layer."
        ),
        changed_files=[
            "vllm_omni/config/config_factory.py",
            "vllm_omni/entrypoints/openai/api_server.py",
            "vllm_omni/model_executor/models/qwen3_omni/model.py",
        ],
    )

    assert review["routing"]["status"] == "ready"
    assert review["routing"]["changed_files_role"] == "scope_validation_only"
    assert [route["owner"] for route in review["knowledge_routes"]] == [
        "configuration",
        "serving",
    ]
    assert review["knowledge_entry"] == review["knowledge_routes"][0]["path"]
    assert all(
        Path(route["path"]).is_file()
        for route in review["knowledge_routes"]
    )
    assert all(
        "## Direct" in route["quick_map"]
        and len(route["quick_map"]) <= 3500
        and route["read_required"] is False
        for route in review["knowledge_routes"]
    )
    scope = {
        item["owner"]: item
        for item in review["routing"]["scope_validation"]
    }
    assert scope["model-executor"]["selected_from_description"] is False
    assert review["execution_budget"]["profile"] == "code"
    assert review["execution_budget"]["knowledge_file_reads"] == 0


def test_direct_docs_only_budget_stays_small(monkeypatch):
    mcp, _core = _fake_mcp(monkeypatch)
    review = mcp.tools["review"](
        target="https://github.com/vllm-project/vllm-omni/pull/4950",
        mode="direct",
        title="Fix MiniCPM-o 4.5 TTS request example",
        body="Correct the serving request and TTS response documentation.",
        changed_files=["recipes/OpenBMB/MiniCPM-o-4_5.md"],
    )

    assert review["execution_budget"]["profile"] == "docs_only"
    assert review["execution_budget"]["validation_commands"] == 2
    assert review["execution_budget"]["total_command_calls"] == 12
    assert review["execution_budget"]["command_output_chars"] == 12000
    assert review["execution_budget"]["hard_ceiling"] is True


def test_direct_serving_quick_map_covers_request_and_lifecycle(monkeypatch):
    mcp, _core = _fake_mcp(monkeypatch)

    docs_review = mcp.tools["review"](
        target="https://github.com/vllm-project/vllm-omni/pull/4950",
        mode="direct",
        title="Fix MiniCPM-o 4.5 TTS request example",
        body="Correct chat_template_kwargs and the TTS response contract.",
        changed_files=["recipes/OpenBMB/MiniCPM-o-4_5.md"],
    )
    assert [
        route["owner"] for route in docs_review["knowledge_routes"]
    ] == ["model:minicpm-o-4-5", "serving"]
    serving_map = next(
        route["quick_map"]
        for route in docs_review["knowledge_routes"]
        if route["owner"] == "serving"
    )
    assert "chat_template_kwargs" in serving_map
    assert "chat_completion_full_generator" in serving_map

    lifecycle_review = mcp.tools["review"](
        target="https://github.com/vllm-project/vllm-omni/pull/4834",
        mode="direct",
        title="[Bugfix] Guard generation during partial wake",
        body=(
            "Preserve sleep/wake stage scope, validate worker ACKs, and make "
            "wake idempotent."
        ),
        changed_files=[
            "vllm_omni/entrypoints/async_omni.py",
            "vllm_omni/worker/base.py",
        ],
    )
    owners = [route["owner"] for route in lifecycle_review["knowledge_routes"]]
    assert owners == ["serving"]
    assert "SERV-5a" in lifecycle_review["knowledge_routes"][0]["quick_map"]


def test_direct_routes_model_rules_without_index_navigation():
    routing = _direct_knowledge_routes(
        "vllm-omni",
        title="Fix MiniCPM-o 4.5 TTS request example",
        body="The serving request must reach the TTS stage input processor.",
        changed_files=["recipes/OpenBMB/MiniCPM-o-4_5.md"],
    )

    assert routing["status"] == "ready"
    assert [route["owner"] for route in routing["routes"]] == [
        "model:minicpm-o-4-5",
        "serving",
        "model-executor",
    ]
    assert len(routing["routes"]) == 3
    assert all(route["quick_map"] for route in routing["routes"])


def test_direct_completion_requires_subtraction_signal_classification():
    result = _direct_completion_result()

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False
    assert result["missing"] == [
        "subtraction_signal must be 'none' or 'triggered'"
    ]


def test_small_fix_accepts_no_subtraction_signal_without_full_proof():
    result = _direct_completion_result(subtraction_signal="none")

    assert result["status"] == "complete"
    assert result["publish_ready"] is True
    assert result["subtraction_required"] is False
    assert result["subtraction_items"] == 0


def test_triggered_subtraction_requires_evidence():
    result = _direct_completion_result(subtraction_signal="triggered")

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False
    assert result["subtraction_required"] is True
    assert result["missing"] == [
        "triggered subtraction requires subtraction items or a concrete "
        "minimality_proof with scope_ledger, abstraction_census, and "
        "why_no_safe_deletion"
    ]


def test_issue_5559_trigger_accepts_single_comment_with_subtractions():
    result = _direct_completion_result(
        subtraction_signal="triggered",
        subtraction=[
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
        ],
    )

    assert result["status"] == "complete"
    assert result["publish_ready"] is True
    assert result["subtraction_required"] is True
    assert result["subtraction_items"] == 2
    assert result["final_comment_count"] == 1


def test_direct_completion_accepts_concrete_minimality_proof():
    result = _direct_completion_result(
        subtraction_signal="triggered",
        minimality_proof={
            "scope_ledger": "Every changed production file maps to the requested API fix.",
            "abstraction_census": "No new helper, class, projection, fallback, or compatibility branch.",
            "why_no_safe_deletion": "Deleting any changed branch removes the only validated consumer path.",
        },
    )

    assert result["status"] == "complete"
    assert result["publish_ready"] is True
    assert result["minimality_proof"] is True


def test_direct_completion_rejects_malformed_subtraction_and_two_comments():
    result = _direct_completion_result(
        subtraction_signal="triggered",
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
    result = _direct_completion_result(
        subtraction_signal="triggered",
        subtraction=[{
            "anchor": "src/adapter.py:42",
            "action": "FIX the incorrect default value",
            "risk": "low",
        }],
    )

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False


def test_no_signal_rejects_contradictory_subtraction_evidence():
    result = _direct_completion_result(
        subtraction_signal="none",
        subtraction=[{
            "anchor": "src/adapter.py:42",
            "action": "DELETE unused compatibility branch",
            "risk": "low",
        }],
    )

    assert result["status"] == "partial_review"
    assert result["publish_ready"] is False
    assert result["missing"] == [
        "subtraction_signal 'none' cannot include subtraction evidence"
    ]


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
    assert core.repo_configurations == [("vllm-omni", "")]


def test_strict_does_not_post_by_default(monkeypatch):
    mcp, core = _fake_mcp(monkeypatch)

    result = mcp.tools["review"](target="PR #6", mode="strict")

    assert result["post"] is False
    assert core.requests[0]["mode"] == "eco"
    assert core.requests[0]["post"] is False


def test_strict_reports_setup_gaps_before_starting(monkeypatch):
    mcp, core = _fake_mcp(monkeypatch)
    core.strict_readiness = lambda repo: [
        "model credential missing",
        "checkout missing",
    ]

    result = mcp.tools["review"](
        target="https://github.com/vllm-project/vllm-omni/pull/5172",
        mode="strict",
    )

    assert result == {
        "error": (
            "Strict mode is not ready: model credential missing; "
            "checkout missing"
        )
    }
    assert core.requests == []
