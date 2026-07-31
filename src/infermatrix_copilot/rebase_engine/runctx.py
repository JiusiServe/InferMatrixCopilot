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


class CheckoutLock:
    """A named exclusive flock under `<checkout>/locks/<name>.lock` — the
    shared-participation lock (plan §8: EXT1 makes the external executable
    take it; the in-process backend and archival take the SAME file)."""

    def __init__(self, checkout: Path, name: str):
        self.path = Path(checkout) / "locks" / f"{name}.lock"
        self._fh = None

    def acquire(self, *, blocking: bool = True) -> bool:
        try:
            import fcntl
        except ImportError:  # pragma: no cover - Windows
            return True  # documented degradation: no fcntl, no exclusion
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, "w")
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(fh, flags)
        except OSError:
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
        returns the labels of finalizers that failed or were skipped when the
        window closed (surfaced by the caller's report)."""
        if self._torn_down:
            return []
        self._torn_down = True
        failures: list[str] = []
        deadline = time.monotonic() + timeout_sec
        for label, fn in reversed(self._finalizers):
            if time.monotonic() > deadline:
                failures.append(f"{label} (skipped: teardown window closed)")
                continue
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 - teardown never raises
                failures.append(f"{label} ({type(exc).__name__}: {exc})")
        self._finalizers.clear()
        return failures


def _loop_id() -> int:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        return 0  # no running loop: sync context gets its own key space


class RuntimeRegistry:
    """Process-wide registry, keyed by (run_dir, event-loop id) under a
    threading.Lock with double-checked creation. `release()` tears the
    runtime down and forgets it; a later acquire builds a fresh one."""

    def __init__(self):
        self._lock = threading.Lock()
        self._runtimes: dict[tuple[str, int], RebaseRuntime] = {}

    def get_or_create(self, run_dir: Path, run_id: str) -> RebaseRuntime:
        key = (str(Path(run_dir)), _loop_id())
        rt = self._runtimes.get(key)
        if rt is not None:
            if rt.run_id != run_id:
                raise RuntimeError_(
                    f"run_dir {key[0]} is registered to run {rt.run_id!r}, "
                    f"not {run_id!r}")
            return rt
        with self._lock:
            rt = self._runtimes.get(key)
            if rt is None:
                rt = RebaseRuntime(run_dir, run_id)
                self._runtimes[key] = rt
            elif rt.run_id != run_id:
                raise RuntimeError_(
                    f"run_dir {key[0]} is registered to run {rt.run_id!r}, "
                    f"not {run_id!r}")
            return rt

    def release(self, run_dir: Path, *, timeout_sec: float = 60.0) -> list[str]:
        key = (str(Path(run_dir)), _loop_id())
        with self._lock:
            rt = self._runtimes.pop(key, None)
        return rt.teardown(timeout_sec=timeout_sec) if rt else []


REGISTRY = RuntimeRegistry()
