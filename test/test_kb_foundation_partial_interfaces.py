"""Offline interface checks; mocked handoff never claims a native approval."""

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service import cli, runner as playbooks
from infermatrix_copilot.kb_service.init_support import InitRecord, InitRuntime
from infermatrix_copilot.kb_service.sources import KnowledgeRepo
from test_kb_depth_campaign import runner, campaign_args, _offline_processes
from test_kb_depth_assembly import assembler, world, _commit, _candidate


@pytest.mark.parametrize("command", [["init", "demo", "--stage", "knowledge"], ["widen", "demo"]])
def test_partial_foundation_cli_forwards_only_explicit_mode(tmp_path, monkeypatch, command):
    seen = []
    monkeypatch.setattr(playbooks, "run_playbook", lambda *_a, **k: (
        seen.append(k["params"]) or SimpleNamespace(status="done"), tmp_path))
    assert cli.main(command + ["--foundation-mode", "partial", "--unlimited-subscription"]) == 0
    assert seen[0]["foundation_mode"] == "partial" and "foundation_record" not in seen[0]


def test_partial_depth_cli_forwards_original_record(tmp_path, monkeypatch):
    seen = []
    record = tmp_path / "published-knowledge.json"
    monkeypatch.setattr(playbooks, "run_playbook", lambda *_a, **k: (
        seen.append(k["params"]) or SimpleNamespace(status="done"), tmp_path))
    assert cli.main(["deepen", "demo", "--foundation-mode", "partial", "--foundation-record", str(record),
                     "--unlimited-subscription"]) == 0
    assert seen[0]["foundation_record"] == str(record)


@pytest.mark.parametrize("options", [
    ["--stage", "modules", "--foundation-mode", "partial", "--unlimited-subscription"],
    ["--stage", "knowledge", "--foundation-mode", "partial"],
    ["--stage", "knowledge", "--foundation-mode", "partial", "--foundation-record", "record.json", "--unlimited-subscription"],
    ["--stage", "knowledge-deepen", "--foundation-mode", "partial", "--unlimited-subscription"],
    ["--stage", "knowledge-deepen", "--foundation-record", "record.json", "--unlimited-subscription"],
])
def test_invalid_partial_cli_never_dispatches(monkeypatch, options):
    monkeypatch.setattr(playbooks, "run_playbook", lambda *_a, **_k: pytest.fail("invalid partial request dispatched"))
    assert cli.main(["init", "demo", *options]) == 2


def test_default_cli_does_not_add_foundation_options(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(playbooks, "run_playbook", lambda *_a, **k: (
        seen.append(k["params"]) or SimpleNamespace(status="done"), tmp_path))
    assert cli.main(["widen", "demo", "--unlimited-subscription"]) == 0
    assert not {"foundation_mode", "foundation_record"} & seen[0].keys()


def _stub_handoff(args, monkeypatch):
    from infermatrix_copilot.kb_service import foundation_publication
    record = args.state / "immutable-foundation.json"
    record.write_text("offline handoff fixture\n")
    binding = {"record_path": str(record.resolve()), "record_sha256": hashlib.sha256(record.read_bytes()).hexdigest(),
               "receipt_path": str(args.state / "receipt.json"), "receipt_sha256": "a" * 64}
    args.foundation_mode, args.foundation_record = "partial", record
    monkeypatch.setattr(foundation_publication, "foundation_handoff", lambda *_a, **_k: binding)
    return binding


def test_campaign_partial_binds_every_child_and_rejects_strict_resume(runner, campaign_args, monkeypatch):
    args = campaign_args
    binding = _stub_handoff(args, monkeypatch)
    _offline_processes(runner, monkeypatch)
    argv = []
    spawn = runner.subprocess.Popen
    monkeypatch.setattr(runner.subprocess, "Popen", lambda a, **k: argv.append(a) or spawn(a, **k))
    assert runner.campaign(args, argparse.ArgumentParser()) == 0
    metadata = json.loads((args.state / "campaign.json").read_text())
    assert metadata["foundation_mode"] == "partial" and metadata["foundation"] == binding
    assert metadata["denominator"] == 553 and metadata["features"] == 79
    for child in argv:
        assert child[child.index("--foundation-mode") + 1] == "partial"
        assert child[child.index("--foundation-record") + 1] == binding["record_path"]
        assert child[child.index("--foundation-record-sha256") + 1] == binding["record_sha256"]
    args.foundation_mode, args.foundation_record = "strict", None
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_a, **_k: pytest.fail("changed mode dispatched"))
    with pytest.raises(SystemExit):
        runner.campaign(args, argparse.ArgumentParser())


