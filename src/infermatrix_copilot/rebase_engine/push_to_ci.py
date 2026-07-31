"""Commit-and-push-to-CI orchestration — port of `92_push_to_ci.sh`'s
deterministic core (the pre-commit auto-fix workflow is injectable; its agent
wiring lands with the assembly PR).

Sequence (each behavior pinned by test):
1. Preflights, fail-closed: the target upstream commit must be a resolved
   40-hex SHA (pushing with an unresolved target bakes "unknown" into the
   commit AND leaves the CI Dockerfile pinned to a stale wheel — the code
   rebases forward while CI installs the OLD upstream, repo-wide
   ImportErrors), and the CI Dockerfile pin must match that commit.
2. Stage everything, unstage generated outputs; commit (signed, retried)
   only when there is something to commit.
3. AUTHORIZATION through `push.guard_push` (constraint C4) with an optional
   SHA-pinned lease when history was rewritten; write the WAL intent; then
   EXECUTE via gitio; mark the WAL record pushed on acceptance.
"""

from __future__ import annotations

import re
import subprocess
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
    """The full deterministic push-to-CI flow. Raises `PushPreflightError` on
    a refused preflight; returns a non-pushed `PushOutcome` with the denial
    reason when authorization or execution fails."""
    import time as _time
    sleep = sleep or _time.sleep
    repo = Path(repo)
    commit = preflight_upstream_commit(upstream_commit)
    preflight_dockerfile_pin(repo, commit, pin)

    gitio.stage_commit_changes(repo, unstage_globs, run=run)
    committed = False
    r = run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    if r.returncode != 0 or extra_commit_flags:
        message = message_template.format(commit=commit, short=commit[:12])
        if not gitio.run_signed_commit(
                repo, message, author_name=author_name,
                author_email=author_email, retries=commit_retries,
                extra_flags=extra_commit_flags, precommit_fix=precommit_fix,
                run=run, log=log):
            return PushOutcome(False, reason=f"commit failed after "
                                             f"{commit_retries} attempts")
        committed = True
    else:
        log("No new changes to commit. Pushing current HEAD.")

    head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    # After a history rewrite, pin the lease to the exact remote tip we
    # fetched — an unqualified lease still races remote movement.
    lease_expect = ""
    pre_push_oid = push_wal.ABSENT
    remote_oid = push_wal.remote_ref_oid(repo, remote,
                                         f"refs/heads/{branch}", run=run)
    if remote_oid != push_wal.ABSENT:
        pre_push_oid = remote_oid
        if rebase_performed:
            lease_expect = remote_oid

    policy = PushPolicy(allowed=True, remote=remote, branch=branch,
                        force_with_lease=rebase_performed and bool(lease_expect),
                        lease_expect=lease_expect)
    decision = guard_push(policy, list(protected_branches))
    if not decision.allowed:
        return PushOutcome(False, committed=committed,
                           reason=f"push denied: {decision.reason}")

    url = gitio.resolve_push_url(repo, remote=remote, token=token, run=run)
    record = push_wal.PushRecord(
        op_id=op_id, repo_root=str(repo), remote_name=remote,
        remote_url=gitio.credential_free_url(url),
        dest_ref=f"refs/heads/{branch}", pre_push_oid=pre_push_oid,
        intended_oid=head)
    push_wal.record_intent(wal_dir, record)

    extra_args = []
    if rebase_performed:
        if lease_expect:
            extra_args.append(f"--force-with-lease={branch}:{lease_expect}")
            log(f"Push: using --force-with-lease={branch}:{lease_expect[:12]}")
        else:
            # Deliberate divergence from the parent, which used raw --force
            # here: a branch that does not exist on the remote is CREATED by
            # a plain push — force adds nothing except a C4 violation. If the
            # branch appears in the ls-remote→push race, the plain push is
            # rejected non-fast-forward and the run fails closed.
            log(f"Push: remote branch {branch} does not exist yet — "
                "plain push creates it")

    ok = gitio.execute_push(decision, repo, url=url, refspec=f"HEAD:{branch}",
                            extra_args=extra_args, token=token,
                            retries=push_retries, base_delay=push_base_delay,
                            run=run, sleep=sleep, log=log)
    if not ok:
        return PushOutcome(False, committed=committed,
                           reason="git push failed after retries")
    push_wal.mark_pushed(wal_dir, record)
    log(f"Pushed commit: {head[:12]} to {remote}/{branch}")
    return PushOutcome(True, pushed_commit=head, committed=committed)
