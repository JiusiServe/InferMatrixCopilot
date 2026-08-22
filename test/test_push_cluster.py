"""PR3 — push cluster: gitio, push WAL, lease_expect/create_only, push_to_ci.

`test_push_partial_e2e` drives the full commit-and-push flow against a real
bare remote, including WAL re-entry and crash reconciliation.
"""

from __future__ import annotations

import errno
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.push import PushDecision, PushPolicy, guard_push
from infermatrix_copilot.rebase_engine import gitio, push_to_ci, push_wal
from infermatrix_copilot.rebase_engine.push_wal import ABSENT, PushRecord
from infermatrix_copilot.rebase_engine.wheel import PinSpec

PIN = PinSpec(dockerfile="docker/Dockerfile.ci",
              url_pattern=r"wheels\.example\.ai/[0-9a-f]{40}",
              url_template="wheels.example.ai/{commit}",
              commit_env_var="PRECOMPILED_WHEEL_COMMIT")

UP = "a" * 40


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(repo), check=True, text=True,
                       capture_output=True)
    return r.stdout.strip()


def _make_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "checkout", "-q", "-B", "main")
    _git(path, "config", "user.name", "fixture")
    _git(path, "config", "user.email", "fixture@example.com")
    return path


def _commit(repo: Path, files: dict[str, str], msg: str) -> str:
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


def _push_kwargs(**over):
    kw = dict(upstream_commit=UP, pin=PIN,
              message_template="rebase: align with upstream {short}",
              unstage_globs=["*.log"], author_name="Bot",
              author_email="bot@example.com", protected_branches=["main"],
              allowed=True, allow_push=True, sleep=lambda s: None)
    kw.update(over)
    return kw


# -- gitio: staging ------------------------------------------------------------

def test_unstage_generated_outputs(tmp_path):
    repo = _make_repo(tmp_path / "r")
    _commit(repo, {"src/ok.py": "1"}, "init")
    for rel in ("src/ok.py", "run.log", "htmlcov/index.html",
                "pkg/__pycache__/m.pyc", "tests/e2e/artifacts/x.wav"):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    globs = ["*.log", "htmlcov/*", "*/__pycache__/*", "tests/*/artifacts/*"]
    removed = gitio.stage_commit_changes(repo, globs)
    staged = _git(repo, "diff", "--cached", "--name-only").splitlines()
    assert staged == ["src/ok.py"]
    assert sorted(removed) == ["htmlcov/index.html", "pkg/__pycache__/m.pyc",
                               "run.log", "tests/e2e/artifacts/x.wav"]


def test_staging_failures_raise(tmp_path):
    """A failed add/diff must never read as 'no changes' (the parent ran
    under set -e; pushing a stale HEAD on a broken index is a regression)."""
    fail = lambda cmd, **kw: SimpleNamespace(returncode=129, stdout="",
                                             stderr="fatal: broken")
    with pytest.raises(gitio.GitIOError, match="git add -A failed"):
        gitio.stage_commit_changes(tmp_path, [], run=fail)

    def add_ok_diff_bad(cmd, **kw):
        if cmd[:2] == ["git", "add"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=129, stdout="", stderr="fatal")
    with pytest.raises(gitio.GitIOError, match="diff --cached failed"):
        gitio.stage_commit_changes(tmp_path, [], run=add_ok_diff_bad)
    with pytest.raises(gitio.GitIOError, match="diff --cached --quiet"):
        gitio.has_staged_changes(tmp_path, run=fail)


# -- gitio: signed commit ------------------------------------------------------

def test_run_signed_commit_identity_and_signoff(tmp_path):
    repo = _make_repo(tmp_path / "r")
    _commit(repo, {"a.py": "1"}, "init")
    (repo / "a.py").write_text("2")
    _git(repo, "add", "-A")
    ok = gitio.run_signed_commit(repo, "test message",
                                 author_name="Sign Bot",
                                 author_email="sign@example.com")
    assert ok
    show = _git(repo, "log", "-1", "--format=%an <%ae>%n%B")
    assert "Sign Bot <sign@example.com>" in show
    assert "Signed-off-by: Sign Bot <sign@example.com>" in show


def test_run_signed_commit_retries_on_formatter_hook():
    calls = SimpleNamespace(commits=0, fixed=0, adds=0)

    def run(cmd, **kw):
        if cmd[:2] == ["git", "commit"]:
            calls.commits += 1
            if calls.commits == 1:
                return SimpleNamespace(returncode=1, stdout="",
                                       stderr="files were modified by this hook")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:2] == ["git", "add"]:
            calls.adds += 1
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    ok = gitio.run_signed_commit(
        Path("."), "m", author_name="a", author_email="b@c",
        precommit_fix=lambda: setattr(calls, "fixed", calls.fixed + 1),
        run=run)
    assert ok and calls.commits == 2 and calls.fixed == 1 and calls.adds == 1


