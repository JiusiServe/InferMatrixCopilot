"""Git commit/push mechanics for rebase runs — port of `lib/git_helpers.sh`
(+ the staging discipline of `92_push_to_ci.sh`).

Repo-neutral: generated-output patterns and the commit identity arrive as
data. AUTHORIZATION is not here — every push must be ruled on by
`push.guard_push` first (constraint C4); this module only stages, commits,
and EXECUTES an allowed decision, and `execute_push` refuses anything else
fail-closed.

Ported behaviors (each pinned by test):
- generated outputs are unstaged after `git add -A`, never committed;
- signed commits retry: a ruff-format hook that edits files fails the first
  attempt, the formatter is re-run, everything restaged, and the commit
  retried up to the bound;
- pushes run in a sanitized env (IDE askpass/credential helpers stripped,
  terminal prompts off) with optional token auth via `http.extraheader`,
  and an SSH origin is rewritten to HTTPS when a token is present (SSH
  would bypass the header entirely);
- push retries back off exponentially and abort immediately on
  auth/permission failures.
"""

from __future__ import annotations

import base64
import fnmatch
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from ..push import PushDecision


def _log(msg: str) -> None:
    print(f"[gitio] {msg}", flush=True)


class GitIOError(RuntimeError):
    """A commit/push mechanical step failed after its bounded retries."""


RunFn = Callable[..., "subprocess.CompletedProcess[str]"]


def _run(cmd: list[str], *, cwd: Path | None = None,
         env: Mapping[str, str] | None = None,
         timeout: float = 600.0) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                          env=dict(env) if env is not None else None,
                          capture_output=True, text=True, errors="replace",
                          timeout=timeout, check=False)


# -- staging -------------------------------------------------------------------

def unstage_generated_outputs(repo: Path, patterns: Sequence[str], *,
                              run: RunFn = _run) -> list[str]:
    """Remove staged entries matching any generated-output glob (fnmatch over
    the repo-relative path — the parent's shell `case` globs are the same
    family) so they are never committed. Returns the unstaged paths."""
    r = run(["git", "diff", "--cached", "--name-only"], cwd=repo)
    removed: list[str] = []
    for rel in (r.stdout or "").splitlines():
        rel = rel.strip()
        if rel and any(fnmatch.fnmatch(rel, pat) for pat in patterns):
            run(["git", "reset", "-q", "HEAD", "--", f":(literal){rel}"],
                cwd=repo)
            removed.append(rel)
    return removed


def stage_commit_changes(repo: Path, patterns: Sequence[str], *,
                         run: RunFn = _run) -> list[str]:
    """`git add -A` then drop generated outputs from the index."""
    run(["git", "add", "-A"], cwd=repo)
    return unstage_generated_outputs(repo, patterns, run=run)


def staged_or_dirty(repo: Path, *, run: RunFn = _run) -> bool:
    """True when there is anything to commit (worktree or index)."""
    dirty = run(["git", "diff", "--quiet", "HEAD"], cwd=repo).returncode != 0
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode != 0
    return dirty or staged


# -- signed commit with formatter-hook retry ----------------------------------

_HOOK_EDIT_RE = re.compile(
    r"ruff-format|ruff format|files were modified by this hook", re.IGNORECASE)


def run_signed_commit(repo: Path, message: str, *,
                      author_name: str, author_email: str,
                      retries: int = 3,
                      extra_flags: Sequence[str] = (),
                      precommit_fix: Callable[[], None] | None = None,
                      run: RunFn = _run,
                      log: Callable[[str], None] = _log) -> bool:
    """`git commit --signoff` under the configured identity, retrying when a
    formatter hook edited files (re-run the formatter, restage, retry).
    Returns True on success, False when the retry budget is exhausted."""
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": author_name,
                "GIT_AUTHOR_EMAIL": author_email,
                "GIT_COMMITTER_NAME": author_name,
                "GIT_COMMITTER_EMAIL": author_email})
    for attempt in range(1, max(1, retries) + 1):
        log(f"Committing with sign-off (attempt {attempt}/{retries})...")
        r = run(["git", "commit", "--signoff", *extra_flags, "-m", message],
                cwd=repo, env=env)
        if r.returncode == 0:
            return True
        output = (r.stdout or "") + (r.stderr or "")
        if _HOOK_EDIT_RE.search(output):
            log("Detected formatter hook edits; running formatter and restaging...")
            if precommit_fix is not None:
                try:
                    precommit_fix()
                except Exception:  # noqa: BLE001 - best-effort, parent `|| true`
                    pass
        run(["git", "add", "-A"], cwd=repo)
    return False


