"""The installed-consumer SDK contract, exercised without either MCP server."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from infermatrix_copilot import __version__
from infermatrix_copilot.sdk import _resources as resource_module
from infermatrix_copilot.sdk.v1 import (
    KNOWLEDGE_API_VERSION,
    ChangedPath,
    DirectClient,
    DirectCompletionRequest,
    DirectReviewRequest,
    QualityReviewRequest,
    RepositoryRef,
    StrictReviewRequest,
    StrictRuntime,
)
from infermatrix_copilot.sdk.v1 import knowledge as knowledge_module

HEAD = "a" * 40


def _request(repo: str, changed: str) -> DirectReviewRequest:
    return DirectReviewRequest(
        review_id="attempt-1",
        repository=RepositoryRef(alias=repo),
        pr_number=7,
        expected_head_sha=HEAD,
        title="Fix runtime scheduling",
        body="Correct the affected runtime path.",
        changed_paths=(ChangedPath(changed, "modified"),),
    )


def test_direct_plan_is_typed_complete_and_path_free():
    client = DirectClient()
    plan = client.plan(
        _request("vllm-omni", "vllm_omni/core/sched/scheduler.py")
    )

    assert plan.protocol_version
    assert plan.review_context_id.startswith("sha256:")
    assert plan.resource_revision.startswith("sha256:")
    assert plan.knowledge_routes
    assert plan.mandatory_review_guides
    assert plan.first_review_checklist
    assert plan.navigation_policy["stop_after_routes"] is True
    assert plan.progress_update["github_comment"] is False
    assert plan.completion_gate["operation"] == "validate_direct_review"
    assert plan.navigation_policy["fallback_document_id"] == "AGENTS.md"
    assert "fallback_entry" not in plan.navigation_policy

    wire = plan.to_dict()
    for document in [
        wire["knowledge_entry"],
        *wire["mandatory_review_guides"],
        *wire["document_maps"],
        *(route["document"] for route in wire["knowledge_routes"]),
    ]:
        assert not Path(document["document_id"]).is_absolute()
        assert "InferMatrixCopilot" not in document["document_id"]
        assert document["sha256"].startswith("sha256:")


def test_second_adapter_routes_from_packaged_adapter_registry():
    plan = DirectClient().plan(
        _request("afd-plugin", "afd_plugin/compat/vllm.py")
    )

    assert plan.routing["status"] == "ready"
    assert plan.knowledge_routes[0].owner == "compatibility"
    assert plan.knowledge_routes[0].document.document_id.startswith(
        "repos/afd-plugin/"
    )


def test_completion_is_bound_to_context_and_frozen_head():
    client = DirectClient()
    plan = client.plan(
        _request("vllm-omni", "vllm_omni/core/sched/scheduler.py")
    )
    accepted = client.validate(DirectCompletionRequest(
        review_context_id=plan.review_context_id,
        expected_head_sha=HEAD,
        evidence_head_sha=HEAD,
        subtraction_signal="none",
        existing_feedback_status="checked",
    ))
    wrong_head = client.validate(DirectCompletionRequest(
        review_context_id=plan.review_context_id,
        expected_head_sha=HEAD,
        evidence_head_sha="b" * 40,
        subtraction_signal="none",
        existing_feedback_status="checked",
    ))

    assert accepted.review_complete is True
    assert wrong_head.review_complete is False
    assert "evidence_head_sha must equal expected_head_sha" in wrong_head.missing


def test_completion_rejects_unknown_other_client_and_evicted_contexts():
    request = _request("vllm-omni", "vllm_omni/core/sched/scheduler.py")
    client = DirectClient(max_issued_contexts=1)
    first = client.plan(request)
    other = DirectClient().validate(DirectCompletionRequest(
        review_context_id=first.review_context_id,
        expected_head_sha=HEAD,
        evidence_head_sha=HEAD,
        subtraction_signal="none",
    ))
    client.plan(replace(request, review_id="attempt-2"))
    evicted = client.validate(DirectCompletionRequest(
        review_context_id=first.review_context_id,
        expected_head_sha=HEAD,
        evidence_head_sha=HEAD,
        subtraction_signal="none",
    ))

    assert other.review_complete is False
    assert evicted.review_complete is False
    assert any("not issued by this DirectClient" in item for item in other.missing)
    assert any("not issued by this DirectClient" in item for item in evicted.missing)


def test_completion_passes_feedback_evidence_to_provider_gate():
    client = DirectClient()
    plan = client.plan(
        _request("vllm-omni", "vllm_omni/core/sched/scheduler.py")
    )
    decision = client.validate(DirectCompletionRequest(
        review_context_id=plan.review_context_id,
        expected_head_sha=HEAD,
        evidence_head_sha=HEAD,
        subtraction_signal="none",
        existing_feedback_status="checked",
        finding_dispositions=({
            "anchor": "src/runtime.py:7",
            "disposition": "duplicate",
            "existing_thread": "thread-1",
        },),
    ))

    assert decision.review_complete is True
    assert decision.details["existing_feedback_status"] == "checked"
    assert decision.details["finding_dispositions"] == 1
    assert decision.details["duplicate_findings_suppressed"] == 1


def test_document_reader_is_bounded_and_content_addressed():
    client = DirectClient()
    page = client.read_document("AGENTS.md", max_bytes=32)

    assert page.document_id == "AGENTS.md"
    assert page.sha256.startswith("sha256:")
    assert 0 < len(page.content.encode("utf-8")) <= 34  # UTF-8 boundary replacement
    assert page.next_offset == 32


def test_capabilities_identify_package_protocols_and_resources():
    caps = DirectClient().capabilities()

    assert caps.sdk_api_version == "1.0.0"
    assert caps.distribution_version == __version__ == "0.2.0"
    assert caps.direct_api_version
    assert caps.strict_api_version
    assert caps.quality_api_version == "1.0.0"
    assert caps.knowledge_api_version == KNOWLEDGE_API_VERSION == "1.0.0"
    assert caps.supports_idempotent_strict_start is True
    assert caps.supports_quality_review is True
    assert caps.supports_knowledge_curation is True
    assert caps.resource_revision.startswith("sha256:")
    assert {"vllm-omni", "afd-plugin"} <= set(caps.supported_repositories)


def test_sdk_resources_ignore_ambient_directory_overrides(tmp_path, monkeypatch):
    fake_knowledge = tmp_path / "knowledge"
    fake_knowledge.mkdir()
    (fake_knowledge / "AGENTS.md").write_text("poisoned\n", encoding="utf-8")
    fake_adapters = tmp_path / "adapters" / "poison"
    fake_adapters.mkdir(parents=True)
    (fake_adapters / "manifest.yaml").write_text("poisoned: true\n", encoding="utf-8")
    monkeypatch.setenv("INFERMATRIX_KNOWLEDGE_DIR", str(fake_knowledge))
    monkeypatch.setenv("INFERMATRIX_ADAPTERS_DIR", str(fake_adapters.parent))

    knowledge = resource_module.knowledge_root()
    adapters = resource_module.adapters_root()

    assert knowledge != fake_knowledge.resolve()
    assert adapters != fake_adapters.parent.resolve()
    assert (knowledge / "AGENTS.md").read_text(encoding="utf-8") != "poisoned\n"


def test_capabilities_fail_closed_when_knowledge_apply_lock_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(knowledge_module, "fcntl", None)

    caps = DirectClient().capabilities()

    assert caps.knowledge_api_version == KNOWLEDGE_API_VERSION
    assert caps.supports_knowledge_curation is False


def test_public_import_does_not_load_server_config_or_legacy_contract():
    script = """