def test_worker_handoff_rejects_changed_record_before_runtime(runner, campaign_args, monkeypatch):
    args = campaign_args
    binding = _stub_handoff(args, monkeypatch)
    args.foundation_record_sha256 = "f" * 64
    monkeypatch.setattr(KnowledgeRepo, "fetch", lambda _: args.baseline)
    monkeypatch.setattr(InitRuntime, "from_env", lambda *_a, **_k: pytest.fail("tampered prerequisite started runtime"))
    with pytest.raises(ValueError, match="changed after campaign binding"):
        runner.run_worker(args, args.state / "worker-0")


def test_worker_partial_forwards_bound_record_without_changing_partition(runner, campaign_args, monkeypatch):
    from infermatrix_copilot.kb_service import init_stages
    args = campaign_args
    binding = _stub_handoff(args, monkeypatch)
    (args.state / "campaign.json").write_text(json.dumps({"foundation_mode": "partial", "foundation": binding}))
    monkeypatch.setattr(KnowledgeRepo, "fetch", lambda _: args.baseline)
    runtime = SimpleNamespace(registry={args.repo: object()}, gateway=SimpleNamespace(configure_zcode_pacing=lambda _: None))
    monkeypatch.setattr(InitRuntime, "from_env", lambda *_a, **_k: runtime)
    seen = []
    def run_stage(*_a, **k):
        seen.append(k)
        return InitRecord(stage="knowledge-deepen", repo=args.repo, pin=args.pin, kb_base_sha=args.baseline, status="partial")
    monkeypatch.setattr(init_stages, "run_stage", run_stage)
    assert runner.run_worker(args, args.state / "worker-0") == 0
    assert seen[0]["feature_ids"] == ("f0",) and seen[0]["foundation_mode"] == "partial"
    assert seen[0]["foundation_record_path"] == Path(binding["record_path"])


def test_partial_assembly_absent_overview_uses_owner_link_with_old_blocks_intact(assembler, world, monkeypatch):
    from infermatrix_copilot.kb_service import foundation_publication
    f1 = world.policy.features[1]
    (world.root / "knowledge" / f1.page).unlink()
    world.campaign["baseline"] = _commit(world.root)
    binding = {"record_path": str(world.state / "published-foundation.json"), "record_sha256": "c" * 64}
    world.campaign.update(foundation_mode="partial", foundation=binding)
    (world.state / "campaign.json").write_text(json.dumps(world.campaign))
    for record, path in zip(world.records, world.checkpoints):
        record["kb_base_sha"] = world.campaign["baseline"]
        record["depth"].update(foundation_mode="partial", foundation=binding)
        path.write_text(json.dumps(record))
    _candidate(world, lambda text: text.replace("[功能概览](feature-f1.md) · [owner 入口](_index.md)",
                                              "[owner 入口](_index.md)"), worker=1)
    monkeypatch.setattr(foundation_publication, "foundation_handoff", lambda *_a, **_k: binding)
    report, writes = assembler.assemble(world.root, world.state, world.source,
        foundation_mode="partial", foundation_record_path=Path(binding["record_path"]))
    assert report["foundation"] == binding and report["denominator"] == 14
    assert report["new_receipt_bound_facets"] == 2 and world.blocks[("f0", "api")] in next(
        text for page, text in writes.items() if page.endswith("feature-depth-f0.md"))
    newpage = next(text for page, text in writes.items() if page.endswith("feature-depth-f1.md"))
    assert "[owner 入口](_index.md)" in newpage and "[功能概览]" not in newpage
    with pytest.raises(ValueError, match="mode differs"):
        assembler.assemble(world.root, world.state, world.source)
