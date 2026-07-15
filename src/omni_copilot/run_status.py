"""`run_status.json` — the durable, single-writer lifecycle record of one run.

The MCP server (mcp_server.py) launches each run as a subprocess and can only
observe it through the filesystem, so the run's state must be *durable* (survives
a server restart) and *unambiguous* (a crashed run is distinguishable from a
running one — file-presence heuristics can't do that). This module is that
record.

Two design invariants make it safe under the plan's multi-server model (Claude
Code and Codex each launch their own server):

- **Single writer.** `reserve_run` (the server) writes the initial `queued`
  record before the child exists. Once launched, the **child is the sole writer**
  during the run: it writes its own pid (`mark_child_started`) as its first act,
  then drives `planning -> running -> {done|blocked|failed}`. The parent never
  writes while the child is alive; it only reconciles *after* `.wait()` (child
  dead). Cross-process reconcilers write only after confirming the writer is
  dead. Every write takes an advisory `flock` and preserves the ownership fields,
  so there are never two concurrent writers and no lost updates.

- **Ownership-aware reconciliation.** Each run stores the `owner_server_id` /
  `owner_server_pid` that reserved it and (once launched) the `child_pid`. A
  server reconciles a non-terminal run to `interrupted` **only** when the owning
  server is confirmed dead *and* the child is dead/absent — so a second server
  never marks another live server's legitimately-`queued` run interrupted.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

try:  # POSIX advisory locking; the copilot targets Linux (H200 box)
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback (no cross-proc lock)
    fcntl = None  # type: ignore

# lifecycle states; TERMINAL states never transition again
QUEUED = "queued"
PLANNING = "planning"
RUNNING = "running"
DONE = "done"
BLOCKED = "blocked"
FAILED = "failed"
INTERRUPTED = "interrupted"
TERMINAL: frozenset[str] = frozenset({DONE, BLOCKED, FAILED, INTERRUPTED})

STATUS_NAME = "run_status.json"
_LOCK_NAME = "run_status.json.lock"


def status_path(run_dir: str | Path) -> Path:
    """Path to the run's status file."""
    return Path(run_dir) / STATUS_NAME


