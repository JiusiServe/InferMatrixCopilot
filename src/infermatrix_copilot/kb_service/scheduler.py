"""``kb serve``: the knowledge service's scheduler.

One process holds the ledger lease for its whole life (a keeper thread renews
it). Every tick:

1. re-sign the control record and the public hold list (the publisher refuses
   to act on a control record older than 10 minutes, so a dead service stops
   all publication within that window);
2. apply the publisher's signed acks and advance each repository's merge flow;
3. per enabled, unpaused repository: intake on its interval, release sweep when
   a release (or the fallback interval) is due;
4. activate a new knowledge snapshot when the knowledge repository's main moved.

Repositories are isolated: an exception in one is recorded and the others go
on. The overturn breaker pauses a repository (and dequeues its open knowledge
PRs) when people close two of its auto-generated PRs unmerged within 24 hours.
"""

from __future__ import annotations

import json
import threading
import time
import traceback
from dataclasses import dataclass, field

from . import merge
from .activate import ActivationError, activate, activation_lock
from .audit import audit_main
from .report import flush_reports
from .external import poll_external
from .runtime import collect_events, publish, run_intake
from .sweep import UpstreamRepo, detect_release, run_sweep

OVERTURN_WINDOW = 24 * 3600
OVERTURN_LIMIT = 2


