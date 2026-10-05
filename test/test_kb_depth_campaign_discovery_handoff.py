"""Real prerequisite handoff uses original bytes and the native merged gate."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.init_support import InitPublisher, InitRecord, InitRuntime
from infermatrix_copilot.kb_service.sources import KnowledgeRepo
from test_kb_depth_campaign import campaign_args, runner, _git, _offline_processes  # noqa: F401


def _frozen_discovery(args, *, status="empty", adapter="demo"):
    """An original completed record plus its real committed catalog/report."""
    if adapter != "demo":
        (args.root / "adapters/demo").rename(args.root / "adapters" / adapter)
    policy_path = args.root / "adapters" / adapter / "knowledge-coverage.yaml"
    policy = policy_path.read_text()
    features = yaml.safe_load(policy)["features"]
    report_path = f"eval/feature-discovery/{args.repo}-{args.pin[:12]}.json"
    report = {"schema_version": 1, "repo": args.repo, "pin": args.pin, "complete": True, "done": True,
              "feature_ids": [row["id"] for row in features], "owner_requests": [],
              "features": [{key: row[key] for key in ("id", "title", "owner")} for row in features],
              "catalog_sha256": hashlib.sha256(policy.encode()).hexdigest()}
    target = args.root / report_path
    target.parent.mkdir(parents=True)
    report_text = json.dumps(report, indent=2) + "\n"
    target.write_text(report_text)
    routes = args.root / "knowledge/repos/demo/_routes.yaml"
    routes.parent.mkdir(parents=True)
    routes.write_text(yaml.safe_dump({"schema_version": 1, "owners": [
        {"owner": "core", "path": "repos/demo/components/core/_index.md", "prefixes": ["src/"]}]}))
    old_baseline = args.baseline
    _git(args.root, "add", ".")
    _git(args.root, "commit", "--quiet", "-m", "Freeze discovered feature catalog")
    args.baseline = _git(args.root, "rev-parse", "HEAD")
    record = InitRecord(stage="feature-discovery", repo=args.repo, pin=args.pin, kb_base_sha=old_baseline,
                        status=status, dry_run=status != "published", pr={"number": 42} if status == "published" else {},
                        notes=["native traces remain /outside/git/archive"], discovery={
                            "done": True, "report_path": report_path, "catalog_sha256": report["catalog_sha256"],
                            "report_sha256": hashlib.sha256(report_text.encode()).hexdigest()})
    args.discovery_record = args.state.parent / "original-feature-discovery.json"
    raw = json.dumps(asdict(record), ensure_ascii=False, indent=3).encode() + b"\n"
    args.discovery_record.write_bytes(raw)
    return raw


def test_campaign_copies_exact_prerequisite_and_binds_every_worker(runner, campaign_args, monkeypatch):
    args = campaign_args
    raw = _frozen_discovery(args)
    processes, _ = _offline_processes(runner, monkeypatch)
    assert runner.campaign(args, argparse.ArgumentParser()) == 0
    summary = json.loads((args.state / "campaign.json").read_bytes())
    binding = summary["discovery"]
    assert binding["record_sha256"] == hashlib.sha256(raw).hexdigest()
    assert binding["pin"] == args.pin and summary["denominator"] == 553
    assert len(processes) == 2
    for number in range(args.workers):
        copied = InitRecord.path(args.state / f"worker-{number}", args.repo, "feature-discovery")
        assert copied.read_bytes() == raw
        assert b"/outside/git/archive" in copied.read_bytes()


def test_aliased_adapter_is_resolved_from_baseline(runner, campaign_args):
    _frozen_discovery(campaign_args, adapter="demo_package")
    assert runner.baseline_inputs(campaign_args)[2] == "adapters/demo_package/knowledge-coverage.yaml"
    assert runner.discovery_handoff(campaign_args)["pin"] == campaign_args.pin


def test_catalog_report_requires_explicit_handoff_before_dispatch(runner, campaign_args, monkeypatch):
    _frozen_discovery(campaign_args)
    campaign_args.discovery_record = None
    processes, _ = _offline_processes(runner, monkeypatch)
    with pytest.raises(SystemExit) as error:
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert error.value.code == 2 and not processes
    assert not (campaign_args.state / "campaign.json").exists()


def test_missing_original_record_blocks_before_dispatch(runner, campaign_args, monkeypatch):
    _frozen_discovery(campaign_args)
    campaign_args.discovery_record.unlink()
    processes, _ = _offline_processes(runner, monkeypatch)
    with pytest.raises(SystemExit):
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert not processes


def test_committed_policy_change_cannot_reuse_record(runner, campaign_args):
    _frozen_discovery(campaign_args)
    policy = campaign_args.root / "adapters/demo/knowledge-coverage.yaml"
    policy.write_text(policy.read_text() + "# changed after discovery\n")
    _git(campaign_args.root, "add", ".")
    _git(campaign_args.root, "commit", "--quiet", "-m", "Change frozen catalog")
    campaign_args.baseline = _git(campaign_args.root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="catalog hash differs"):
        runner.discovery_handoff(campaign_args)


@pytest.mark.parametrize("field,value", [
    ("stage", "modules"), ("repo", "other"), ("pin", "b" * 40),
    ("status", "dry_run"), ("discovery.done", False),
    ("discovery.catalog_sha256", "b" * 64), ("discovery.report_sha256", "b" * 64),
])
def test_invalid_record_is_rejected_before_model_runtime(runner, campaign_args, monkeypatch, field, value):
    _frozen_discovery(campaign_args)
    path = campaign_args.discovery_record
    data = json.loads(path.read_bytes())
    if "." in field:
        parent, key = field.split(".")
        data[parent][key] = value
    else:
        data[field] = value
    path.write_text(json.dumps(data))
    monkeypatch.setattr(InitRuntime, "from_env", lambda *_a, **_k: pytest.fail("invalid handoff started models"))
    with pytest.raises(ValueError, match="handoff"):
        runner.discovery_handoff(campaign_args)


@pytest.mark.parametrize("merged", [False, True])
def test_published_record_requires_actual_merged_pr(runner, campaign_args, monkeypatch, merged):
    _frozen_discovery(campaign_args, status="published")
    checked = []
    monkeypatch.setattr(InitPublisher, "pr_state", lambda self, number: checked.append(number) or ("MERGED" if merged else "OPEN"))
    if merged:
        assert runner.discovery_handoff(campaign_args)["pin"] == campaign_args.pin
    else:
        with pytest.raises(ValueError, match="merge the feature-discovery PR"):
            runner.discovery_handoff(campaign_args)
    assert checked == [42]


def test_changed_original_record_cannot_resume_campaign(runner, campaign_args, monkeypatch):
    raw = _frozen_discovery(campaign_args)
    _offline_processes(runner, monkeypatch)
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    data = json.loads(raw)
    data["notes"].append("changed after dispatch")
    campaign_args.discovery_record.write_text(json.dumps(data))
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_a, **_k: pytest.fail("changed record dispatched"))
    with pytest.raises(SystemExit) as error:
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert error.value.code == 2
    assert InitRecord.path(campaign_args.state / "worker-0", campaign_args.repo, "feature-discovery").read_bytes() == raw


def test_worker_record_cannot_be_overwritten(runner, campaign_args):
    raw = _frozen_discovery(campaign_args)
    binding = runner.discovery_handoff(campaign_args)
    state = campaign_args.state / "worker-0"
    runner.install_discovery_handoff(campaign_args, state, binding)
    path = InitRecord.path(state, campaign_args.repo, "feature-discovery")
    path.write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="worker discovery prerequisite differs"):
        runner.install_discovery_handoff(campaign_args, state, binding)
    assert path.read_bytes() == raw + b" "


@pytest.mark.parametrize("mismatch", ["hash", "metadata"])
def test_worker_rechecks_hash_and_parent_binding_before_models(runner, campaign_args, monkeypatch, mismatch):
    raw = _frozen_discovery(campaign_args)
    campaign_args.discovery_record_sha256 = "b" * 64 if mismatch == "hash" else hashlib.sha256(raw).hexdigest()
    (campaign_args.state / "campaign.json").write_text(json.dumps({"discovery": {}}))
    monkeypatch.setattr(KnowledgeRepo, "fetch", lambda _: campaign_args.baseline)
    monkeypatch.setattr(InitRuntime, "from_env", lambda *_a, **_k: pytest.fail("unbound worker started runtime"))
    with pytest.raises((ValueError, RuntimeError), match="binding|identity"):
        runner.run_worker(campaign_args, campaign_args.state / "worker-0")


def test_genuine_worker_dispatch_reuses_original_record(runner, campaign_args, monkeypatch):
    from infermatrix_copilot.kb_service import init_stages

    args = campaign_args
    raw = _frozen_discovery(args)
    binding = runner.discovery_handoff(args)
    args.discovery_record_sha256 = binding["record_sha256"]
    (args.state / "campaign.json").write_text(json.dumps({"discovery": binding}))
    monkeypatch.setattr(KnowledgeRepo, "fetch", lambda _: args.baseline)
    state = args.state / "worker-0"
    runtime = SimpleNamespace(registry={args.repo: object()}, gateway=SimpleNamespace(configure_zcode_pacing=lambda _: None))

    def get_runtime(*_a, **_k):
        assert InitRecord.path(state, args.repo, "feature-discovery").read_bytes() == raw
        return runtime

    def run_stage(*_a, **kwargs):
        assert kwargs["from_existing"] and kwargs["feature_ids"] == ("f0",)
        assert InitRecord.load(state, args.repo, "feature-discovery").status == "empty"
        return InitRecord(stage="knowledge-deepen", repo=args.repo, pin=args.pin, kb_base_sha=args.baseline, status="dry_run")

    monkeypatch.setattr(InitRuntime, "from_env", get_runtime)
    monkeypatch.setattr(init_stages, "run_stage", run_stage)
    assert runner.run_worker(args, state) == 0
    assert InitRecord.path(state, args.repo, "feature-discovery").read_bytes() == raw
