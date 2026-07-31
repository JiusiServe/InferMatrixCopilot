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

import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Literal

from .gitio import credential_free_url

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
    except OSError:
        pass  # same errno policy as progress.json: best-effort dir fsync


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


def remote_ref_oid(repo: Path, remote: str, dest_ref: str, *,
                   run: RunFn = _run) -> str:
    """The remote's current OID for `dest_ref`, ABSENT when the ref does not
    exist, or raises on network/remote failure (reconciliation must not
    mistake 'cannot reach the remote' for 'ref absent')."""
    r = run(["git", "ls-remote", remote, dest_ref], cwd=repo)
    if r.returncode != 0:
        raise PushWalError(f"ls-remote failed for {remote} {dest_ref}: "
                           f"{(r.stderr or '').strip()}")
    line = (r.stdout or "").strip()
    return line.split()[0] if line else ABSENT


def reconcile(repo: Path, record: PushRecord, *,
              run: RunFn = _run) -> Reconciliation:
    """Exact reconciliation of one `intent` record after a crash window.

    Identity first: the record's credential-free remote URL must still match
    the named remote — comparing OIDs against a different repository would
    'reconcile' against the wrong world, so a reconfigured remote escalates.
    Then the OID trichotomy: intended ⇒ pushed; pre-push ⇒ retry;
    anything else ⇒ escalate."""
    if record.state == "pushed":
        return "pushed"
    r = run(["git", "remote", "get-url", record.remote_name], cwd=repo)
    if r.returncode != 0:
        return "escalate"
    if credential_free_url((r.stdout or "").strip()) != record.remote_url:
        return "escalate"
    current = remote_ref_oid(repo, record.remote_name, record.dest_ref,
                             run=run)
    if current == record.intended_oid:
        return "pushed"
    if current == record.pre_push_oid:  # includes ABSENT == ABSENT
        return "retry"
    return "escalate"