@dataclass
class Scheduler:
    rt: object
    tick_seconds: float = 60.0
    intake_every: float = 900.0
    release_every: float = 3600.0
    audit_every: float = 24 * 3600.0
    log: list[dict] = field(default_factory=list)
    _last: dict[str, float] = field(default_factory=dict)

    def _due(self, key: str, every: float) -> bool:
        now = self.rt.clock()
        if now - self._last.get(key, 0.0) >= every:
            self._last[key] = now
            return True
        return False

    def _record(self, repo: str, event: str, **detail) -> None:
        entry = {"at": self.rt.clock(), "repo": repo, "event": event, **detail}
        self.log.append(entry)
        path = self.rt.state_dir / "traces" / "scheduler.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _public_repos(self) -> set[str]:
        return {name for name, lc in self.rt.registry.items() if lc.publishes}

    def tick(self) -> None:
        rt = self.rt
        if rt.outbox is not None:
            rt.outbox.transition(lambda: None, public_repos=self._public_repos())
            if rt.publisher_public_key is not None:
                merge.apply_acks(rt, rt.outbox.collect_acks(rt.publisher_public_key))
        for lifecycle in rt.registry.values():
            if not lifecycle.enabled:
                continue
            try:
                self._repo_tick(lifecycle)
            except Exception as exc:  # isolate repositories from each other
                self._record(lifecycle.repo, "error", error=repr(exc), trace=traceback.format_exc()[-2000:])
        if self._due("audit", self.audit_every):
            try:  # every knowledge change on main must have been recorded
                for finding in audit_main(rt, self._pause):
                    self._record("*", "audit", finding=finding)
            except Exception as exc:
                self._record("*", "error", error=repr(exc), trace=traceback.format_exc()[-2000:])
        if self._due("external", self.intake_every) and not merge.is_paused(rt.ledger, "*"):
            try:  # knowledge PRs the service did not open (source 4, human approvals)
                for event in poll_external(rt):
                    self._record("*", "external", detail=event)
            except Exception as exc:
                self._record("*", "error", error=repr(exc), trace=traceback.format_exc()[-2000:])
        try:
            sha = rt.knowledge.fetch()
            with activation_lock(rt.state_dir):  # the pin cannot change under this decision
                pin = rt.ledger.get_cursor("*", "rollback_pin")
                pinned_main = json.loads(pin)["main"] if pin else None
                if pinned_main == sha:
                    pass  # rolled back away from this main: stay there until main moves on
                elif sha != rt.ledger.active_snapshot():
                    activate(rt, sha, locked=True)
                    self._record("*", "activated", snapshot=sha)
        except ActivationError as exc:
            rt.ledger.enqueue_human("*", f"snapshot activation refused: {exc}")
            self._record("*", "activation_refused", error=str(exc))
        except Exception as exc:  # a fetch failure etc. must not stop the service
            self._record("*", "activation_error", error=repr(exc))

    def _repo_tick(self, lifecycle) -> None:
        rt = self.rt
        for event in merge.advance(rt, lifecycle):
            self._record(lifecycle.repo, "merge", detail=event)
        self._overturn_breaker(lifecycle)
        if merge.is_paused(rt.ledger, lifecycle.repo):
            return
        # durable recovery: anything gated but not yet handed over (a crash or an
        # exception between staging and publishing) is published now; publish
        # is idempotent per change set
        for changeset in rt.ledger.changesets(lifecycle.repo, ("gated",)):
            status = publish(rt, lifecycle, changeset["id"])
            self._record(lifecycle.repo, "published", changeset=changeset["id"], status=status)
        if self._due(f"intake:{lifecycle.repo}", self.intake_every):
            new = collect_events(rt, lifecycle)
            changeset_id = run_intake(rt, lifecycle)
            if changeset_id:
                status = publish(rt, lifecycle, changeset_id)
                self._record(lifecycle.repo, "intake", new_events=new, changeset=changeset_id, status=status)
        if lifecycle.full_name and self._due(f"release:{lifecycle.repo}", self.release_every):
            upstream = UpstreamRepo(rt.state_dir / "upstream" / f"{lifecycle.repo}.git", lifecycle.full_name)
            sweep = detect_release(rt, lifecycle, upstream)
            if sweep is not None:
                report = run_sweep(rt, lifecycle, rt.lease_owner, sweep, upstream)
                for changeset_id in report["changesets"]:
                    publish(rt, lifecycle, changeset_id)

                self._record(lifecycle.repo, "sweep", tag=sweep["tag"], reason=sweep["reason"],
                             changesets=report["changesets"], breaker=report["breaker"])
        for run_id in flush_reports(rt, lifecycle):  # queued by settled sweeps; retried until done
            self._record(lifecycle.repo, "sweep_report", run_id=run_id)

    def _overturn_breaker(self, lifecycle) -> None:
        rt = self.rt
        # only the service's own PRs: an author closing their own PR is no overturn
        recent = [cs for cs in rt.ledger.changesets(lifecycle.repo, ("closed",))
                  if cs["kind"] != "external" and rt.clock() - float(cs["updated_at"]) < OVERTURN_WINDOW]
        state = rt.ledger.repo_state(lifecycle.repo)
        if len(recent) >= OVERTURN_LIMIT and not state["paused"]:
            self._pause(lifecycle.repo, f"overturn breaker: {len(recent)} knowledge PRs closed unmerged within 24h")

    def _pause(self, repo: str, reason: str) -> None:
        """Pause a repository ("*": all of them) and dequeue its open PRs."""
        rt = self.rt
        if rt.ledger.repo_state(repo)["paused"]:
            rt.ledger.enqueue_human(repo if repo != "*" else next(iter(rt.registry)), reason)
            return
        # publish the pause in the same locked transition as the state change,
        # so the publisher and the gate see it at once, then dequeue open PRs
        if rt.outbox is not None:
            rt.outbox.transition(lambda: rt.ledger.bump_generation(repo, pause=True, reason=reason),
                                 public_repos=self._public_repos())
        else:
            rt.ledger.bump_generation(repo, pause=True, reason=reason)
        for name in ([repo] if repo != "*" else [lc.repo for lc in rt.registry.values()]):
            merge.pause_open_prs(rt.ledger, rt.outbox, name, reason)
        rt.ledger.enqueue_human(repo if repo != "*" else next(iter(rt.registry)), reason)
        self._record(repo, "paused", reason=reason)

    def serve(self, stop: threading.Event | None = None, *, once: bool = False) -> None:
        stop = stop or threading.Event()
        with self.rt.ledger.lease() as owner:
            self.rt.lease_owner = owner
            try:
                while not stop.is_set():
                    started = time.monotonic()
                    self.tick()
                    if once:
                        return
                    stop.wait(max(1.0, self.tick_seconds - (time.monotonic() - started)))
            finally:
                self.rt.lease_owner = None
