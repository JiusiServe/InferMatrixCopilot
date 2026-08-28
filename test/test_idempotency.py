"""One run, and one *execution*, per idempotency key — including across the
crash windows a reservation is exposed to. All offline."""

from __future__ import annotations

import json
import tempfile
import threading
from pathlib import Path

import pytest

from infermatrix_copilot import idempotency as idem
from infermatrix_copilot import run_status as rs
from infermatrix_copilot.cli.copilot import Copilot
from infermatrix_copilot.task_spec import TaskSpec

KEY = "attempt-abc123"


def _spec(pr: int = 7, **kw) -> TaskSpec:
    return TaskSpec(kind="pr_review", repo="vllm-omni", pr=pr, **kw)


def _reserve(cop: Copilot, spec: TaskSpec, key: str = KEY,
             owner: str = "S1", pid: int = 1234):
    return cop.reserve_run(spec, owner_server_id=owner, owner_server_pid=pid,
                           idempotency_key=key)


def _isolated_root(tmp: Path | None = None) -> Path:
    """A worktree root no real checkout lives under.

    `reap_stale` defaults to `~/.infermatrix-copilot/worktrees`, which is the
    developer's actual scratch directory; a test must never sweep it."""
    root = Path(tmp) if tmp is not None else Path(tempfile.mkdtemp())
    root.mkdir(parents=True, exist_ok=True)
    return root


# ── key validation ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bad", ["a b", "a/b", "../x", "x" * 129, "a;b"])
def test_key_charset_is_enforced(bad):
    with pytest.raises(idem.IdempotencyError):
        idem.validate_key(bad)


def test_absent_key_is_allowed_and_means_always_create(settings):
    cop = Copilot(settings)
    first, c1 = cop.reserve_run(_spec(), owner_server_id="S1",
                                owner_server_pid=1)
    second, c2 = cop.reserve_run(_spec(), owner_server_id="S1",
                                 owner_server_pid=1)
    assert first != second and c1 and c2


# ── dedupe ────────────────────────────────────────────────────────────────────
def test_same_key_returns_the_same_run_and_creates_once(settings):
    cop = Copilot(settings)
    first, created_first = _reserve(cop, _spec())
    second, created_second = _reserve(cop, _spec())
    assert first == second
    assert created_first is True and created_second is False


def test_same_key_still_dedupes_after_the_run_is_terminal(settings):
    """The whole point: a retry that lost the response must be handed the
    FINISHED run and its result, not a second review of the same commit."""
    cop = Copilot(settings)
    run_id, _ = _reserve(cop, _spec())
    rs.mark(Path(settings.run_root) / run_id, rs.DONE)
    again, created = _reserve(cop, _spec())
    assert again == run_id and created is False


def test_a_new_key_with_the_same_spec_starts_a_fresh_run(settings):
    """A deliberate new generation is not a retry, even byte-identical."""
    cop = Copilot(settings)
    first, _ = _reserve(cop, _spec(), key="attempt-gen1")
    second, created = _reserve(cop, _spec(), key="attempt-gen2")
    assert first != second and created is True


def test_a_known_key_with_a_different_spec_is_rejected(settings):
    """The index is a cache; the persisted request is the authority. Serving the
    old run would quietly review the wrong thing under a name the caller
    believes means something else."""
    cop = Copilot(settings)
    _reserve(cop, _spec(pr=7))
    with pytest.raises(idem.IdempotencyError, match="different request"):
        _reserve(cop, _spec(pr=8))


def test_specs_differing_only_in_review_depth_are_different(settings):
    cop = Copilot(settings)
    a, _ = _reserve(cop, _spec(params={"review_depth": "light"}), key="k-a")
    b, _ = _reserve(cop, _spec(params={"review_depth": "full"}), key="k-b")
    assert a != b
    with pytest.raises(idem.IdempotencyError):
        _reserve(cop, _spec(params={"review_depth": "full"}), key="k-a")


def test_fingerprint_covers_every_spec_field_automatically(settings):
    """Whole-dict, so a field added later cannot silently collapse two
    different requests onto one key."""
    base = _spec().model_dump()
    for field, value in [("expected_head_sha", "a" * 40), ("mode", "performance"),
                         ("pr", 9), ("repo", "other")]:
        changed = {**base, field: value}
        assert idem.spec_fingerprint(changed) != idem.spec_fingerprint(base)


