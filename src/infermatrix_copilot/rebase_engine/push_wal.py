"""Push write-ahead log — exact crash reconciliation for rebase pushes
(plan §5.2 / Rev 8 §3.2).

Before any pipeline push, a durable record captures the FULL push identity —
repo, remote name, credential-free remote URL, destination ref — plus the
remote's pre-push OID (or ABSENT) and the intended OID. A crash between push
and acknowledgment is then exactly reconcilable by re-reading the remote:
same-as-intended ⇒ the push landed (mark it); same-as-pre-push ⇒ it did not
(retry is safe); anything else ⇒ ESCALATE, never guess. Reconciliation
refuses to compare OIDs against a DIFFERENT repository: a reconfigured
remote escalates first.

Rollback support: records are ordered; a RUNBOOK rollback walks them in
reverse, restoring `pre_push_oid` with a lease, and deletes branches that
were ABSENT before the run.
"""

from __future__ import annotations

import errno
import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Literal

from .gitio import canonical_remote_identity

ABSENT = "ABSENT"


class PushWalError(RuntimeError):
    """The WAL is unusable (corrupt record, unwritable directory)."""


@dataclass
class PushRecord:
    """One intended push, durable before the push runs."""

    op_id: str                 # unique, ordering-friendly (caller-supplied)
    repo_root: str
    remote_name: str
    remote_url: str            # credential-free canonical form
    dest_ref: str              # refs/heads/<branch>
    pre_push_oid: str          # 40-hex or ABSENT
    intended_oid: str
    state: Literal["intent", "pushed"] = "intent"
    created_at: float = field(default_factory=time.time)

    def path(self, wal_dir: Path) -> Path:
        return Path(wal_dir) / f"{self.op_id}.json"


# directories that cannot be fsynced (filesystem semantics) are tolerated;
# REAL storage failures (EIO, ENOSPC, ...) propagate — a push must never
# proceed on an intent record the disk may not actually hold (same errno
# policy as the executor's progress.json writes)
_DIR_FSYNC_TOLERATED = {errno.EINVAL, errno.ENOTSUP if hasattr(errno, "ENOTSUP")
                        else errno.EOPNOTSUPP, errno.EOPNOTSUPP,
                        errno.EACCES, errno.EPERM, errno.EISDIR, errno.EBADF}


def _durable_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError as e:
        if e.errno not in _DIR_FSYNC_TOLERATED:
            raise PushWalError(
                f"WAL directory fsync failed ({errno.errorcode.get(e.errno, e.errno)}): "
                f"the intent record's durability cannot be guaranteed") from e


def record_intent(wal_dir: Path, record: PushRecord) -> Path:
    if record.state != "intent":
        raise PushWalError("a new record must start in state=intent")
    if not re.fullmatch(r"[0-9a-f]{40}", record.intended_oid):
        raise PushWalError(f"intended_oid is not a 40-hex commit: "
                           f"{record.intended_oid!r}")
    if record.pre_push_oid != ABSENT and not re.fullmatch(
            r"[0-9a-f]{40}", record.pre_push_oid):
        raise PushWalError(f"pre_push_oid must be 40-hex or ABSENT: "
                           f"{record.pre_push_oid!r}")
    if not record.dest_ref.startswith("refs/heads/"):
        raise PushWalError(f"dest_ref must be a full branch ref: "
                           f"{record.dest_ref!r}")
    p = record.path(wal_dir)
    if p.exists():
        # an op_id is one push attempt's identity: overwriting an existing
        # record would destroy its rollback target (pre_push_oid) or erase a
        # pushed acknowledgment — resume flows must reconcile, then either
        # reuse the record untouched or mint a fresh op_id
        raise PushWalError(f"WAL record already exists for op_id "
                           f"{record.op_id!r}; reconcile it, do not overwrite")
    _durable_write(p, asdict(record))
    return p


def mark_pushed(wal_dir: Path, record: PushRecord) -> None:
    record.state = "pushed"
    _durable_write(record.path(wal_dir), asdict(record))


