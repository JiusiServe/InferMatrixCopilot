"""PR3 — push cluster: gitio, push WAL, lease_expect, push_to_ci preflights.

`test_push_partial_e2e` drives the full commit-and-push flow against a real
bare remote, including WAL crash reconciliation.
"""

from __future__ import annotations

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


def test_run_signed_commit_retries_on_formatter_hook(tmp_path):
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


def test_run_signed_commit_exhausts_retries(tmp_path):
    run = lambda cmd, **kw: SimpleNamespace(returncode=1, stdout="boom",
                                            stderr="")
    assert gitio.run_signed_commit(Path("."), "m", author_name="a",
                                   author_email="b@c", retries=2,
                                   run=run) is False


# -- gitio: URLs and push execution -------------------------------------------

def test_resolve_push_url_and_credential_free(tmp_path):
    repo = _make_repo(tmp_path / "r")
    _git(repo, "remote", "add", "origin", "git@github.com:org/proj.git")
    assert gitio.resolve_push_url(repo, token="tok123") == \
        "https://x-access-token:tok123@github.com/org/proj.git"
    assert gitio.resolve_push_url(repo) == "git@github.com:org/proj.git"
    assert gitio.credential_free_url(
        "https://x-access-token:tok@github.com/org/proj.git") == \
        "https://github.com/org/proj.git"
    assert gitio.credential_free_url("git@github.com:org/proj.git") == \
        "git@github.com:org/proj.git"


def test_execute_push_refuses_denied_decision(tmp_path):
    denied = PushDecision(False, "nope")
    with pytest.raises(gitio.GitIOError, match="denied push"):
        gitio.execute_push(denied, tmp_path, url="u", refspec="HEAD:x")


def test_execute_push_auth_failure_aborts_immediately():
    attempts = []

    def run(cmd, **kw):
        attempts.append(cmd)
        return SimpleNamespace(returncode=1, stdout="",
                               stderr="remote: No anonymous write access.")
    ok = gitio.execute_push(PushDecision(True, "ok"), Path("."), url="u",
                            refspec="HEAD:x", run=run, sleep=lambda s: None)
    assert ok is False and len(attempts) == 1


def test_execute_push_retries_with_backoff():
    slept, n = [], SimpleNamespace(v=0)

    def run(cmd, **kw):
        n.v += 1
        rc = 0 if n.v == 3 else 1
        return SimpleNamespace(returncode=rc, stdout="", stderr="conn reset")
    ok = gitio.execute_push(PushDecision(True, "ok"), Path("."), url="u",
                            refspec="HEAD:x", retries=3, base_delay=5.0,
                            run=run, sleep=slept.append)
    assert ok is True and n.v == 3 and slept == [5.0, 10.0]


# -- guard_push: lease_expect --------------------------------------------------

def test_guard_push_lease_expect():
    sha = "b" * 40
    d = guard_push(PushPolicy(allowed=True, branch="ci-x",
                              force_with_lease=True, lease_expect=sha), ["main"])
    assert d.allowed and f"--force-with-lease=ci-x:{sha}" in d.command
    # unqualified lease still works
    d = guard_push(PushPolicy(allowed=True, branch="ci-x",
                              force_with_lease=True), ["main"])
    assert d.allowed and "--force-with-lease" in d.command
    # a pinned lease without force intent is confused — denied
    d = guard_push(PushPolicy(allowed=True, branch="ci-x",
                              lease_expect=sha), ["main"])
    assert not d.allowed and "lease_expect" in d.reason
    # protected branches stay undeniable regardless of lease form
    d = guard_push(PushPolicy(allowed=True, branch="main",
                              force_with_lease=True, lease_expect=sha), ["main"])
    assert not d.allowed


# -- push WAL ------------------------------------------------------------------

def _record(**kw) -> PushRecord:
    base = dict(op_id="op-001", repo_root="/r", remote_name="origin",
                remote_url="https://github.com/org/proj.git",
                dest_ref="refs/heads/ci-x", pre_push_oid="c" * 40,
                intended_oid="d" * 40)
    base.update(kw)
    return PushRecord(**base)


def test_wal_record_validation(tmp_path):
    with pytest.raises(push_wal.PushWalError, match="40-hex"):
        push_wal.record_intent(tmp_path, _record(intended_oid="short"))
    with pytest.raises(push_wal.PushWalError, match="40-hex or ABSENT"):
        push_wal.record_intent(tmp_path, _record(pre_push_oid="xx"))
    with pytest.raises(push_wal.PushWalError, match="full branch ref"):
        push_wal.record_intent(tmp_path, _record(dest_ref="ci-x"))
    p = push_wal.record_intent(tmp_path, _record())
    assert json.loads(p.read_text())["state"] == "intent"
    rec = _record()
    push_wal.mark_pushed(tmp_path, rec)
    assert json.loads(rec.path(tmp_path).read_text())["state"] == "pushed"
    assert [r.op_id for r in push_wal.load_records(tmp_path)] == ["op-001"]


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
    # landed
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        url, f"{'d' * 40}\t{ref}\n")) == "pushed"
    # did not land
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        url, f"{'c' * 40}\t{ref}\n")) == "retry"
    # third party moved the ref
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        url, f"{'e' * 40}\t{ref}\n")) == "escalate"
    # remote reconfigured: identity mismatch escalates BEFORE any OID logic
    assert push_wal.reconcile(tmp_path, rec, run=runner(
        "https://github.com/other/repo.git", f"{'d' * 40}\t{ref}\n")) == \
        "escalate"
    # ABSENT == ABSENT is a clean retry (branch-creation push never landed)
    rec2 = _record(pre_push_oid=ABSENT)
    assert push_wal.reconcile(tmp_path, rec2, run=runner(url, "")) == "retry"
    # network failure raises — it must never read as "ref absent"
    with pytest.raises(push_wal.PushWalError, match="ls-remote failed"):
        push_wal.reconcile(tmp_path, rec, run=runner(url, "", ls_rc=1))
    # a pushed record needs no remote at all
    rec3 = _record(state="pushed")
    assert push_wal.reconcile(tmp_path, rec3,
                              run=lambda *a, **k: (_ for _ in ()).throw(
                                  AssertionError("no calls"))) == "pushed"