def test_issue_tasks_are_not_collapsed_onto_one_key(settings):
    """`start()` never passes a key, precisely because `issue_answer` carries no
    PR and no head — a spec-derived key would make issue #1 resolve to #500."""
    cop = Copilot(settings)
    one, _ = cop.reserve_run(TaskSpec(kind="issue_answer", repo="vllm-omni",
                                      issue=1),
                             owner_server_id="S1", owner_server_pid=1)
    other, _ = cop.reserve_run(TaskSpec(kind="issue_answer", repo="vllm-omni",
                                        issue=500),
                               owner_server_id="S1", owner_server_pid=1)
    assert one != other


# ── concurrency: assert on LAUNCHES, not ids ──────────────────────────────────
def test_concurrent_same_key_reservations_create_exactly_one_run(settings):
    cop = Copilot(settings)
    results: list[tuple[str, bool]] = []
    barrier = threading.Barrier(8)

    def go():
        barrier.wait()
        results.append(_reserve(cop, _spec()))

    threads = [threading.Thread(target=go) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len({r for r, _ in results}) == 1
    # exactly one caller is told to enqueue: deduping the id alone would still
    # launch eight children
    assert sum(1 for _, created in results if created) == 1
    assert len(list(Path(settings.run_root).glob("run-*"))) == 1


def test_start_strict_enqueues_only_a_run_it_created(settings, monkeypatch):
    from infermatrix_copilot.mcp_server import CopilotMCP

    core = CopilotMCP(settings)
    try:
        enqueued: list = []
        monkeypatch.setattr(core._q, "put", enqueued.append)
        req = {"kind": "pr_review", "repo": "vllm-omni", "pr": 7,
               "idempotency_key": KEY}
        first = core.start_strict_review(dict(req))
        second = core.start_strict_review(dict(req))
        assert first == second
        assert len(enqueued) == 1
    finally:
        core.close()


# ── crash windows ─────────────────────────────────────────────────────────────
def test_crash_before_the_index_entry_leaves_a_fresh_run_for_the_retry(settings,
                                                                       monkeypatch):
    """Killed after the run dir exists but before the entry is published: the
    retry has no hit, so it opens a fresh run. The orphan reconciles to
    interrupted and is left in place — run directories are the audit trail and
    this feature does not prune them."""
    cop = Copilot(settings)
    boom = RuntimeError("server died")
    monkeypatch.setattr(idem, "write_entry",
                        lambda *a, **k: (_ for _ in ()).throw(boom))
    with pytest.raises(RuntimeError):
        _reserve(cop, _spec())
    monkeypatch.undo()

    run_id, created = _reserve(cop, _spec())
    assert created is True
    assert idem.read_entry(settings.run_root, KEY)["run_id"] == run_id


def test_crash_before_enqueue_makes_the_retry_relaunch_the_same_run(settings):
    """The window that silently hung: the entry is published, the server dies
    before `_q.put`, and a terminal-ignoring index would hand the retry a run
    nobody will ever execute."""
    cop = Copilot(settings)
    run_id, created = _reserve(cop, _spec())
    assert created is True
    run_dir = Path(settings.run_root) / run_id
    # what startup_reconcile does to a queued run whose owner is gone
    rs.mark(run_dir, rs.INTERRUPTED)
    assert idem.relaunchable(run_dir) and not idem.resolvable(run_dir)

    again, created_again = _reserve(cop, _spec(), owner="S2", pid=4321)
    assert again == run_id
    assert created_again is True  # the retry is told to launch it
    status = rs.read_status(run_dir)
    assert status["state"] == rs.QUEUED and status["child_pid"] is None
    assert status["owner_server_id"] == "S2"  # re-stamped to the live server


def test_two_retries_racing_a_never_launched_reservation_enqueue_once(settings):
    """The re-arm is what stops the second retry: it observes `queued` with a
    live owner rather than `interrupted`."""
    cop = Copilot(settings)
    run_id, _ = _reserve(cop, _spec())
    rs.mark(Path(settings.run_root) / run_id, rs.INTERRUPTED)

    results: list[tuple[str, bool]] = []
    barrier = threading.Barrier(4)

    def go():
        barrier.wait()
        results.append(_reserve(cop, _spec(), owner="S2", pid=4321))

    threads = [threading.Thread(target=go) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert {r for r, _ in results} == {run_id}
    assert sum(1 for _, created in results if created) == 1


def test_an_interrupted_run_that_did_start_is_not_relaunched(settings):
    """It did partial work, so it is a real outcome. A genuine second attempt is
    a new key, not a rewind."""
    cop = Copilot(settings)
    run_id, _ = _reserve(cop, _spec())
    run_dir = Path(settings.run_root) / run_id
    rs.mark_child_started(run_dir, child_pid=999)
    rs.mark(run_dir, rs.INTERRUPTED)
    assert not idem.relaunchable(run_dir) and idem.resolvable(run_dir)
    again, created = _reserve(cop, _spec())
    assert again == run_id and created is False


# ── the execution claim ───────────────────────────────────────────────────────
def test_claim_is_a_compare_and_set_not_a_write(tmp_path):
    run_dir = tmp_path / "run-20260828-101010-abc123"
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=1)
    assert rs.claim_for_execution(run_dir, child_pid=100) is True
    assert rs.claim_for_execution(run_dir, child_pid=100) is True  # idempotent
    assert rs.claim_for_execution(run_dir, child_pid=200) is False
    assert rs.read_status(run_dir)["child_pid"] == 100


def test_a_finished_run_cannot_be_claimed_again(tmp_path):
    """The serial-child window: A is spawned, the server dies before A records
    its pid, the reservation is reclaimed and B enqueued; A then runs to
    completion and releases the lock, and B finds it free. Only the state check
    catches that — `RunLock` never saw them overlap."""
    run_dir = tmp_path / "run-20260828-101010-abc124"
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=1)
    assert rs.claim_for_execution(run_dir, child_pid=100) is True   # child A
    rs.mark(run_dir, rs.DONE)
    assert rs.claim_for_execution(run_dir, child_pid=200) is False  # child B
    assert rs.read_status(run_dir)["state"] == rs.DONE


