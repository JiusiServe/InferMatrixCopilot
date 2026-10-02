"""Offline campaign checks: no generator, judge or external process is started."""

import argparse
import fcntl
import importlib.util
import json
import signal
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.init_support import InitRecord, InitRuntime
from infermatrix_copilot.kb_service.sources import KnowledgeRepo


@pytest.fixture
def runner():
    path = Path(__file__).resolve().parents[1] / "eval/knowledge-depth/run_depth_campaign.py"
    spec = importlib.util.spec_from_file_location("offline_depth_campaign", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def campaign_args(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "--quiet", "-b", "main")
    _git(root, "config", "user.name", "Offline test")
    _git(root, "config", "user.email", "offline@example.invalid")
    adapter = root / "adapters/demo"
    adapter.mkdir(parents=True)
    (adapter / "manifest.yaml").write_text(yaml.safe_dump({"knowledge": {"repo_subdir": "repos/demo"}}))
    features = [{"id": f"f{i}", "title": f"Feature {i}", "owner": "core", "source_globs": ["src/core.py"],
                 "docs": ["docs/guide.md"], "page": f"repos/demo/components/core/feature-f{i}.md"}
                for i in range(79)]
    policy = {"schema_version": 1, "core": {"roots": ["src/"], "exclude": ["*/tests/*"]},
              "semantic_depth": {"per_facet_gt": 0.90}, "features": features}
    (adapter / "knowledge-coverage.yaml").write_text(yaml.safe_dump(policy))
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "Temporary campaign fixture")
    baseline = _git(root, "rev-parse", "HEAD")
    state = tmp_path / "campaign"
    state.mkdir()
    return SimpleNamespace(root=root, state=state, repo="demo", pin=baseline, baseline=baseline,
                           upstream_mirror=root / ".git", workers=2, retry=False,
                           worker=0, feature_ids="f0")


def _offline_processes(runner, monkeypatch, codes=(0, 0), fail_after=None, term_race=False):
    processes, signals = [], []

    class Child:
        def __init__(self, code, log):
            self.returncode, self.log = code, log
            self.pid = 100_000 + len(processes)
            self.waited = False

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.waited = True
            if self.returncode is None:
                self.returncode = -signal.SIGTERM
            return self.returncode

    def spawn(argv, **kwargs):
        assert kwargs["start_new_session"]
        if fail_after is not None and len(processes) == fail_after:
            raise OSError("offline spawn failure")
        process = Child(codes[len(processes)], kwargs["stdout"])
        processes.append(process)
        return process

    def kill_group(pid, sig):
        signals.append((pid, sig))
        if term_race:
            raise ProcessLookupError("worker finished before termination")

    # Replacing this module's facade leaves real local Git subprocesses usable.
    monkeypatch.setattr(runner, "subprocess", SimpleNamespace(
        run=subprocess.run, check_output=subprocess.check_output, Popen=spawn,
        STDOUT=subprocess.STDOUT, DEVNULL=subprocess.DEVNULL, TimeoutExpired=subprocess.TimeoutExpired))
    monkeypatch.setattr(runner.os, "killpg", kill_group)
    return processes, signals


