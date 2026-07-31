"""Commit-and-push-to-CI orchestration — port of `92_push_to_ci.sh`'s
deterministic core (the pre-commit auto-fix workflow is injectable; its agent
wiring lands with the assembly PR).

Sequence (each behavior pinned by test):
1. Preflights, fail-closed: the target upstream commit must be a resolved
   40-hex SHA (pushing with an unresolved target bakes "unknown" into the
   commit AND leaves the CI Dockerfile pinned to a stale wheel — the code
   rebases forward while CI installs the OLD upstream, repo-wide
   ImportErrors), and the CI Dockerfile pin must match that commit.
2. WAL re-entry hygiene: unresolved prior intents for this destination are
   reconciled first — a landed one is acknowledged, an escalation refuses
   the push; an already-pushed record under this op_id makes resume
   idempotent.
3. Stage everything, unstage generated outputs; commit (signed, retried
   with the SAME exclusions) only when there is something to commit.
4. AUTHORIZATION is never self-granted: the caller passes `allowed` (the
   task/adapter governance verdict) and `allow_push` (the ALLOW_PUSH env
   gate) — C4's double gate. `push.guard_push` rules; without `allow_push`
   the flow stops before the WAL as a dry-run reporting the exact
   authorized command. Execution derives its arguments from the authorized
   command itself (`gitio.execute_push`).
5. One canonical transport: the remote URL is resolved (token/SSH→HTTPS)
   BEFORE the pre-push probe, and probe, push, and the WAL's canonical
   remote identity all use it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from ..push import PushPolicy, guard_push
from . import gitio, push_wal
from .wheel import PinSpec, is_pinned


def _log(msg: str) -> None:
    print(f"[push_to_ci] {msg}", flush=True)


class PushPreflightError(RuntimeError):
    """A fail-closed preflight refused the push."""


@dataclass(frozen=True)
class PushOutcome:
    pushed: bool
    pushed_commit: str = ""
    committed: bool = False
    dry_run: bool = False
    reason: str = ""


def preflight_upstream_commit(commit: str) -> str:
    commit = (commit or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise PushPreflightError(
            f"refusing to push: target upstream commit is missing or not a "
            f"40-hex SHA (got {commit!r}); re-run the wheel picker first")
    return commit


def preflight_dockerfile_pin(repo: Path, commit: str, pin: PinSpec) -> None:
    path = Path(repo) / pin.dockerfile
    if not path.is_file():
        return  # parent parity: a missing CI Dockerfile is not this gate's job
    if not is_pinned(path.read_text(encoding="utf-8"), commit, pin):
        raise PushPreflightError(
            f"refusing to push: {pin.dockerfile} wheel pin does not match the "
            f"resolved upstream commit {commit[:12]}; re-run the pin step")


def commit_and_push(repo: Path, *,
                    upstream_commit: str,
                    pin: PinSpec,
                    branch: str,
                    message_template: str,
                    unstage_globs: Sequence[str],
                    author_name: str, author_email: str,
                    protected_branches: Sequence[str],
                    wal_dir: Path, op_id: str,
                    allowed: bool = False,
                    allow_push: bool = False,
                    remote: str = "origin",
                    token: str = "",
                    rebase_performed: bool = False,
                    extra_commit_flags: Sequence[str] = (),
                    commit_retries: int = 3,
                    push_retries: int = 3,
                    push_base_delay: float = 5.0,
                    precommit_fix: Callable[[], None] | None = None,
                    run: gitio.RunFn = gitio._run,
                    sleep: Callable[[float], None] = None,
                    log: Callable[[str], None] = _log) -> PushOutcome:
    """The full deterministic push-to-CI flow. `allowed` and `allow_push`
    arrive from the caller's governance (task spec / adapter policy and the
    ALLOW_PUSH env flag) — this function NEVER self-authorizes. Raises
    `PushPreflightError` on a refused preflight; returns a non-pushed
    `PushOutcome` with the reason when authorization, reconciliation, or
    execution refuses."""
    import time as _time
    sleep = sleep or _time.sleep
    repo = Path(repo)
    commit = preflight_upstream_commit(upstream_commit)
    preflight_dockerfile_pin(repo, commit, pin)
    dest_ref = f"refs/heads/{branch}"

    # re-entry hygiene BEFORE any new work: unresolved intents settle first
    pending = push_wal.resolve_pending(repo, wal_dir, remote_name=remote,
                                       dest_ref=dest_ref, token=token, run=run)
    if pending == "escalate":
        return PushOutcome(False, reason="unresolved push intent for "
                                         f"{dest_ref} escalated — human "
                                         "review required, not retrying")

    gitio.stage_commit_changes(repo, unstage_globs, run=run)
    committed = False
    if gitio.has_staged_changes(repo, run=run) or extra_commit_flags:
        message = message_template.format(commit=commit, short=commit[:12])
        if not gitio.run_signed_commit(
                repo, message, author_name=author_name,
                author_email=author_email, retries=commit_retries,
                extra_flags=extra_commit_flags, unstage_patterns=unstage_globs,
                precommit_fix=precommit_fix, run=run, log=log):
            return PushOutcome(False, reason=f"commit failed after "
                                             f"{commit_retries} attempts")
        committed = True
    else:
        log("No new changes to commit. Pushing current HEAD.")

    head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    # resume semantics per prior record under this op_id:
    # pushed+same-head ⇒ idempotent no-op; intent+same-head ⇒ resume THAT
    # record (a crash between record_intent and push; resolve_pending above
    # already proved it reconciles to retry, and re-recording would trip the
    # overwrite guard while a fresh op_id would orphan it into a later false
    # escalation); anything else ⇒ a different push needs a fresh op_id.
    all_records = push_wal.load_records(wal_dir)
    prior = next((r for r in all_records if r.op_id == op_id), None)
    resumed = None
    same_op_shape = (prior is not None and prior.dest_ref == dest_ref
                     and prior.remote_name == remote
                     and prior.repo_root == str(repo))
    if prior is not None:
        # idempotent success needs the COMPLETE operation identity to match
        # — a reused op_id pointing at another branch/remote/repo must not
        # falsely report that destination as pushed
        if (prior.state == "pushed" and prior.intended_oid == head
                and same_op_shape):
            log(f"op {op_id} already pushed {head[:12]}; nothing to do.")
            return PushOutcome(True, pushed_commit=head, committed=committed)
        if (prior.state == "intent" and prior.intended_oid == head
                and same_op_shape):
            log(f"op {op_id} has an unfinished intent for {head[:12]}; "
                "resuming it.")
            resumed = prior
        else:
            return PushOutcome(False, committed=committed,
                               reason=f"op_id {op_id!r} already has a record "
                                      "for a different push — use a fresh "
                                      "op_id")

    # one canonical transport for probe, WAL identity, and push — resolved
    # ONCE; execution receives this exact URL so a concurrent `remote
    # set-url` cannot redirect the push after the probe
    url = gitio.resolve_push_url(repo, remote=remote, token=token, run=run)
    if resumed is not None and gitio.canonical_remote_identity(url) != \
            resumed.remote_url:
        return PushOutcome(False, committed=committed,
                           reason="remote identity changed since the "
                                  "unfinished intent was recorded — escalate")
    remote_oid = push_wal.remote_ref_oid(repo, url, dest_ref, token=token,
                                         run=run)
    if resumed is not None:
        # a resumed intent is bound to its RECORDED world: the remote must
        # still be at the recorded pre-push tip (complete the push, leased
        # to that exact tip) or already at the intended one (it landed) —
        # any other OID appeared between reconciliation and this probe and
        # overwriting it under a fresh lease would destroy a third party's
        # update
        if remote_oid == resumed.intended_oid:
            push_wal.mark_pushed(wal_dir, resumed)
            log(f"op {op_id}: the recorded push already landed; acknowledged.")
            return PushOutcome(True, pushed_commit=head, committed=committed)
        if remote_oid != resumed.pre_push_oid:
            return PushOutcome(False, committed=committed,
                               reason="remote moved since the unfinished "
                                      "intent was recorded — escalate")
    lease_expect = ""
    pre_push_oid = push_wal.ABSENT
    if remote_oid != push_wal.ABSENT:
        pre_push_oid = remote_oid
        if rebase_performed or resumed is not None:
            # resumed pushes are ALWAYS leased to the recorded pre-push tip
            lease_expect = remote_oid

    policy = PushPolicy(allowed=allowed, remote=remote, branch=branch,
                        force_with_lease=bool(lease_expect),
                        lease_expect=lease_expect,
                        create_only=(remote_oid == push_wal.ABSENT))
    decision = guard_push(policy, list(protected_branches))
    if not decision.allowed:
        return PushOutcome(False, committed=committed,
                           reason=f"push denied: {decision.reason}")
    if not allow_push:
        log(f"[dry-run] ALLOW_PUSH not set; would run: "
            f"{' '.join(decision.command)}")
        return PushOutcome(False, committed=committed, dry_run=True,
                           reason="dry-run: ALLOW_PUSH not set")

    if resumed is not None:
        record = resumed   # the durable intent already exists; do not touch
    else:
        # a NEW operation for this destination durably retires any remaining
        # retryable intents (different push, fresh op_id): left as `intent`,
        # they would later see neither their pre-push nor intended OID and
        # surface as a permanent false escalation
        for stale in all_records:
            if (stale.state == "intent" and stale.op_id != op_id
                    and stale.dest_ref == dest_ref
                    and stale.remote_name == remote):
                push_wal.mark_superseded(wal_dir, stale)
                log(f"op {stale.op_id}: retryable intent superseded by "
                    f"{op_id}.")
        record = push_wal.PushRecord(
            op_id=op_id, repo_root=str(repo), remote_name=remote,
            remote_url=gitio.canonical_remote_identity(url),
            dest_ref=dest_ref, pre_push_oid=pre_push_oid, intended_oid=head)
        push_wal.record_intent(wal_dir, record)

    if lease_expect:
        log(f"Push: using --force-with-lease={branch}:{lease_expect[:12]}")
    elif remote_oid == push_wal.ABSENT:
        # Deliberate divergence from the parent's raw --force here: creation
        # runs under an ABSENCE-pinned lease (--force-with-lease=<branch>:)
        # so a branch created by someone else in the observe-to-push race
        # fails the push closed instead of being silently fast-forwarded.
        log(f"Push: remote branch {branch} does not exist — create-only "
            "(absence-pinned lease)")

    ok = gitio.execute_push(decision, repo, url=url, token=token,
                            retries=push_retries, base_delay=push_base_delay,
                            run=run, sleep=sleep, log=log)
    if not ok:
        return PushOutcome(False, committed=committed,
                           reason="git push failed after retries")
    push_wal.mark_pushed(wal_dir, record)
    log(f"Pushed commit: {head[:12]} to {remote}/{branch}")
    return PushOutcome(True, pushed_commit=head, committed=committed)
