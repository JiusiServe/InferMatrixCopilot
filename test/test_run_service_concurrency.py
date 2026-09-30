"""The run service executes up to `STRICT_MAX_WORKERS` runs at once, never two
on the same checkout+PR, and its housekeeping never removes a tree a run is
about to use. Real threads, fake launches; all offline."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

import pytest

from infermatrix_copilot import idempotency as idem
from infermatrix_copilot import run_status as rs
from infermatrix_copilot.app.run_service import UNKEYED, RunQueue, RunService
from infermatrix_copilot.config import Settings

WAIT = 5.0


def _service(settings, workers: int) -> RunService:
    settings.strict_max_workers = workers
    return RunService(settings)


def _queue_run(core: RunService, run_id: str, *, pr, repo: str = "vllm-omni",
               repo_path: str = "") -> str:
    """A reserved-looking run: the persisted request is what the queue keys
    on, and the queued status is what a failed launch marks."""
    run_dir = core.run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    request = {"kind": "pr_review" if pr is not None else "issue_filter",
               "repo": repo, "pr": pr, "repo_path": repo_path}
    (run_dir / "request.json").write_text(json.dumps(request), encoding="utf-8")
    rs.init_queued(run_dir, run_id=run_id, owner_server_id=core.server_id,
                   owner_server_pid=core.pid)
    return run_id


class _Recorder:
    """A fake `_launch` that blocks each run until released and records how
    many ran at once, overall and per PR."""

    def __init__(self):
        self.lock = threading.Lock()
        self.running: dict[str, int] = {}
        self.started: list[str] = []
        self.peak = 0
        self.gates: dict[str, threading.Event] = {}
        self.started_event = threading.Condition(self.lock)

    def gate(self, run_id: str) -> threading.Event:
        with self.lock:
            return self.gates.setdefault(run_id, threading.Event())

    def launch(self, run_id: str, *, strict_compat: bool = False) -> None:
        with self.lock:
            self.running[run_id] = 1
            self.started.append(run_id)
            self.peak = max(self.peak, len(self.running))
            self.started_event.notify_all()
        try:
            assert self.gate(run_id).wait(WAIT), f"{run_id} never released"
        finally:
            with self.lock:
                self.running.pop(run_id, None)

    def wait_started(self, *run_ids: str) -> None:
        deadline = time.monotonic() + WAIT
        with self.lock:
            while not set(run_ids) <= set(self.started):
                left = deadline - time.monotonic()
                assert left > 0, f"not started: {set(run_ids) - set(self.started)}"
                self.started_event.wait(left)

    def release(self, run_id: str) -> None:
        self.gate(run_id).set()


def _wait_until(predicate, what: str) -> None:
    deadline = time.monotonic() + WAIT
    while not predicate():
        assert time.monotonic() < deadline, what
        time.sleep(0.01)


# ── configuration and handshake ───────────────────────────────────────────────
def test_default_is_one_worker_and_the_handshake_says_so(settings):
    core = RunService(settings)
    assert core.capabilities()["max_strict_workers"] == 1
    assert len(core._workers) == 1


def test_configured_workers_are_started_and_reported(settings):
    core = _service(settings, 4)
    assert core.capabilities()["max_strict_workers"] == 4
    assert len(core._workers) == 4
    assert all(worker.is_alive() for worker in core._workers)


@pytest.mark.parametrize("bad", [0, -1, 33])
def test_out_of_range_worker_counts_fail_at_startup(tmp_path, bad):
    with pytest.raises(ValueError, match="STRICT_MAX_WORKERS"):
        Settings(_env_file=None, run_root=tmp_path / "runs",
                 strict_max_workers=bad)


def test_worker_count_is_read_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("STRICT_MAX_WORKERS", "6")
    assert Settings(_env_file=None, run_root=tmp_path).strict_max_workers == 6


# ── parallelism ───────────────────────────────────────────────────────────────
def test_runs_on_different_prs_execute_concurrently(settings, monkeypatch):
    core = _service(settings, 3)
    rec = _Recorder()
    monkeypatch.setattr(core, "_launch", rec.launch)
    ids = [_queue_run(core, f"run-20260930-000000-00000{i}", pr=10 + i)
           for i in range(3)]
    for run_id in ids:
        core._q.put((run_id, True))

    rec.wait_started(*ids)  # all three in flight at once
    assert rec.peak == 3
    for run_id in ids:
        rec.release(run_id)
    _wait_until(lambda: not rec.running, "runs never finished")


def test_never_more_runs_than_workers(settings, monkeypatch):
    core = _service(settings, 2)
    rec = _Recorder()
    monkeypatch.setattr(core, "_launch", rec.launch)
    ids = [_queue_run(core, f"run-20260930-000001-00000{i}", pr=20 + i)
           for i in range(4)]
    for run_id in ids:
        core._q.put((run_id, True))

    rec.wait_started(ids[0], ids[1])
    time.sleep(0.2)  # give an over-eager third worker the chance to exist
    assert rec.peak == 2 and len(rec.started) == 2
    for run_id in ids:
        rec.release(run_id)
    _wait_until(lambda: len(rec.started) == 4 and not rec.running,
                "queued runs never drained")
    assert rec.peak == 2


def test_runs_on_the_same_pr_never_overlap(settings, monkeypatch):
    """They share the PR-time worktree, and a harness writes its tool-bridge
    config into that tree — overlapping would bind one run's agent to the
    other's tool scope."""
    core = _service(settings, 3)
    rec = _Recorder()
    monkeypatch.setattr(core, "_launch", rec.launch)
    first = _queue_run(core, "run-20260930-000002-000001", pr=7)
    second = _queue_run(core, "run-20260930-000002-000002", pr=7)
    other = _queue_run(core, "run-20260930-000002-000003", pr=8)
    for run_id in (first, second, other):
        core._q.put((run_id, True))

    # the busy PR does not stall the queue behind it
    rec.wait_started(first, other)
    time.sleep(0.2)
    assert second not in rec.started
    queued, busy = core._q.snapshot()
    assert queued == [second]

    rec.release(first)
    rec.wait_started(second)
    for run_id in (second, other):
        rec.release(run_id)
    _wait_until(lambda: not rec.running, "runs never finished")


