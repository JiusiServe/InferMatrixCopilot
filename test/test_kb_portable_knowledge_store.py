import hashlib
import json
from dataclasses import replace

import pytest

from infermatrix_copilot.knowledge_view import KnowledgeView, KnowledgeViewError
from infermatrix_copilot.kb_service.activate import verify_snapshot
from infermatrix_copilot.kb_service.knowledge_store import KnowledgeStore, KnowledgeStoreError, immutable_json, local_acceptance_receipt, validate_local_acceptance
from infermatrix_copilot.kb_service.repo_spec import RepoSpec, RepoSpecError, canonical_json, list_snapshot_repos, resolve_snapshot_repo

S0 = "1" * 40
S1 = "2" * 40


def _tree(root, spec=None):
    spec = spec or RepoSpec(repo_id="library", aliases=("lib",), source_pin=S0,
                            catalog_hash="a" * 64, policy_hash="b" * 64)
    def page(title):
        return f'---\ntitle: "{title}"\ncreated: 2026-10-06\nupdated: 2026-10-06\ntype: index\ntags: [general]\nsources: []\n---\n\n# {title}\n'
    files = {"AGENTS.md": "Existing contribution format\n", "_format.yaml": "format_version: 2\n",
             "_repositories.yaml": canonical_json({"schema_version": 1, "repos": {spec.repo_id: spec.to_dict()}}).decode(),
             "repos/_index.md": page("Repositories"), "general/_index.md": page("General"),
             "repos/library/_index.md": page("Library"), "repos/library/components/_index.md": page("Components"),
             "repos/library/components/runtime/_index.md": page("Runtime"),
             "repos/library/_routes.yaml": "schema_version: 1\nowners:\n- owner: runtime\n  path: repos/library/components/runtime/_index.md\n  signals: [api]\n  scope_prefixes: [src/]\n"}
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    hashes = {rel: hashlib.sha256(text.encode()).hexdigest() for rel, text in files.items()}
    return KnowledgeView(root, "fixed-snapshot", hashes), files


def test_served_registry_aliases_bound_only_to_current_verified_view(tmp_path):
    view, _ = _tree(tmp_path / "knowledge")
    binding = resolve_snapshot_repo(view, "lib")
    assert binding.repo_id == "library" and binding.knowledge_slice == "repos/library"
    assert binding.catalog_hash == "a" * 64 and binding.policy_hash == "b" * 64
    assert binding.source_pin == S0 and binding.owner_routes[0]["owner"] == "runtime"
    assert list_snapshot_repos(view) == (binding,)
    assert resolve_snapshot_repo(view, "unregistered") is None
    assert resolve_snapshot_repo(view, "../library") is None
    (view.root / "_repositories.yaml").write_text("tampered registry")
    with pytest.raises(KnowledgeViewError):
        resolve_snapshot_repo(view, "lib")


def test_old_snapshot_exact_slice_preserved_without_invented_pin_or_policy(tmp_path):
    view, files = _tree(tmp_path / "knowledge")
    (view.root / "_repositories.yaml").unlink()
    del files["_repositories.yaml"]
    view = KnowledgeView(view.root, "old", {k: hashlib.sha256(v.encode()).hexdigest() for k, v in files.items()})
    binding = resolve_snapshot_repo(view, "library")
    assert binding.repo_id == "library" and binding.source_pin == "" and binding.catalog_hash == "" and binding.policy_hash == ""
    assert resolve_snapshot_repo(view, "lib") is None
    assert list_snapshot_repos(view) == (binding,)