def test_commit_retry_restage_keeps_exclusions(tmp_path):
    """The retry restage must reapply the generated-output exclusions — an
    unrestricted add -A would sweep junk into the retried commit."""
    repo = _make_repo(tmp_path / "r")
    _commit(repo, {"a.py": "1", ".pre-commit-config.yaml": "x"}, "init")
    (repo / "a.py").write_text("2")
    (repo / "sneaky.log").write_text("junk appears before the retry")
    gitio.stage_commit_changes(repo, ["*.log"])
    first = SimpleNamespace(done=False)
    real_run = gitio._run

    def run(cmd, **kw):
        if cmd[:2] == ["git", "commit"] and not first.done:
            first.done = True
            return SimpleNamespace(returncode=1, stdout="",
                                   stderr="ruff-format... files were modified "
                                          "by this hook")
        return real_run(cmd, **kw)

    ok = gitio.run_signed_commit(repo, "m", author_name="a",
                                 author_email="b@c",
                                 unstage_patterns=["*.log"], run=run)
    assert ok
    committed = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert committed == ["a.py"]          # sneaky.log excluded on the retry too


def test_run_signed_commit_exhausts_retries():
    def run(cmd, **kw):
        if cmd[:2] == ["git", "commit"]:
            return SimpleNamespace(returncode=1, stdout="boom", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    assert gitio.run_signed_commit(Path("."), "m", author_name="a",
                                   author_email="b@c", retries=2,
                                   run=run) is False


# -- gitio: URLs, identity, and push execution ---------------------------------

def test_resolve_push_url_and_canonical_identity(tmp_path):
    repo = _make_repo(tmp_path / "r")
    _git(repo, "remote", "add", "origin", "git@github.com:org/proj.git")
    # the token NEVER lands in the URL — auth rides in the header transport
    assert gitio.resolve_push_url(repo, token="tok123") == \
        "https://github.com/org/proj.git"
    assert gitio.resolve_push_url(repo) == "git@github.com:org/proj.git"
    assert gitio.apply_token_transport("git@github.com:org/proj.git", "t") == \
        "https://github.com/org/proj.git"
    # every transport/credential form of one repo → ONE identity
    forms = ["git@github.com:org/proj.git", "git@github.com:org/proj",
             "https://github.com/org/proj.git",
             "https://x-access-token:tok@github.com/org/proj.git"]
    assert {gitio.canonical_remote_identity(u) for u in forms} == \
        {"github.com/org/proj"}
    assert gitio.canonical_remote_identity("/local/path/origin.git") == \
        "/local/path/origin.git"
    # schemes are case-insensitive: a mixed-case URL must strip creds and
    # canonicalize to the same identity
    assert gitio.credential_free_url("HTTPS://user:SECRET@github.com/o/p.git") \
        == "HTTPS://github.com/o/p.git"
    assert gitio.canonical_remote_identity(
        "HTTPS://user:SECRET@GitHub.com/org/proj.git") == "github.com/org/proj"
    assert "SECRET" not in gitio.apply_token_transport(
        "HTTPS://user:SECRET@github.com/o/p.git", "tok")


def _allowed_decision(branch="ci-x", *, options=()) -> PushDecision:
    return PushDecision(True, "ok", ("git", "push", "origin",
                                     f"HEAD:{branch}", *options))


def test_execute_push_refuses_denied_decision(tmp_path):
    with pytest.raises(gitio.GitIOError, match="denied push"):
        gitio.execute_push(PushDecision(False, "nope"), tmp_path)


def test_execute_push_binds_to_authorized_command():
    """Execution takes remote/refspec/options from the DECISION — there is no
    parameter through which a caller could add --force or retarget."""
    remote, refspec, options = gitio.decision_push_args(
        _allowed_decision("ci-x", options=("--force-with-lease=ci-x:" + "b" * 40,)))
    assert (remote, refspec) == ("origin", "HEAD:ci-x")
    assert options == ["--force-with-lease=ci-x:" + "b" * 40]
    with pytest.raises(gitio.GitIOError, match="unexpected option"):
        gitio.decision_push_args(_allowed_decision(options=("--force",)))
    with pytest.raises(gitio.GitIOError, match="unrecognized authorized"):
        gitio.decision_push_args(PushDecision(True, "ok", ("git", "push")))


def test_execute_push_runs_exactly_the_decision(tmp_path):
    pushes = []

    def run(cmd, **kw):
        if cmd[:3] == ["git", "remote", "get-url"]:
            return SimpleNamespace(returncode=0, stdout="u://r\n", stderr="")
        if "push" in cmd:
            pushes.append(cmd)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(cmd)
    ok = gitio.execute_push(
        _allowed_decision("ci-x", options=("--force-with-lease=ci-x:",)),
        tmp_path, run=run, sleep=lambda s: None)
    assert ok
    (cmd,) = pushes
    assert cmd[-2:] == ["--force-with-lease=ci-x:", "HEAD:ci-x"]
    assert "u://r" in cmd and "--force" not in cmd


def test_execute_push_auth_failure_aborts_immediately(tmp_path):
    attempts = []

    def run(cmd, **kw):
        if cmd[:3] == ["git", "remote", "get-url"]:
            return SimpleNamespace(returncode=0, stdout="u://r\n", stderr="")
        attempts.append(cmd)
        return SimpleNamespace(returncode=1, stdout="",
                               stderr="remote: No anonymous write access.")
    ok = gitio.execute_push(_allowed_decision(), tmp_path, run=run,
                            sleep=lambda s: None)
    assert ok is False and len(attempts) == 1


def test_execute_push_retries_with_backoff(tmp_path):
    slept, n = [], SimpleNamespace(v=0)

    def run(cmd, **kw):
        if cmd[:3] == ["git", "remote", "get-url"]:
            return SimpleNamespace(returncode=0, stdout="u://r\n", stderr="")
        n.v += 1
        rc = 0 if n.v == 3 else 1
        return SimpleNamespace(returncode=rc, stdout="", stderr="conn reset")
    ok = gitio.execute_push(_allowed_decision(), tmp_path, retries=3,
                            base_delay=5.0, run=run, sleep=slept.append)
    assert ok is True and n.v == 3 and slept == [5.0, 10.0]


# -- guard_push: lease_expect / create_only ------------------------------------

def test_guard_push_lease_expect_and_create_only():
    sha = "b" * 40
    d = guard_push(PushPolicy(allowed=True, branch="ci-x",
                              force_with_lease=True, lease_expect=sha), ["main"])
    assert d.allowed and f"--force-with-lease=ci-x:{sha}" in d.command
    d = guard_push(PushPolicy(allowed=True, branch="ci-x",
                              force_with_lease=True), ["main"])
    assert d.allowed and "--force-with-lease" in d.command
    d = guard_push(PushPolicy(allowed=True, branch="ci-x", lease_expect=sha),
                   ["main"])
    assert not d.allowed and "lease_expect" in d.reason
    # create-only emits the ABSENCE-pinned lease
    d = guard_push(PushPolicy(allowed=True, branch="ci-x", create_only=True),
                   ["main"])
    assert d.allowed and "--force-with-lease=ci-x:" in d.command
    # create_only + a lease on an existing tip is contradictory
    d = guard_push(PushPolicy(allowed=True, branch="ci-x", create_only=True,
                              force_with_lease=True, lease_expect=sha), ["main"])
    assert not d.allowed and "create_only" in d.reason
    # protected branches stay undeniable regardless of form
    for pol in (PushPolicy(allowed=True, branch="main", force_with_lease=True,
                           lease_expect=sha),
                PushPolicy(allowed=True, branch="main", create_only=True)):
        assert not guard_push(pol, ["main"]).allowed


# -- push WAL ------------------------------------------------------------------

def _record(**kw) -> PushRecord:
    base = dict(op_id="op-001", repo_root="/r", remote_name="origin",
                remote_url="github.com/org/proj",
                dest_ref="refs/heads/ci-x", pre_push_oid="c" * 40,
                intended_oid="d" * 40)
    base.update(kw)
    return PushRecord(**base)


def test_wal_record_validation_and_overwrite_guard(tmp_path):
    with pytest.raises(push_wal.PushWalError, match="40-hex"):
        push_wal.record_intent(tmp_path, _record(intended_oid="short"))
    with pytest.raises(push_wal.PushWalError, match="40-hex or ABSENT"):
        push_wal.record_intent(tmp_path, _record(pre_push_oid="xx"))
    with pytest.raises(push_wal.PushWalError, match="full branch ref"):
        push_wal.record_intent(tmp_path, _record(dest_ref="ci-x"))
    p = push_wal.record_intent(tmp_path, _record())
    assert json.loads(p.read_text())["state"] == "intent"
    # an existing record is never overwritten — its rollback target would die
    with pytest.raises(push_wal.PushWalError, match="already exists"):
        push_wal.record_intent(tmp_path, _record(pre_push_oid="e" * 40))
    rec = _record()
    push_wal.mark_pushed(tmp_path, rec)
    assert json.loads(rec.path(tmp_path).read_text())["state"] == "pushed"
    assert [r.op_id for r in push_wal.load_records(tmp_path)] == ["op-001"]


def test_wal_dir_fsync_storage_failure_propagates(tmp_path, monkeypatch):
    """ENOSPC/EIO on the directory fsync must fail the intent write — a push
    must never proceed on an intent the disk may not hold."""
    import os as _os
    real_fsync = _os.fsync
    calls = SimpleNamespace(n=0)

    def fsync(fd):
        calls.n += 1
        if calls.n == 2:   # 1st = record file, 2nd = directory
            raise OSError(errno.ENOSPC, "no space")
        return real_fsync(fd)
    monkeypatch.setattr("os.fsync", fsync)
    with pytest.raises(push_wal.PushWalError, match="durability"):
        push_wal.record_intent(tmp_path, _record())


def test_wal_reconcile_matrix(tmp_path):
    rec = _record()

    def runner(remote_url, ls_out, ls_rc=0):
        def run(cmd, **kw):
            if cmd[:3] == ["git", "remote", "get-url"]:
                return SimpleNamespace(returncode=0, stdout=remote_url + "\n",
                                       stderr="")
            if cmd[:2] == ["git", "ls-remote"]:
                return SimpleNamespace(returncode=ls_rc, stdout=ls_out,
                                       stderr="net down" if ls_rc else "")
            raise AssertionError(cmd)
        return run

    url = "https://github.com/org/proj.git"
    ref = "refs/heads/ci-x"
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        url, f"{'d' * 40}\t{ref}\n")) == "pushed"
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        url, f"{'c' * 40}\t{ref}\n")) == "retry"
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        url, f"{'e' * 40}\t{ref}\n")) == "escalate"
    # transport change is NOT an identity change: ssh form of the same repo
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        "git@github.com:org/proj.git", f"{'d' * 40}\t{ref}\n")) == "pushed"
    # a genuinely different repository escalates before any OID logic
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        "https://github.com/other/repo.git", f"{'d' * 40}\t{ref}\n")) == \
        "escalate"
    rec2 = _record(pre_push_oid=ABSENT)
    assert push_wal.reconcile(tmp_path, rec2, run=runner(url, "")) == "retry"
    with pytest.raises(push_wal.PushWalError, match="ls-remote failed"):
        push_wal.reconcile(tmp_path, rec, run=runner(url, "", ls_rc=1))
    rec3 = _record(state="pushed")
    assert push_wal.reconcile(tmp_path, rec3,
                              run=lambda *a, **k: (_ for _ in ()).throw(
                                  AssertionError("no calls"))) == "pushed"


