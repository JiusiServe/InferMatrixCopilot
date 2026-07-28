"""GPU mutex + orphan/VRAM hygiene — port of the rebase agent's gpu_lock.sh.

The on-disk protocol is kept byte-compatible with the shell implementation
(`<lock_dir>/lock` created with O_EXCL holding the owner pid, plus an `owner`
file, dead-owner steal via kill(pid, 0)) so shell-era and Python-era processes
interlock correctly while both exist.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Iterable


def _log(msg: str) -> None:
    print(f"[gpu_lock] {msg}", flush=True)


class GpuLockTimeout(RuntimeError):
    """The lock stayed held past the acquire timeout."""


class GpuLock:
    """File-based mutex serializing GPU access across processes.

    noclobber-equivalent create (O_CREAT|O_EXCL) of `<lock_dir>/lock` with the
    owner pid as content; a stale lock whose owner pid is dead is stolen."""

    def __init__(self, lock_dir: Path, *, poll_sec: float = 5.0,
                 timeout_sec: float = 3600.0):
        self.lock_dir = Path(lock_dir)
        self.lock_file = self.lock_dir / "lock"
        self.owner_file = self.lock_dir / "owner"
        self.poll_sec = poll_sec
        self.timeout_sec = timeout_sec
        self._held = False
        self._owner = ""

    # Content the shell can't have written yet counts as stale only after a
    # grace window (a crash between O_EXCL create and the pid write must not
    # wedge the lock for an hour, but a writer mid-create must not be robbed).
    EMPTY_LOCK_GRACE_SEC = 60.0

    def acquire(self, owner_pid: int | None = None) -> "GpuLock":
        owner = str(owner_pid or os.getpid())
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        elapsed = 0.0
        while elapsed < self.timeout_sec:
            try:
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(owner)
                # owner file is written for shell-era readers only; staleness
                # decisions never consult it (it lags the lock file)
                self.owner_file.write_text(owner)
                self._held = True
                self._owner = owner
                _log(f"GPU lock acquired by: {owner}")
                return self
            except FileExistsError:
                pass
            if self._steal_if_stale():
                continue  # retry the O_EXCL create immediately
            time.sleep(self.poll_sec)
            elapsed += self.poll_sec
        raise GpuLockTimeout(
            f"GPU lock timeout after {self.timeout_sec:.0f}s "
            f"(held by: {self._lock_content() or 'unknown'})")

    def _steal_if_stale(self) -> bool:
        """Steal a dead owner's lock without ever unlinking a live one.

        Staleness is judged from the LOCK file itself (authoritative — the
        owner file lags it). The steal is an atomic rename to a private name,
        then the renamed file's content is re-verified: if a live owner's
        fresh lock was swept up in the race window, it is restored via
        `os.link` (which fails atomically rather than clobbering a newer
        lock). Returns True when the caller should retry the create."""
        content = self._lock_content()
        if content is None:
            return False  # lock vanished; retry create
        if content.isdigit():
            if _pid_alive(int(content)):
                return False
        else:
            # empty/garbled: a writer mid-create, or a crash artifact
            try:
                age = time.time() - self.lock_file.stat().st_mtime
            except OSError:
                return False
            if age < self.EMPTY_LOCK_GRACE_SEC:
                return False
        claim = self.lock_file.with_name(f".steal.{os.getpid()}")
        try:
            os.rename(self.lock_file, claim)
        except OSError:
            return False  # someone else stole first; retry create
        try:
            taken = claim.read_text().strip()
        except OSError:
            taken = ""
        if taken.isdigit() and _pid_alive(int(taken)):
            # raced a fresh live lock: put it back without clobbering
            try:
                os.link(claim, self.lock_file)
            except OSError:
                _log(f"GPU lock steal race lost against pid={taken}; "
                     "could not restore — proceeding as contender")
            claim.unlink(missing_ok=True)
            return False
        _log(f"GPU lock owner (pid={taken or 'unknown'}) is dead. "
             "Stealing lock.")
        claim.unlink(missing_ok=True)
        return True

    def release(self) -> None:
        # only unlink a lock file we still own — ours may have been stolen
        if self._held:
            if self._lock_content() in (self._owner, None):
                self.lock_file.unlink(missing_ok=True)
            self.owner_file.unlink(missing_ok=True)
            self._held = False
            _log("GPU lock released.")

    def _lock_content(self) -> str | None:
        try:
            return self.lock_file.read_text().strip()
        except OSError:
            return None

    def __enter__(self) -> "GpuLock":
        return self.acquire()

    def __exit__(self, *exc) -> None:
        self.release()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:  # exists, other user
        return True


# -- nvidia-smi hygiene (injectable for tests) ---------------------------------

def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _device_pids(gpu_idx: str, run: Callable[[list[str]], str]) -> set[int]:
    """Compute-app pids ∪ pmon pids for one device — pmon catches processes
    holding the device without a CUDA context (an init lock, for instance).

    pmon rows are `<gpu> <pid> <type> ...`; the pid is field 2. The shell
    version awk'd field 1 (the gpu index) — on GPU 0 that meant `kill 0`,
    signalling its own process group. Deliberately fixed, not ported.
    Non-positive pids are rejected for the same reason."""
    pids: set[int] = set()
    out = run(["nvidia-smi", f"--id={gpu_idx}", "--query-compute-apps=pid",
               "--format=csv,noheader,nounits"])
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit() and int(line) > 0:
            pids.add(int(line))
    out = run(["nvidia-smi", "pmon", "-c", "1", "-i", gpu_idx, "--select", "C"])
    for line in out.splitlines()[2:]:
        fields = line.split()
        if len(fields) >= 2 and fields[1].isdigit() and int(fields[1]) > 0:
            pids.add(int(fields[1]))
    return pids


def cleanup_orphan_gpu_procs(devices: str, *,
                             run: Callable[[list[str]], str] = _run,
                             kill: Callable[[int, int], None] | None = None,
                             sleep: Callable[[float], None] = time.sleep) -> int:
    """TERM → 2 s → KILL every process on the visible `devices` (comma list),
    excluding our own process and parent. Safe while holding the GPU lock: the
    lock serializes all GPU test invocations, so anything found is an orphan.
    Returns the number of processes TERMed."""
    if not devices or (run is _run and shutil.which("nvidia-smi") is None):
        return 0
    kill = kill or (lambda pid, sig: os.kill(pid, sig))
    own = {os.getpid(), os.getppid()}
    idxs = [d for d in devices.split(",") if d.strip()]

    killed = 0
    for idx in idxs:
        for pid in _device_pids(idx, run) - own:
            _log(f"GPU cleanup: killing orphan process {pid} on GPU {idx}")
            try:
                kill(pid, 15)
            except OSError:
                pass
            killed += 1
    if killed:
        sleep(2)
        for idx in idxs:
            for pid in _device_pids(idx, run) - own:
                try:
                    kill(pid, 9)
                except OSError:
                    pass
        sleep(1)
        _log(f"GPU cleanup: killed {killed} orphan process(es), "
             "waiting for VRAM release.")
    return killed


def wait_gpu_memory_idle(devices: str, *, max_usage_frac: float = 0.10,
                         timeout_sec: float = 120.0, poll_sec: float = 3.0,
                         run: Callable[[list[str]], str] = _run,
                         sleep: Callable[[float], None] = time.sleep) -> bool:
    """Wait until every visible device is ≤ `max_usage_frac` VRAM, so the next
    test doesn't hit "Free memory ... is less than desired" errors. Timeout is
    a warning, never fatal (shell parity). Returns True when idle was reached."""
    if not devices or (run is _run and shutil.which("nvidia-smi") is None):
        return True
    idxs = [d for d in devices.split(",") if d.strip()]
    waited = 0.0
    while waited < timeout_sec:
        all_idle = True
        for idx in idxs:
            out = run(["nvidia-smi", f"--id={idx}",
                       "--query-gpu=memory.used,memory.total",
                       "--format=csv,noheader,nounits"])
            try:
                used, total = (int(x) for x in out.strip().split(",")[:2])
            except (ValueError, IndexError):
                all_idle = False
                continue
            if total > 0 and used / total > max_usage_frac:
                all_idle = False
        if all_idle:
            return True
        sleep(poll_sec)
        waited += poll_sec
    _log(f"GPU memory wait timed out after {timeout_sec:.0f}s; "
         "proceeding with potentially dirty VRAM.")
    return False
