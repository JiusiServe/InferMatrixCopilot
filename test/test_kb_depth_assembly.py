"""Assemble checkpoint fixtures offline; no generation or native approval claims."""

import importlib.util
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.init_stages import _page_frontmatter
from infermatrix_copilot.kb_service.knowledge_coverage import feature_metadata, load_policy
from infermatrix_copilot.kb_service.knowledge_depth import depth_page, digest, render_block
from infermatrix_copilot.knowledge_service.lifecycle import Page


@pytest.fixture
def assembler():
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "eval/knowledge-depth/assemble_depth_campaign.py"
    spec = importlib.util.spec_from_file_location("offline_depth_assembler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _write(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def _commit(root):
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "Offline assembly fixture")
    return _git(root, "rev-parse", "HEAD")


def _page(feature, blocks, extra=""):
    text = _page_frontmatter(feature.title + "：实现深读", kind="architecture", today="2026-10-02", tags=["demo"])
    text += f"[功能概览](feature-{feature.id}.md) · [owner 入口](_index.md)\n\n"
    return text + "\n\n".join(blocks) + "\n" + extra


@pytest.fixture
def world(tmp_path):
    root, source, state = (tmp_path / name for name in ("repository", "source", "state"))
    for repo in (root, source):
        repo.mkdir()
        _git(repo, "init", "--quiet", "-b", "main")
        _git(repo, "config", "user.name", "Offline test")
        _git(repo, "config", "user.email", "offline@example.invalid")
    _write(source, "pkg/core.py", "TIMEOUT = 17\ndef run(value):\n    return value + 1\n")
    _write(source, "docs/guide.md", "The feature increments the input.\n")
    pin = _commit(source)
    policy_data = {"schema_version": 1, "core": {"roots": ["pkg/"], "exclude": ["*/tests/*"]},
                   "semantic_depth": {"per_facet_gt": 0.90}, "features": [
                       {"id": f"f{i}", "title": f"Feature {i}", "owner": "core", "source_globs": ["pkg/core.py"],
                        "entry_points": ["pkg/core.py"], "docs": ["docs/guide.md"],
                        "page": f"repos/demo/components/core/feature-f{i}.md"} for i in range(2)]}
    text = yaml.safe_dump(policy_data)
    policy = load_policy(text, "repos/demo")
    _write(root, "adapters/demo/manifest.yaml", yaml.safe_dump({"knowledge": {"repo_subdir": "repos/demo"}}))
    _write(root, "adapters/demo/knowledge-coverage.yaml", text)
    blocks = {}
    for feature, facet in ((policy.features[0], "api"), (policy.features[0], "configuration"), (policy.features[1], "dependencies")):
        section = {"facet": facet, "title": facet, "body": "The pinned implementation increments input with a timeout default of 17.",
                   "interpretation": "fact", "evidence": [{"path": "pkg/core.py", "start": 1, "end": 3}]}
        blocks[(feature.id, facet)] = render_block(feature, section, source, "owner/demo", pin)
    f0, f1 = policy.features
    old = feature_metadata(_page(f0, [blocks[("f0", "api")]], "Existing owner note.\n"), f0)
    old = Page.parse(old).with_sources(["existing-source"]).render()
    _write(root, "knowledge/" + depth_page(f0), old)
    for feature in policy.features:
        _write(root, "knowledge/" + feature.page, "Existing overview remains unchanged.\n")
    index = "repos/demo/components/core/_index.md"
    _write(root, "knowledge/" + index, "Existing index body.\n- [Existing depth](feature-depth-f0.md)\n")
    baseline = _commit(root)
    campaign = {"repo": "demo", "baseline": baseline, "pin": pin, "features": 2, "denominator": 14,
                "workers": 2, "partitions": {"0": ["f0"], "1": ["f1"]}}
    _write(state, "campaign.json", json.dumps(campaign))
    records, checkpoints = [], []
    for n, feature in enumerate(policy.features):
        facet = "configuration" if n == 0 else "dependencies"
        block = blocks[(feature.id, facet)]
        candidate = _page(feature, [blocks[("f0", "api")], block], "Existing owner note.\n") if n == 0 else _page(feature, [block])
        candidate = Page.parse(candidate).with_sources(["new-source"]).render()
        result = {"verdict": "pass", "reason": "Pinned source supports this fixture.",
                  "dimensions": {"faithful": "yes", "non_contradictory": "yes", "does_not_weaken": "yes"}}
        call = {"facets": {facet: result}, "model": "codex:gpt-5.4", "native_trace_id": f"fixture-call-{n}",
                "native_reply_sha256": str(n + 1) * 64}
        receipt = {**result, **{key: call[key] for key in ("model", "native_trace_id", "native_reply_sha256")},
                   "block_sha256": digest(block)}
        record = {"stage": "knowledge-deepen", "repo": "demo", "pin": pin, "kb_base_sha": baseline, "status": "partial",
                  "depth": {"accepted": {depth_page(feature): candidate}, "features": {
                      f.id: {"attempts": 1 if f.id == feature.id else 0, **({"accepted_sha256": digest(candidate)} if f.id == feature.id else {})}
                      for f in policy.features}}, "verdicts": {"depth:" + feature.id: {"facets": {facet: receipt}, "calls": [call]}}}
        path = state / f"worker-{n}/init/demo/knowledge-deepen.json"
        _write(state, path.relative_to(state), json.dumps(record))
        _write(state, f"worker-{n}/.worker.lock", "")
        records.append(record)
        checkpoints.append(path)
    _write(state, ".campaign.lock", "")
    return SimpleNamespace(root=root, source=source, state=state, records=records, checkpoints=checkpoints,
                           blocks=blocks, policy=policy, old=old, index=index, campaign=campaign)


