import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from infermatrix_copilot.knowledge_context import ContextBudget, ContextError, KnowledgeContextService
from infermatrix_copilot.knowledge_view import KnowledgeView, KnowledgeViewError, build_manifest


PIN = "a" * 40


def setup(tmp_path, body="Useful source-linked context. " * 200, *, dependencies=()):
    root = tmp_path / "snapshot" / "knowledge"
    root.mkdir(parents=True)
    (root / "AGENTS.md").write_text("knowledge")
    for name in ("r", "other"):
        folder = root / "repos" / name
        folder.mkdir(parents=True)
        (folder / "doc.md").write_text(
            f"---\ntitle: API\ntype: guide\nfeature: api\nsources: [acme/r@{PIN}:src/api.py]\n---\n\n" + body)
    manifest = build_manifest(root, "snapshot-1")
    (root.parent / "MANIFEST.json").write_text(json.dumps(manifest))
    view = KnowledgeView(root, "snapshot-1", manifest["files"])
    bindings = {
        name: {"repo_id": name, "knowledge_slice": f"repos/{name}", "source_pin": PIN,
               "catalog_hash": "b" * 64, "policy_hash": "c" * 64,
               "dependencies": dependencies if name == "r" else ()}
        for name in ("r", "other")}
    service = KnowledgeContextService(view, tmp_path / "ledger.db", resolver=lambda view, selector: bindings.get(selector))
    return service, view, bindings


def open_session(service, initial=1000, maximum=4000, **kwargs):
    return service.open_session("r", source_pin=PIN, review_id="review", budget=ContextBudget(
        initial_tokens=initial, max_tokens=maximum, model_context_tokens=8000,
        source_reserve_tokens=2000, output_reserve_tokens=1000, **kwargs))["session_id"]


def test_cumulative_budget_counts_headers_and_preserves_unicode(tmp_path):
    service, _, _ = setup(tmp_path, "真实的源码解释。" * 1000)
    session = open_session(service)
    first = service.read(session, "repos/r/doc.md")
    assert first["truncated"]
    assert len(first["model_content"].encode()) <= 1000
    assert first["consumed_tokens"] <= 1000
    assert first["next_offset"] < 1000
    assert "content" not in first["documents"][0]
    assert "真实" in first["model_content"]
    assert first["actual_provider_usage"] == "unknown"


def test_same_request_is_idempotent_across_restart_and_expansion_continues(tmp_path):
    service, view, bindings = setup(tmp_path)
    session = open_session(service)
    first = service.read(session, "repos/r/doc.md")
    restarted = KnowledgeContextService(view, tmp_path / "ledger.db", resolver=lambda view, selector: bindings.get(selector))
    assert restarted.read(session, "repos/r/doc.md") == first
    assert restarted.status(session)["consumed_tokens"] == first["consumed_tokens"]
    restarted.expand(session, target_tokens=4000, reason="Read remaining API contract")
    second = restarted.read(session, "repos/r/doc.md")
    assert second["documents"][0]["continuation"]
    assert second["consumed_tokens"] <= 4000
    assert second["consumed_tokens"] > first["consumed_tokens"]


def test_reserve_capacity_cannot_be_expanded_away(tmp_path):
    service, _, _ = setup(tmp_path)
    budget = ContextBudget(initial_tokens=24000, max_tokens=64000, model_context_tokens=50000,
                           source_reserve_tokens=32000, output_reserve_tokens=8192)
    status = service.open_session("r", source_pin=PIN, review_id="small", budget=budget)
    assert status["capacity_tokens"] == 9808
    assert status["active_tokens"] == 9808
    with pytest.raises(ContextError, match="capacity"):
        service.expand(status["session_id"], target_tokens=10000, reason="Large PR")


def test_parallel_reads_cannot_overspend(tmp_path):
    service, _, _ = setup(tmp_path)
    session = open_session(service)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda n: service.read(session, "repos/r/doc.md", offset=n * 50), range(8)))
    assert service.status(session)["consumed_tokens"] <= 1000
    assert any(result["status"] == "budget_exhausted" for result in results)


def test_cached_delivery_still_rejects_snapshot_tampering(tmp_path):
    service, view, _ = setup(tmp_path)
    session = open_session(service)
    service.read(session, "repos/r/doc.md")
    (view.root / "repos/r/doc.md").write_text("changed")
    with pytest.raises(KnowledgeViewError):
        service.read(session, "repos/r/doc.md")


def test_cached_packet_content_tampering_is_not_returned_unmetered(tmp_path):
    import sqlite3
    service, _, _ = setup(tmp_path)
    session = open_session(service)
    service.read(session, "repos/r/doc.md")
    with sqlite3.connect(tmp_path / "ledger.db") as db:
        state = json.loads(db.execute("SELECT state FROM sessions WHERE id=?", (session,)).fetchone()[0])
        receipt = next(iter(state["requests"].values()))
        receipt["result"]["model_content"] = "UNMETERED SUBSTITUTION " * 1000
        db.execute("UPDATE sessions SET state=? WHERE id=?", (json.dumps(state), session))
    with pytest.raises(ContextError, match="integrity"):
        service.read(session, "repos/r/doc.md")


