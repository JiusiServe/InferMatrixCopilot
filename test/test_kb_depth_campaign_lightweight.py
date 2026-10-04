"""Offline checks for bounded parallel dispatch, shared inputs and draining."""

import argparse
import hashlib
import json
import os
import signal
import sys
from types import SimpleNamespace

import pytest

from test_kb_depth_campaign import runner, campaign_args, _offline_processes, _git
from infermatrix_copilot.kb_service.init_support import InitRecord, InitRuntime
from infermatrix_copilot.kb_service.sources import KnowledgeRepo
from infermatrix_copilot.trace_store import TraceStore


def test_default_thirteen_workers_and_explicit_fourteen_is_rejected(runner, campaign_args, monkeypatch):
    args = campaign_args
    argv = ["campaign", "--root", str(args.root), "--state", str(args.state), "--repo", args.repo,
            "--pin", args.pin, "--baseline", args.baseline, "--upstream-mirror", str(args.upstream_mirror)]
    seen = []
    monkeypatch.setattr(runner, "campaign", lambda received, _: seen.append(received) or 0)
    monkeypatch.setattr(sys, "argv", argv)
    assert runner.main() == 0
    assert seen[0].workers == 13 and seen[0].acceptance_mode == "lightweight"
    monkeypatch.setattr(sys, "argv", argv + ["--workers", "14"])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2 and len(seen) == 1


def test_thirteen_partitions_retain_full_policy_and_isolated_logs(runner, campaign_args, monkeypatch):
    campaign_args.workers = 13
    processes, _ = _offline_processes(runner, monkeypatch, codes=(0,) * 13)
    argv_seen = []
    spawn = runner.subprocess.Popen
    monkeypatch.setattr(runner.subprocess, "Popen", lambda argv, **kwargs: argv_seen.append(argv) or spawn(argv, **kwargs))
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    summary = json.loads((campaign_args.state / "campaign.json").read_text())
    flat = sum(summary["partitions"].values(), [])
    assert len(flat) == len(set(flat)) == 79 and summary["denominator"] == 553
    assert len(processes) == len({child.log.name for child in processes}) == 13
    assert all(argv[argv.index("--workers") + 1] == "13" for argv in argv_seen)
    assert all("--stop-file" in argv for argv in argv_seen)


def test_parent_builds_one_read_only_index_and_reuses_exact_snapshot(runner, campaign_args, monkeypatch):
    args = campaign_args
    (args.root / "src").mkdir()
    (args.root / "src/core.py").write_text("def entry(value=17):\n    return value\n")
    _git(args.root, "add", ".")
    _git(args.root, "commit", "--quiet", "-m", "Tracked production fixture")
    args.pin = args.baseline = _git(args.root, "rev-parse", "HEAD")
    args.acceptance_mode = "lightweight"
    _offline_processes(runner, monkeypatch)
    argv_seen = []
    spawn = runner.subprocess.Popen
    monkeypatch.setattr(runner.subprocess, "Popen", lambda argv, **kwargs: argv_seen.append(argv) or spawn(argv, **kwargs))
    assert runner.campaign(args, argparse.ArgumentParser()) == 0
    cache = args.state / "depth-index.json"
    index = json.loads(cache.read_text())
    summary = json.loads((args.state / "campaign.json").read_text())
    assert index["data"]["production"] == ["src/core.py"]
    assert summary["depth_index_sha256"] == index["sha256"]
    assert all(argv[argv.index("--depth-index-path") + 1] == str(cache) for argv in argv_seen)
    import infermatrix_copilot.kb_service.depth_index as owner
    monkeypatch.setattr(owner, "build_depth_index", lambda *_a, **_k: pytest.fail("rebuilt shared snapshot"))
    _offline_processes(runner, monkeypatch)
    assert runner.campaign(args, argparse.ArgumentParser()) == 0
    damaged = json.loads(cache.read_text())
    damaged["data"]["production"] = []
    cache.write_text(json.dumps(damaged))
    with pytest.raises(ValueError, match="content hash"):
        runner.campaign(args, argparse.ArgumentParser())


def test_worker_forwards_lightweight_index_and_stop_boundary(runner, campaign_args, monkeypatch):
    import infermatrix_copilot.kb_service.init_stages as owner
    args = campaign_args
    args.acceptance_mode = "lightweight"
    args.depth_index_path = args.state / "depth-index.json"
    args.stop_file = args.state / "STOP"
    monkeypatch.setattr(KnowledgeRepo, "fetch", lambda _: args.baseline)
    pacing = []
    runtime = SimpleNamespace(registry={args.repo: "lifecycle"}, gateway=SimpleNamespace(configure_zcode_pacing=pacing.append))
    monkeypatch.setattr(InitRuntime, "from_env", lambda *_a, **_k: runtime)
    seen = []
    monkeypatch.setenv("KB_DEPTH_REPAIR_GUIDANCE", "/stale/inherited-guidance.json")
    monkeypatch.setenv("KB_DEPTH_REPAIR_GUIDANCE_SHA256", "a" * 64)

    def run_stage(*_a, **kwargs):
        assert "KB_DEPTH_REPAIR_GUIDANCE" not in os.environ
        assert "KB_DEPTH_REPAIR_GUIDANCE_SHA256" not in os.environ
        seen.append(kwargs)
        return InitRecord(stage="knowledge-deepen", repo=args.repo, kb_base_sha=args.baseline, pin=args.pin, status="complete")

    monkeypatch.setattr(owner, "run_stage", run_stage)
    assert runner.run_worker(args, args.state / "worker-0") == 0
    assert seen[0]["acceptance_mode"] == "lightweight"
    assert seen[0]["depth_index_path"] == args.depth_index_path and seen[0]["stop_file"] == args.stop_file
    assert seen[0]["unlimited_subscription"] is True
    assert pacing[0].path == args.state / "zcode-pacing.json"
    assert pacing[0].config["start_interval_s"] == 15 and pacing[0].config["rate_cooldown_s"] == 90