def test_execute_push_uses_provided_url_without_reresolving(tmp_path):
    """With a pre-probed URL supplied, the remote NAME is never consulted
    again — a concurrent `remote set-url` cannot redirect the push."""
    pushes = []

    def run(cmd, **kw):
        if cmd[:3] == ["git", "remote", "get-url"]:
            raise AssertionError("remote name must not be re-resolved")
        pushes.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    ok = gitio.execute_push(_allowed_decision(), tmp_path, url="probed://url",
                            run=run, sleep=lambda s: None)
    assert ok and "probed://url" in pushes[0]


def test_wal_reconcile_uses_token_transport_single_lookup(tmp_path):
    """An SSH origin with token-only credentials: recovery probes over the
    header-authenticated HTTPS transport (URL credential-free, token never
    in argv URLs), and the remote is looked up exactly ONCE — a second
    get-url would reopen the set-url race."""
    rec = _record()
    lookups, probes = [], []

    def run(cmd, **kw):
        if cmd[:3] == ["git", "remote", "get-url"]:
            lookups.append(cmd)
            return SimpleNamespace(returncode=0,
                                   stdout="git@github.com:org/proj.git\n",
                                   stderr="")
        if "ls-remote" in cmd:
            url = cmd[cmd.index("ls-remote") + 1]
            probes.append((url, "extraheader" in " ".join(cmd)))
            if url.startswith("git@"):
                return SimpleNamespace(returncode=128, stdout="",
                                       stderr="Permission denied (publickey)")
            return SimpleNamespace(
                returncode=0,
                stdout=f"{'d' * 40}\trefs/heads/ci-x\n", stderr="")
        raise AssertionError(cmd)

    assert push_wal.reconcile(tmp_path, rec, token="tok", run=run) == "pushed"
    assert len(lookups) == 1
    assert probes == [("https://github.com/org/proj.git", True)]
    assert all("tok" not in u for u, _ in probes)