def test_registry_ambiguous_alias_or_cross_slice_route_is_refused(tmp_path):
    view, files = _tree(tmp_path / "knowledge")
    registry = json.loads(files["_repositories.yaml"])
    registry["repos"]["other"] = RepoSpec(repo_id="other", aliases=("lib",)).to_dict()
    (view.root / "_repositories.yaml").write_bytes(canonical_json(registry))
    plain = KnowledgeView(view.root, "unverified")
    with pytest.raises(RepoSpecError, match="ambiguous"):
        resolve_snapshot_repo(plain, "lib")
    registry["repos"].pop("other")
    (view.root / "_repositories.yaml").write_bytes(canonical_json(registry))
    (view.root / "repos/library/_routes.yaml").write_text("owners:\n- owner: other\n  path: repos/other/_index.md\n")
    with pytest.raises(RepoSpecError, match="crosses"):
        resolve_snapshot_repo(plain, "library")


@pytest.mark.parametrize("mode", ["central", "in_repo"])
def test_canonical_snapshot_same_format_with_separate_source_and_publication_commits(tmp_path, mode):
    root = tmp_path / ("central/knowledge" if mode == "central" else "source/.infermatrix/knowledge")
    _tree(root)
    store = KnowledgeStore(root, "library", mode=mode)
    manifest = store.snapshot(tmp_path / "accepted-snapshot", source_pin=S0, publication_head=S1)
    assert manifest["source_pin"] == S0 and manifest["publication_head"] == S1
    assert manifest["source_pin"] != manifest["publication_head"]
    assert manifest["knowledge_storage"] == mode and manifest["schema_version"] == 1
    verified = verify_snapshot(tmp_path / "accepted-snapshot")
    assert resolve_snapshot_repo(verified, "library").source_pin == S0
    assert manifest["knowledge_format"] == 2 and manifest["tree_sha256"] == verified.tree_sha256
    with pytest.raises(KnowledgeStoreError):
        store.snapshot(root / "self-update", source_pin=S0, publication_head=S1)


def test_mirror_is_verified_read_only_and_edited_or_unbound_copy_never_overwritten(tmp_path):
    root = tmp_path / "canonical"
    _tree(root)
    store = KnowledgeStore(root, "library")
    mirror = tmp_path / "mirror"
    first = store.sync_mirror(mirror, source_pin=S0, publication_head=S1)
    assert KnowledgeStore.verify_mirror(mirror) == first
    automatic_readonly = KnowledgeStore(mirror / "knowledge", "library")
    with pytest.raises(KnowledgeStoreError, match="read-only"):
        automatic_readonly.write_files({"repos/library/_index.md": "edit"})
    page = mirror / "knowledge/repos/library/_index.md"
    original = page.read_bytes()
    page.write_bytes(b"local conflict")
    with pytest.raises(KnowledgeStoreError):
        store.sync_mirror(mirror, source_pin=S0, publication_head="3" * 40)
    assert page.read_bytes() == b"local conflict"
    page.write_bytes(original)
    (mirror / "unbound.txt").write_text("user work")
    with pytest.raises(KnowledgeStoreError, match="unbound"):
        store.sync_mirror(mirror, source_pin=S0, publication_head=S1)
    assert (mirror / "unbound.txt").read_text() == "user work"


def test_clean_mirror_update_keeps_canonical_authority_and_refuses_other_repository(tmp_path):
    root = tmp_path / "canonical"
    _tree(root)
    store = KnowledgeStore(root, "library")
    mirror = tmp_path / "mirror"
    old = store.sync_mirror(mirror, source_pin=S0, publication_head=S1)
    store.write_files({"repos/library/_index.md": "New reviewed index\n"})
    new = store.sync_mirror(mirror, source_pin=S0, publication_head="3" * 40)
    assert old["snapshot"] != new["snapshot"] and new["source_pin"] == S0
    assert (mirror / "knowledge/repos/library/_index.md").read_text() == "New reviewed index\n"
    with pytest.raises(KnowledgeStoreError, match="another repository"):
        KnowledgeStore(root, "other").sync_mirror(mirror, source_pin=S0, publication_head=S1)