def test_reclaim_refuses_an_interrupted_run_that_had_a_child(tmp_path):
    run_dir = tmp_path / "run-20260828-101010-abc125"
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=1)
    rs.mark_child_started(run_dir, child_pid=100)
    rs.mark(run_dir, rs.INTERRUPTED)
    assert rs.reclaim_queued(run_dir, owner_server_id="S2",
                             owner_server_pid=2) is False
    assert rs.read_status(run_dir)["state"] == rs.INTERRUPTED


@pytest.mark.parametrize("state", [rs.DONE, rs.FAILED, rs.BLOCKED, rs.RUNNING])
def test_reclaim_never_rewinds_a_run_that_matters(tmp_path, state):
    run_dir = tmp_path / "run-20260828-101010-abc126"
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=1)
    rs.mark(run_dir, state)
    assert rs.reclaim_queued(run_dir, owner_server_id="S2",
                             owner_server_pid=2) is False
    assert rs.read_status(run_dir)["state"] == state


def test_execute_reserved_exits_without_running_when_already_claimed(settings):
    """A losing child must not plan, execute, or write status."""
    cop = Copilot(settings)
    run_id, _ = cop.reserve_run(_spec(), owner_server_id="S1",
                                owner_server_pid=1)
    run_dir = Path(settings.run_root) / run_id
    rs.mark_child_started(run_dir, child_pid=4242)
    rs.mark(run_dir, rs.DONE)

    assert cop.execute_reserved(run_id) == 0
    status = rs.read_status(run_dir)
    assert status["state"] == rs.DONE and status["child_pid"] == 4242
    assert not (run_dir / "task.json").exists()  # never planned


# ── retention ─────────────────────────────────────────────────────────────────
def test_reaper_drops_entries_whose_run_is_gone(settings):
    """A missing run dir is stale by definition: dropping the entry lets a later
    request with that key open a fresh run instead of resolving to a run that
    cannot be read."""
    cop = Copilot(settings)
    run_id, _ = _reserve(cop, _spec())
    import shutil

    shutil.rmtree(Path(settings.run_root) / run_id)
    counts = idem.reap_stale(settings.run_root, worktree_root=_isolated_root())
    assert counts["entries"] == 1
    assert idem.read_entry(settings.run_root, KEY) is None
    fresh, created = _reserve(cop, _spec())
    assert created is True and fresh != run_id


def test_reaper_never_touches_a_live_run(settings):
    cop = Copilot(settings)
    run_id, _ = _reserve(cop, _spec())
    rs.mark(Path(settings.run_root) / run_id, rs.RUNNING)
    idem.reap_stale(settings.run_root, retention_days=0,
                    worktree_root=_isolated_root())
    assert idem.read_entry(settings.run_root, KEY)["run_id"] == run_id


