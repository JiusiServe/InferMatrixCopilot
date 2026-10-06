"""Activation receipt checks on real snapshot bytes; no model calls are simulated."""
import hashlib
import json

import pytest
import yaml

from infermatrix_copilot.kb_service.activate import verify_snapshot
from infermatrix_copilot.kb_service.knowledge_store import KnowledgeStore, KnowledgeStoreError
from infermatrix_copilot.kb_service.portable_publication import check_publication
from infermatrix_copilot.kb_service.repo_spec import RepoSpec
from infermatrix_copilot.knowledge_view import KnowledgeViewError, build_manifest


PIN = "a" * 40
HEAD = "b" * 40


def _snapshot(tmp_path, tier="final"):
    root = tmp_path / "canonical" / "knowledge"
    catalog = "schema_version: 1\nfixture_catalog: fixed\n"
    catalog_hash = hashlib.sha256(catalog.encode()).hexdigest()
    spec = RepoSpec("library", source_pin=PIN, catalog_hash=catalog_hash, policy_hash=catalog_hash)
    def page(title):
        return (f'---\ntitle: "{title}"\ncreated: 2026-10-06\nupdated: 2026-10-06\n'
                f'type: index\ntags: [general]\nsources: []\n---\n\n# {title}\n')
    files = {"AGENTS.md": "Knowledge governance\n", "_format.yaml": "format_version: 2\n",
             "_repositories.yaml": yaml.safe_dump({"schema_version": 1, "repos": {"library": spec.to_dict()}}),
             "general/_index.md": page("General"), "repos/_index.md": page("Repositories"),
             "repos/library/_index.md": page("Library"), "repos/library/_catalog.yaml": catalog}
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    summary = {"tier": tier, "init_complete": tier == "final", "source_pin": PIN,
               "catalog_sha256": catalog_hash,
               "checks": {"source": True, "native": True, "structural": True, "format": True,
                          "retrieval": True, "semantic_depth": tier == "final"}}
    snapshot = tmp_path / "snapshot"
    KnowledgeStore(root, "library").snapshot(snapshot, source_pin=PIN, publication_head=HEAD, acceptance=summary)
    return snapshot


def _rebind_bytes(snapshot):
    """Rebuild format integrity only; never renew the publication acceptance scope."""
    manifest = json.loads((snapshot / "MANIFEST.json").read_text())
    manifest.update(build_manifest(snapshot / "knowledge", manifest["snapshot"]))
    (snapshot / "MANIFEST.json").write_text(json.dumps(manifest))


def test_final_publication_acceptance_is_bound_to_verified_snapshot(tmp_path):
    view = verify_snapshot(_snapshot(tmp_path))
    assert check_publication(view) == {"tiers": {"library": "final"}, "init_complete": True}


def test_foundation_activation_requires_explicit_partial_choice(tmp_path):
    view = verify_snapshot(_snapshot(tmp_path, "foundation"))
    with pytest.raises(KnowledgeStoreError, match="incomplete"):
        check_publication(view)
    assert check_publication(view, allow_partial=True) == {
        "tiers": {"library": "foundation"}, "init_complete": False}


def test_rehashing_format_manifest_does_not_renew_publication_scope(tmp_path):
    snapshot = _snapshot(tmp_path)
    (snapshot / "knowledge/repos/library/_index.md").write_text(
        (snapshot / "knowledge/repos/library/_index.md").read_text() + "Changed after acceptance.\n")
    _rebind_bytes(snapshot)
    view = verify_snapshot(snapshot)
    with pytest.raises(KnowledgeStoreError, match="no longer binds"):
        check_publication(view)


def test_catalog_drift_is_refused_even_with_new_format_hashes(tmp_path):
    snapshot = _snapshot(tmp_path)
    (snapshot / "knowledge/repos/library/_catalog.yaml").write_text("Changed catalog.\n")
    _rebind_bytes(snapshot)
    view = verify_snapshot(snapshot)
    with pytest.raises(KnowledgeStoreError, match="identity"):
        check_publication(view)


def test_verified_view_rejects_receipt_byte_substitution(tmp_path):
    snapshot = _snapshot(tmp_path)
    view = verify_snapshot(snapshot)
    receipt = snapshot / "knowledge/_publication-library.json"
    receipt.write_text(receipt.read_text() + "\n")
    with pytest.raises(KnowledgeViewError):
        check_publication(view)