def test_crossrepo_requires_host_and_confirmed_exact_pin(tmp_path):
    link = {"repo_id": "other", "status": "confirmed", "source_pin": PIN, "catalog_hash": "b" * 64}
    service, view, bindings = setup(tmp_path, dependencies=(link,))
    session = open_session(service)
    with pytest.raises(ContextError, match="authorized"):
        service.read(session, "repos/other/doc.md", repository="other")
    authorized = KnowledgeContextService(view, tmp_path / "allowed.db", resolver=lambda view, selector: bindings.get(selector),
                                         allowed_repositories=("other",))
    session = open_session(authorized)
    result = authorized.read(session, "repos/other/doc.md", repository="other")
    assert result["documents"][0]["repo_id"] == "other"
    assert authorized.status(session)["consumed_tokens"] > 0
    bindings["r"]["dependencies"] = ({**link, "source_pin": "d" * 40},)
    with pytest.raises(ContextError, match="confirmed"):
        authorized.read(session, "repos/other/doc.md", offset=4, repository="other")


def test_custom_tokenizer_identity_and_expansion_reason(tmp_path):
    service, view, bindings = setup(tmp_path)
    custom = KnowledgeContextService(view, tmp_path / "custom.db", resolver=lambda view, selector: bindings.get(selector),
                                     tokenizer=lambda text: len(text), tokenizer_id="character-test-v1")
    session = open_session(custom)
    result = custom.read(session, "repos/r/doc.md")
    assert result["token_accounting"] == "character-test-v1"
    assert result["consumed_tokens"] == len(result["model_content"])
    with pytest.raises(ContextError, match="reason"):
        custom.expand(session, target_tokens=2000, reason=" ")
    with pytest.raises(ContextError, match="tokenizer"):
        KnowledgeContextService(view, tmp_path / "custom.db", resolver=lambda view, selector: bindings.get(selector)).status(session)


def test_sdk_dynamic_snapshot_uses_budgeted_context_without_extra_excerpts(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service.repo_spec import RepoSpec
    from infermatrix_copilot.sdk.v1 import ChangedPath, DirectClient, DirectReviewRequest, RepositoryRef
    import yaml
    _, view, _ = setup(tmp_path, "A source-linked API contract. " * 1000)
    (view.root / "repos/r/_index.md").write_text("Repository navigation")
    guide = view.root / "general/review/guides/simplification-audit.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("Read actual code before declaring a finding.")
    spec = RepoSpec("r", aliases=("git.example/subgroup/r",), source_pin=PIN,
                    catalog_hash="b" * 64, policy_hash="c" * 64)
    (view.root / "_repositories.yaml").write_text(yaml.safe_dump({"schema_version": 1, "repos": {"r": spec.to_dict()}}))
    manifest = build_manifest(view.root, "snapshot-2")
    (view.root.parent / "MANIFEST.json").write_text(json.dumps(manifest))
    monkeypatch.setenv("KNOWLEDGE_ROOT", str(view.root.parent))
    request = DirectReviewRequest("dynamic-review", RepositoryRef("git.example/subgroup/r"),
                                  0, PIN, "API", "API contract", (ChangedPath("src/api.py"),))
    client = DirectClient(knowledge_context_path=tmp_path / "sdk.db")
    legacy = client.plan(request)
    assert legacy.related_knowledge["content_chars"] <= 6000
    adaptive = client.plan_adaptive(request)
    assert len(adaptive["model_content"].encode()) <= 24000
    assert len(adaptive["model_content"]) > legacy.related_knowledge["content_chars"]
    assert all("excerpt" not in reference and "content" not in reference for reference in adaptive["documents"])
    assert adaptive["budget"]["identity"]["repository"]["catalog_hash"] == "b" * 64
    # A new SDK instance resumes from the pinned tree, not whichever tree is active later.
    restarted = DirectClient(knowledge_context_path=tmp_path / "sdk.db")
    assert restarted.expand_knowledge_context(adaptive["session_id"], target_tokens=64000,
                                               reason="Read the remaining contract")["capacity_tokens"] == 64000


def test_adaptive_git_sha256_pin_is_supported(tmp_path):
    service, _, _ = setup(tmp_path)
    status = service.open_session("r", source_pin="e" * 64, review_id="sha256-source")
    assert status["identity"]["source_pin"] == "e" * 64


def test_strict_docs_use_same_pinned_budget_and_manifest_checks(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from infermatrix_copilot.engine.agent_runtime.knowledge import _repo_docs_tool
    _, view, _ = setup(tmp_path)
    (view.root / "repos/r/_index.md").write_text("navigation")
    manifest = build_manifest(view.root, "strict-snapshot")
    (view.root.parent / "MANIFEST.json").write_text(json.dumps(manifest))
    monkeypatch.setenv("KNOWLEDGE_ROOT", str(view.root.parent))
    run_dir = tmp_path / "strict-run"
    run_dir.mkdir()
    traces = []
    ctx = SimpleNamespace(
        settings=SimpleNamespace(knowledge_dir=view.root, allowed_knowledge_repositories=(), knowledge_general_docs=[]),
        state={"task_spec": {"repo": "r", "expected_head_sha": PIN}},
        params={"knowledge_context_profile": "adaptive", "knowledge_context_budget": {"initial_tokens": 1000, "max_tokens": 4000}},
        run_dir=run_dir, trace=SimpleNamespace(record=lambda event, **data: traces.append((event, data))))
    tools = _repo_docs_tool(ctx, None)
    packet = json.loads(tools["doc_related"].handler(["src/api.py"]))
    assert packet["consumed_tokens"] <= 1000
    assert traces[0][1]["model_content"] == packet["model_content"]
    read = json.loads(tools["doc_read"].handler("repos/r/doc.md"))
    assert read["consumed_tokens"] <= 1000
    assert "doc_context_expand" in tools
    (view.root / "repos/r/doc.md").write_text("tampered")
    with pytest.raises(KnowledgeViewError):
        tools["doc_read"].handler("repos/r/doc.md")
