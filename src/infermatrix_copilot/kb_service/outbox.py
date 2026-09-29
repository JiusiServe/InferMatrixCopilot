"""The signed hand-off between the knowledge service and the GPU-box publisher.

The service holds no GitHub write credential. Every GitHub write is an outbox
item the service signs; the publisher (on another host, with the owner's ``gh``
login) pulls items over SSH, re-checks them and performs them. Layout under the
service state directory::

    outbox/<id>.json      signed item (purpose kb-outbox-item)
    outbox/control.json   signed control record, refreshed every minute
    inbox/acks/<id>.json  the publisher's result for an item
    public/holds.json     signed hold list, served read-only over HTTP; the
                          kb-gate verifier fails knowledge segments it names

Staleness is enforced on both sides. Each item carries the repository's and the
global generation at issue time and an expiry; any pause, circuit break,
rollback or switch to shadow bumps a generation, so everything issued before it
is void when the publisher next runs (``pause`` and ``close`` excepted: they only
ever stop things). The publisher also refuses to act on a control record older
than ``CONTROL_MAX_AGE``.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from ..knowledge_service.signing import canonical_json, sign, verify

ITEM_KINDS = (
    "open_pr", "open_companion_pr", "post_verdict", "enqueue",
    "update_branch", "pause", "close", "open_issue", "merge", "post_findings",
)
ALWAYS_EXECUTABLE = frozenset({"pause", "close"})
ITEM_TTL = {
    "open_pr": 24 * 3600, "open_companion_pr": 24 * 3600,
    "post_verdict": 30 * 60, "enqueue": 30 * 60, "merge": 30 * 60, "post_findings": 24 * 3600,
    "update_branch": 24 * 3600, "pause": 24 * 3600, "close": 24 * 3600,
    "open_issue": 7 * 24 * 3600,
}
CONTROL_MAX_AGE = 10 * 60
HOLDS_MAX_AGE = 10 * 60


class OutboxError(RuntimeError):
    """An item is invalid, stale, or must not be executed."""


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical_json(data))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


@dataclass(frozen=True)
class OutboxItem:
    id: str
    kind: str
    repo: str
    generation: int
    global_generation: int
    issued_at: float
    expires_at: float
    body: dict

    def to_payload(self) -> dict:
        return {
            "id": self.id, "kind": self.kind, "repo": self.repo,
            "generation": self.generation, "global_generation": self.global_generation,
            "issued_at": self.issued_at, "expires_at": self.expires_at, "body": self.body,
        }

    @classmethod
    def from_payload(cls, payload: Any) -> "OutboxItem":
        if not isinstance(payload, dict) or set(payload) != {
            "id", "kind", "repo", "generation", "global_generation", "issued_at", "expires_at", "body",
        }:
            raise OutboxError("outbox item payload has the wrong fields")
        if payload["kind"] not in ITEM_KINDS:
            raise OutboxError(f"unknown outbox item kind: {payload['kind']}")
        if not isinstance(payload["body"], dict):
            raise OutboxError("outbox item body must be a mapping")
        return cls(
            id=str(payload["id"]), kind=str(payload["kind"]), repo=str(payload["repo"]),
            generation=int(payload["generation"]), global_generation=int(payload["global_generation"]),
            issued_at=float(payload["issued_at"]), expires_at=float(payload["expires_at"]),
            body=payload["body"],
        )


class Outbox:
    """Service side: write signed items, control records, holds; read acks."""

    def __init__(self, state_dir: str | Path, key, ledger, *, clock):
        self.root = Path(state_dir)
        self._key = key
        self._ledger = ledger
        self._clock = clock
        self._local = threading.local()  # re-entrancy is per thread, never shared

    @contextmanager
    def publication_lock(self) -> Iterator[None]:
        """Interprocess lock around every "read ledger state -> sign -> write"
        publication, and around state transitions that must be published
        atomically (pause/resume). Without it a refresh that read the state
        before a pause could overwrite the pause's newer control record."""
        depth = getattr(self._local, "depth", 0)
        if depth:
            self._local.depth = depth + 1
            try:
                yield
            finally:
                self._local.depth -= 1
            return
        self.root.mkdir(parents=True, exist_ok=True)
        # a fresh descriptor per acquisition: flock excludes other descriptors
        # (other threads and processes) and is released when this one closes
        fd = os.open(self.root / ".publish.lock", os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            self._local.depth = 1
            try:
                yield
            finally:
                self._local.depth = 0
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    @property
    def outbox_dir(self) -> Path:
        return self.root / "outbox"

    @property
    def acks_dir(self) -> Path:
        return self.root / "inbox" / "acks"

    @property
    def holds_path(self) -> Path:
        return self.root / "public" / "holds.json"

    def issue(self, repo: str, kind: str, body: dict) -> OutboxItem:
        if kind not in ITEM_KINDS:
            raise OutboxError(f"unknown outbox item kind: {kind}")
        state = self._ledger.repo_state(repo)
        now = self._clock()
        item = OutboxItem(
            id=f"{int(now)}-{uuid.uuid4().hex[:12]}", kind=kind, repo=repo,
            generation=int(state["generation"]),
            global_generation=int(self._ledger.repo_state("*")["generation"]),
            issued_at=now, expires_at=now + ITEM_TTL[kind], body=body,
        )
        envelope = sign("kb-outbox-item", item.to_payload(), self._key)
        digest = hashlib.sha256(canonical_json(envelope)).hexdigest()
        self._ledger.record_outbox(item.id, repo, kind, item.generation, item.expires_at, digest)
        atomic_write_json(self.outbox_dir / f"{item.id}.json", envelope)
        return item

    def _control_payload(self) -> dict:
        repos = {
            row["repo"]: {"generation": int(row["generation"]), "mode": row["mode"],
                          "paused": bool(row["paused"])}
            for row in self._ledger.all_repo_states()
        }
        return {"issued_at": self._clock(), "repos": repos}

    def refresh_control(self) -> dict:
        with self.publication_lock():
            payload = self._control_payload()
            atomic_write_json(self.outbox_dir / "control.json", sign("kb-control", payload, self._key))
            return payload

    def transition(self, change, *, public_repos: set[str]) -> Any:
        """Apply a ledger state change (pause/resume/mode) and republish the
        control record and hold list, all under the publication lock."""
        with self.publication_lock():
            result = change()
            self.refresh_control()
            sequence = int(self._ledger.get_cursor("*", "holds_sequence") or 0) + 1
            self._ledger.set_cursor("*", "holds_sequence", str(sequence))
            self.publish_holds(sequence=sequence, public_repos=public_repos)
            return result

    def publish_holds(self, *, sequence: int, public_repos: set[str]) -> dict:
        """Signed hold list: paused repositories and PRs whose change sets are
        paused. It is served publicly, so ONLY repositories in ``public_repos``
        (public upstreams) may appear; a private upstream's name, pause state
        or PRs never do (it publishes nothing, so it has no PR to hold)."""
        with self.publication_lock():
            return self._publish_holds(sequence, frozenset(public_repos))

    def _publish_holds(self, sequence: int, public_repos: frozenset[str]) -> dict:
        states = [row for row in self._ledger.all_repo_states()
                  if row["repo"] == "*" or row["repo"] in public_repos]
        paused = [row["repo"] for row in states if row["paused"] and row["repo"] != "*"]
        global_hold = any(row["repo"] == "*" and row["paused"] for row in states)
        prs = sorted({
            int(cs["pr_number"])
            for row in states if row["repo"] != "*"
            for cs in self._ledger.changesets(row["repo"], ("paused",))
            if cs["pr_number"] is not None
        })
        payload = {"issued_at": self._clock(), "sequence": sequence, "global": global_hold,
                   "repos": sorted(paused), "prs": prs}
        atomic_write_json(self.holds_path, sign("kb-holds", payload, self._key))
        return payload

    def collect_acks(self, public_key) -> list[dict]:
        """Read publisher acks (signed by the PUBLISHER's key), record them, remove the files."""
        results = []
        if not self.acks_dir.is_dir():
            return results
        for path in sorted(self.acks_dir.glob("*.json")):
            try:
                payload = verify("kb-ack", json.loads(path.read_text(encoding="utf-8")), public_key)
                item_id = str(payload["item_id"])
                status = "acked" if payload.get("ok") else "rejected"
                self._ledger.ack_outbox(item_id, status, payload)
                results.append(payload)
            except Exception as exc:  # malformed or forged ack: keep for inspection
                path.rename(path.with_suffix(".invalid"))
                results.append({"invalid": path.name, "error": str(exc)})
                continue
            path.unlink()
            (self.outbox_dir / f"{item_id}.json").unlink(missing_ok=True)
        return results


# -- publisher side --------------------------------------------------------------

def check_item(envelope: Any, control_envelope: Any, public_key, *, now: float,
               repo_publishes: bool, repo_auto_merge: bool) -> OutboxItem:
    """What the publisher runs before ANY write. Raises ``OutboxError`` if the
    item must not be executed; returns the verified item otherwise."""
    control = verify("kb-control", control_envelope, public_key)
    if now - float(control["issued_at"]) > CONTROL_MAX_AGE:
        raise OutboxError("control record is stale; the service may be down — doing nothing")
    item = OutboxItem.from_payload(verify("kb-outbox-item", envelope, public_key))
    repos = control["repos"]
    if item.repo not in repos:
        raise OutboxError(f"control record does not know repo {item.repo}")
    if item.kind in ALWAYS_EXECUTABLE:
        return item
    if now > item.expires_at:
        raise OutboxError("item expired")
    current = repos[item.repo]
    if item.generation != current["generation"] or item.global_generation != repos["*"]["generation"]:
        raise OutboxError("item was issued before a pause, rollback or mode change (stale generation)")
    if current["paused"] or repos["*"]["paused"]:
        raise OutboxError("repository is paused")
    if not repo_publishes:
        raise OutboxError("repository has a private upstream: nothing may be published")
    # shadow records what it WOULD do and publishes nothing; a disabled repo
    # does nothing. Only an auto_merge repository gets non-stop GitHub writes,
    # and both the signed control record and the publisher's own copy of the
    # adapter configuration must say so.
    if current["mode"] != "auto_merge" or not repo_auto_merge:
        raise OutboxError(f"repository is not in auto_merge mode (control: {current['mode']})")
    return item


def verify_holds(envelope: Any, public_key, *, now: float) -> dict:
    """Used by the kb-gate verifier: a stale or unverifiable hold list fails closed."""
    holds = verify("kb-holds", envelope, public_key)
    if now - float(holds["issued_at"]) > HOLDS_MAX_AGE:
        raise OutboxError("hold list is stale")
    return holds