def load_records(wal_dir: Path) -> list[PushRecord]:
    out: list[PushRecord] = []
    wal_dir = Path(wal_dir)
    if not wal_dir.is_dir():
        return out
    for p in sorted(wal_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append(PushRecord(**data))
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            raise PushWalError(f"corrupt WAL record {p}: {e}") from e
    return out


# -- reconciliation ------------------------------------------------------------

Reconciliation = Literal["pushed", "retry", "escalate"]

RunFn = Callable[..., "subprocess.CompletedProcess[str]"]


def _run(cmd: list[str], *, cwd: Path | None = None,
         timeout: float = 120.0) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, errors="replace",
                          timeout=timeout, check=False)


def remote_ref_oid(repo: Path, remote_or_url: str, dest_ref: str, *,
                   run: RunFn = _run) -> str:
    """The remote's current OID for `dest_ref`, ABSENT when the ref does not
    exist, or raises on network/remote failure (reconciliation must not
    mistake 'cannot reach the remote' for 'ref absent'). Accepts a remote
    name OR a resolved URL — probing and pushing must use ONE transport, or
    an SSH-configured origin without SSH credentials fails the probe while
    the token-authenticated HTTPS push would have worked."""
    r = run(["git", "ls-remote", remote_or_url, dest_ref], cwd=repo)
    if r.returncode != 0:
        raise PushWalError(f"ls-remote failed for {remote_or_url} {dest_ref}: "
                           f"{(r.stderr or '').strip()}")
    line = (r.stdout or "").strip()
    return line.split()[0] if line else ABSENT


def reconcile(repo: Path, record: PushRecord, *, token: str = "",
              run: RunFn = _run) -> Reconciliation:
    """Exact reconciliation of one `intent` record after a crash window.

    Identity first (no network): the record's canonical remote identity
    (transport- and credential-independent) must still match the named
    remote — comparing OIDs against a different repository would 'reconcile'
    against the wrong world, so a reconfigured remote escalates. Then the
    OID trichotomy over the SAME token-capable transport the original
    probe/push used (an SSH origin with token-only credentials must not make
    recovery raise where the push itself worked): intended ⇒ pushed;
    pre-push ⇒ retry; anything else ⇒ escalate."""
    from .gitio import resolve_push_url

    if record.state == "pushed":
        return "pushed"
    r = run(["git", "remote", "get-url", record.remote_name], cwd=repo)
    if r.returncode != 0:
        return "escalate"
    configured = (r.stdout or "").strip()
    if canonical_remote_identity(configured) != \
            canonical_remote_identity(record.remote_url):
        return "escalate"
    url = resolve_push_url(repo, remote=record.remote_name, token=token,
                           run=run)
    current = remote_ref_oid(repo, url, record.dest_ref, run=run)
    if current == record.intended_oid:
        return "pushed"
    if current == record.pre_push_oid:  # includes ABSENT == ABSENT
        return "retry"
    return "escalate"


def resolve_pending(repo: Path, wal_dir: Path, *, remote_name: str,
                    dest_ref: str, token: str = "",
                    run: RunFn = _run) -> Reconciliation | None:
    """Re-entry hygiene: before a NEW intent for `dest_ref` is recorded,
    every unresolved prior intent for the same destination must be settled.
    A landed one is marked pushed; a clean retry poses no obstacle (the new
    intent takes over with a fresh pre-push observation); an escalation is
    returned for the caller to refuse the push. Returns the worst pending
    outcome, or None when nothing was pending."""
    worst: Reconciliation | None = None
    for rec in load_records(wal_dir):
        if rec.state != "intent":
            continue
        if rec.remote_name != remote_name or rec.dest_ref != dest_ref:
            continue
        outcome = reconcile(repo, rec, token=token, run=run)
        if outcome == "pushed":
            mark_pushed(wal_dir, rec)
        if worst is None or outcome == "escalate":
            worst = outcome
    return worst