def _save(world, worker=0):
    world.checkpoints[worker].write_text(json.dumps(world.records[worker]))


def _candidate(world, edit, worker=0):
    record = world.records[worker]
    feature = world.policy.features[worker]
    page = depth_page(feature)
    record["depth"]["accepted"][page] = edit(record["depth"]["accepted"][page])
    record["depth"]["features"][feature.id]["accepted_sha256"] = digest(record["depth"]["accepted"][page])
    _save(world, worker)


def test_assembly_preserves_old_body_metadata_and_overviews_with_distinct_hashes(assembler, world):
    report, writes = assembler.assemble(world.root, world.state, world.source)
    page = depth_page(world.policy.features[0])
    proposed = writes[page]
    assert world.blocks[("f0", "api")] in proposed
    assert assembler._body(proposed).startswith(assembler._body(world.old))
    assert Page.parse(proposed).frontmatter_data()["feature"] == "f0"
    assert Page.parse(proposed).sources() == ["existing-source", "new-source"]
    assert report["pages"][0]["checkpoint_accepted_sha256"] != report["pages"][0]["assembled_sha256"]
    assert report["baseline_facets"] == 1 and report["new_receipt_bound_facets"] == 2
    assert report["source_verified_facets"] == 3 and report["denominator"] == 14
    assert report["recognized_feature_count"] == 2 and report["all_features_recognized"]
    assert report["native_archive_audit_required"] and not report["source_target_met"]
    assert set(writes) == {page, depth_page(world.policy.features[1]), world.index}
    assert writes[world.index].startswith((world.root / "knowledge" / world.index).read_text())
    assert writes[world.index].count("](feature-depth-f1.md)") == 1
    assert not any(feature.page in writes for feature in world.policy.features)


@pytest.mark.parametrize("key", ["pin", "kb_base_sha", "repo", "stage"])
def test_checkpoint_identity_mismatch_fails(assembler, world, key):
    world.records[0][key] = "different"
    _save(world)
    with pytest.raises(ValueError, match="identity"):
        assembler.assemble(world.root, world.state, world.source)


def test_overlapping_partition_ownership_cannot_assemble(assembler, world):
    world.campaign["partitions"]["1"] = ["f0", "f1"]
    (world.state / "campaign.json").write_text(json.dumps(world.campaign))
    with pytest.raises(ValueError, match="exactly once"):
        assembler.assemble(world.root, world.state, world.source)


def test_worker_cannot_touch_another_partition(assembler, world):
    world.records[0]["depth"]["features"]["f1"]["attempts"] = 1
    _save(world)
    with pytest.raises(ValueError, match="another partition"):
        assembler.assemble(world.root, world.state, world.source)


def test_durable_accepted_hash_must_match_exact_page(assembler, world):
    world.records[0]["depth"]["features"]["f0"]["accepted_sha256"] = "0" * 64
    _save(world)
    with pytest.raises(ValueError, match="page hash"):
        assembler.assemble(world.root, world.state, world.source)


