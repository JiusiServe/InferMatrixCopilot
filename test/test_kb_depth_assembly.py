"""Assemble checkpoint fixtures offline; no generation or native approval claims."""

import importlib.util
import json
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.init_stages import _page_frontmatter
from infermatrix_copilot.kb_service.knowledge_coverage import feature_metadata, load_policy
from infermatrix_copilot.kb_service.knowledge_depth import depth_page, digest, render_block
from infermatrix_copilot.knowledge_service.lifecycle import DEPTH_BLOCK, Page


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


def test_thirteen_worker_assembly_keeps_unique_ownership_and_full_policy(assembler, world):
    world.campaign["workers"] = 13
    for number in range(2, 13):
        world.campaign["partitions"][str(number)] = []
        record = {**world.records[0], "depth": {"accepted": {}, "features": {}}, "verdicts": {}}
        _write(world.state, f"worker-{number}/init/demo/knowledge-deepen.json", json.dumps(record))
        _write(world.state, f"worker-{number}/.worker.lock", "")
    (world.state / "campaign.json").write_text(json.dumps(world.campaign))
    report, _ = assembler.assemble(world.root, world.state, world.source)
    assert report["workers"] == 13 and report["denominator"] == 14
    assert report["new_receipt_bound_facets"] == 2
    assert report["source_verified_facets"] == 3


def test_retained_seed_navigation_is_restored_without_a_new_worker_approval(assembler, world):
    _write(world.root, "knowledge/" + world.index, "Immutable foundation navigation.\n")
    baseline = _commit(world.root)
    world.campaign["baseline"] = baseline
    (world.state / "campaign.json").write_text(json.dumps(world.campaign))
    world.records[0]["depth"]["accepted"] = {}
    world.records[0]["verdicts"] = {}
    for number, record in enumerate(world.records):
        record["kb_base_sha"] = baseline
        _save(world, number)

    report, writes = assembler.assemble(world.root, world.state, world.source)
    retained_page = depth_page(world.policy.features[0])
    assert retained_page not in writes
    assert (world.root / "knowledge" / retained_page).read_text() == world.old
    assert writes[world.index].startswith("Immutable foundation navigation.\n")
    assert writes[world.index].count("](feature-depth-f0.md)") == 1
    assert report["baseline_facets"] == 1
    assert report["new_receipt_bound_facets"] == 1


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


def _replace_block_body(block, change, *, pin=None, facet=None):
    match = DEPTH_BLOCK.fullmatch(block)
    body = change(match[5])
    return (f"<!-- kb:depth feature={match[1]} facet={facet or match[2]} pin={pin or match[3]} "
            f"sha256={digest(body)} -->\n" + body + "\n<!-- /kb:depth -->")


def _archive(world, block):
    match = DEPTH_BLOCK.fullmatch(block)
    feature = world.policy.features[0]
    page = depth_page(feature)
    approval = {"feature": feature.id, "facet": match[2], "page": page, "pin": world.campaign["pin"],
                "block_sha256": digest(block), "native_trace_id": "historical-fixture-call",
                "native_reply_sha256": "a" * 64,
                "dimensions": {d: "yes" for d in ("faithful", "non_contradictory", "does_not_weaken")},
                "model": {"role": "judge", "provider": "codex", "model": "gpt-5.4", "served_model": ""}}
    return {"schema_version": 1, "repo": "demo", "pin": world.campaign["pin"], "feature": feature.id,
            "facet": match[2], "page": page, "historical_knowledge_base_sha": world.campaign["baseline"],
            "original_page_sha256": digest(world.old), "raw_block_sha256": digest(block),
            "body_sha256": match[4], "raw_block": block, "native_approval": approval,
            "current_status": "unknown_pending_replacement"}