def test_parent_binds_every_guided_child_to_its_captured_input_hash(runner, campaign_args, monkeypatch):
    args = campaign_args
    (args.root / "src").mkdir()
    (args.root / "src/core.py").write_text("def entry():\n    return 17\n")
    _git(args.root, "add", ".")
    _git(args.root, "commit", "--quiet", "-m", "Pinned repair evidence fixture")
    args.pin = args.baseline = _git(args.root, "rev-parse", "HEAD")
    args.acceptance_mode = "lightweight"
    args.repair_guidance = args.state / "guidance.json"
    policy = (args.root / "adapters/demo/knowledge-coverage.yaml").read_bytes()
    args.repair_guidance.write_text(json.dumps({
        "schema": "depth-repair-guidance-v1", "pin": args.pin, "baseline": args.baseline,
        "policy_sha256": hashlib.sha256(policy).hexdigest(),
        "rows": [{"feature": "f0", "facet": "flow",
                  "evidence": [{"path": "src/core.py", "start": 1, "end": 2}]}],
    }))
    expected_hash = hashlib.sha256(args.repair_guidance.read_bytes()).hexdigest()
    _offline_processes(runner, monkeypatch)
    seen = []
    spawn = runner.subprocess.Popen
    monkeypatch.setattr(runner.subprocess, "Popen", lambda argv, **kwargs: seen.append(argv) or spawn(argv, **kwargs))
    assert runner.campaign(args, argparse.ArgumentParser()) == 0
    assert seen and all(argv[argv.index("--repair-guidance-sha256") + 1] == expected_hash for argv in seen)
    assert all(argv[argv.index("--repair-guidance") + 1] == str(args.repair_guidance) for argv in seen)
    assert json.loads((args.state / "campaign.json").read_text())["repair_guidance_sha256"] == expected_hash

    # Removing the flag must not erase the existing campaign's input binding.
    original_metadata = (args.state / "campaign.json").read_bytes()
    args.repair_guidance = None
    resumed, _ = _offline_processes(runner, monkeypatch)
    with pytest.raises(SystemExit) as error:
        runner.campaign(args, argparse.ArgumentParser())
    assert error.value.code == 2 and not resumed
    assert (args.state / "campaign.json").read_bytes() == original_metadata


@pytest.mark.parametrize("supplied_hash", [None, "a" * 63, "Z" * 64])
def test_guided_worker_rejects_missing_or_malformed_parent_hash_before_dispatch(
    runner, campaign_args, monkeypatch, supplied_hash,
):
    args = campaign_args
    argv = ["campaign", "--root", str(args.root), "--state", str(args.state), "--repo", args.repo,
            "--pin", args.pin, "--baseline", args.baseline, "--upstream-mirror", str(args.upstream_mirror),
            "--worker", "0", "--feature-ids", "f0", "--repair-guidance", str(args.state / "guidance.json")]
    if supplied_hash is not None:
        argv += ["--repair-guidance-sha256", supplied_hash]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(runner, "worker", lambda *_: pytest.fail("invalid guided worker dispatched"))
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2


def test_existing_stop_file_prevents_new_workers_and_saves_drain_snapshot(runner, campaign_args, monkeypatch):
    processes, signals = _offline_processes(runner, monkeypatch)
    (campaign_args.state / "STOP").write_text("requested")
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    assert not processes and not signals
    report = json.loads((campaign_args.state / "drain.json").read_text())
    assert report["running_workers"] == []
    assert json.loads((campaign_args.state / "campaign.json").read_text())["drained"] is True


def test_supervisor_signal_drains_and_records_inflight_without_early_group_kill(runner, campaign_args, monkeypatch):
    processes, signals = _offline_processes(runner, monkeypatch, codes=(None, 0))
    archive = TraceStore(campaign_args.state / "worker-0/init/traces").begin_call({"provider": "zcode", "system": "s", "prompt": "p"})
    record = InitRecord(stage="knowledge-deepen", repo=campaign_args.repo, status="running")
    record.depth = {"features": {"f0": {"attempts": 1, "status": "extracting"}}, "accepted": {}}
    record.save(campaign_args.state / "worker-0")
    sleeps = []

    def sleep(_seconds):
        sleeps.append(_seconds)
        assert not signals  # native worker is still active; stop requests do not kill it
        if len(sleeps) == 1:
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        else:
            drain = json.loads((campaign_args.state / "drain.json").read_text())
            assert drain["inflight"][0]["id"] == archive.id and drain["progress"][0]["active"] == ["f0"]
            processes[0].returncode = 0

    monkeypatch.setattr(runner.time, "sleep", sleep)
    prior_handler = signal.getsignal(signal.SIGTERM)
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    assert len(sleeps) == 2 and sleeps[1] == 2
    assert signal.getsignal(signal.SIGTERM) is prior_handler
    assert all(child.waited and child.log.closed for child in processes)