def test_issue_tasks_on_one_checkout_serialize(settings, monkeypatch):
    """Issue tasks carry no PR and work in the live checkout itself."""
    core = _service(settings, 2)
    rec = _Recorder()
    monkeypatch.setattr(core, "_launch", rec.launch)
    a = _queue_run(core, "run-20260930-000003-000001", pr=None)
    b = _queue_run(core, "run-20260930-000003-000002", pr=None)
    for run_id in (a, b):
        core._q.put((run_id, False))

    rec.wait_started(a)
    time.sleep(0.2)
    assert b not in rec.started
    rec.release(a)
    rec.wait_started(b)
    rec.release(b)
    _wait_until(lambda: not rec.running, "runs never finished")


def test_conflict_key_is_the_checkout_plus_pr(settings, tmp_path):
    settings.repo_paths = {"vllm-omni": str(tmp_path / "clone")}
    core = RunService(settings)
    a = _queue_run(core, "run-20260930-000004-000001", pr=5)
    b = _queue_run(core, "run-20260930-000004-000002", pr=5,
                   repo_path=str(tmp_path / "clone" / "."))
    c = _queue_run(core, "run-20260930-000004-000003", pr=5,
                   repo_path=str(tmp_path / "other-clone"))
    # an explicit path naming the configured checkout is the same checkout
    assert core._conflict_key(a) == core._conflict_key(b)
    # the same PR number in a different clone is a different tree
    assert core._conflict_key(a) != core._conflict_key(c)
    # an unreadable request still gets a key, shared with its kind
    assert core._conflict_key("run-20260930-000004-999999") == UNKEYED


def test_a_malformed_request_still_enqueues_and_never_kills_a_worker(
        settings, monkeypatch):
    """A tampered `pr` (unhashable) must not raise inside `take()` — that would
    kill the worker holding the queue's condition."""
    core = _service(settings, 1)
    rec = _Recorder()
    monkeypatch.setattr(core, "_launch", rec.launch)
    bad = _queue_run(core, "run-20260930-000006-000001", pr=[1, 2])
    boom = "run-20260930-000006-000002"
    _queue_run(core, boom, pr=3)
    monkeypatch.setattr(core, "_conflict_key",
                        lambda run_id: (_ for _ in ()).throw(RuntimeError("x"))
                        if run_id == boom else RunService._conflict_key(core, run_id))
    core._q.put((bad, True))
    core._q.put((boom, True))    # the key function itself blew up
    rec.wait_started(bad)
    rec.release(bad)
    rec.wait_started(boom)       # enqueued under UNKEYED, still executed
    rec.release(boom)
    _wait_until(lambda: not rec.running and core._workers[0].is_alive(),
                "the worker died on a malformed request")