def test_resolve_push_url_uses_push_url_and_strips_creds(tmp_path):
    """Fork setups configure a distinct pushurl — pushing to the FETCH URL
    would target upstream and bypass the pushurl friction. And a configured
    credential-bearing URL must never reach argv."""
    repo = _make_repo(tmp_path / "r")
    _git(repo, "remote", "add", "origin", "https://github.com/upstream/proj.git")
    _git(repo, "remote", "set-url", "--push", "origin",
         "https://user:SECRET@github.com/fork/proj.git")
    url = gitio.resolve_push_url(repo)
    assert url == "https://github.com/fork/proj.git"     # push URL, no creds
    assert "SECRET" not in url and "upstream" not in url
    # reconcile's single lookup also observes the PUSH URL
    rec = _record(remote_url="github.com/fork/proj")
    calls = []

    def run(cmd, **kw):
        if cmd[:4] == ["git", "remote", "get-url", "--push"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://user:SECRET@github.com/fork/proj.git\n",
                stderr="")
        if "ls-remote" in cmd:
            calls.append(cmd[cmd.index("ls-remote") + 1])
            return SimpleNamespace(
                returncode=0, stdout=f"{'d' * 40}\trefs/heads/ci-x\n",
                stderr="")
        raise AssertionError(cmd)
    assert push_wal.reconcile(tmp_path, rec, run=run) == "pushed"
    assert calls == ["https://github.com/fork/proj.git"]  # creds stripped