def test_all_destination_conflicts_checked_before_any_canonical_write(tmp_path):
    root = tmp_path / "canonical"
    _, files = _tree(root)
    store = KnowledgeStore(root, "library")
    rel = "repos/library/_index.md"
    second = "repos/library/components/runtime/_index.md"
    with pytest.raises(KnowledgeStoreError, match="changed"):
        store.write_files({rel: "replacement", second: "replacement"}, expected_hashes={rel: hashlib.sha256(files[rel].encode()).hexdigest(), second: "0" * 64})
    assert (root / rel).read_text() == files[rel]
    with pytest.raises(KnowledgeStoreError, match="crosses"):
        store.write_files({"repos/other/_index.md": "wrong owner"})


def test_local_acceptance_exact_files_heads_and_real_review_artifacts(tmp_path):
    native = tmp_path / "genuine-review.json"
    native.write_text('{"genuine_saved_review":true}\n')
    files = {"knowledge/repos/library/_index.md": "Reviewed knowledge\n"}
    kwargs = dict(repo_id="library", source_pin=S0, publication_head=S1, files=files)
    receipt = local_acceptance_receipt(**kwargs, checks={"source_integrity": True, "native_review": True, "format": True}, accepted=True, review_receipts=(native,))
    assert receipt["source_pin"] == S0 and receipt["publication_head"] == S1 and receipt["forge"] == "none"
    output = tmp_path / "local-acceptance.json"
    h = immutable_json(output, receipt)
    assert h == hashlib.sha256(output.read_bytes()).hexdigest()
    validate_local_acceptance(receipt, **kwargs)
    with pytest.raises(KnowledgeStoreError):
        validate_local_acceptance(receipt, **{**kwargs, "files": {next(iter(files)): "changed"}})
    with pytest.raises(KnowledgeStoreError):
        immutable_json(output, {**receipt, "publication_head": "3" * 40})
    native.write_text("changed actual review record")
    with pytest.raises(KnowledgeStoreError):
        validate_local_acceptance(receipt, **kwargs)
    with pytest.raises(KnowledgeStoreError):
        local_acceptance_receipt(**kwargs, checks={"native_review": None}, accepted=True)
    with pytest.raises(KnowledgeStoreError):
        local_acceptance_receipt(**kwargs, checks={"native_review": True}, accepted=False)


@pytest.mark.parametrize("tier", ["final", "foundation"])
def test_mirror_preserves_actual_canonical_acceptance_tier_and_refuses_stale_scope(tmp_path, tier):
    root = tmp_path / "canonical"
    _tree(root)
    store = KnowledgeStore(root, "library")
    final = tier == "final"
    acceptance = {"tier": tier, "init_complete": final, "source_pin": S0, "catalog_sha256": "a" * 64,
                  "checks": {"source": True, "native": True, "structural": True,
                             "semantic_depth": final, "retrieval": final}}
    published = store.snapshot(tmp_path / "published", source_pin=S0, publication_head=S1, acceptance=acceptance)
    assert published["acceptance"] == acceptance
    assert verify_snapshot(tmp_path / "published").verified
    copied = store.sync_mirror(tmp_path / "mirror", source_pin=S0, publication_head=S1)
    assert copied["acceptance"] == acceptance and copied["canonical_snapshot"] == published["snapshot"]
    assert copied["snapshot"] != published["snapshot"]
    assert verify_snapshot(tmp_path / "mirror").verified
    with pytest.raises(KnowledgeStoreError):
        store.sync_mirror(tmp_path / "wrong-summary", source_pin=S0, publication_head=S1,
                          acceptance={**acceptance, "init_complete": not final})
    (root / "repos/library/_index.md").write_text("changed after acceptance")
    with pytest.raises(KnowledgeStoreError, match="no longer binds"):
        store.sync_mirror(tmp_path / "mirror", source_pin=S0, publication_head=S1)