# ── failure isolation ─────────────────────────────────────────────────────────
def test_a_failed_launch_marks_the_run_and_frees_its_pr(settings, monkeypatch):
    core = _service(settings, 2)
    rec = _Recorder()
    boom = "run-20260930-000005-000001"
    after = "run-20260930-000005-000002"

    def launch(run_id, *, strict_compat=False):
        if run_id == boom:
            raise RuntimeError("spawn failed")
        rec.launch(run_id, strict_compat=strict_compat)

    monkeypatch.setattr(core, "_launch", launch)
    for run_id in (boom, after):
        _queue_run(core, run_id, pr=9)
        core._q.put((run_id, True))

    rec.wait_started(after)  # same PR: only possible once the key was freed
    status = rs.read_status(core.run_root / boom) or {}
    assert status.get("state") == rs.FAILED
    assert "spawn failed" in status.get("note", "")
    rec.release(after)
    _wait_until(lambda: all(w.is_alive() for w in core._workers) and not rec.running,
                "a worker died with its launch")


# ── the queue itself ──────────────────────────────────────────────────────────
def test_queue_hands_out_the_oldest_run_whose_key_is_free():
    keys = {"a1": "A", "a2": "A", "b1": "B"}
    q = RunQueue(keys.__getitem__)
    for run_id in ("a1", "a2", "b1"):
        q.put((run_id, False))
    assert q.take()[0] == "a1"
    assert q.take()[0] == "b1"   # a2 waits behind a1's key, b1 skips ahead
    got: list[str] = []
    waiter = threading.Thread(target=lambda: got.append(q.take()[0]))
    waiter.start()
    time.sleep(0.1)
    assert got == []             # a2's key is still busy
    q.done("A")
    waiter.join(WAIT)
    assert got == ["a2"]


# ── housekeeping vs live runs ─────────────────────────────────────────────────
def test_only_one_sweep_runs_at_a_time(settings, monkeypatch):
    core = RunService(settings)
    calls = []
    monkeypatch.setattr(idem, "reap_stale", lambda *a, **k: calls.append(1))
    with core._reap_lock:
        core._reap()          # another worker is already sweeping
    assert calls == []
    core._reap()
    assert calls == [1]