def test_reaper_drops_an_aged_out_terminal_entry(settings):
    cop = Copilot(settings)
    run_id, _ = _reserve(cop, _spec())
    rs.mark(Path(settings.run_root) / run_id, rs.DONE)
    path = idem._entry_path(settings.run_root, KEY)
    entry = json.loads(path.read_text())
    entry["created"] = 0.0  # long past any retention window
    path.write_text(json.dumps(entry))
    idem.reap_stale(settings.run_root, worktree_root=_isolated_root())
    assert idem.read_entry(settings.run_root, KEY) is None


def test_reaper_only_touches_worktrees_it_keys(settings, tmp_path, git_repo):
    """The worktrees root is shared scratch that has long held other tooling's
    checkouts under other naming schemes. A sweep that removed whatever it found
    there destroyed one before this guard existed."""
    import os
    import subprocess

    from infermatrix_copilot.engine import worktrees as wt
    from infermatrix_copilot.engine.steps._common import git as _git

    root = _isolated_root(tmp_path / "worktrees")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=git_repo,
                         capture_output=True, text=True).stdout.strip()
    ours = wt.dest_for(git_repo, 1, sha, root=root)
    assert wt.materialize(git_repo, sha, ours, _git)[0]
    # a foreign tree, named the way earlier tooling named them
    foreign = root / "vllm-omni-eval-pr4762"
    assert wt.materialize(git_repo, sha, foreign, _git)[0]
    for dest in (ours, foreign):
        os.utime(dest, (0, 0))

    assert wt.is_managed_dest(ours) and not wt.is_managed_dest(foreign)
    counts = idem.reap_stale(settings.run_root, worktree_root=root)
    assert not ours.exists()      # ours, aged out
    assert foreign.exists()       # never ours to remove
    assert counts["worktrees"] == 1


def test_reaper_leaves_a_held_worktree_and_removes_an_unheld_one(settings,
                                                                 tmp_path,
                                                                 git_repo):
    """Liveness is the tree's own shared lock, because `run_status.json` exists
    only for MCP-reserved runs — a registry-based sweep would delete the tree a
    CLI review is reading."""
    import os
    import subprocess

    from infermatrix_copilot.engine import worktrees as wt
    from infermatrix_copilot.engine.steps._common import git as _git

    root = tmp_path / "worktrees"
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=git_repo,
                         capture_output=True, text=True).stdout.strip()
    held = wt.dest_for(git_repo, 1, sha, root=root)
    free = wt.dest_for(git_repo, 2, sha, root=root)
    for dest in (held, free):
        assert wt.materialize(git_repo, sha, dest, _git)[0]
        os.utime(dest, (0, 0))  # older than any retention window

    fd = os.open(str(wt.lock_path(held)), os.O_RDWR | os.O_CREAT, 0o644)
    import fcntl as _fcntl

    _fcntl.flock(fd, _fcntl.LOCK_SH | _fcntl.LOCK_NB)
    try:
        counts = idem.reap_stale(settings.run_root, worktree_root=root)
    finally:
        _fcntl.flock(fd, _fcntl.LOCK_UN)
        os.close(fd)

    assert held.exists()          # a run is using it
    assert not free.exists()      # nothing is
    assert counts["worktrees"] == 1


def test_reaper_deletes_only_dead_runs_pinned_refs(settings, tmp_path):
    """Scoped to the run id, so a sweep can never unpin a live run's base or
    head — those refs are what hold both against a concurrent `git gc`."""
    import subprocess

    from infermatrix_copilot.engine.steps._common import git as _git

    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for cfg in (("user.email", "t@e.x"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(repo), "config", *cfg], check=True)
    (repo / "f").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "c"], check=True)
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()

    live = Path(settings.run_root) / "run-20260828-101010-aaaaaa"
    live.mkdir(parents=True)
    _git(repo, "update-ref", f"refs/imx/{live.name}/base", sha)
    _git(repo, "update-ref", "refs/imx/run-20260828-101010-bbbbbb/base", sha)

    counts = idem.reap_stale(settings.run_root, repo_paths=[repo],
                             worktree_root=_isolated_root())
    assert counts["refs"] == 1
    remaining = _git(repo, "for-each-ref", "--format=%(refname)", "refs/imx/")[1]
    assert live.name in remaining and "bbbbbb" not in remaining