def test_parent_lock_rejects_duplicate_campaign_before_dispatch(runner, campaign_args, monkeypatch, capsys):
    args = campaign_args
    monkeypatch.setattr(runner, "campaign", lambda *_: pytest.fail("duplicate campaign was dispatched"))
    monkeypatch.setattr(sys, "argv", ["campaign", "--root", str(args.root), "--state", str(args.state),
                                    "--repo", args.repo, "--pin", args.pin, "--baseline", args.baseline,
                                    "--upstream-mirror", str(args.upstream_mirror)])
    with (args.state / ".campaign.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit) as error:
            runner.main()
    assert error.value.code == 2
    assert "already running" in capsys.readouterr().err


def test_worker_lock_blocks_duplicate_after_supervisor_is_gone(runner, campaign_args, monkeypatch):
    state = campaign_args.state / "worker-0"
    state.mkdir()
    calls = []
    monkeypatch.setattr(runner, "run_worker", lambda *_: calls.append("run") or 0)
    with (state / ".worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            runner.worker(campaign_args)
    assert not calls
    assert runner.worker(campaign_args) == 0 and calls == ["run"]


def test_partitions_preserve_global_denominator_and_are_disjoint(runner, campaign_args, monkeypatch):
    processes, _ = _offline_processes(runner, monkeypatch)
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    summary = json.loads((campaign_args.state / "campaign.json").read_text())
    groups = [set(group) for group in summary["partitions"].values()]
    assert summary["features"] == 79 and summary["denominator"] == 553
    assert len(set.union(*groups)) == 79 and not set.intersection(*groups)
    assert all(child.waited and child.log.closed for child in processes)


@pytest.mark.parametrize("key", ["baseline", "pin", "repo", "workers", "partitions"])
def test_changed_campaign_identity_fails_before_spawning(runner, campaign_args, monkeypatch, key):
    _offline_processes(runner, monkeypatch)
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    path = campaign_args.state / "campaign.json"
    previous = json.loads(path.read_text())
    previous[key] = "different"
    path.write_text(json.dumps(previous))
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_a, **_k: pytest.fail("changed campaign started a worker"))
    with pytest.raises(SystemExit) as error:
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert error.value.code == 2
    assert json.loads(path.read_text()) == previous


def test_reused_worker_clone_cannot_switch_remote(runner, campaign_args, monkeypatch):
    _offline_processes(runner, monkeypatch)
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    clone = campaign_args.state / "worker-0/init/knowledge-repo"
    _git(clone, "remote", "set-url", "origin", str(campaign_args.root))
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_a, **_k: pytest.fail("foreign clone dispatched a worker"))
    with pytest.raises(SystemExit) as error:
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert error.value.code == 2


@pytest.mark.parametrize("mismatch", ["fetch", "checkpoint_base", "checkpoint_pin"])
def test_worker_rejects_baseline_or_source_mismatch_before_runtime(runner, campaign_args, monkeypatch, mismatch):
    args = campaign_args
    state = args.state / "worker-0"
    fetched = "b" * 40 if mismatch == "fetch" else args.baseline
    monkeypatch.setattr(KnowledgeRepo, "fetch", lambda _: fetched)
    monkeypatch.setattr(InitRuntime, "from_env", lambda *_a, **_k: pytest.fail("mismatch initialized native runtime"))
    if mismatch != "fetch":
        InitRecord(stage="knowledge-deepen", repo=args.repo,
                   kb_base_sha="b" * 40 if mismatch == "checkpoint_base" else args.baseline,
                   pin="b" * 40 if mismatch == "checkpoint_pin" else args.pin).save(state)
    with pytest.raises(RuntimeError, match="baseline differs"):
        runner.run_worker(args, state)


def test_signaled_worker_is_failure_and_its_group_is_cleaned(runner, campaign_args, monkeypatch):
    processes, signals = _offline_processes(runner, monkeypatch, codes=(-signal.SIGTERM, 0))
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 1
    assert (processes[0].pid, signal.SIGTERM) in signals
    assert all(child.waited and child.log.closed for child in processes)


@pytest.mark.parametrize("term_race", [False, True])
def test_spawn_failure_stops_and_reaps_prior_children(runner, campaign_args, monkeypatch, term_race):
    processes, signals = _offline_processes(runner, monkeypatch, codes=(None,), fail_after=1, term_race=term_race)
    with pytest.raises(OSError, match="offline spawn failure"):
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert signals == [(processes[0].pid, signal.SIGTERM)]
    assert processes[0].waited and processes[0].log.closed


def test_exit_during_termination_does_not_skip_other_cleanup(runner, campaign_args, monkeypatch):
    processes, signals = _offline_processes(runner, monkeypatch, term_race=True)
    assert runner.campaign(campaign_args, argparse.ArgumentParser()) == 0
    assert len(signals) == len(processes) == 2
    assert all(child.waited and child.log.closed for child in processes)


def test_mutable_source_reference_is_rejected_before_spawning(runner, campaign_args, monkeypatch):
    campaign_args.pin = "main"
    processes, _ = _offline_processes(runner, monkeypatch)
    with pytest.raises(SystemExit) as error:
        runner.campaign(campaign_args, argparse.ArgumentParser())
    assert error.value.code == 2 and not processes