@pytest.fixture
def retired_world(world):
    # The old lexical checker confused the homonymous class method on line 3
    # with the module helper actually called by run. The stronger proof gate
    # rejects this exact historical trace; the source and prose stay intact.
    source = "function helper() { return 1; }\nclass Wrong {\n  helper() { return 2; }\n}\nfunction run() { return helper(); }\n"
    _write(world.source, "pkg/client.ts", source)
    old_pin, pin = world.campaign["pin"], _commit(world.source)

    def repin(text):
        return DEPTH_BLOCK.sub(lambda m: _replace_block_body(m.group(), lambda body: body.replace(old_pin, pin), pin=pin), text)

    world.blocks = {key: repin(block) for key, block in world.blocks.items()}
    world.old = repin(world.old)
    flow = {"facet": "flow", "title": "Module helper path", "body": "run returns the module helper result.",
            "interpretation": "fact", "evidence": [{"path": "pkg/client.ts", "start": 1, "end": 5}],
            "trace": [{"path": "pkg/client.ts", "symbol": "run", "start": 5, "end": 5},
                      {"path": "pkg/client.ts", "symbol": "helper", "start": 1, "end": 1}]}
    valid = render_block(world.policy.features[0], flow, world.source, "owner/demo", pin)

    def wrong_ownership(body):
        proof = re.search(r"<!-- kb:depth-proof (.*?) -->", body, re.S)
        data = json.loads(proof[1])
        data["trace"][1].update(start=3, end=3)
        return body.replace(proof[1], json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    legacy = _replace_block_body(valid, wrong_ownership)
    world.old += "\n" + legacy + "\n"
    _write(world.root, "knowledge/" + depth_page(world.policy.features[0]), world.old)
    world.campaign.update(pin=pin, baseline=_commit(world.root))
    (world.state / "campaign.json").write_text(json.dumps(world.campaign))
    for worker, record in enumerate(world.records):
        record.update(pin=pin, kb_base_sha=world.campaign["baseline"])
        feature = world.policy.features[worker]
        page = depth_page(feature)
        candidate = repin(record["depth"]["accepted"][page])
        if worker == 0:
            candidate += "\n" + legacy + "\n"
        record["depth"]["accepted"][page] = candidate
        record["depth"]["features"][feature.id]["accepted_sha256"] = digest(candidate)
        for facet, row in record["verdicts"]["depth:" + feature.id]["facets"].items():
            row["block_sha256"] = digest(world.blocks[(feature.id, facet)])
        _save(world, worker)
    archive = _archive(world, legacy)
    report = world.state / "retirement.json"
    report.write_text(json.dumps(archive))
    return SimpleNamespace(world=world, archive=archive, report=report, block=legacy, valid_replacement=valid)


def test_archived_invalid_retirement_preserves_other_blocks_and_raw_checkpoint_hash(assembler, retired_world):
    w, archive = retired_world.world, retired_world.archive
    page = depth_page(w.policy.features[0])
    accepted = w.records[0]["depth"]["accepted"][page]
    with pytest.raises(ValueError, match="source proof"):
        assembler.assemble(w.root, w.state, w.source)
    report, writes = assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])
    assert retired_world.block not in writes[page]
    assert w.blocks[("f0", "api")] in writes[page] and w.blocks[("f0", "configuration")] in writes[page]
    assert assembler._body(writes[page]).startswith(assembler._body(w.old.replace(retired_world.block, "")))
    assert report["pages"][0]["checkpoint_accepted_sha256"] == digest(accepted)
    assert report["original_baseline_facets"] == 2 and report["baseline_facets"] == 1
    assert report["new_receipt_bound_facets"] == 2 and report["source_verified_facets"] == 3
    assert report["denominator"] == 14 and report["facet_counts"]["flow"] == 0
    assert report["retired_facets"][0]["status"] == "unknown_pending_replacement"
    assert report["retired_facets"][0]["block_sha256"] == archive["raw_block_sha256"]
    assert report["native_archive_audit_required"] and "raw_block" not in report["retired_facets"][0]
    for target, text in writes.items():
        _write(w.root, "knowledge/" + target, text)
    assert not assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])[1]


def test_retirement_proposes_filtered_baseline_without_an_accepted_worker_page(assembler, retired_world):
    w = retired_world.world
    w.records[0]["depth"]["accepted"] = {}
    w.records[0]["verdicts"] = {}
    _save(w)
    page = depth_page(w.policy.features[0])
    report, writes = assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])
    assert writes[page] == w.old.replace(retired_world.block, "")
    assert report["source_verified_facets"] == 2 and report["facet_counts"]["flow"] == 0
    # Root may have already retired the exact archived bytes before salvage.
    _write(w.root, "knowledge/" + page, writes[page])
    assert page not in assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])[1]


def test_retiring_a_features_only_block_leaves_it_unknown_in_full_denominator(assembler, retired_world):
    w = retired_world.world
    page = depth_page(w.policy.features[0])
    w.old = w.old.replace(w.blocks[("f0", "api")], "")
    _write(w.root, "knowledge/" + page, w.old)
    w.campaign["baseline"] = _commit(w.root)
    (w.state / "campaign.json").write_text(json.dumps(w.campaign))
    for worker, record in enumerate(w.records):
        record["kb_base_sha"] = w.campaign["baseline"]
        if worker == 0:
            record["depth"]["accepted"] = {}
            record["verdicts"] = {}
        _save(w, worker)
    retired_world.report.write_text(json.dumps(_archive(w, retired_world.block)))
    report, writes = assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])
    assert retired_world.block not in writes[page]
    assert report["baseline_facets"] == 0 and report["source_verified_facets"] == 1
    assert report["recognized_feature_count"] == 1 and not report["all_features_recognized"]
    assert report["denominator"] == 14 and not report["source_target_met"]


