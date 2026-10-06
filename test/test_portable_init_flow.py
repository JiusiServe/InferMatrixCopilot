"""Portable initialization on real Git trees and real offline native receipts.

The transports are scripted; inventory, committed source export, stage gates,
validators, trace archives and local acceptance use their production paths.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.feature_discovery_index import build_for_stage
from infermatrix_copilot.kb_service.git_source import GitSource
from infermatrix_copilot.kb_service.gate import JUDGE_SYSTEM
from infermatrix_copilot.kb_service.depth_inputs import SYSTEM_DEPTH_LIGHTWEIGHT
from infermatrix_copilot.kb_service.init_knowledge_inputs import SYSTEM_KNOWLEDGE
from infermatrix_copilot.kb_service.init_feature_discovery import SYSTEM_CONSOLIDATE, SYSTEM_DISCOVER, SYSTEM_REVIEW
from infermatrix_copilot.kb_service.init_stages import SYSTEM_MAP, SYSTEM_RULES, run_stage
from infermatrix_copilot.kb_service.init_support import InitError, InitRecord
from infermatrix_copilot.kb_service.models import ModelGateway
from infermatrix_copilot.kb_service.portable_init import accept_stage, bootstrap_workspace, portable_runtime, stage_receipt
from infermatrix_copilot.kb_service.portable_commands import publish_portable
from infermatrix_copilot.kb_service.portable_publication import check_publication
from infermatrix_copilot.kb_service.knowledge_store import KnowledgeStoreError
from infermatrix_copilot.kb_service.knowledge_coverage import inventory, load_policy
from infermatrix_copilot.kb_service.activate import verify_snapshot
from infermatrix_copilot.kb_service.repo_spec import RepoRegistry, RepoSpec, acceptance_receipt, propose_repository, repository_inventory
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.trace_store import TraceStore


def _git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout.decode().strip()


class PortableNativeScript:
    subscription_billing = True
    supports_native_events = True
    stops_at_spend = True

    def __init__(self):
        self.calls = []

    def complete(self, *, system, messages, model, role, native_event_sink=None, **kwargs):
        prompt = messages[0]["content"]
        payload = json.loads(prompt.split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        self.calls.append({"system": system, "role": role, "payload": payload, "model": model})
        if system == SYSTEM_MAP:
            page = next(p for p in payload["offered_pages"] if p.endswith("/rules.md"))
            data = {"title": "Portable library", "rules_title": "Library rules", "contents_heading": "Pages",
                    "index_intro": "Public library and web interface entry points.",
                    "architecture_md": "The library exports a value; the web interface exposes a ready contract.",
                    "owners": [{"owner": "core", "title": "Core", "page": page,
                                "signals": ["public", "ready"], "scope_prefixes": ["src/", "ui/", "lib/"]}],
                    "general_links": []}
        elif system == SYSTEM_RULES:
            data = {"rules": []}
        elif system == SYSTEM_DISCOVER:
            rows = []
            if payload["round"] != "doc":
                for path, line, fid, description in (
                        ("src/library.py", 1, "public-library", "Return the public library value."),
                        ("ui/ready.ts", 530, "ready-contract", "Expose the frontend ready contract.")):
                    if any(f["path"] == path and f["start"] <= line <= f["end"] for f in payload.get("files", [])):
                        rows.append({"id": fid, "title": fid.replace("-", " ").title(), "owner": "core",
                                     "description": description, "relation": "new", "related_id": "", "aliases": [],
                                     "evidence": [{"path": path, "start": line, "end": line}]})
            data = {"candidates": rows}
        elif system in (SYSTEM_REVIEW, SYSTEM_CONSOLIDATE):
            data = {"decisions": {row["id"]: {"supported": "yes", "relation": "new", "related_id": "",
                    "reason": "The cited public implementation supports this distinct contract."}
                    for row in payload["candidates"]}}
        elif system.startswith(SYSTEM_KNOWLEDGE):
            sections = []
            if "api" in payload["facets"]:
                if any(f["path"] == "src/library.py" for f in payload["files"]):
                    ref = {"path": "src/library.py", "start": 1, "end": 1}
                    body = ("The public_value entry takes no arguments and returns the integer 7. "
                            "This exact function returns its constant value without reading any caller argument.")
                else:
                    ref = {"path": "ui/ready.ts", "start": 530, "end": 530}
                    body = ("The exported ready entry takes no arguments and returns true as a boolean. "
                            "The visible return branch is unconditional within this exact function.")
                sections = [{"facet": "api", "title": "Public return contract", "body": body,
                             "interpretation": "fact", "evidence": [ref]}]
            data = {"title": "Supported API context", "sections": sections}
        elif system == JUDGE_SYSTEM:
            data = {"dimensions": {dimension: "yes" for dimension in payload["dimensions_to_answer"]},
                    "reasons": {"faithful": "The exact shown branch establishes this narrow return contract."}}
        elif system == SYSTEM_DEPTH_LIGHTWEIGHT:
            data = {"title": "Unresolved depth", "sections": [],
                    "unknown_facets": [{"facet": facet, "reason": "The fixture intentionally leaves this depth explanation unsupported."}
                                       for facet in payload["facets"]]}
        else:
            raise AssertionError(f"unexpected model call: {system[:100]}")
        if native_event_sink:
            native_event_sink({"type": "native.session.started", "payload": {"session_id": role + "-portable-fixture"}})
            native_event_sink({"type": "native.response", "payload": {"model": model}})
        return Reply(blocks=[Block(type="text", text=json.dumps(data))], stop_reason="end_turn",
                     usage={"input_tokens": 50, "output_tokens": 25}, model=model)


@pytest.fixture
def portable_world(tmp_path, monkeypatch, request):
    monkeypatch.delenv("KB_GENERATOR", raising=False)
    monkeypatch.delenv("KB_JUDGE", raising=False)
    # Archive-only publication replay needs no credentials or ambient .env;
    # keep fixture failure diagnostics independent of host Settings secrets.
    monkeypatch.setattr("infermatrix_copilot.config.Settings", lambda: SimpleNamespace())
    source_root = tmp_path / "local-library"
    source_root.mkdir()
    overrides = dict(getattr(request, "param", {}))
    object_format = overrides.pop("git_object_format", "sha1")
    _git(source_root, "init", "-q", "-b", "main", f"--object-format={object_format}")
    _git(source_root, "config", "user.email", "fixture@example.invalid")
    _git(source_root, "config", "user.name", "Portable fixture")
    ts = "\n".join(["// filler"] * 529 + ["export function ready(): boolean { return true; }"] + ["// tail"] * 90) + "\n"
    source_files = {"src/__init__.py": "", "src/library.py": "def public_value(): return 7\n", "ui/ready.ts": ts,
                    "lib/contract.langx": "public function unknown_language() { return caller_value; }\n",
                    "sdk/tests/deep/test_library.py": "from src.library import public_value\nassert public_value() == 7\n",
                    "README.md": "# Portable library\n\nUse the public library value and frontend ready contract.\n",
                    "vendor/foreign.py": "def excluded(): return 0\n"}
    for rel, text in source_files.items():
        target = source_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(source_root, "add", ".")
    _git(source_root, "commit", "-qm", "Fixture public contracts")
    source = GitSource(source_root)
    proposal = propose_repository(source, repo_id="portable-library")
    spec = RepoSpec.from_dict({**proposal["spec"], **overrides})
    state = tmp_path / "state"
    registry = RepoRegistry(state)
    registry.register(spec, acceptance_receipt(spec, source, source.head(), accepted=True),
                      source_path=source_root, knowledge_root=tmp_path / "canonical" / "knowledge")
    script = PortableNativeScript()
    traces = TraceStore(state / "init" / "traces")
    gateway = ModelGateway(None, transport_factory=lambda provider: script, recorder=trace_recorder(traces))
    gateway.configure_zcode_pacing = lambda pacer: None
    rt, lifecycle = portable_runtime(None, state, spec.repo_id, gateway=gateway)
    rt.environ = {}
    return {"source": source, "spec": spec, "state": state, "registry": registry,
            "rt": rt, "lifecycle": lifecycle, "script": script, "traces": traces}


def _skeleton(world):
    result = run_stage(world["rt"], world["lifecycle"], "skeleton", dry_run=True,
                       pin=world["spec"].source_pin, subscription_generator=True)
    assert result.status == "dry_run", result.problems
    receipt = stage_receipt(world["state"], world["spec"].repo_id, "skeleton", reviewer="Fixture reviewer")
    return accept_stage(world["state"], world["spec"].repo_id, "skeleton", receipt)


def _discovery(world):
    return run_stage(world["rt"], world["lifecycle"], "feature-discovery", dry_run=True,
                     pin=world["spec"].source_pin, unlimited_subscription=True)


def test_portable_bootstrap_full_inventory_preserves_nested_tests_and_unknown_language(portable_world, tmp_path):
    world = portable_world
    root = bootstrap_workspace(world["state"], world["registry"].get(world["spec"].repo_id))
    assert root == world["rt"].knowledge.path
    manifest = yaml.safe_load((root / "adapters" / world["spec"].repo_id / "manifest.yaml").read_text())
    inv = repository_inventory(world["source"], world["spec"])
    assert set(inv["production"]) == {"src/__init__.py", "src/library.py", "ui/ready.ts", "lib/contract.langx"}
    assert inv["tests"] == ["sdk/tests/deep/test_library.py"]
    assert ".langx" in manifest["portable_scope"]["suffixes"]
    assert manifest["knowledge_lifecycle"]["enabled"] is False
    # Dirty source changes never contaminate the committed source export.
    (world["source"].path / "src/library.py").write_text("dirty source\n")
    tree = world["source"].export(world["spec"].source_pin, tmp_path / "committed-source")
    stage = type("IndexStage", (), {"manifest": manifest, "lifecycle": world["lifecycle"],
        "record": InitRecord("feature-discovery", world["spec"].repo_id, pin=world["spec"].source_pin),
        "rt": world["rt"], "_base_sha": world["rt"].knowledge.main_sha()})()
    index = build_for_stage(tree, stage)
    assert index.files["src/library.py"]["text"] == "def public_value(): return 7\n"
    assert set(index.production) == set(inv["production"]) - {"src/__init__.py"}
    assert index.entries["src/__init__.py"]["classification"] == "empty_package_marker"
    assert "sdk/tests/deep/test_library.py" in index.files
    assert index.files["sdk/tests/deep/test_library.py"]["kind"] == "test"
    assert "vendor/foreign.py" not in index.files


@pytest.mark.parametrize("portable_world", [{}, {"git_object_format": "sha256"}], indirect=True)
def test_portable_accepted_skeleton_discovery_preserves_native_hashes_and_long_ts_evidence(portable_world):
    world = portable_world
    skeleton = _skeleton(world)
    assert skeleton.status == "accepted" and not skeleton.pr.get("number")
    result = _discovery(world)
    assert result.status == "dry_run", result.problems
    assert result.pr["checked_files_sha256"]
    receipt = stage_receipt(world["state"], world["spec"].repo_id, "feature-discovery", reviewer="Fixture reviewer")
    accepted = accept_stage(world["state"], world["spec"].repo_id, "feature-discovery", receipt)
    assert accepted.status == "accepted"
    report_text = world["rt"].knowledge.show(accepted.pr["local_acceptance"]["head_sha"], accepted.discovery["report_path"])
    assert hashlib.sha256(report_text.encode()).hexdigest() == accepted.discovery["report_sha256"]
    report = json.loads(report_text)
    assert report["scan_mode"] == "full"
    assert report["scan_summary"]["production_files"] == 3
    # An empty package marker is present in the reviewed scope and retained in
    # the shared inventory, but contributes no implementation to core coverage.
    catalog_path = f"adapters/{world['spec'].repo_id}/knowledge-coverage.yaml"
    catalog_text = world["rt"].knowledge.show(accepted.pr["local_acceptance"]["head_sha"], catalog_path)
    policy = load_policy(catalog_text, world["lifecycle"].knowledge_dir)
    tree = world["source"].export(world["spec"].source_pin, world["source"].path.parent / "accepted-catalog-source")
    assert set(inventory(tree, policy)) == {"src/library.py", "ui/ready.ts", "lib/contract.langx"}
    assert set(report["evidence_bundles"]) == {"public-library", "ready-contract"}
    assert any(ref["path"] == "ui/ready.ts" and ref["start"] == 530
               for ref in report["evidence_bundles"]["ready-contract"]["refs"])
    for bundle in report["evidence_bundles"].values():
        assert bundle["pin"] == world["spec"].source_pin
        assert bundle["receipts"]
        for receipt in bundle["receipts"]:
            archived = world["traces"].get(receipt["trace_id"])
            assert archived["result"]["native_attempt_id"]
            assert archived["model"]["provider"] in ("zcode", "codex")
    # Both validators ran against the actual preview: no CI/gate function is mocked.
    assert result.problems == []
    assert {c["role"] for c in world["script"].calls} == {"generator", "judge"}
    assert not list(world["state"].rglob("kb.db"))
    modules = run_stage(world["rt"], world["lifecycle"], "modules", dry_run=True,
                        pin=world["spec"].source_pin, unlimited_subscription=True)
    assert modules.status in ("dry_run", "empty"), modules.problems
    assert modules.discovery["catalog_binding"]["catalog_sha256"] == report["catalog_sha256"]
    assert modules.coverage["modules"]["after"] == 1.0
    assert modules.coverage["unrouted"] == []


@pytest.mark.parametrize("stage", ["skeleton", "feature-discovery"])
def test_portable_direct_stage_rejects_new_source_pin_before_model_calls(portable_world, stage):
    world = portable_world
    (world["source"].path / "src/library.py").write_text("def public_value(): return 8\n", encoding="utf-8")
    _git(world["source"].path, "add", "src/library.py")
    _git(world["source"].path, "commit", "-qm", "Change source after approved proposal")
    changed_pin = world["source"].head()
    assert changed_pin != world["spec"].source_pin
    calls = len(world["script"].calls)
    with pytest.raises(InitError, match="portable source pin differs from the accepted batch"):
        run_stage(world["rt"], world["lifecycle"], stage, dry_run=True,
                  pin=changed_pin, subscription_generator=True,
                  unlimited_subscription=stage == "feature-discovery")
    assert len(world["script"].calls) == calls
    assert InitRecord.load(world["state"], world["spec"].repo_id, stage) is None


def test_portable_unaccepted_catalog_blocks_modules_before_model_calls(portable_world):
    world = portable_world
    _skeleton(world)
    catalog = _discovery(world)
    assert catalog.status == "dry_run", catalog.problems
    calls = len(world["script"].calls)
    result = run_stage(world["rt"], world["lifecycle"], "modules", dry_run=True,
                       pin=world["spec"].source_pin, unlimited_subscription=True)
    assert result.status == "blocked"
    assert any("discovery" in message and ("accept" in message or "catalog" in message) for message in result.problems)
    assert len(world["script"].calls) == calls


def test_portable_acceptance_refuses_modified_preview(portable_world):
    world = portable_world
    _skeleton(world)
    result = _discovery(world)
    assert result.status == "dry_run", result.problems
    report = Path(result.pr["dry_run_dir"]) / "tree" / result.discovery["report_path"]
    report.write_text(report.read_text() + "\n")
    with pytest.raises(InitError, match="preview files changed"):
        stage_receipt(world["state"], world["spec"].repo_id, "feature-discovery", reviewer="Fixture reviewer")


@pytest.mark.parametrize("portable_world", [{"per_facet_gt": 0.95}], indirect=True)
def test_portable_new_catalog_retains_reviewed_stricter_facet_target(portable_world):
    world = portable_world
    _skeleton(world)
    result = _discovery(world)
    assert result.status == "dry_run", result.problems
    path = Path(result.pr["dry_run_dir"]) / "tree" / "adapters" / world["spec"].repo_id / "knowledge-coverage.yaml"
    policy = yaml.safe_load(path.read_text())
    assert policy["semantic_depth"]["per_facet_gt"] == 0.95


@pytest.mark.parametrize("mismatch", ["scope", "targets", "missing_depth"])
def test_portable_existing_catalog_migration_cannot_shrink_scope_or_relax_targets(portable_world, mismatch):
    world = portable_world
    _skeleton(world)
    policy = {"schema_version": 1, "required": True,
        "core": {"roots": ["."], "suffixes": [".py", ".ts", ".langx"],
                 "exclude": list(world["spec"].exclude) + list(world["spec"].test_globs), "target": 0.85},
        "semantic_depth": {"per_facet_gt": 0.90, "acceptance_mode": "lightweight"},
        "features": [{"id": "existing-library", "title": "Existing library", "owner": "core", "docs": [],
                      "source_globs": ["src/library.py"], "entry_points": ["src/library.py"],
                      "page": "repos/portable-library/components/core/feature-existing-library.md"}]}
    if mismatch == "scope":
        policy["core"]["suffixes"] = [".py"]
    elif mismatch == "targets":
        policy["semantic_depth"]["per_facet_gt"] = 0.89
    else:
        policy.pop("semantic_depth")
    root = world["rt"].knowledge.path
    path = root / "adapters" / world["spec"].repo_id / "knowledge-coverage.yaml"
    path.write_text(yaml.safe_dump(policy, sort_keys=False))
    _git(root, "add", ".")
    _git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Import historical catalog for migration audit")
    calls = len(world["script"].calls)
    result = _discovery(world)
    assert result.status == "blocked"
    assert any("scope/policy migration" in message for message in result.problems)
    assert result.discovery["scope_migration"]["status"] == "reviewed_proposal_required"
    assert len(world["script"].calls) == calls


@pytest.mark.parametrize("portable_world", [{}, {"git_object_format": "sha256"}], indirect=True)
def test_portable_foundation_unknowns_continue_to_depth_without_final_acceptance(portable_world):
    world = portable_world
    _skeleton(world)
    discovery = _discovery(world)
    assert discovery.status == "dry_run", discovery.problems
    receipt = stage_receipt(world["state"], world["spec"].repo_id, "feature-discovery", reviewer="Fixture reviewer")
    accept_stage(world["state"], world["spec"].repo_id, "feature-discovery", receipt)
    modules = run_stage(world["rt"], world["lifecycle"], "modules", dry_run=True,
                        pin=world["spec"].source_pin, unlimited_subscription=True)
    assert modules.status in ("empty", "dry_run"), modules.problems
    if modules.status == "dry_run":
        receipt = stage_receipt(world["state"], world["spec"].repo_id, "modules", reviewer="Fixture reviewer")
        accept_stage(world["state"], world["spec"].repo_id, "modules", receipt)
    foundation = run_stage(world["rt"], world["lifecycle"], "knowledge", dry_run=True,
                           pin=world["spec"].source_pin, unlimited_subscription=True)
    assert foundation.status == "dry_run", foundation.problems
    summary = foundation.coverage["foundation"]
    assert summary["mode"] == "partial" and summary["tier"] == "foundation"
    assert summary["init_complete"] is False and summary["foundation_targets_met"] is False
    assert set(summary["unknown_features"]) == {"public-library", "ready-contract"}
    assert all("validation" in facets and "api" not in facets for facets in summary["unknown_features"].values())
    receipt = stage_receipt(world["state"], world["spec"].repo_id, "knowledge", reviewer="Fixture reviewer")
    accepted = accept_stage(world["state"], world["spec"].repo_id, "knowledge", receipt)
    assert accepted.status == "accepted" and accepted.coverage["foundation"] == summary
    snapshot = world["state"].parent / "foundation-snapshot"
    calls = len(world["script"].calls)
    manifest = publish_portable(world["state"], world["spec"].repo_id, snapshot, partial=True)
    assert len(world["script"].calls) == calls
    assert manifest["acceptance"]["tier"] == "foundation"
    assert manifest["acceptance"]["init_complete"] is False
    view = verify_snapshot(snapshot)
    with pytest.raises(KnowledgeStoreError, match="foundation publication is incomplete"):
        check_publication(view)
    assert check_publication(view, allow_partial=True) == {
        "tiers": {world["spec"].repo_id: "foundation"}, "init_complete": False}
    canonical = Path(world["registry"].get(world["spec"].repo_id)["bindings"]["knowledge_root"])
    before = {path.relative_to(canonical).as_posix(): path.read_bytes()
              for path in canonical.rglob("*") if path.is_file()}
    occupied = world["state"].parent / "occupied-snapshot"
    occupied.mkdir()
    (occupied / "keep.txt").write_bytes(b"preexisting destination")
    with pytest.raises(InitError, match="destination exists"):
        publish_portable(world["state"], world["spec"].repo_id, occupied, partial=True)
    assert {path.relative_to(canonical).as_posix(): path.read_bytes()
            for path in canonical.rglob("*") if path.is_file()} == before
    assert (occupied / "keep.txt").read_bytes() == b"preexisting destination"
    depth = run_stage(world["rt"], world["lifecycle"], "knowledge-deepen", dry_run=True,
                      pin=world["spec"].source_pin, unlimited_subscription=True,
                      acceptance_mode="lightweight", foundation_mode="partial")
    assert any(call["system"] == SYSTEM_DEPTH_LIGHTWEIGHT for call in world["script"].calls)
    assert depth.depth["foundation"]["local_head_sha"] == accepted.pr["local_acceptance"]["head_sha"]
    assert depth.depth["target_met"] is False and depth.depth["done"] is False
    assert depth.coverage["semantic_depth"]["total_facets"] == 14
    assert depth.coverage["semantic_depth"]["recognized_facets"] == 0
    assert depth.status in ("blocked", "partial")
    with pytest.raises(InitError, match="finished preview"):
        stage_receipt(world["state"], world["spec"].repo_id, "knowledge-deepen", reviewer="Fixture reviewer")
    with pytest.raises(InitError, match="explicitly accepted knowledge preview"):
        publish_portable(world["state"], world["spec"].repo_id,
                         world["state"].parent / "forbidden-final-snapshot")
    assert {path.relative_to(canonical).as_posix(): path.read_bytes()
            for path in canonical.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize("repository", ["repo://library", "owner/library", "https://git.example/group/nested/library"])
def test_sha256_source_links_and_native_depth_prose_replay_are_exact(tmp_path, repository):
    from infermatrix_copilot.kb_service.knowledge_depth import render_block
    from infermatrix_copilot.kb_service.native_depth_audit import _generated_prose, _judged_evidence, _prose
    from infermatrix_copilot.knowledge_service.lifecycle import DEPTH_BLOCK

    pin = "a" * 64
    (tmp_path / "library.py").write_text("def public_value(): return 7\n")
    feature = SimpleNamespace(id="public-api", title="Public API")
    section = {"facet": "api", "title": "Constant return contract", "interpretation": "fact",
               "body": "The public_value entry takes no arguments and returns the constant integer seven.",
               "evidence": [{"path": "library.py", "start": 1, "end": 1}]}
    block = render_block(feature, section, tmp_path, repository, pin, acceptance_mode="lightweight")
    assert DEPTH_BLOCK.fullmatch(block.rstrip("\n")) is not None
    assert _generated_prose(section, repository, pin) == _prose(block)
    _judged_evidence({"evidence": [{"kind": "upstream_text", "text": ["1: def public_value(): return 7"],
        "source_reference": repository + "@" + pin + ":library.py:L1-L1"}]}, block, repository, pin, "api")