def test_unstage_reset_failure_fails_closed(tmp_path):
    """A failed reset leaves the generated file staged — committing it would
    break the never-committed promise, so the flow must raise."""
    def run(cmd, **kw):
        if cmd[:2] == ["git", "add"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:4] == ["git", "diff", "--cached", "--name-only"]:
            return SimpleNamespace(returncode=0, stdout="junk.log\n", stderr="")
        if cmd[:2] == ["git", "reset"]:
            return SimpleNamespace(returncode=128, stdout="",
                                   stderr="fatal: index locked")
        raise AssertionError(cmd)
    with pytest.raises(gitio.GitIOError, match="failed to unstage"):
        gitio.stage_commit_changes(tmp_path, ["*.log"], run=run)


def test_wal_op_id_cannot_escape(tmp_path):
    for bad in ("a/b", "../evil", "", "x" * 101, "."):
        with pytest.raises(push_wal.PushWalError, match="unsafe op_id"):
            push_wal.record_intent(tmp_path, _record(op_id=bad))
    assert not (tmp_path.parent / "evil.json").exists()


def test_wal_load_rejects_mistyped_state(tmp_path):
    """A parseable record with state 'intnet' must fail closed — silently
    skipping it would wave a new push past an unresolved intent."""
    p = push_wal.record_intent(tmp_path, _record())
    data = json.loads(p.read_text())
    data["state"] = "intnet"
    p.write_text(json.dumps(data))
    with pytest.raises(push_wal.PushWalError, match="unknown state"):
        push_wal.load_records(tmp_path)
    data["state"] = "intent"
    data["intended_oid"] = "zz"
    p.write_text(json.dumps(data))
    with pytest.raises(push_wal.PushWalError, match="bad intended_oid"):
        push_wal.load_records(tmp_path)


