"""Repo-neutral Direct routing over a per-request KnowledgeView.

The golden file was recorded from the router BEFORE the vllm-omni owner table
moved out of `direct_routing.py` into `knowledge/repos/vllm-omni/_routes.yaml`:
150 merged vllm-omni PRs (title, first 1,200 body chars, changed files) plus
adapter-only and unsupported repos. Any drift in status, owners, order, reasons
or scope validation is a regression of the extraction, not a style change.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from infermatrix_copilot import direct_routing
from infermatrix_copilot.direct_routing import (
    _direct_knowledge_routes,
    direct_review_plan,
    load_routes,
)
from infermatrix_copilot.knowledge_view import (
    KNOWLEDGE_ROOT_ENV,
    KnowledgeView,
    KnowledgeViewError,
    _load_view,
    build_manifest,
)

GOLDEN = Path(__file__).parent / "fixtures" / "direct_routing" / "golden_routes.jsonl"


def _normalized(result: dict, view: KnowledgeView) -> dict:
    out = json.loads(json.dumps(result))
    for route in out.get("routes", []):
        route["path"] = view.relative(route["path"])
        route.pop("quick_map", None)
    return out


def _cases():
    return [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines()]


def test_golden_routes_unchanged_by_extraction():
    view = KnowledgeView.current()
    cases = _cases()
    assert len(cases) >= 150
    drifted = []
    for case in cases:
        got = _direct_knowledge_routes(
            case.get("repo", "vllm-omni"),
            title=case["title"], body=case["body"],
            changed_files=case["changed_files"], view=view,
        )
        if _normalized(got, view) != case["expected"]:
            drifted.append(case.get("pr") or case.get("repo"))
    assert not drifted, f"routing drifted for: {drifted[:10]}"


def test_router_names_no_repository():
    source = Path(direct_routing.__file__).read_text(encoding="utf-8")
    for literal in ("vllm-omni", "vllm_omni", "afd-plugin", "afd_plugin"):
        assert literal not in source


def test_repo_is_required():
    with pytest.raises(ValueError, match="repo is required"):
        _direct_knowledge_routes("", title="scheduler", changed_files=[])


def test_aliases_come_from_adapters():
    assert direct_routing._normalize_repo("vllm-project/vllm-omni") == "vllm-omni"
    assert direct_routing._normalize_repo("vllm_omni") == "vllm-omni"
    assert direct_routing._normalize_repo("vllm-project/afd-plugin") == "afd-plugin"


def test_path_like_repo_is_unsupported_not_an_escape():
    result = _direct_knowledge_routes("../../etc", title="x", changed_files=["a.py"])
    assert result["status"] == "unsupported_exact_router"


def _copy_tree(tmp_path: Path) -> Path:
    src = KnowledgeView.current().root
    dst = tmp_path / "knowledge"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def _second_repo(root: Path) -> None:
    repo = root / "repos" / "demo-repo"
    (repo / "core").mkdir(parents=True)
    (repo / "_index.md").write_text("# demo\n", encoding="utf-8")
    (repo / "core" / "rules.md").write_text(
        "# Core rules\n\n## Direct quick map\n\n- DEMO-1a — keep the queue bounded\n",
        encoding="utf-8",
    )
    (repo / "_routes.yaml").write_text(
        "schema_version: 1\n"
        "owners:\n"
        "  - owner: core\n"
        "    path: repos/demo-repo/core/rules.md\n"
        "    signals: [queue]\n"
        "    scope_prefixes: [demo/core/]\n",
        encoding="utf-8",
    )


def test_second_repo_routes_through_its_own_table(tmp_path, monkeypatch):
    root = _copy_tree(tmp_path)
    _second_repo(root)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(root))
    _load_view.cache_clear()
    result = _direct_knowledge_routes(
        "demo-repo", title="Bound the queue", changed_files=["demo/core/x.py"])
    assert result["status"] == "ready"
    assert [route["owner"] for route in result["routes"]] == ["core"]
    assert "DEMO-1a" in result["routes"][0]["quick_map"]


def test_routes_table_fails_closed_on_missing_page(tmp_path, monkeypatch):
    root = _copy_tree(tmp_path)
    _second_repo(root)
    (root / "repos" / "demo-repo" / "core" / "rules.md").unlink()
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(root))
    _load_view.cache_clear()
    with pytest.raises(FileNotFoundError):
        load_routes("demo-repo")


def _snapshot(tmp_path: Path, name: str, retire: bool) -> Path:
    base = tmp_path / "snapshots" / name
    root = base / "knowledge"
    shutil.copytree(KnowledgeView.current().root, root,
                    ignore=shutil.ignore_patterns("__pycache__"))
    if retire:
        (root / "repos" / "vllm-omni" / "_routes.yaml").write_text(
            (root / "repos" / "vllm-omni" / "_routes.yaml").read_text(encoding="utf-8")
            .replace("signals: [scheduler, scheduling,", "signals: [scheduling,"),
            encoding="utf-8",
        )
    (base / "MANIFEST.json").write_text(json.dumps(build_manifest(root, name)), encoding="utf-8")
    return base


def test_activation_switch_takes_effect_on_next_request(tmp_path, monkeypatch):
    old = _snapshot(tmp_path, "a" * 40, retire=False)
    new = _snapshot(tmp_path, "b" * 40, retire=True)
    active = tmp_path / "active"
    active.symlink_to(old)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(active))
    _load_view.cache_clear()

    first = direct_review_plan("vllm-omni", title="scheduler fix", changed_files=[])
    assert first["diagnostics"]["knowledge_snapshot"] == "a" * 40
    assert any(r["owner"] == "scheduler" for r in first["knowledge_routes"])

    tmp_link = tmp_path / "active.tmp"
    tmp_link.symlink_to(new)
    tmp_link.replace(active)  # the atomic swap the knowledge service performs

    second = direct_review_plan("vllm-omni", title="scheduler fix", changed_files=[])
    assert second["diagnostics"]["knowledge_snapshot"] == "b" * 40
    assert not any(r["owner"] == "scheduler" for r in second["knowledge_routes"])


def test_snapshot_tampering_fails_closed(tmp_path, monkeypatch):
    base = _snapshot(tmp_path, "c" * 40, retire=False)
    page = base / "knowledge" / "repos" / "vllm-omni" / "components" / "scheduler" / "rules.md"
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(base))
    _load_view.cache_clear()
    view = KnowledgeView.current()
    page.write_text(page.read_text(encoding="utf-8") + "\ninjected\n", encoding="utf-8")
    with pytest.raises(KnowledgeViewError, match="does not match manifest"):
        view.path("repos/vllm-omni/components/scheduler/rules.md")


def test_snapshot_with_unlisted_file_is_rejected(tmp_path, monkeypatch):
    base = _snapshot(tmp_path, "d" * 40, retire=False)
    (base / "knowledge" / "extra.md").write_text("x", encoding="utf-8")
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(base))
    _load_view.cache_clear()
    with pytest.raises(KnowledgeViewError, match="differs from manifest"):
        KnowledgeView.current()


def test_sdk_completion_pins_the_plan_snapshot(tmp_path, monkeypatch):
    from infermatrix_copilot.sdk.v1 import (
        ChangedPath, DirectClient, DirectCompletionRequest, DirectReviewRequest,
        RepositoryRef,
    )

    old = _snapshot(tmp_path, "e" * 40, retire=False)
    new = _snapshot(tmp_path, "f" * 40, retire=True)
    active = tmp_path / "active"
    active.symlink_to(old)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(active))
    _load_view.cache_clear()

    client = DirectClient()
    head = "1" * 40
    plan = client.plan(DirectReviewRequest(
        review_id="r1", repository=RepositoryRef(alias="vllm-omni"), pr_number=1,
        expected_head_sha=head, title="scheduler fix", body="",
        changed_paths=(ChangedPath(path="vllm_omni/core/sched/a.py"),),
    ))
    assert plan.diagnostics["knowledge_snapshot"] == "e" * 40
    assert plan.knowledge_snapshot == "e" * 40
    manifest = json.loads((old / "MANIFEST.json").read_text())
    assert plan.knowledge_tree_sha256 == manifest["tree_sha256"]
    assert plan.to_dict()["knowledge_snapshot"] == "e" * 40

    tmp_link = tmp_path / "active.tmp"
    tmp_link.symlink_to(new)
    tmp_link.replace(active)

    decision = client.validate(DirectCompletionRequest(
        review_context_id=plan.review_context_id, expected_head_sha=head,
        evidence_head_sha=head, subtraction_signal="none",
        existing_feedback_status="not_applicable",
    ))
    assert "provider resources changed after the review context was issued" not in decision.missing


def test_plans_from_a_development_tree_never_expose_its_path(tmp_path, monkeypatch):
    from infermatrix_copilot.sdk.v1 import ChangedPath, DirectClient, DirectReviewRequest, RepositoryRef

    root = _copy_tree(tmp_path)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(root))
    _load_view.cache_clear()
    plan = DirectClient().plan(DirectReviewRequest(
        review_id="r3", repository=RepositoryRef(alias="vllm-omni"), pr_number=3,
        expected_head_sha="3" * 40, title="scheduler fix", body="",
        changed_paths=(ChangedPath(path="vllm_omni/core/sched/a.py"),),
    ))
    assert plan.knowledge_snapshot == "unverified" and plan.knowledge_tree_sha256 == ""
    assert str(tmp_path) not in json.dumps(plan.to_dict())


def test_sdk_document_reads_follow_the_plan_snapshot(tmp_path, monkeypatch):
    from infermatrix_copilot.sdk.v1 import (
        ChangedPath, DirectClient, DirectReviewRequest, RepositoryRef,
    )

    old = _snapshot(tmp_path, "7" * 40, retire=False)
    new = _snapshot(tmp_path, "8" * 40, retire=True)
    active = tmp_path / "active"
    active.symlink_to(old)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(active))
    _load_view.cache_clear()
    client = DirectClient()
    plan = client.plan(DirectReviewRequest(
        review_id="r2", repository=RepositoryRef(alias="vllm-omni"), pr_number=2,
        expected_head_sha="2" * 40, title="scheduler fix", body="",
        changed_paths=(ChangedPath(path="vllm_omni/core/sched/a.py"),),
    ))
    tmp_link = tmp_path / "active.tmp"
    tmp_link.symlink_to(new)
    tmp_link.replace(active)

    doc = "repos/vllm-omni/_routes.yaml"
    pinned = client.read_document(
        doc, max_bytes=65536, review_context_id=plan.review_context_id)
    current = client.read_document(doc, max_bytes=65536)
    assert "signals: [scheduler, scheduling," in pinned.content
    assert "signals: [scheduler, scheduling," not in current.content
    with pytest.raises(Exception, match="not issued"):
        client.read_document(doc, review_context_id="sha256:" + "0" * 64)


def test_mcp_document_reader_refuses_tampered_snapshot(tmp_path, monkeypatch):
    from infermatrix_copilot.knowledge_docs import KnowledgeDocs
    from infermatrix_copilot.thin_mcp_server import _docs

    base = _snapshot(tmp_path, "9" * 40, retire=False)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(base))
    _load_view.cache_clear()
    rel = "repos/vllm-omni/components/scheduler/rules.md"
    docs = _docs("vllm-omni")
    assert isinstance(docs, KnowledgeDocs)
    assert docs.read(rel)["content"]
    page = base / "knowledge" / rel
    page.write_text(page.read_text(encoding="utf-8") + "\ninjected\n", encoding="utf-8")
    with pytest.raises(KnowledgeViewError, match="does not match manifest"):
        _docs("vllm-omni").read(rel)
    with pytest.raises(KnowledgeViewError, match="does not match manifest"):
        _docs("vllm-omni").search("scheduler")


@pytest.mark.parametrize("mutation", ["modify", "delete"])
def test_sdk_completion_detects_post_plan_change_to_pinned_tree(tmp_path, monkeypatch, mutation):
    from infermatrix_copilot.sdk.v1 import (
        ChangedPath, DirectClient, DirectCompletionRequest, DirectReviewRequest,
        RepositoryRef,
    )

    base = _snapshot(tmp_path, ("5" if mutation == "modify" else "6") * 40, retire=False)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(base))
    _load_view.cache_clear()
    client = DirectClient()
    head = "3" * 40
    plan = client.plan(DirectReviewRequest(
        review_id="r3", repository=RepositoryRef(alias="vllm-omni"), pr_number=3,
        expected_head_sha=head, title="scheduler fix", body="",
        changed_paths=(ChangedPath(path="vllm_omni/core/sched/a.py"),),
    ))
    page = base / "knowledge" / "repos" / "vllm-omni" / "components" / "scheduler" / "rules.md"
    if mutation == "modify":
        page.write_text(page.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    else:
        page.unlink()
    decision = client.validate(DirectCompletionRequest(
        review_context_id=plan.review_context_id, expected_head_sha=head,
        evidence_head_sha=head, subtraction_signal="none",
        existing_feedback_status="not_applicable",
    ))
    assert not decision.review_complete
    assert "provider resources changed after the review context was issued" in decision.missing


def test_routes_table_deleted_from_loaded_snapshot_fails_closed(tmp_path, monkeypatch):
    base = _snapshot(tmp_path, "4" * 40, retire=False)
    monkeypatch.setenv(KNOWLEDGE_ROOT_ENV, str(base))
    _load_view.cache_clear()
    direct_routing._load_routes.cache_clear()
    KnowledgeView.current()  # loaded while intact
    (base / "knowledge" / "repos" / "vllm-omni" / "_routes.yaml").unlink()
    with pytest.raises(KnowledgeViewError, match="listed in manifest is missing"):
        _direct_knowledge_routes(
            "vllm-omni", title="scheduler", changed_files=["vllm_omni/core/sched/a.py"])