# -- clean-env push execution --------------------------------------------------

_IDE_ENV_VARS = (
    "GIT_ASKPASS", "SSH_ASKPASS",
    "VSCODE_GIT_IPC_HANDLE", "VSCODE_GIT_ASKPASS_NODE",
    "VSCODE_GIT_ASKPASS_EXTRA_ARGS", "VSCODE_GIT_ASKPASS_MAIN",
    "CURSOR_GIT_IPC_HANDLE", "CURSOR_GIT_ASKPASS_NODE",
    "CURSOR_GIT_ASKPASS_EXTRA_ARGS", "CURSOR_GIT_ASKPASS_MAIN",
)

_AUTH_FAILURE_RE = re.compile(
    r"authentication failed|403|permission denied|no anonymous write access",
    re.IGNORECASE)


def _clean_push_env() -> dict[str, str]:
    """An inherited IDE askpass helper dies with its IDE and then fails every
    push against a dead socket — strip all of them and disable prompts."""
    env = {k: v for k, v in os.environ.items() if k not in _IDE_ENV_VARS}
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "/bin/true"
    env["SSH_ASKPASS"] = "/bin/true"
    return env


def resolve_push_url(repo: Path, *, remote: str = "origin", token: str = "",
                     run: RunFn = _run) -> str:
    """The remote's URL — rewritten from SSH to HTTPS when a token is
    present, because SSH would bypass `http.extraheader` auth entirely."""
    r = run(["git", "remote", "get-url", remote], cwd=repo)
    url = (r.stdout or "").strip()
    m = re.match(r"^git@github\.com:(.+?)(\.git)?$", url)
    if token and m:
        return f"https://x-access-token:{token}@github.com/{m.group(1)}.git"
    return url


def credential_free_url(url: str) -> str:
    """Canonical remote identity for durable records: userinfo stripped."""
    return re.sub(r"^(https?://)[^@/]*@", r"\1", url)


def push_once(repo: Path, url: str, refspec: str, *,
              extra_args: Sequence[str] = (), token: str = "",
              run: RunFn = _run) -> "subprocess.CompletedProcess[str]":
    """One sanitized-env push. Token auth goes through `http.extraheader`
    (never the credential store); IDE credential helpers are disabled."""
    git_extra = ["-c", "core.askPass=", "-c", "credential.helper="]
    if token:
        b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        git_extra += ["-c", f"http.extraheader=AUTHORIZATION: basic {b64}"]
    return run(["git", *git_extra, "push", url, *extra_args, refspec],
               cwd=repo, env=_clean_push_env(), timeout=900)


def execute_push(decision: PushDecision, repo: Path, *,
                 url: str, refspec: str,
                 extra_args: Sequence[str] = (), token: str = "",
                 retries: int = 3, base_delay: float = 5.0,
                 run: RunFn = _run,
                 sleep: Callable[[float], None] = time.sleep,
                 log: Callable[[str], None] = _log) -> bool:
    """Execute an ALLOWED push decision with bounded exponential retries.
    Fail-closed belt: a non-allowed decision raises — authorization lives in
    `push.guard_push`, and nothing may execute around it. Auth/permission
    failures abort immediately (retrying cannot fix credentials)."""
    if not decision.allowed:
        raise GitIOError(f"refusing to execute a denied push: {decision.reason}")
    delay = base_delay
    for attempt in range(1, max(1, retries) + 1):
        log(f"Pushing {refspec} (attempt {attempt}/{retries})...")
        r = push_once(repo, url, refspec, extra_args=extra_args, token=token,
                      run=run)
        if r.returncode == 0:
            return True
        output = (r.stdout or "") + (r.stderr or "")
        log(output.strip().splitlines()[-1] if output.strip() else "push failed")
        if _AUTH_FAILURE_RE.search(output):
            return False
        if attempt < retries:
            log(f"Push failed; retrying in {delay:.0f}s...")
            sleep(delay)
            delay *= 2
    return False
