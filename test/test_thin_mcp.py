from infermatrix_copilot.thin_mcp_server import _review_knowledge


def _entry(entries, path):
    return next(item for item in entries if item["path"] == path)


def test_thin_mcp_routes_afd_changed_files_and_keeps_unmatched_visible():
    entries = _review_knowledge("afd-plugin", [
        "afd_plugin/compat/patches/config_validation.py",
        "afd_plugin/connectors/npu/camp2p.py",
        "afd_plugin/v1/worker/attention_worker.py",
        "csrc/npu/a2e/op_kernel/a2e.cpp",
        "tests/e2e/features/test_serving_npu.py",
        "docs/design/module/index.md",
    ])

    routing = _entry(entries, "changed-file-routing")["content"]
    assert "compat" in routing
    assert "connectors-distributed" in routing
    assert "workers-runners" in routing
    assert "native-backends" in routing
    assert "tests" in routing
    assert "docs/design/module/index.md" in routing
    assert "must not be treated as covered" in routing
    assert any(item["path"] == "repos/afd-plugin/rules.md" for item in entries)


def test_thin_mcp_routes_vllm_omni_from_manifest_not_core_branch():
    entries = _review_knowledge("vllm-omni", [
        "vllm_omni/config/schema.py",
        "vllm_omni/model_executor/runner.py",
    ])
    paths = {item["path"] for item in entries}
    assert "repos/vllm-omni/components/configuration/rules.md" in paths
    assert "repos/vllm-omni/components/model-executor/rules.md" in paths