@pytest.mark.parametrize("field", ["pin", "historical_knowledge_base_sha", "original_page_sha256", "raw_block_sha256", "body_sha256", "page", "feature", "facet"])
def test_retirement_rejects_wrong_identity_or_hashes(assembler, retired_world, field):
    retired_world.archive[field] = "wrong"
    retired_world.report.write_text(json.dumps(retired_world.archive))
    w = retired_world.world
    with pytest.raises(ValueError, match="retirement archive"):
        assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])


def test_retirement_rejects_foreign_raw_bytes_even_with_recomputed_receipt_hash(assembler, retired_world):
    w = retired_world.world
    foreign = retired_world.block.replace("module helper result", "changed module helper result")
    foreign = _replace_block_body(foreign, lambda body: body)
    retired_world.archive = _archive(w, foreign)
    retired_world.report.write_text(json.dumps(retired_world.archive))
    with pytest.raises(ValueError, match="exact baseline"):
        assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])


@pytest.mark.parametrize("field,value", [
    ("block_sha256", "0" * 64), ("pin", "0" * 40), ("native_trace_id", ""),
    ("native_reply_sha256", "invalid"), ("dimensions", {"faithful": "unsure"}),
])
def test_retirement_requires_exact_historical_native_receipt(assembler, retired_world, field, value):
    retired_world.archive["native_approval"][field] = value
    retired_world.report.write_text(json.dumps(retired_world.archive))
    w = retired_world.world
    with pytest.raises(ValueError, match="historical native approval"):
        assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])


@pytest.mark.parametrize("approved", [False, True])
def test_retired_facet_replacement_needs_its_own_current_successful_receipt(assembler, retired_world, approved):
    w = retired_world.world
    block = retired_world.valid_replacement
    _candidate(w, lambda text: text.replace(retired_world.block, block))
    if approved:
        result = {"verdict": "pass", "reason": "The module helper is bound to its own definition.",
                  "dimensions": {d: "yes" for d in ("faithful", "non_contradictory", "does_not_weaken")}}
        call = {"facets": {"flow": result}, "model": "codex:gpt-5.4", "native_trace_id": "replacement-flow-call",
                "native_reply_sha256": "b" * 64}
        prior = w.records[0]["verdicts"]["depth:f0"]
        prior["facets"]["flow"] = {**result, **{k: call[k] for k in ("model", "native_trace_id", "native_reply_sha256")},
                                     "block_sha256": digest(block)}
        prior["calls"].append(call)
        _save(w)
        report, writes = assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])
        page = depth_page(w.policy.features[0])
        assert block in writes[page] and retired_world.block not in writes[page]
        assert report["new_receipt_bound_facets"] == 3 and report["source_verified_facets"] == 4
        assert report["facet_counts"]["flow"] == 1 and report["denominator"] == 14
        assert any(row["facet"] == "flow" and row["native_trace_id"] == "replacement-flow-call"
                   for row in report["receipts"])
    else:
        with pytest.raises(ValueError, match="exact successful receipt"):
            assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])


def test_currently_valid_block_cannot_be_retired(assembler, world):
    archive = world.state / "valid-retirement.json"
    archive.write_text(json.dumps(_archive(world, world.blocks[("f0", "api")])))
    with pytest.raises(ValueError, match="fail current pinned proof"):
        assembler.assemble(world.root, world.state, world.source, retirement_reports=[archive])


def test_retirement_does_not_allow_editing_another_baseline_block(assembler, retired_world):
    w = retired_world.world
    _candidate(w, lambda text: text.replace(w.blocks[("f0", "api")], ""))
    with pytest.raises(ValueError, match="existing depth block"):
        assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])


def test_duplicate_archive_or_duplicate_retired_candidate_is_rejected(assembler, retired_world):
    w = retired_world.world
    with pytest.raises(ValueError, match="duplicate retired"):
        assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report] * 2)
    _candidate(w, lambda text: text + retired_world.block + "\n")
    with pytest.raises(ValueError, match="duplicate archived"):
        assembler.assemble(w.root, w.state, w.source, retirement_reports=[retired_world.report])


def test_retirement_cli_default_remains_read_only(assembler, retired_world, monkeypatch, capsys):
    w = retired_world.world
    before = {p: p.read_bytes() for p in (w.root / "knowledge").rglob("*.md")}
    report = w.state / "assembly-retirement-report.json"
    monkeypatch.setattr(sys, "argv", ["assemble", "--root", str(w.root), "--state", str(w.state),
        "--source-tree", str(w.source), "--retirement-report", str(retired_world.report), "--report", str(report)])
    assert assembler.main() == 0
    assert {p: p.read_bytes() for p in (w.root / "knowledge").rglob("*.md")} == before
    assert json.loads(report.read_text())["retired_facets"][0]["facet"] == "flow"
    assert '"applied": false' in capsys.readouterr().out