@pytest.mark.parametrize("mutation", ["no_pass", "no_trace", "wrong_block", "unsure", "missing_call"])
def test_new_block_requires_successful_exact_checkpoint_receipt(assembler, world, mutation):
    prior = world.records[0]["verdicts"]["depth:f0"]
    receipt = prior["facets"]["configuration"]
    if mutation == "no_pass":
        receipt["verdict"] = "fail"
    elif mutation == "no_trace":
        receipt["native_trace_id"] = ""
    elif mutation == "wrong_block":
        receipt["block_sha256"] = "0" * 64
    elif mutation == "unsure":
        receipt["dimensions"]["faithful"] = "unsure"
    else:
        prior["calls"] = []
    _save(world)
    with pytest.raises(ValueError, match="receipt"):
        assembler.assemble(world.root, world.state, world.source)


def test_old_blocks_and_unapproved_outside_prose_cannot_be_removed(assembler, world):
    _candidate(world, lambda text: text.replace(world.blocks[("f0", "api")], ""))
    with pytest.raises(ValueError, match="existing depth block"):
        assembler.assemble(world.root, world.state, world.source)


def test_outside_block_body_is_not_rewritten(assembler, world):
    _candidate(world, lambda text: text.replace("Existing owner note.", "Rewritten owner note."))
    with pytest.raises(ValueError, match="outside approved"):
        assembler.assemble(world.root, world.state, world.source)


def test_ignored_source_witness_is_not_evidence_at_the_pin(assembler, world):
    (world.source / ".git/info/exclude").write_text("pkg/extra.py\n")
    _write(world.source, "pkg/extra.py", "def invented():\n    return 17\n")
    section = {"facet": "configuration", "title": "configuration", "body": "Invented implementation returns 17.",
               "interpretation": "fact", "evidence": [{"path": "pkg/extra.py", "start": 1, "end": 2}]}
    replacement = render_block(world.policy.features[0], section, world.source, "owner/demo", world.campaign["pin"])
    world.records[0]["verdicts"]["depth:f0"]["facets"]["configuration"]["block_sha256"] = digest(replacement)
    _candidate(world, lambda text: text.replace(world.blocks[("f0", "configuration")], replacement))
    with pytest.raises(ValueError, match="outside the pinned source"):
        assembler.assemble(world.root, world.state, world.source)


@pytest.mark.parametrize("routes", [1, 2])
def test_owner_index_link_is_reused_once_or_rejects_duplicates(assembler, world, routes):
    target = world.root / "knowledge" / world.index
    target.write_text(target.read_text() + "- [Already routed](feature-depth-f1.md)\n" * routes)
    baseline = _commit(world.root)
    world.campaign["baseline"] = baseline
    (world.state / "campaign.json").write_text(json.dumps(world.campaign))
    for n, record in enumerate(world.records):
        record["kb_base_sha"] = baseline
        _save(world, n)
    if routes == 1:
        report, writes = assembler.assemble(world.root, world.state, world.source)
        assert not report["index_links"] and world.index not in writes
    else:
        with pytest.raises(ValueError, match="duplicate owner index"):
            assembler.assemble(world.root, world.state, world.source)


def test_changed_source_and_unrelated_target_changes_are_rejected(assembler, world):
    _write(world.source, "pkg/core.py", "def run(value):\n    return 99\n")
    with pytest.raises(ValueError, match="clean source"):
        assembler.assemble(world.root, world.state, world.source)
    _git(world.source, "checkout", "--", "pkg/core.py")
    _write(world.root, "knowledge/" + depth_page(world.policy.features[0]), world.old + "Manual edit.\n")
    with pytest.raises(ValueError, match="unrelated changes"):
        assembler.assemble(world.root, world.state, world.source)


def test_cli_dry_run_does_not_write_pages(assembler, world, monkeypatch, capsys):
    before = {p: p.read_bytes() for p in (world.root / "knowledge").rglob("*.md")}
    report = world.state / "assembly-report.json"
    monkeypatch.setattr(sys, "argv", ["assemble", "--root", str(world.root), "--state", str(world.state),
                                     "--source-tree", str(world.source), "--report", str(report)])
    assert assembler.main() == 0
    assert {p: p.read_bytes() for p in (world.root / "knowledge").rglob("*.md")} == before
    assert not json.loads(report.read_text())["applied"]
    assert '"applied": false' in capsys.readouterr().out
