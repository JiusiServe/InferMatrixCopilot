"""Run-resource lifecycle — `RebaseRuntime` + loop-scoped registry
(plan §4 / Rev 8 §3.4).

A runtime owns one run's process-lifetime resources: the substate handle,
named checkout flocks (e.g. the shared `omni.lock` every user of a checkout
must hold), registered finalizers, and the abort flag. The registry hands out
runtimes keyed by ``(run_dir, event-loop id)`` — asyncio primitives created
inside a runtime must never cross ``asyncio.run`` boundaries, so a second
`asyncio.run` over the same run_dir gets a FRESH runtime rather than one
holding another loop's dead primitives. Repeated sequential runs are the
normal chat/CLI pattern; the pinning test drives exactly that.

Teardown runs finalizers newest-first inside a bounded window and never
raises across the boundary — the caller's shielded `finally` (PR0's
`run_guarded`) depends on that.
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import Callable

from .substate import Substate


class RuntimeError_(RuntimeError):
    """Runtime acquisition/teardown failed."""


def _ensure_lock_dir_excluded(checkout: Path) -> bool:
    """Mark `locks/` git-ignored via the LOCAL `.git/info/exclude` (never a
    committed file, never dirt itself). Without this the live lock file is
    an untracked entry, and any workspace-hygiene pass — the parent's
    phase-1 clean-tree guard with its L2 `git clean` cleanup (which v1
    backend runs execute against this same checkout), or a bulk
    `git add -A` staging — would delete or commit it. A `git clean`ed lock
    file leaves its holder flocking a DELETED inode while a new run locks
    a fresh one at the same path: mutual exclusion defeated. Ignored files
    are exempt from status, non-`-x` clean, and `add -A`.

    Returns True when the exclusion is verifiably in place — or the
    directory is not a git checkout (no git, no hygiene hazard). False
    when the checkout IS git but the write failed: the caller FAILS
    CLOSED. Idempotent; worktree-aware (a RELATIVE `gitdir:` pointer
    resolves against the `.git` file's directory, as git does). Call only
    while HOLDING the flock — the flock serializes writers, so a losing
    contender never touches the file."""
    checkout = Path(checkout)
    git = checkout / ".git"
    if git.is_dir():
        info = git / "info"
    elif git.is_file():  # linked worktree: `gitdir: …/.git/worktrees/<n>`
        try:
            target = Path(git.read_text().strip()
                          .removeprefix("gitdir:").strip())
        except OSError:
            return False
        if not target.is_absolute():
            target = (checkout / target).resolve()
        info = (target.parent.parent / "info"
                if target.parent.name == "worktrees" else target / "info")
    else:
        return True
    try:
        info.mkdir(parents=True, exist_ok=True)
        exclude = info / "exclude"
        text = exclude.read_text() if exclude.exists() else ""
        if "locks/" not in text.split("\n"):
            exclude.write_text(
                (text.rstrip("\n") + "\n" if text.strip() else "")
                + "# rebase checkout flock — never dirt, never cleaned\n"
                  "locks/\n")
        return "locks/" in exclude.read_text().split("\n")
    except OSError:
        return False


class CheckoutLock:
    """A named exclusive flock under `<checkout>/locks/<name>.lock` — the
    shared-participation lock (plan §8: EXT1 makes the external executable
    take it; the in-process backend and archival take the SAME file)."""

    def __init__(self, checkout: Path, name: str):
        self.checkout = Path(checkout)
        self.path = Path(checkout) / "locks" / f"{name}.lock"
        self._fh = None

    def acquire(self, *, blocking: bool = True) -> bool:
        try:
            import fcntl
        except ImportError:  # pragma: no cover - Windows
            return True  # documented degradation: no fcntl, no exclusion
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fh = open(self.path, "w")
        except OSError:
            return False
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(fh, flags)
        except OSError:
            fh.close()
            return False
        # the hygiene shield is installed UNDER the flock (winner-only
        # writer) and is a HARD prerequisite on git checkouts: an unignored
        # lock file faces the guard/L2 `git clean` deletion path, so
        # failing to shield it means failing to lock
        if not _ensure_lock_dir_excluded(self.checkout):
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
            except OSError:
                pass
            fh.close()
            return False
        self._fh = fh
        return True

    def release(self) -> None:
        if self._fh is not None:
            try:
                import fcntl
                fcntl.flock(self._fh, fcntl.LOCK_UN)
            except (ImportError, OSError):
                pass
            self._fh.close()
            self._fh = None

    @property
    def held(self) -> bool:
        return self._fh is not None


class RebaseRuntime:
    """One run's resource owner. Created only via `RuntimeRegistry`."""

    def __init__(self, run_dir: Path, run_id: str):
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.substate = Substate(run_dir, run_id)
        self.abort_requested = False
        self._finalizers: list[tuple[str, Callable[[], None]]] = []
        self._checkout_locks: dict[str, CheckoutLock] = {}
        self._torn_down = False

    def acquire_checkout_lock(self, checkout: Path, name: str, *,
                              blocking: bool = True) -> bool:
        """Idempotent per (checkout, name); the lock is owned by the runtime
        and released in teardown (reverse order via finalizers)."""
        key = f"{Path(checkout)}::{name}"
        lock = self._checkout_locks.get(key)
        if lock is not None and lock.held:
            return True
        lock = CheckoutLock(checkout, name)
        if not lock.acquire(blocking=blocking):
            return False
        self._checkout_locks[key] = lock
        self.add_finalizer(f"release {name} lock", lock.release)
        return True

    def add_finalizer(self, label: str, fn: Callable[[], None]) -> None:
        if self._torn_down:
            raise RuntimeError_("runtime already torn down")
        self._finalizers.append((label, fn))

    def request_abort(self) -> None:
        """Signal handlers ONLY set this flag (and cancel the task); actual
        cleanup belongs to teardown — plan §4 signal contract."""
        self.abort_requested = True

    def teardown(self, *, timeout_sec: float = 60.0) -> list[str]:
        """Run finalizers newest-first inside a bounded window. Never raises;
        returns the labels of finalizers that failed, hung past their share
        of the window, or were skipped when it closed.

        Each finalizer runs in a daemon thread joined against the REMAINING
        window — a blocked finalizer (dead NFS, wedged subprocess) cannot
        hang teardown forever and defeat the lifecycle contract. Python
        cannot kill the hung thread; it is abandoned (daemon) and reported,
        which the caller surfaces as a lock-leak warning."""
        if self._torn_down:
            return []
        self._torn_down = True
        failures: list[str] = []
        deadline = time.monotonic() + timeout_sec
        for label, fn in reversed(self._finalizers):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failures.append(f"{label} (skipped: teardown window closed)")
                continue
            outcome: list[str] = []

            def runner(fn=fn, outcome=outcome):
                try:
                    fn()
                except Exception as exc:  # noqa: BLE001 - never raises out
                    outcome.append(f"{type(exc).__name__}: {exc}")

            t = threading.Thread(target=runner, daemon=True)
            t.start()
            t.join(remaining)
            if t.is_alive():
                failures.append(f"{label} (hung past the teardown window; "
                                "thread abandoned)")
            elif outcome:
                failures.append(f"{label} ({outcome[0]})")
        self._finalizers.clear()
        return failures


def _current_loop() -> "asyncio.AbstractEventLoop | None":
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


class RuntimeRegistry:
    """Process-wide registry keyed by (run_dir, event loop) under a
    threading.Lock with double-checked creation. The loop key is a WEAK
    reference to the loop OBJECT — `id(loop)` is unusable, since a dead
    loop's memory address is routinely reused by the next `asyncio.run` and
    the stale runtime (holding the dead loop's primitives) would be handed
    out again. When the loop is garbage-collected its runtimes vanish with
    it. `release()` tears the runtime down and forgets it; a later acquire
    builds a fresh one. Sync (no-loop) contexts get their own bucket."""

    def __init__(self):
        import weakref
        self._lock = threading.Lock()
        # loop -> {run_dir -> runtime}; entries die with their loop
        self._by_loop: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
        self._sync: dict[str, RebaseRuntime] = {}

    def _bucket(self) -> dict:
        loop = _current_loop()
        if loop is None:
            return self._sync
        bucket = self._by_loop.get(loop)
        if bucket is None:
            bucket = {}
            self._by_loop[loop] = bucket
        return bucket

    def get_or_create(self, run_dir: Path, run_id: str) -> RebaseRuntime:
        key = str(Path(run_dir))
        with self._lock:
            bucket = self._bucket()
            rt = bucket.get(key)
            if rt is None:
                rt = RebaseRuntime(run_dir, run_id)
                bucket[key] = rt
            elif rt.run_id != run_id:
                raise RuntimeError_(
                    f"run_dir {key} is registered to run {rt.run_id!r}, "
                    f"not {run_id!r}")
            return rt

    def release(self, run_dir: Path, *, timeout_sec: float = 60.0) -> list[str]:
        key = str(Path(run_dir))
        with self._lock:
            rt = self._bucket().pop(key, None)
        return rt.teardown(timeout_sec=timeout_sec) if rt else []


REGISTRY = RuntimeRegistry()