def test_supersession_requires_same_remote_identity(tmp_path):
    """origin re-pointed to another repository: the old intent keeps its
    reconciliation data (and will escalate on its own) — a new push to the
    NEW repository must not retire it."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "a.py": "1"}, "base")
    bare_b = tmp_path / "repo-b.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare_b)], check=True)
    _git(repo, "remote", "add", "origin", str(bare_b))
    wal = tmp_path / "wal"
    # intent recorded when origin pointed at repository A
    push_wal.record_intent(wal, PushRecord(
        op_id="op-a", repo_root=str(repo), remote_name="origin",
        remote_url="github.com/org/repo-a",
        dest_ref="refs/heads/ci-x", pre_push_oid=ABSENT,
        intended_oid="e" * 40))
    out = push_to_ci.commit_and_push(
        repo, branch="ci-x", wal_dir=wal, op_id="op-b",
        **_push_kwargs(unstage_globs=[]))
    # the mismatched-identity intent escalates the run — never superseded
    assert not out.pushed and "escalated" in out.reason
    recs = {r.op_id: r for r in push_wal.load_records(wal)}
    assert recs["op-a"].state == "intent"


def test_remote_ref_oid_error_is_credential_free(tmp_path):
    def run(cmd, **kw):
        return SimpleNamespace(returncode=128, stdout="", stderr="denied")
    with pytest.raises(push_wal.PushWalError) as ei:
        push_wal.remote_ref_oid(
            tmp_path, "https://x-access-token:SECRET@github.com/o/p.git",
            "refs/heads/x", token="SECRET", run=run)
    assert "SECRET" not in str(ei.value)


def test_resumed_intent_bound_to_recorded_world(tmp_path):
    """Between reconciliation and the pre-push probe a third party moves the
    remote: the resumed push must ESCALATE, never re-lease onto the new
    tip — and when the remote is still at the recorded pre-push tip the
    resumed push runs under a lease pinned to exactly that tip."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "a.py": "1"}, "base")
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "origin", "HEAD:ci-x")
    pre = _git(repo, "rev-parse", "HEAD")
    head = _commit(repo, {"a.py": "2"}, "work")
    wal = tmp_path / "wal"
    push_wal.record_intent(wal, PushRecord(
        op_id="op-r", repo_root=str(repo), remote_name="origin",
        remote_url=gitio.canonical_remote_identity(str(bare)),
        dest_ref="refs/heads/ci-x", pre_push_oid=pre, intended_oid=head))

    # third party moves the ref AFTER reconciliation, BEFORE the probe:
    # resolve_pending sees pre (retry); the second ls-remote sees the mover
    real_run = gitio._run
    state = SimpleNamespace(probes=0)

    def race_run(cmd, **kw):
        if "ls-remote" in cmd:
            state.probes += 1
            if state.probes == 2:   # the pre-push probe
                subprocess.run(["git", "push", "-q", str(bare),
                                f"{pre}:refs/heads/ci-x", "--force"],
                               cwd=str(repo), check=True)
                mover = _commit(repo, {"b.py": "x"}, "mover")
                subprocess.run(["git", "push", "-q", str(bare),
                                f"{mover}:refs/heads/ci-x", "--force"],
                               cwd=str(repo), check=True)
                _git(repo, "reset", "-q", "--hard", head)
        return real_run(cmd, **kw)

    out = push_to_ci.commit_and_push(
        repo, branch="ci-x", wal_dir=wal, op_id="op-r", run=race_run,
        **_push_kwargs(unstage_globs=[]))
    assert not out.pushed and "remote moved" in out.reason
    # untouched: the intent survives for human review
    recs = {r.op_id: r for r in push_wal.load_records(wal)}
    assert recs["op-r"].state == "intent"


