"""Run-lifecycle primitives: the same-run lock and the finalizer hook point.

Two guarantees the executor itself cannot give, because it knows nothing about
processes:

* `RunLock` — an exclusive advisory `flock` on `<run_dir>/.lock`. Two
  invocations of the same run (e.g. a second `--resume` while the first is
  still working) would interleave progress writes and share the checkout; the
  second holder fails fast instead.
* finalizers — per-run async callables invoked exactly once when the run
  leaves the event loop, whether it completed, failed, or raised. With nothing
  registered (every current playbook) the hook is a no-op; the rebase pipeline
  registers teardown (locks, scratch clones, store flushes) here so that
  resume, crash, and success all release resources the same way.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Awaitable, Callable

try:  # same guard as run_status.py: fcntl is POSIX-only
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore

Finalizer = Callable[[Any], Awaitable[None]]

_finalizers: dict[str, list[Finalizer]] = {}


class RunLockHeld(RuntimeError):
    """Another process already holds this run's lock."""


class RunLock:
    """Exclusive advisory lock on `<run_dir>/.lock` for the duration of a run.

    `flock` contention is per open file description, so a second `acquire` on
    the same path — even inside the same process — fails while the first is
    held. The lock file is left in place after release: its existence carries
    no meaning, only the flock does."""

    def __init__(self, run_dir: Path):
        self.path = Path(run_dir) / ".lock"
        self._fd: int | None = None

    def acquire(self) -> "RunLock":
        if fcntl is None:  # non-POSIX: no advisory locking; keep runs working
            return self
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            raise RunLockHeld(
                f"run lock {self.path} is held by another process — "
                "is this run already executing (a concurrent --resume)?")
        self._fd = fd
        return self

    def release(self) -> None:
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> "RunLock":
        return self.acquire()

    def __exit__(self, *exc) -> None:
        self.release()


def register_finalizer(run_dir: Path, fn: Finalizer) -> None:
    """Register an async finalizer for `run_dir`, called as `fn(outcome)` where
    outcome is the RunOutcome, or None if the executor raised before producing
    one. Finalizers run in registration order and exactly once per run."""
    _finalizers.setdefault(str(Path(run_dir)), []).append(fn)


async def finalize(run_dir: Path, outcome: Any) -> None:
    """Run and consume `run_dir`'s finalizers. Popping before running makes a
    second call a no-op, and a finalizer that raises never suppresses the
    run's own outcome or blocks its siblings."""
    for fn in _finalizers.pop(str(Path(run_dir)), []):
        try:
            await fn(outcome)
        except (Exception, asyncio.CancelledError):
            # CancelledError is BaseException: without naming it, a finalizer
            # awaiting an already-cancelled task would mask the run's outcome
            # and skip its siblings.
            pass


async def run_guarded(run: Awaitable[Any], run_dir: Path) -> Any:
    """Await the executor coroutine, then ALWAYS finalize — on completion,
    failure, or exception — inside the same event loop. The shield keeps a
    cancellation delivered during teardown from abandoning it halfway."""
    outcome: Any = None
    try:
        outcome = await run
        return outcome
    finally:
        await asyncio.shield(finalize(run_dir, outcome))
