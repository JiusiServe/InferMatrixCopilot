"""GR reviews use packaged owner routes and the existing SDK head gate."""

from dataclasses import replace

import pytest

from infermatrix_copilot.sdk.v1 import (
    ChangedPath,
    DirectClient,
    DirectCompletionRequest,
    DirectReviewRequest,
    RepositoryRef,
)


HEAD = "abe0335e4823fa5c2564471d761194b44c66abff"


def request(alias, paths, title="Update implementation", body=""):
    return DirectReviewRequest(
        review_id="gr-review-424",
        repository=RepositoryRef(alias=alias, full_name="JiusiServe/vllm-gr"),
        pr_number=424,
        expected_head_sha=HEAD,
        title=title,
        body=body,
        changed_paths=tuple(ChangedPath(path, "modified") for path in paths),
    )


@pytest.mark.parametrize("alias", ["vllm-gr", "vllm_gr"])
@pytest.mark.parametrize("path,owner", [
    ("vllm_gr/v1/engine/core.py", "engine-core"),
    ("rust/beam-proc/src/worker/io_worker.rs", "beam-proc"),
    ("rust/ce-transport/src/lib.rs", "beam-proc"),
    ("vllm_gr/entrypoints/openai/serving_engine.py", "serving"),
    ("vllm_gr/v1/attention/backends/beam_attn_gpu.py", "attention"),
    ("setup.py", "packaging"),
])
def test_gr_sdk_accepts_repository_and_routes_the_changed_owner(alias, path, owner):
    client = DirectClient()
    assert "vllm-gr" in client.capabilities().supported_repositories
    plan = client.plan(request(alias, [path]))

    assert plan.routing["status"] == "scope_fallback"
    assert [route.owner for route in plan.knowledge_routes] == [owner]
    route = plan.knowledge_routes[0]
    assert route.document.document_id.startswith("repos/vllm-gr/")
    assert route.quick_map_status == "ok"
    assert route.quick_map
    assert client.read_document(
        route.document.document_id,
        review_context_id=plan.review_context_id,
    ).sha256 == route.document.sha256


def test_gr_beamproc_review_keeps_exact_routes_and_head_validation():
    client = DirectClient()
    plan = client.plan(request(
        "vllm-gr",
        ["vllm_gr/v1/engine/core.py", "rust/ce-transport/src/lib.rs", "setup.py"],
        title="Optimize BeamProc scheduling and add Rust shared-memory transport",
        body="Move EngineCore TX/RX workers into Rust. Build and package the native library.",
    ))

    assert 1 <= len(plan.knowledge_routes) <= 3
    assert {route.owner for route in plan.knowledge_routes} == {
        "engine-core", "beam-proc", "packaging",
    }
    assert all(route.quick_map_status == "ok" for route in plan.knowledge_routes)
    completion = DirectCompletionRequest(
        review_context_id=plan.review_context_id,
        expected_head_sha=HEAD,
        evidence_head_sha=HEAD,
        subtraction_signal="none",
        existing_feedback_status="checked",
    )
    assert client.validate(completion).review_complete
    assert not client.validate(replace(completion, evidence_head_sha="b" * 40)).review_complete


def test_gr_mcp_and_sdk_use_the_same_repository_routes():
    from infermatrix_copilot.direct_routing import direct_review_plan

    path = "vllm_gr/v1/engine/core.py"
    sdk = DirectClient().plan(request("vllm-gr", [path]))
    mcp = direct_review_plan("JiusiServe/vllm-gr", changed_files=[path])
    assert [route.owner for route in sdk.knowledge_routes] == [
        route["owner"] for route in mcp["knowledge_routes"]
    ]