def test_new_op_supersedes_stale_retryable_intent(tmp_path):
    """HEAD changed and the caller correctly minted a fresh op_id: the old
    retryable intent is durably retired (superseded) so it can never
    resurface as a false escalation."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "a.py": "1"}, "base")
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "origin", "HEAD:ci-x")
    pre = _git(repo, "rev-parse", "HEAD")
    old_head = _commit(repo, {"a.py": "2"}, "old work")
    wal = tmp_path / "wal"
    push_wal.record_intent(wal, PushRecord(
        op_id="op-old", repo_root=str(repo), remote_name="origin",
        remote_url=gitio.canonical_remote_identity(str(bare)),
        dest_ref="refs/heads/ci-x", pre_push_oid=pre, intended_oid=old_head))
    _commit(repo, {"a.py": "3"}, "new work")

    out = push_to_ci.commit_and_push(
        repo, branch="ci-x", wal_dir=wal, op_id="op-new",
        **_push_kwargs(unstage_globs=[]))
    assert out.pushed
    recs = {r.op_id: r for r in push_wal.load_records(wal)}
    assert recs["op-old"].state == "superseded"
    assert recs["op-new"].state == "pushed"
    # and a later run does NOT trip over the superseded record
    _commit(repo, {"a.py": "4"}, "later")
    out2 = push_to_ci.commit_and_push(
        repo, branch="ci-x", wal_dir=wal, op_id="op-later",
        **_push_kwargs(unstage_globs=[]))
    assert out2.pushed


def test_idempotent_success_requires_full_op_identity(tmp_path):
    """A pushed record reused with the SAME op_id but another destination
    must refuse, not falsely report that destination as pushed."""
    repo = _make_repo(tmp_path / "work")
    head = _commit(repo,
                   {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n"},
                   "base")
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "origin", "HEAD:ci-a")
    wal = tmp_path / "wal"
    rec = PushRecord(
        op_id="op-x", repo_root=str(repo), remote_name="origin",
        remote_url=gitio.canonical_remote_identity(str(bare)),
        dest_ref="refs/heads/ci-a", pre_push_oid=ABSENT, intended_oid=head,
        state="pushed")
    push_wal.mark_pushed(wal, rec)
    out = push_to_ci.commit_and_push(
        repo, branch="ci-b", wal_dir=wal, op_id="op-x",
        **_push_kwargs(unstage_globs=[]))
    assert not out.pushed and "different push" in out.reason
    assert not _git(repo, "ls-remote", str(bare), "refs/heads/ci-b")


# -- push_to_ci preflights and governance --------------------------------------

def test_preflight_upstream_commit():
    assert push_to_ci.preflight_upstream_commit(f"  {UP}\n") == UP
    for bad in ("", "unknown", UP[:12]):
        with pytest.raises(push_to_ci.PushPreflightError, match="40-hex"):
            push_to_ci.preflight_upstream_commit(bad)


def test_preflight_dockerfile_pin(tmp_path):
    push_to_ci.preflight_dockerfile_pin(tmp_path, UP, PIN)  # missing file: ok
    d = tmp_path / "docker"
    d.mkdir()
    (d / "Dockerfile.ci").write_text(f"ENV PRECOMPILED_WHEEL_COMMIT={'0' * 40}\n")
    with pytest.raises(push_to_ci.PushPreflightError, match="does not match"):
        push_to_ci.preflight_dockerfile_pin(tmp_path, UP, PIN)
    (d / "Dockerfile.ci").write_text(f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n")
    push_to_ci.preflight_dockerfile_pin(tmp_path, UP, PIN)


# -- partial e2e ---------------------------------------------------------------

def _bare_origin(tmp_path: Path, repo: Path, branch: str) -> Path:
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "origin", f"HEAD:{branch}")
    return bare


def test_push_partial_e2e(tmp_path):
    """commit_and_push over a real bare remote: preflights, staging
    discipline, signed commit, C4 double gate, WAL intent → push → pushed,
    idempotent resume, and re-entry/crash reconciliation."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "src/mod.py": "v1"}, "base")
    bare = _bare_origin(tmp_path, repo, "ci-test")
    old_tip = _git(repo, "rev-parse", "HEAD")

    (repo / "src/mod.py").write_text("v2")
    (repo / "junk.log").write_text("noise")
    wal_dir = tmp_path / "wal"

    # governance: not allowed → denied, and NOTHING recorded
    out = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-000",
        **_push_kwargs(allowed=False))
    assert not out.pushed and "denied" in out.reason
    assert not list(wal_dir.glob("*.json")) if wal_dir.exists() else True

    # governance: allowed but ALLOW_PUSH unset → dry-run, no WAL, no push
    out = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-000",
        **_push_kwargs(allow_push=False))
    assert out.dry_run and not out.pushed
    assert _git(repo, "ls-remote", str(bare),
                "refs/heads/ci-test").split()[0] == old_tip

    # fully gated push
    out = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-001",
        **_push_kwargs())
    assert out.pushed
    head = _git(repo, "rev-parse", "HEAD")
    assert out.pushed_commit == head
    assert _git(repo, "ls-remote", str(bare),
                "refs/heads/ci-test").split()[0] == head
    committed_files = _git(repo, "show", "--name-only", "--format=",
                           "HEAD").split()
    assert committed_files == ["src/mod.py"]          # junk.log never entered
    msg = _git(repo, "log", "-1", "--format=%B")
    assert f"rebase: align with upstream {UP[:12]}" in msg
    assert "Signed-off-by: Bot <bot@example.com>" in msg

    recs = {r.op_id: r for r in push_wal.load_records(wal_dir)}
    assert recs["push-001"].state == "pushed"
    assert recs["push-001"].pre_push_oid == old_tip
    assert recs["push-001"].intended_oid == head

    # idempotent resume: same op_id, same HEAD → no second push, still True
    out2 = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-001",
        **_push_kwargs())
    assert out2.pushed and out2.pushed_commit == head and not out2.committed

    # PRE-push crash: intent recorded, push never ran (simulated by an auth
    # failure) — resuming the SAME op_id picks up the durable intent and
    # completes it instead of refusing or orphaning it
    (repo / "src/mod.py").write_text("v2.5")
    real_run = gitio._run
    deny = SimpleNamespace(on=True)

    def failing_push(cmd, **kw):
        if "push" in cmd and any("HEAD:ci-test" in c for c in cmd) and deny.on:
            return SimpleNamespace(returncode=1, stdout="",
                                   stderr="remote: No anonymous write access.")
        return real_run(cmd, **kw)

    outA = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-001b",
        run=failing_push, **_push_kwargs())
    assert not outA.pushed and "failed after retries" in outA.reason
    recs = {r.op_id: r for r in push_wal.load_records(wal_dir)}
    assert recs["push-001b"].state == "intent"     # durable, unfinished
    deny.on = False
    outB = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-001b",
        **_push_kwargs())
    assert outB.pushed
    recs = {r.op_id: r for r in push_wal.load_records(wal_dir)}
    assert recs["push-001b"].state == "pushed"
    head = _git(repo, "rev-parse", "HEAD")

    # crash window: intent written, push landed, mark never happened —
    # the NEXT run's re-entry hygiene acknowledges it and proceeds
    crashed = PushRecord(
        op_id="push-002", repo_root=str(repo), remote_name="origin",
        remote_url=gitio.canonical_remote_identity(str(bare)),
        dest_ref="refs/heads/ci-test", pre_push_oid=old_tip,
        intended_oid=head)
    push_wal.record_intent(wal_dir, crashed)
    (repo / "src/mod.py").write_text("v3")
    out3 = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-003",
        **_push_kwargs())
    assert out3.pushed
    recs = {r.op_id: r for r in push_wal.load_records(wal_dir)}
    assert recs["push-002"].state == "pushed"     # acknowledged on re-entry

    # third party moves the ref; a stale intent then ESCALATES and the next
    # run refuses to push
    stale = PushRecord(
        op_id="push-004", repo_root=str(repo), remote_name="origin",
        remote_url=gitio.canonical_remote_identity(str(bare)),
        dest_ref="refs/heads/ci-test", pre_push_oid=old_tip,
        intended_oid="f" * 40)
    push_wal.record_intent(wal_dir, stale)
    out4 = push_to_ci.commit_and_push(
        repo, branch="ci-test", wal_dir=wal_dir, op_id="push-005",
        **_push_kwargs())
    assert not out4.pushed and "escalated" in out4.reason