def _sha(repo: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()


def test_reusing_an_old_tree_keeps_the_reaper_off_it(settings, tmp_path,
                                                     git_repo):
    """A run takes its shared hold only when a later step first uses the tree,
    so reuse itself must mark the tree live."""
    from infermatrix_copilot.engine import worktrees as wt
    from infermatrix_copilot.engine.steps._common import git as _git

    root = tmp_path / "worktrees"
    sha = _sha(git_repo)
    dest = wt.dest_for(git_repo, 1, sha, root=root)
    assert wt.materialize(git_repo, sha, dest, _git)[0]
    os.utime(dest, (0, 0))    # older than any retention window

    ok, detail = wt.materialize(git_repo, sha, dest, _git)
    assert ok and detail.startswith("reused")
    idem.reap_stale(settings.run_root, worktree_root=root)
    assert dest.exists()


def test_reaper_rechecks_age_under_its_lock(settings, tmp_path, git_repo,
                                            monkeypatch):
    """A reuse can land between the reaper's unlocked age check and its
    exclusive lock; the removal decision is re-read under the lock."""
    from infermatrix_copilot.engine import worktrees as wt
    from infermatrix_copilot.engine.steps._common import git as _git

    root = tmp_path / "worktrees"
    sha = _sha(git_repo)
    dest = wt.dest_for(git_repo, 3, sha, root=root)
    assert wt.materialize(git_repo, sha, dest, _git)[0]
    os.utime(dest, (0, 0))

    real_flock = idem.fcntl.flock

    def flock(fd, flags):
        if flags & idem.fcntl.LOCK_EX:
            os.utime(dest)    # a run reused the tree just before this lock
        return real_flock(fd, flags)

    monkeypatch.setattr(idem.fcntl, "flock", flock)
    counts = idem.reap_stale(settings.run_root, worktree_root=root)
    assert dest.exists()
    assert counts["worktrees"] == 0


# ── the embedded SDK binding ──────────────────────────────────────────────────
def test_sdk_config_sets_the_worker_count_and_the_handshake_reports_it(
        tmp_path, monkeypatch):
    from infermatrix_copilot.sdk.v1 import (RepositoryRef, StrictRuntime,
                                            StrictRuntimeConfig)

    # an explicit config beats whatever the host environment says
    monkeypatch.setenv("STRICT_MAX_WORKERS", "1")
    config = StrictRuntimeConfig(
        repository=RepositoryRef("demo", "owner/demo"),
        checkout_path=str(tmp_path), allowed_root=str(tmp_path),
        run_root=str(tmp_path / "runs"), max_workers=5)
    with StrictRuntime(config=config) as runtime:
        assert runtime.capabilities().max_strict_workers == 5
        assert len(runtime._core._workers) == 5


@pytest.mark.parametrize("bad", [0, -2, True, "3"])
def test_sdk_config_refuses_a_bad_worker_count(tmp_path, bad):
    from infermatrix_copilot.sdk.v1 import (InvalidRequestError, RepositoryRef,
                                            StrictRuntimeConfig)

    with pytest.raises(InvalidRequestError, match="max_workers"):
        StrictRuntimeConfig(
            repository=RepositoryRef("demo", "owner/demo"),
            checkout_path=str(tmp_path), allowed_root=str(tmp_path),
            max_workers=bad)


# ── the checkout key goes through the execution path's resolver ──────────────
_ADAPTER_MANIFEST = """\
name: vllm_omni
status: active
repo:
  path: {repo_path}
  default_branch: main
push:
  default_remote: origin
  protected_branches: [main]
"""


def test_adapter_backed_checkout_keys_implicit_and_explicit_alike(
        settings, git_repo):
    """No REPO_PATHS entry: the adapter manifest supplies the checkout, and a
    request naming that checkout explicitly is the same tree."""
    adapter = settings.adapters_dir / "vllm_omni"
    adapter.mkdir(parents=True)
    (adapter / "manifest.yaml").write_text(
        _ADAPTER_MANIFEST.format(repo_path=git_repo))
    core = RunService(settings)
    implicit = _queue_run(core, "run-20260930-000007-000001", pr=11)
    explicit = _queue_run(core, "run-20260930-000007-000002", pr=11,
                          repo_path=str(git_repo))
    assert core._conflict_key(implicit) == core._conflict_key(explicit)
    assert core._conflict_key(implicit)[0] == str(git_repo.resolve())


# ── cursor sessions in a shared checkout ──────────────────────────────────────
_RECORDING_CLI = """#!/usr/bin/env python3
import json, os, sys, time, uuid
here = os.path.dirname(os.path.abspath(__file__))
sys.stdin.read()
start = time.time()
cfg = json.load(open(os.path.join(os.getcwd(), ".cursor", "mcp.json")))
spec = cfg["mcpServers"]["infermatrix-tools"]["args"][-1]
time.sleep(0.4)
cfg_after = json.load(open(os.path.join(os.getcwd(), ".cursor", "mcp.json")))
with open(os.path.join(here, "calls", uuid.uuid4().hex + ".json"), "w") as f:
    json.dump({"start": start, "end": time.time(), "spec": spec,
               "spec_after": cfg_after["mcpServers"]["infermatrix-tools"]["args"][-1]}, f)
print(json.dumps({"type": "result", "result": "OK " + spec}))
"""


def _recording_transport(tmp_path: Path):
    import stat

    from infermatrix_copilot.providers.cursor import CursorTransport

    cli = tmp_path / "bin" / "cursor-agent"
    (tmp_path / "bin" / "calls").mkdir(parents=True)
    cli.write_text(_RECORDING_CLI, encoding="utf-8")
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    return CursorTransport(Settings(_env_file=None, strict_backend="cursor",
                                    strict_backend_cli=str(cli)))


def _session(tmp_path: Path, cwd: Path, run: str, timeout_s: float = 30.0):
    from infermatrix_copilot.providers.base import AgentSessionRequest
    from infermatrix_copilot.scopes import read_only_scope
    from infermatrix_copilot.tool_bridge import write_bridge_spec

    run_dir = tmp_path / run
    run_dir.mkdir()
    base = read_only_scope()
    scope = type(base)(name=base.name, allowed_tools=base.allowed_tools,
                       read_only=True, root=str(cwd))
    bridge = write_bridge_spec(run_dir=run_dir, step_name="agent.answer",
                               scope=scope, repo="vllm-omni")
    return AgentSessionRequest(
        system="S", prompt="P", scope=scope, model="", max_iters=4,
        timeout_s=timeout_s, run_dir=run_dir, step_name="agent.answer",
        bridge_spec_path=bridge, trace=None), str(bridge)


def test_cursor_sessions_of_two_runs_in_one_checkout_never_overlap(
        tmp_path, git_repo):
    """The live checkout is where issue tasks and degraded PR runs work, and
    `.cursor/mcp.json` has one path per directory: overlapping sessions would
    each read the other run's tool-bridge spec."""
    transport = _recording_transport(tmp_path)
    requests = [_session(tmp_path, git_repo, f"run{i}") for i in range(3)]
    outcomes: list = [None] * 3

    def one(i):
        outcomes[i] = transport.run_session(requests[i][0])

    threads = [threading.Thread(target=one, args=(i,)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(WAIT * 4)

    calls = sorted((json.loads(p.read_text()) for p in
                    (tmp_path / "bin" / "calls").glob("*.json")),
                   key=lambda c: c["start"])
    assert len(calls) == 3
    for earlier, later in zip(calls, calls[1:]):
        assert earlier["end"] <= later["start"]      # strictly one at a time
    assert all(c["spec"] == c["spec_after"] for c in calls)
    assert sorted(c["spec"] for c in calls) == sorted(r[1] for r in requests)
    assert all(o.text.startswith("OK ") for o in outcomes)
    assert not (git_repo / ".cursor").exists()       # the tree is restored


def test_a_busy_checkout_times_out_loudly(tmp_path, git_repo):
    import fcntl

    from infermatrix_copilot.providers.cursor import _session_lock_path

    transport = _recording_transport(tmp_path)
    req, _ = _session(tmp_path, git_repo, "run0", timeout_s=0.0)
    req = type(req)(**{**req.__dict__, "trace": _Trace()})
    fd = os.open(str(_session_lock_path(git_repo)), os.O_RDWR | os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        # another run's session holds it for longer than we may wait
        import infermatrix_copilot.providers.cursor as cursor_mod

        real = cursor_mod._exclusive_cwd
        outcome = None
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(cursor_mod, "_exclusive_cwd",
                       lambda cwd, _t: real(cwd, 0.3))
            outcome = transport.run_session(req)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    assert outcome.text == "" and outcome.truncated
    assert "busy" in outcome.refusals[0]
    assert any(e["kind"] == "capability_gap" for e in req.trace.events)
    assert list((tmp_path / "bin" / "calls").glob("*.json")) == []


class _Trace:
    def __init__(self):
        self.events = []

    def record(self, kind, **fields):
        self.events.append({"kind": kind, **fields})


def test_only_shared_checkouts_are_locked(tmp_path, git_repo):
    from infermatrix_copilot.engine import worktrees as wt
    from infermatrix_copilot.providers.cursor import _session_lock_path

    # a managed PR-time tree is one PR head's, serialized by the run queue
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=git_repo,
                         capture_output=True, text=True).stdout.strip()
    managed = wt.dest_for(git_repo, 4, sha, root=tmp_path / "worktrees")
    assert wt.materialize(git_repo, sha, managed, _git_runner())[0]
    assert _session_lock_path(managed) is None
    # a run's own directory is nobody else's
    plain = tmp_path / "run-dir"
    plain.mkdir()
    assert _session_lock_path(plain) is None
    # a clone, and an unmanaged linked worktree, are shared checkouts
    assert _session_lock_path(git_repo) == git_repo / ".git" / "imx-cursor-session.lock"
    linked = tmp_path / "linked"
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(linked)],
                   cwd=git_repo, check=True)
    lock = _session_lock_path(linked)
    assert lock is not None and lock.parent.is_dir()
    assert not str(lock).startswith(str(linked) + os.sep)  # never in the tree


def _git_runner():
    from infermatrix_copilot.engine.steps._common import git as _git

    return _git