def test_final_status_requires_passing_gates_and_matching_catalog(tmp_path):
    root = tmp_path / "canonical"
    _tree(root)
    store = KnowledgeStore(root, "library")
    incomplete = {"tier": "final", "init_complete": True, "source_pin": S0, "catalog_sha256": "a" * 64,
                  "checks": {"source": True, "native": True, "structural": True,
                             "semantic_depth": False, "retrieval": True}}
    with pytest.raises(KnowledgeStoreError, match="required passing"):
        store.record_acceptance(source_pin=S0, publication_head=S1, acceptance=incomplete)
    with pytest.raises(KnowledgeStoreError, match="frozen served registry"):
        store.record_acceptance(source_pin=S0, publication_head=S1,
                                acceptance={**incomplete, "catalog_sha256": "c" * 64,
                                            "checks": {**incomplete["checks"], "semantic_depth": True}})


def test_mirror_contains_only_selected_repository_and_shared_general(tmp_path):
    root = tmp_path / "canonical"
    _, files = _tree(root)
    other = root / "repos/secret/_index.md"
    other.parent.mkdir(parents=True)
    other.write_text(files["repos/library/_index.md"].replace("Library", "Secret internal repo"))
    other_summary = root / "_publication-secret.json"
    other_summary.write_text('{"internal":"unrelated repo receipt"}\n')
    (root / "repos/_index.md").write_text(files["repos/_index.md"] + "\n- [Secret](secret/_index.md)\n")
    registry = json.loads(files["_repositories.yaml"])
    registry["repos"]["secret"] = RepoSpec(repo_id="secret", source_pin="3" * 40).to_dict()
    (root / "_repositories.yaml").write_bytes(canonical_json(registry))
    store = KnowledgeStore(root, "library")
    full = store.snapshot(tmp_path / "full", source_pin=S0, publication_head=S1)
    mirror = store.sync_mirror(tmp_path / "mirror", source_pin=S0, publication_head=S1)
    assert "repos/secret/_index.md" in full["files"]
    assert not any("secret" in path for path in mirror["files"])
    assert mirror["canonical_snapshot"] == full["snapshot"]
    assert mirror["snapshot"] != full["snapshot"]
    served = verify_snapshot(tmp_path / "mirror")
    assert list_snapshot_repos(served)[0].repo_id == "library"
    assert len(list_snapshot_repos(served)) == 1
    assert resolve_snapshot_repo(served, "secret") is None
    assert "Secret" not in served.read_text("repos/_index.md")
    assert served.read_text("general/_index.md") == files["general/_index.md"]
    assert "secret" not in served.read_text("_repositories.yaml")


def test_mirror_rejects_invalid_manifest_even_if_marker_rehashed(tmp_path):
    root = tmp_path / "canonical"
    _tree(root)
    store = KnowledgeStore(root, "library")
    mirror = tmp_path / "mirror"
    store.sync_mirror(mirror, source_pin=S0, publication_head=S1)
    path = mirror / "MANIFEST.json"
    manifest = json.loads(path.read_text())
    manifest["tree_sha256"] = "0" * 64
    path.write_bytes(canonical_json(manifest))
    marker_path = mirror / "MIRROR.json"
    marker = json.loads(marker_path.read_text())
    marker["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    marker_path.write_bytes(canonical_json(marker))
    with pytest.raises(KnowledgeStoreError, match="verified knowledge manifest"):
        KnowledgeStore.verify_mirror(mirror)


def test_saved_acceptance_cannot_advertise_final_with_failed_gate(tmp_path):
    root = tmp_path / "canonical"
    _tree(root)
    store = KnowledgeStore(root, "library")
    acceptance = {"tier": "final", "init_complete": True, "source_pin": S0, "catalog_sha256": "a" * 64,
                  "checks": {"source": True, "native": True, "structural": True,
                             "semantic_depth": True, "retrieval": True}}
    store.record_acceptance(source_pin=S0, publication_head=S1, acceptance=acceptance)
    stored = json.loads(store.acceptance_path.read_text())
    stored["acceptance"]["checks"]["native"] = False
    store.acceptance_path.write_bytes(canonical_json(stored))
    with pytest.raises(KnowledgeStoreError, match="required passing"):
        store.sync_mirror(tmp_path / "mirror", source_pin=S0, publication_head=S1)