def test_push_e2e_lease_after_rewrite_and_create_only(tmp_path):
    """History rewrite pushes under a SHA-pinned lease; an absent branch is
    created under an ABSENCE-pinned lease (deliberate divergence from the
    parent's raw --force), and a branch created by a racer fails closed."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "a.py": "1"}, "base")
    bare = _bare_origin(tmp_path, repo, "ci-lease")
    _git(repo, "commit", "-q", "--amend", "-m", "rewritten base")

    out = push_to_ci.commit_and_push(
        repo, branch="ci-lease", wal_dir=tmp_path / "wal", op_id="op-1",
        rebase_performed=True, **_push_kwargs(unstage_globs=[]))
    assert out.pushed

    out2 = push_to_ci.commit_and_push(
        repo, branch="ci-new", wal_dir=tmp_path / "wal", op_id="op-2",
        rebase_performed=True, **_push_kwargs(unstage_globs=[]))
    assert out2.pushed
    recs = {r.op_id: r for r in push_wal.load_records(tmp_path / "wal")}
    assert recs["op-2"].pre_push_oid == ABSENT

    # create race: someone else creates the branch AT AN ANCESTOR between
    # our observe and push — a plain push would silently fast-forward it; the
    # ABSENCE-pinned lease must refuse. (A racer at our EXACT commit is a
    # git no-op — remote content equals what we intended — and is harmless.)
    _commit(repo, {"a.py": "2"}, "second")
    real_run = gitio._run
    raced = SimpleNamespace(done=False)

    def racing_run(cmd, **kw):
        if "push" in cmd and "HEAD:ci-raced" in cmd and not raced.done:
            raced.done = True
            subprocess.run(["git", "push", "-q", str(bare),
                            "HEAD~1:refs/heads/ci-raced"],
                           cwd=str(repo), check=True)
        return real_run(cmd, **kw)

    out3 = push_to_ci.commit_and_push(
        repo, branch="ci-raced", wal_dir=tmp_path / "wal", op_id="op-3",
        rebase_performed=True, run=racing_run,
        **_push_kwargs(unstage_globs=[], sleep=lambda s: None))
    assert not out3.pushed
    # the racer's branch is untouched — no silent fast-forward happened
    assert _git(repo, "ls-remote", str(bare),
                "refs/heads/ci-raced").split()[0] == \
        _git(repo, "rev-parse", "HEAD~1")
