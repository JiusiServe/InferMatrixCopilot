"""EXT1 e2e — mutual exclusion between the EXTERNAL orchestrator's
startup flock and the copilot's `CheckoutLock`, in both directions.

The external guard (`agent/lib/checkout_lock.py` in the canonical
vllm-omni-rebase-agent checkout) is deliberately stdlib-only so this
suite can load the FILE directly — no `agent` package import, no
langgraph — and prove the two sides contend on the same
`<checkout>/locks/omni.lock` protocol. Skips cleanly on machines
without the external checkout (the copilot suite stays offline-green
everywhere; this test is inherently about THIS deployment)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.rebase_engine.runctx import CheckoutLock

_CANDIDATES = [
    Path(os.environ.get("REBASE_AGENT_ROOT", "")),
    Settings.model_fields["rebase_agent_root"].default,
    Path("/data/zhoutaichang/rebase/vllm-omni-rebase-agent"),
]


def _external_guard():
    """(module, root) for the first candidate checkout CARRYING the EXT1
    guard — the presence of checkout_lock.py is what selects the root, so
    every assertion in this file (including source-order checks) reads the
    SAME checkout the guard came from (a stale sibling working copy
    without EXT1 must never be inspected instead)."""
    for root in _CANDIDATES:
        if root and (Path(root) / "agent/lib/checkout_lock.py").is_file():
            spec = importlib.util.spec_from_file_location(
                "ext1_checkout_lock",
                Path(root) / "agent/lib/checkout_lock.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, Path(root)
    return None, None


guard, GUARD_ROOT = _external_guard()
pytestmark = pytest.mark.skipif(
    guard is None, reason="external vllm-omni-rebase-agent checkout (with "
                          "the EXT1 guard) not present on this machine")


def test_mutual_exclusion_both_directions(tmp_path):
    checkout = tmp_path / "omni"
    checkout.mkdir()

    # copilot holds -> external refused
    ours = CheckoutLock(checkout, "omni")
    assert ours.acquire(blocking=False) is True
    assert guard.acquire_checkout_lock(checkout) is False
    ours.release()

    # external holds -> copilot refused; release frees
    assert guard.acquire_checkout_lock(checkout) is True
    probe = CheckoutLock(checkout, "omni")
    assert probe.acquire(blocking=False) is False
    guard.release_checkout_lock()
    assert probe.acquire(blocking=False) is True
    probe.release()

    # both sides lock the SAME file (protocol identity, not coincidence)
    assert ours.path == checkout / "locks" / "omni.lock"
    assert (checkout / "locks" / "omni.lock").exists()


def test_release_leaves_the_file(tmp_path):
    """Deleting a lock file while another process holds its flock would
    break exclusion via a fresh inode — both sides deliberately leave it
    in place."""
    checkout = tmp_path / "omni"
    checkout.mkdir()
    assert guard.acquire_checkout_lock(checkout) is True
    guard.release_checkout_lock()
    assert (checkout / "locks" / "omni.lock").exists()


def test_exclusion_failure_fails_closed(tmp_path):
    """Round-2 P1: on a GIT checkout where the hygiene shield cannot be
    installed, acquisition must FAIL (an unignored lock file faces the
    guard/L2 deletion path) — and must not leave the flock held."""
    import subprocess
    for side in ("external", "copilot"):
        checkout = tmp_path / f"omni-{side}"
        checkout.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
        # make `.git/info` an unwritable location: a FILE where the dir
        # must go -> mkdir raises, the shield cannot install
        import shutil
        shutil.rmtree(checkout / ".git" / "info", ignore_errors=True)
        (checkout / ".git" / "info").write_text("not a dir")
        if side == "external":
            assert guard.acquire_checkout_lock(checkout) is False
        else:
            assert CheckoutLock(checkout, "omni").acquire(
                blocking=False) is False
        # the failed acquisition released the flock
        probe = CheckoutLock(tmp_path / "clean", "omni")
        (tmp_path / "clean").mkdir(exist_ok=True)
        import fcntl
        with open(checkout / "locks" / "omni.lock") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)  # acquirable
            fcntl.flock(fh, fcntl.LOCK_UN)


def test_losing_contender_never_touches_exclude(tmp_path):
    """Round-2 P1: the exclusion write happens UNDER the flock — a losing
    contender must not read-modify-write (and possibly truncate)
    `info/exclude` while the winner is active."""
    import subprocess
    checkout = tmp_path / "omni"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    winner = CheckoutLock(checkout, "omni")
    assert winner.acquire(blocking=False) is True
    exclude = checkout / ".git" / "info" / "exclude"
    before = exclude.read_bytes()
    sentinel = before + b"# sentinel: losers must not rewrite this file\n"
    exclude.write_bytes(sentinel)
    # both kinds of loser are refused BEFORE any exclude write
    assert guard.acquire_checkout_lock(checkout) is False
    assert CheckoutLock(checkout, "omni").acquire(blocking=False) is False
    assert exclude.read_bytes() == sentinel
    winner.release()


def test_relative_gitdir_resolves_against_dotgit_file(tmp_path):
    """Round-2 P2: a RELATIVE `gitdir:` pointer resolves against the
    directory containing the `.git` file (as git does), never our cwd —
    otherwise a valid worktree layout shields the wrong repository."""
    main_repo = tmp_path / "main"
    (main_repo / ".git" / "worktrees" / "wt").mkdir(parents=True)
    # every real git dir carries HEAD — the plausibility check requires it
    (main_repo / ".git" / "worktrees" / "wt" / "HEAD").write_text(
        "ref: refs/heads/main\n")
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: ../main/.git/worktrees/wt\n")
    assert guard.acquire_checkout_lock(wt) is True
    guard.release_checkout_lock()
    common_exclude = main_repo / ".git" / "info" / "exclude"
    assert common_exclude.exists()
    assert "/locks/" in common_exclude.read_text().split("\n")
    # the copilot side resolves identically
    wt2 = tmp_path / "wt2"
    wt2.mkdir()
    (wt2 / ".git").write_text("gitdir: ../main/.git/worktrees/wt\n")
    lock = CheckoutLock(wt2, "omni")
    assert lock.acquire(blocking=False) is True
    lock.release()


def test_orchestrator_main_ordering():
    """Round-2 P2: the guard is taken AFTER the dry-run exit and BEFORE
    both baseline detection (checkout READS must not capture another
    holder's intermediate state) and resume detection (the first
    mutation). Pinned against the external main() source and the v1
    runtime builder."""
    src = (GUARD_ROOT / "agent/orchestrator.py").read_text()
    main_src = src[src.index("async def main("):]
    order = [main_src.index("if args.dry_run:"),
             main_src.index("acquire_checkout_lock("),
             main_src.index("settings = detect_baseline(settings)"),
             main_src.index("# Resume detection")]
    assert order == sorted(order), order
    # v1: the in-process backend orders identically
    from infermatrix_copilot.engine.steps import rebase_native
    v1_src = Path(rebase_native.__file__).read_text()
    build_src = v1_src[v1_src.index("def _ensure_runtime("):]
    assert build_src.index("_ensure_omni_lock(ctx, settings)") \
        < build_src.index("orch.detect_baseline(settings)")


def test_unreadable_git_metadata_fails_closed(tmp_path):
    """Round-3 P1: git metadata that EXISTS but cannot be decoded is
    "unknown git", never "no git" — acquisition must fail (an unshielded
    lock on a real git checkout faces the hygiene deletion path), with a
    setup diagnostic, not a contention claim."""
    for side in ("external", "copilot"):
        checkout = tmp_path / f"omni-{side}"
        checkout.mkdir()
        (checkout / ".git").write_bytes(b"gitdir: \xff\xfe\x00broken")
        if side == "external":
            assert guard.acquire_checkout_lock(checkout) is False
            assert "not contention" in guard.last_failure()
        else:
            lock = CheckoutLock(checkout, "omni")
            assert lock.acquire(blocking=False) is False
            assert "not contention" in lock.last_failure


def test_exclusion_is_root_anchored(tmp_path):
    """Round-3 P2 + round-4 P2: the ignore pattern must be `/locks/`
    (root-anchored — a bare `locks/` would hide a legitimate NESTED
    `locks` source dir); ONLY the comment-paired entry we own is
    migrated, while a FOREIGN standalone `locks/` user rule is preserved
    verbatim (deleting it could expose/stage deliberately-ignored
    files)."""
    import subprocess
    checkout = tmp_path / "omni"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    exclude = checkout / ".git" / "info" / "exclude"
    foreign = exclude.read_text()
    our_comment = "# rebase checkout flock — never dirt, never cleaned"
    # a FOREIGN standalone rule + an OWNED (comment-paired) stale entry
    exclude.write_text(foreign + "locks/\n" + our_comment + "\nlocks/\n")
    lock = CheckoutLock(checkout, "omni")
    assert lock.acquire(blocking=False) is True
    lines = exclude.read_text().split("\n")
    assert "/locks/" in lines                        # anchored entry in
    assert lines.count("locks/") == 1                # FOREIGN rule kept,
    #                                                  owned pair migrated
    for ln in foreign.strip().split("\n"):
        assert ln in lines                           # foreign content kept
    # a NESTED locks dir stays visible to git... under the ANCHORED entry
    # (the preserved foreign `locks/` would hide it — that is the USER's
    # deliberate rule, so verify anchoring on a clean second checkout)
    lock.release()
    checkout2 = tmp_path / "omni2"
    checkout2.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout2, check=True)
    assert guard.acquire_checkout_lock(checkout2) is True
    lines2 = (checkout2 / ".git" / "info" / "exclude").read_text().split("\n")
    assert "/locks/" in lines2 and "locks/" not in lines2
    nested = checkout2 / "src" / "locks"
    nested.mkdir(parents=True)
    (nested / "semaphore.py").write_text("x")
    out = subprocess.run(["git", "status", "--porcelain"], cwd=checkout2,
                         capture_output=True, text=True, check=True).stdout
    assert "src/" in out                             # nested NOT hidden
    assert "locks/omni.lock" not in out              # root lock hidden
    guard.release_checkout_lock()


def test_failure_diagnostics_are_distinct(tmp_path):
    """Round-3 P2: contention and setup failures must be reported
    differently — a permanent permissions/metadata failure misdiagnosed
    as "another run holds the lock" sends the operator to wait forever."""
    import subprocess
    checkout = tmp_path / "omni"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    holder = CheckoutLock(checkout, "omni")
    assert holder.acquire(blocking=False) is True
    assert guard.acquire_checkout_lock(checkout) is False
    assert guard.last_failure().startswith("contention")
    loser = CheckoutLock(checkout, "omni")
    assert loser.acquire(blocking=False) is False
    assert loser.last_failure.startswith("contention")
    holder.release()
    # ...and the orchestrator branches on it (source pin: both messages)
    src = (GUARD_ROOT / "agent/orchestrator.py").read_text()
    assert 'reason.startswith("contention")' in src
    assert "SETUP failed" in src


def test_symlinked_lock_paths_fail_closed(tmp_path):
    """Round-4 P1: a symlinked `locks` dir (or lock file) must refuse —
    open() would truncate an arbitrary target, and git's `/locks/`
    DIRECTORY pattern does not match a symlink, so `git clean -fd` could
    remove it and a later run would lock a DIFFERENT inode at the same
    path."""
    import subprocess
    for side in ("external", "copilot"):
        checkout = tmp_path / f"omni-dir-{side}"
        checkout.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
        elsewhere = tmp_path / f"elsewhere-{side}"
        elsewhere.mkdir()
        (checkout / "locks").symlink_to(elsewhere)
        if side == "external":
            assert guard.acquire_checkout_lock(checkout) is False
            assert "not contention" in guard.last_failure()
        else:
            lock = CheckoutLock(checkout, "omni")
            assert lock.acquire(blocking=False) is False
            assert "not contention" in lock.last_failure
    # ...and a symlinked lock FILE inside a real dir refuses too
    checkout = tmp_path / "omni-file"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    (checkout / "locks").mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("do not truncate")
    (checkout / "locks" / "omni.lock").symlink_to(victim)
    assert guard.acquire_checkout_lock(checkout) is False
    assert "not contention" in guard.last_failure()
    lock = CheckoutLock(checkout, "omni")
    assert lock.acquire(blocking=False) is False
    assert victim.read_text() == "do not truncate"   # never followed


def test_non_conflict_flock_errors_are_setup_failures(tmp_path,
                                                      monkeypatch):
    """Round-4 P2: only a lock CONFLICT (EAGAIN/EWOULDBLOCK/EACCES) is
    contention — ENOLCK/EIO/unsupported-filesystem errors are broken
    setup, and telling the operator to wait would be wrong."""
    import errno
    import fcntl as fcntl_mod
    import subprocess
    checkout = tmp_path / "omni"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)

    def broken_flock(fh, flags):
        raise OSError(errno.ENOLCK, "No locks available")
    monkeypatch.setattr(fcntl_mod, "flock", broken_flock)
    assert guard.acquire_checkout_lock(checkout) is False
    assert "not contention" in guard.last_failure()
    assert "flock" in guard.last_failure()
    lock = CheckoutLock(checkout, "omni")
    assert lock.acquire(blocking=False) is False
    assert "not contention" in lock.last_failure


def test_malformed_git_pointers_fail_closed(tmp_path):
    """Round-4 P2: existing-but-INVALID `.git` pointers (no `gitdir:`
    prefix, empty target, multiline, or a target that is not a git dir)
    follow the same fail-closed path as undecodable metadata — an empty
    `gitdir:` must never resolve to the checkout itself and 'shield' an
    invented `info/` there."""
    cases = ["random contents\n", "gitdir:\n", "gitdir: \n",
             "gitdir: a\nb\n", "gitdir: ../does/not/exist\n"]
    for i, content in enumerate(cases):
        for side in ("external", "copilot"):
            checkout = tmp_path / f"omni-{i}-{side}"
            checkout.mkdir()
            (checkout / ".git").write_text(content)
            if side == "external":
                assert guard.acquire_checkout_lock(checkout) is False, \
                    (content, side)
                assert "not contention" in guard.last_failure()
            else:
                lock = CheckoutLock(checkout, "omni")
                assert lock.acquire(blocking=False) is False, \
                    (content, side)
                assert "not contention" in lock.last_failure
            # no invented shield location was created
            assert not (checkout / "info").exists()


def test_missing_checkout_is_not_fabricated(tmp_path):
    """Round-5 P2: acquiring on a nonexistent checkout (typo, missing
    mount) must FAIL with a setup diagnostic — and must not invent an
    empty directory whose lock then 'succeeds'."""
    for side in ("external", "copilot"):
        ghost = tmp_path / f"no-such-checkout-{side}"
        if side == "external":
            assert guard.acquire_checkout_lock(ghost) is False
            assert "does not exist" in guard.last_failure()
            assert "not contention" in guard.last_failure()
        else:
            lock = CheckoutLock(ghost, "omni")
            assert lock.acquire(blocking=False) is False
            assert "does not exist" in lock.last_failure
        assert not ghost.exists()                    # never fabricated


def test_exclude_write_failure_preserves_foreign_rules(tmp_path,
                                                       monkeypatch):
    """Round-5 P2: the exclude rewrite is ATOMIC — a failed write must
    fail the acquisition WITHOUT truncating the user's existing ignore
    rules (the old in-place write_text destroyed them on ENOSPC/EIO)."""
    import os as os_mod
    import subprocess
    checkout = tmp_path / "omni"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    exclude = checkout / ".git" / "info" / "exclude"
    our_comment = "# rebase checkout flock — never dirt, never cleaned"
    seeded = "user-rule.bin\nlocks/\n" + our_comment + "\nlocks/\n"
    exclude.write_text(seeded)                       # forces a rewrite

    def broken_replace(src, dst):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(os_mod, "replace", broken_replace)
    lock = CheckoutLock(checkout, "omni")
    assert lock.acquire(blocking=False) is False
    assert "not contention" in lock.last_failure
    assert exclude.read_text() == seeded             # NOT truncated
    assert guard.acquire_checkout_lock(checkout) is False
    assert exclude.read_text() == seeded
    monkeypatch.undo()
    # with the write path healthy the same acquisition succeeds
    assert CheckoutLock(checkout, "omni").acquire(blocking=False) is True


def test_unsupported_git_entries_fail_closed(tmp_path):
    """Round-5 P2: a `.git` that exists as a dangling symlink or FIFO is
    'unknown git', never 'no git' — acquisition fails closed on both
    sides."""
    import os as os_mod
    shapes = {"dangling": lambda g: g.symlink_to(tmp_path / "gone"),
              "fifo": lambda g: os_mod.mkfifo(g)}
    for shape, make in shapes.items():
        for side in ("external", "copilot"):
            checkout = tmp_path / f"omni-{shape}-{side}"
            checkout.mkdir()
            make(checkout / ".git")
            if side == "external":
                assert guard.acquire_checkout_lock(checkout) is False, \
                    (shape, side)
                assert "not contention" in guard.last_failure()
            else:
                lock = CheckoutLock(checkout, "omni")
                assert lock.acquire(blocking=False) is False, (shape, side)
                assert "not contention" in lock.last_failure


def test_lock_survives_workspace_hygiene(tmp_path):
    """The round-1 P1: on a REAL git checkout the live lock file must be
    invisible to every hygiene pass the parent's phase 1 (and the
    copilot's guards) run — `git status` (the clean-tree verdict),
    `git clean -fd` (the L2 dirty-worktree cleanup), and `git add -A`
    (push staging). Both sides write `locks/` into the LOCAL
    `.git/info/exclude` at acquire time; the flock must still be on the
    SAME inode afterwards (a cleaned-and-recreated file would defeat
    mutual exclusion)."""
    import subprocess

    def git(*args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=checkout, check=True, capture_output=True, text=True)

    for side, take, drop in (
            ("external", lambda c: guard.acquire_checkout_lock(c),
             lambda: guard.release_checkout_lock()),
            ("copilot", None, None)):
        checkout = tmp_path / f"omni-{side}"
        checkout.mkdir()
        git("init", "-q")
        (checkout / "seed.txt").write_text("s")
        git("add", "-A")
        git("commit", "-qm", "seed")
        if side == "copilot":
            lock = CheckoutLock(checkout, "omni")
            assert lock.acquire(blocking=False) is True
            drop = lock.release
        else:
            assert take(checkout) is True
        lock_file = checkout / "locks" / "omni.lock"
        inode = lock_file.stat().st_ino
        # 1. the clean-tree verdict: nothing to report
        assert git("status", "--porcelain").stdout.strip() == "", side
        # 2. the L2 cleanup: a non-`-x` git clean must not touch it
        git("clean", "-fdq")
        assert lock_file.exists(), side
        assert lock_file.stat().st_ino == inode, side   # SAME inode
        # ...and the flock is still held on it
        probe = CheckoutLock(checkout, "omni")
        assert probe.acquire(blocking=False) is False, side
        # 3. push staging: `git add -A` stages nothing
        git("add", "-A")
        assert git("diff", "--cached", "--name-only").stdout.strip() \
            == "", side
        drop()
        assert probe.acquire(blocking=False) is True, side
        probe.release()