def read_status(run_dir: str | Path) -> Optional[dict]:
    """Read the status record, or None when absent/unreadable (a partially
    written file is never observed because writes are atomic `os.replace`)."""
    p = status_path(run_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _locked_update(run_dir: str | Path,
                   fn: Callable[[dict], Optional[dict]]) -> Optional[dict]:
    """Read-modify-write the status file under an exclusive advisory lock.

    `fn` receives the current record (``{}`` if none) and returns the fields to
    merge, or None to leave the file untouched. Holding the lock across the whole
    read+decide+write is what lets a reconciler safely check "still non-terminal?"
    and write in one critical section without racing another reconciler. The
    write itself is a tmp-file + `os.replace` so readers never see a torn file.
    Returns the new record, or the current one when `fn` opts out."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = run_dir / _LOCK_NAME
    with open(lock, "w", encoding="utf-8") as lf:
        if fcntl is not None:
            fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            cur = read_status(run_dir) or {}
            updates = fn(cur)
            if updates is None:
                return cur or None
            now = time.time()
            new = {**cur, **updates, "updated": now}
            new.setdefault("created", now)
            tmp = run_dir / f".{STATUS_NAME}.{os.getpid()}.tmp"
            tmp.write_text(json.dumps(new, indent=2, default=str), encoding="utf-8")
            os.replace(tmp, status_path(run_dir))
            return new
        finally:
            if fcntl is not None:
                fcntl.flock(lf, fcntl.LOCK_UN)


# ── writers ───────────────────────────────────────────────────────────────────
def init_queued(run_dir: str | Path, *, run_id: str, owner_server_id: str,
                owner_server_pid: int) -> dict:
    """Server-side initial write (before the child exists): `queued` + the
    ownership stamps used later for reconciliation. `child_pid` starts null."""
    return _locked_update(run_dir, lambda _cur: {
        "run_id": run_id, "state": QUEUED,
        "owner_server_id": owner_server_id, "owner_server_pid": int(owner_server_pid),
        "child_pid": None, "note": "",
    })  # type: ignore[return-value]


def mark_child_started(run_dir: str | Path, *, child_pid: int,
                       state: str = PLANNING) -> dict:
    """The child's FIRST write: record its own pid and enter `planning`. Doing
    this first (rather than the parent recording the pid after Popen) keeps the
    single-writer invariant — the parent never writes while the child lives."""
    return _locked_update(run_dir, lambda _cur: {
        "child_pid": int(child_pid), "state": state,
    })  # type: ignore[return-value]


def mark(run_dir: str | Path, state: str, *, note: str = "") -> dict:
    """Child-side transition to `state` (running, or a terminal state). Ownership
    fields are preserved by the merge in `_locked_update`."""
    upd: dict[str, Any] = {"state": state}
    if note:
        upd["note"] = note
    return _locked_update(run_dir, lambda _cur: upd)  # type: ignore[return-value]


# ── liveness ──────────────────────────────────────────────────────────────────
def pid_alive(pid: Optional[int]) -> bool:
    """True if `pid` names a live process. `os.kill(pid, 0)` probes without
    signalling; PermissionError means it exists but is owned by another user."""
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OverflowError, ValueError):
        return False
    return True


def _servers_dir(run_root: str | Path) -> Path:
    """Directory of per-server liveness tokens under the run root."""
    return Path(run_root) / "servers"


def register_server(run_root: str | Path, server_id: str, pid: int) -> None:
    """Write this server's liveness token (`servers/<id>` -> pid). Best-effort:
    liveness failures should never crash a server."""
    d = _servers_dir(run_root)
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / server_id).write_text(str(int(pid)), encoding="utf-8")
    except OSError:
        pass


def unregister_server(run_root: str | Path, server_id: str) -> None:
    """Remove this server's liveness token on graceful shutdown (best-effort)."""
    try:
        (_servers_dir(run_root) / server_id).unlink()
    except OSError:
        pass


def server_alive(run_root: str | Path, server_id: Optional[str]) -> bool:
    """True when the server's token exists and its pid is live. (pid reuse can
    in theory give a false positive; graceful shutdown removes the token, and
    reconciliation only ever *delays*, never corrupts, in that rare case.)"""
    if not server_id:
        return False
    token = _servers_dir(run_root) / server_id
    try:
        pid = int(token.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    return pid_alive(pid)


# ── reconciliation ────────────────────────────────────────────────────────────
def reconcile_after_wait(run_dir: str | Path, *, note: str = "") -> Optional[dict]:
    """Called by the launching parent immediately after `Popen.wait()` — the
    child is already reaped, so we are the sole writer. If the run is still
    non-terminal (the child died before writing a terminal state, e.g. SIGKILL),
    mark it `interrupted`. A run that terminated cleanly is left as-is."""
    def _fn(cur: dict) -> Optional[dict]:
        if not cur or cur.get("state") in TERMINAL:
            return None
        return {"state": INTERRUPTED,
                "note": note or "child exited without a terminal status"}
    return _locked_update(run_dir, _fn)


def reconcile_if_dead(run_dir: str | Path, run_root: str | Path) -> Optional[dict]:
    """Ownership-aware reconciliation for any server (lazy at read, at startup,
    or from a periodic sweep). Marks a non-terminal run `interrupted` **only**
    when its owning server is confirmed dead AND its child is dead/absent — so a
    live owner's `queued`/`running` run is never touched. The terminal check and
    the write share the lock, so two reconcilers can't both act."""
    def _fn(cur: dict) -> Optional[dict]:
        if not cur or cur.get("state") in TERMINAL:
            return None
        if server_alive(run_root, cur.get("owner_server_id")):
            return None  # the owner is alive; its worker/child still governs
        if pid_alive(cur.get("child_pid")):
            return None  # child still running; it will write its own terminal
        return {"state": INTERRUPTED,
                "note": "owner server and child both dead — reconciled"}
    return _locked_update(run_dir, _fn)


def startup_reconcile(run_root: str | Path) -> int:
    """Sweep every run dir once at server startup, reconciling dead-owner runs.
    Returns the count reconciled. A backstop for runs orphaned by a server death
    before any later poll would trigger the lazy path."""
    root = Path(run_root)
    if not root.exists():
        return 0
    n = 0
    for run_dir in root.glob("run-*"):
        if not run_dir.is_dir():
            continue
        res = reconcile_if_dead(run_dir, run_root)
        if res and res.get("state") == INTERRUPTED:
            n += 1
    return n