import sys
from infermatrix_copilot.sdk.v1 import DirectClient, StrictRuntime
blocked = {
    'infermatrix_copilot.config',
    'infermatrix_copilot.contract',
    'infermatrix_copilot.direct_routing',
    'infermatrix_copilot.mcp_server',
}
loaded = sorted(blocked.intersection(sys.modules))
assert not loaded, loaded
assert DirectClient and StrictRuntime
"""
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    subprocess.run([sys.executable, "-c", script], check=True, env=env)


class _FakeStrictCore:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.created = True

    def capabilities(self):
        return {"max_strict_workers": 1, "supports_file_locking": True}

    def strict_readiness(self, repo, repo_path=""):
        return []

    def quality_readiness(self, repo, repo_path=""):
        return []

    def reserve_strict_review(self, payload):
        self.requests.append(payload)
        return "run-20260829-010101-abcdef", self.created

    def reserve_quality_review(self, payload):
        self.requests.append(payload)
        return "run-quality-20260831-abcdef", self.created

    def get_status(self, run_id):
        return {
            "run_id": run_id,
            "status": {"state": "running"},
            "progress": {"completed": {}},
        }

    def get_result(self, run_id, offset=0):
        return {
            "run_id": run_id,
            "state": "done",
            "report": "complete",
            "report_path": "/private/provider/run/RUN_REPORT.md",
            "next_offset": None,
            "result": {"verdict": "APPROVE"},
            "offset_seen": offset,
        }

    def get_quality_result(self, run_id):
        return {
            "run_id": run_id,
            "state": "done",
            "result": {
                "contract_version": "1.0.0",
                "reviewed_head_sha": HEAD,
                "verdict": "ready",
                "confidence": "high",
                "reasons": [],
            },
        }

    def close(self):
        return None


def test_strict_facade_preserves_idempotency_and_hides_private_paths():
    runtime = object.__new__(StrictRuntime)
    core = _FakeStrictCore()
    runtime._core = core
    request = StrictReviewRequest(
        repository=RepositoryRef("vllm-omni"),
        pr_number=7,
        expected_head_sha=HEAD,
        repo_path="/authorized/checkout",
        idempotency_key="attempt-1",
        review_depth="full",
    )

    first = runtime.reserve_review(request)
    core.created = False
    retry = runtime.start_review(request)
    status = runtime.get_status(first.run_id)
    result = runtime.get_result(first.run_id, offset=12)

    assert first.created is True and retry.created is False
    assert core.requests[0]["params"] == {"review_depth": "full"}
    assert "review_depth" not in core.requests[0]
    assert status.to_dict()["payload"]["progress"] == {"completed": {}}
    assert result.to_dict()["payload"]["result"] == {"verdict": "APPROVE"}
    assert result.payload["offset_seen"] == 12
    assert "report_path" not in result.payload
    assert runtime.capabilities().distribution_version == "0.2.0"


def test_quality_facade_is_typed_idempotent_and_head_bound():
    runtime = object.__new__(StrictRuntime)
    core = _FakeStrictCore()
    runtime._core = core
    request = QualityReviewRequest(
        repository=RepositoryRef("vllm-omni"),
        pr_number=7,
        expected_head_sha=HEAD,
        repo_path="/authorized/checkout",
        idempotency_key="quality-attempt-1",
        deterministic_signals=("Q2: no test changes",),
    )

    first = runtime.reserve_quality_review(request)
    core.created = False
    retry = runtime.start_quality_review(request)
    result = runtime.get_quality_result(first.run_id)

    assert first.created is True and retry.created is False
    assert core.requests[0]["kind"] == "pr_quality"
    assert core.requests[0]["post"] is False
    assert core.requests[0]["expected_head_sha"] == HEAD
    assert core.requests[0]["params"] == {
        "deterministic_signals": ["Q2: no test changes"],
    }
    assert result.terminal and result.payload["result"]["verdict"] == "ready"


def test_strict_runtime_public_capabilities_smoke(tmp_path):
    with StrictRuntime(settings_overrides={
        "_env_file": None,
        "run_root": tmp_path / "runs",
    }) as runtime:
        caps = runtime.capabilities()

    assert caps.distribution_version == "0.2.0"
    assert caps.strict_api_version == "1.0.0"
    assert caps.knowledge_api_version == KNOWLEDGE_API_VERSION
    assert caps.supports_knowledge_curation is True