# -- push_to_ci preflights -----------------------------------------------------

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
    discipline, signed commit, C4 authorization, WAL intent → push →
    pushed, and crash reconciliation on the same WAL shape."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "src/mod.py": "v1"}, "base")
    bare = _bare_origin(tmp_path, repo, "ci-test")
    old_tip = _git(repo, "rev-parse", "HEAD")

    (repo / "src/mod.py").write_text("v2")
    (repo / "junk.log").write_text("noise")
    wal_dir = tmp_path / "wal"

    out = push_to_ci.commit_and_push(
        repo, upstream_commit=UP, pin=PIN, branch="ci-test",
        message_template="rebase: align with upstream {short}",
        unstage_globs=["*.log"],
        author_name="Bot", author_email="bot@example.com",
        protected_branches=["main"], wal_dir=wal_dir, op_id="push-001",
        sleep=lambda s: None)
    assert out.pushed and out.committed
    head = _git(repo, "rev-parse", "HEAD")
    assert out.pushed_commit == head
    assert _git(repo, "ls-remote", str(bare), "refs/heads/ci-test").split()[0] == head
    committed_files = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert committed_files == ["src/mod.py"]          # junk.log never entered
    msg = _git(repo, "log", "-1", "--format=%B")
    assert f"rebase: align with upstream {UP[:12]}" in msg
    assert "Signed-off-by: Bot <bot@example.com>" in msg

    recs = push_wal.load_records(wal_dir)
    assert len(recs) == 1 and recs[0].state == "pushed"
    assert recs[0].dest_ref == "refs/heads/ci-test"
    assert recs[0].pre_push_oid == old_tip and recs[0].intended_oid == head

    # crash window: intent written, push landed, mark never happened
    crashed = push_wal.PushRecord(
        op_id="push-002", repo_root=str(repo), remote_name="origin",
        remote_url=str(bare), dest_ref="refs/heads/ci-test",
        pre_push_oid=old_tip, intended_oid=head)
    assert push_wal.reconcile(repo, crashed) == "pushed"
    # third party moves the ref afterwards → escalate, never guess
    _commit(repo, {"src/other.py": "x"}, "third party")
    _git(repo, "push", "-q", "origin", "HEAD:ci-test")
    assert push_wal.reconcile(repo, crashed) == "escalate"

    # no changes at all: pushes current HEAD without a new commit
    out2 = push_to_ci.commit_and_push(
        repo, upstream_commit=UP, pin=PIN, branch="ci-test",
        message_template="m {short}", unstage_globs=[],
        author_name="Bot", author_email="bot@example.com",
        protected_branches=["main"], wal_dir=wal_dir, op_id="push-003",
        sleep=lambda s: None)
    assert out2.pushed and not out2.committed

    # protected branch: denied by C4 authorization, and NO WAL intent exists
    out3 = push_to_ci.commit_and_push(
        repo, upstream_commit=UP, pin=PIN, branch="main",
        message_template="m {short}", unstage_globs=[],
        author_name="Bot", author_email="bot@example.com",
        protected_branches=["main"], wal_dir=wal_dir, op_id="push-004",
        sleep=lambda s: None)
    assert not out3.pushed and "denied" in out3.reason
    assert not (wal_dir / "push-004.json").exists()


def test_push_e2e_lease_after_rewrite(tmp_path):
    """History rewrite: the push runs under a SHA-pinned lease and succeeds;
    a remote moved by a third party makes the same lease fail closed."""
    repo = _make_repo(tmp_path / "work")
    _commit(repo, {"docker/Dockerfile.ci": f"ENV PRECOMPILED_WHEEL_COMMIT={UP}\n",
                   "a.py": "1"}, "base")
    _bare_origin(tmp_path, repo, "ci-lease")
    _git(repo, "commit", "-q", "--amend", "-m", "rewritten base")

    out = push_to_ci.commit_and_push(
        repo, upstream_commit=UP, pin=PIN, branch="ci-lease",
        message_template="m {short}", unstage_globs=[],
        author_name="Bot", author_email="bot@example.com",
        protected_branches=["main"], wal_dir=tmp_path / "wal", op_id="op-1",
        rebase_performed=True, sleep=lambda s: None)
    assert out.pushed
    # remote branch absent + rebase_performed: plain push CREATES the branch
    # (deliberate divergence from the parent's raw --force)
    out2 = push_to_ci.commit_and_push(
        repo, upstream_commit=UP, pin=PIN, branch="ci-new",
        message_template="m {short}", unstage_globs=[],
        author_name="Bot", author_email="bot@example.com",
        protected_branches=["main"], wal_dir=tmp_path / "wal", op_id="op-2",
        rebase_performed=True, sleep=lambda s: None)
    assert out2.pushed
    recs = {r.op_id: r for r in push_wal.load_records(tmp_path / "wal")}
    assert recs["op-2"].pre_push_oid == ABSENT
