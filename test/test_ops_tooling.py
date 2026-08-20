"""PR6/PR7 operational tooling (design D9): comparison gate, archival.

The comparison tool must FAIL CLOSED (GATE-ELIGIBLE: NO) on any missing or
mismatched artifact evidence and stamp YES only when every gate check
passes; the archival tool must abort on tracked secrets outside the
allowlist, exclude+inventory untracked ones, prove the tree clean except
the enumerated exceptions, and restore round-trip.
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import compare_validation  # noqa: E402
from infermatrix_copilot.rebase_engine import knowledge_attest as ka  # noqa: E402


def _worlds(tmp_path, *, drift=False, slug_mismatch=False,
            nat_phase="done"):
    ext_state = tmp_path / "ext_state.json"
    ext_state.write_text(json.dumps({
        "phase": "done", "vllm_commit": "f" * 40,
        "modules": {"core_mod": {"status": "done"}}}), encoding="utf-8")
    ext_manifest = tmp_path / "ext_manifest.json"
    ext_manifest.write_text(json.dumps(
        {"jobs": [{"slug": "quick"}, {"slug": "soak"}]}), encoding="utf-8")
    nat_run = tmp_path / "nat-run"
    nat_run.mkdir()
    digest = "d" * 64
    skills_digest = "e" * 64
    open_block = {"parent_debug_db": {"digest": digest},
                  "parent_skills_dir": {"digest": skills_digest}}
    (nat_run / "substate.json").write_text(json.dumps({
        "run_id": "run-n", "phase": nat_phase,
        "upstream_commit": "f" * 40,
        "modules": {"core_mod": {"status": "done"}},
        "tests": {"pipeline": {"failed_tests": []}},
        "knowledge": {"open": open_block,
                      "close": dict(open_block),
                      "drift": drift}}), encoding="utf-8")
    (nat_run / "test_manifest.json").write_text(json.dumps(
        {"jobs": [{"slug": "quick"},
                  {"slug": "different" if slug_mismatch else "soak"}]}),
        encoding="utf-8")
    return ext_state, ext_manifest, nat_run, digest


def _args(ext_state, ext_manifest, nat_run, digest, **over):
    golden = Path(nat_run).parent / "routing_golden.json"
    if not golden.exists():
        golden.write_text(json.dumps({"assignment_routing": {
            "quick": "core_mod", "soak": "core_mod"}}), encoding="utf-8")
    ext_results = Path(nat_run).parent / "ext_results.json"
    if not ext_results.exists():
        ext_results.write_text(json.dumps(
            {"quick": "passed", "soak": "passed"}), encoding="utf-8")
    base = dict(ext_state=str(ext_state), ext_manifest=str(ext_manifest),
                nat_run=str(nat_run), frozen_target="a" * 40,
                frozen_upstream="f" * 40, snapshot_digest=digest,
                snapshot_skills_digest="e" * 64,
                ext_open_digest=digest, ext_open_skills_digest="e" * 64,
                ext_start_head="a" * 40, nat_start_head="a" * 40,
                ext_head="1" * 40, nat_head="2" * 40,
                routing_golden=str(golden), ext_results=str(ext_results),
                ext_wallclock_sec=100.0,
                nat_wallclock_sec=110.0, out="")
    base.update(over)
    import argparse
    return argparse.Namespace(**base)


def test_gate_eligible_yes_when_evidence_matches(tmp_path):
    report, eligible = compare_validation.build_report(
        _args(*_worlds(tmp_path)))
    assert eligible and "GATE-ELIGIBLE: YES" in report
    assert "core_mod: ext=done nat=done — equal" in report
    assert "WITHIN BOUND" in report


@pytest.mark.parametrize("mutate,needle", [
    (dict(snapshot_digest="9" * 64, ext_open_digest="9" * 64),
     "did not open from the restored"),
    (dict(frozen_upstream=""), "--frozen-upstream not supplied"),
    (dict(nat_wallclock_sec=200.0), "exceeds the 1.25x bound"),
    (dict(nat_wallclock_sec=0.0), "missing or invalid"),
    (dict(snapshot_skills_digest=""),
     "--snapshot-skills-digest not supplied"),
    (dict(ext_open_digest="9" * 64),
     "ext opening debug digest != Phase-1 snapshot"),
    (dict(ext_open_skills_digest="9" * 64),
     "ext opening skills digest != Phase-1 snapshot"),
    (dict(ext_head=""), "--ext-head not supplied"),
    (dict(nat_start_head="b" * 40),
     "nat start head" ),
    (dict(nat_start_head=""), "--nat-start-head not supplied"),
    (dict(routing_golden=""), "--routing-golden not supplied"),
    (dict(nat_wallclock_sec=float("nan")), "missing or invalid"),
    (dict(nat_wallclock_sec=-5.0), "missing or invalid"),
])
def test_gate_fail_closed_on_mismatched_evidence(tmp_path, mutate, needle):
    report, eligible = compare_validation.build_report(
        _args(*_worlds(tmp_path), **mutate))
    assert not eligible and "GATE-ELIGIBLE: NO" in report and needle in report


def test_gate_fail_closed_on_incomplete_knowledge_evidence(tmp_path):
    """PR-boundary F16: absent drift, a missing close block, or a
    mismatched close digest each block — evidence must be COMPLETE."""
    import json as _json

    ext_state, ext_manifest, nat_run, digest = _worlds(tmp_path)
    sub = _json.loads((nat_run / "substate.json").read_text())
    sub["knowledge"].pop("drift")
    (nat_run / "substate.json").write_text(_json.dumps(sub))
    report, eligible = compare_validation.build_report(
        _args(ext_state, ext_manifest, nat_run, digest))
    assert not eligible and "drift == False explicitly" in report
    sub["knowledge"]["drift"] = False
    sub["knowledge"]["close"] = {}
    (nat_run / "substate.json").write_text(_json.dumps(sub))
    report, eligible = compare_validation.build_report(
        _args(ext_state, ext_manifest, nat_run, digest))
    assert not eligible and "no CLOSING knowledge attestation" in report


def test_gate_fail_closed_on_per_slug_regression(tmp_path):
    """PR-boundary F17: a slug the ext world passed but the nat world
    failed is a hard equal-or-better violation."""
    import json as _json

    ext_state, ext_manifest, nat_run, digest = _worlds(tmp_path)
    sub = _json.loads((nat_run / "substate.json").read_text())
    sub["tests"]["pipeline"]["failed_tests"] = ["quick"]
    (nat_run / "substate.json").write_text(_json.dumps(sub))
    report, eligible = compare_validation.build_report(
        _args(ext_state, ext_manifest, nat_run, digest))
    assert not eligible and "per-slug regression: quick" in report
    assert "quick [core_mod]" in report  # routed via assignment_routing
    # and missing ext results is itself a blocker
    report, eligible = compare_validation.build_report(
        _args(ext_state, ext_manifest, nat_run, digest, ext_results=""))
    assert not eligible and "--ext-results not supplied" in report


def test_gate_fail_closed_on_incomplete_nat_run(tmp_path):
    report, eligible = compare_validation.build_report(
        _args(*_worlds(tmp_path, nat_phase="needs_human")))
    assert not eligible and "did not reach phase=done" in report


def test_gate_fail_closed_on_empty_manifest(tmp_path):
    ext_state, ext_manifest, nat_run, digest = _worlds(tmp_path)
    ext_manifest.write_text(json.dumps({"jobs": []}), encoding="utf-8")
    report, eligible = compare_validation.build_report(
        _args(ext_state, ext_manifest, nat_run, digest))
    assert not eligible and "valid but EMPTY" in report


def test_gate_fail_closed_on_drift_and_slugs(tmp_path):
    report, eligible = compare_validation.build_report(
        _args(*_worlds(tmp_path, drift=True, slug_mismatch=True)))
    assert not eligible
    assert "knowledge DRIFT" in report and "slug sets differ" in report


def test_gate_fail_closed_on_missing_artifacts(tmp_path):
    ext_state, ext_manifest, nat_run, digest = _worlds(tmp_path)
    (nat_run / "substate.json").unlink()
    report, eligible = compare_validation.build_report(
        _args(ext_state, ext_manifest, nat_run, digest))
    assert not eligible and "no substate.json" in report


# ── archival ────────────────────────────────────────────────────────────────

def _git(repo, *cmd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    *cmd], cwd=repo, check=True, capture_output=True)


def _parent_fixture(tmp_path):
    repo = tmp_path / "parent"
    (repo / "agent" / "store").mkdir(parents=True)
    (repo / "rebase_logs").mkdir()
    (repo / "locks").mkdir()
    _git(repo, "init", "-q")
    (repo / "code.py").write_text("print('hi')\n")
    (repo / "agent" / ".env").write_text("OPENAI_API_KEY=sk-secret123456\n")
    _git(repo, "add", "code.py")
    _git(repo, "commit", "-qm", "seed")
    # runtime state: dirty tracked file + untracked artifacts
    (repo / "code.py").write_text("print('changed')\n")
    (repo / "rebase_logs" / "run.log").write_text("log line\n")
    # a token-bearing log: must be excluded from the TARBALL too
    (repo / "rebase_logs" / "env-dump.log").write_text(
        "api_key=leaked-in-a-log-000111\n")
    # …and one whose credential sits DEEP past the old 64 KiB head-scan
    (repo / "rebase_logs" / "deep.log").write_text(
        ("benign line\n" * 8000) + "token=deep-secret-abcdef123456\n")
    db = repo / "agent" / "store" / "debug_memory.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE debug_entries (id INTEGER PRIMARY KEY, "
              "module TEXT)")
    c.execute("INSERT INTO debug_entries (module) VALUES ('core')")
    c.commit()
    c.close()
    # an UNTRACKED secret and a TRACKED secret
    (repo / "sk.token").write_text("token=abcdefgh12345678\n")
    (repo / "tracked_key.txt").write_text("clean for now\n")
    _git(repo, "add", "tracked_key.txt")
    _git(repo, "commit", "-qm", "add tracked_key")
    target = tmp_path / "target"
    (target / "locks").mkdir(parents=True)
    _git(target, "init", "-q")
    return repo, target


def _run_archive(repo, target, archive, extra=()):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "archive_parent_repo.py"),
         "--parent-repo", str(repo), "--target-checkout", str(target),
         "--lock-name", "omni", "--archive-dir", str(archive), *extra],
        capture_output=True, text=True)


def test_archive_aborts_on_tracked_secret(tmp_path):
    repo, target = _parent_fixture(tmp_path)
    (repo / "tracked_key.txt").write_text("api_key=very-secret-value-123\n")
    r = _run_archive(repo, target, tmp_path / "archive")
    assert r.returncode == 3
    assert "tracked_key.txt" in r.stderr


def test_archive_excludes_and_inventories_with_allowlist(tmp_path):
    repo, target = _parent_fixture(tmp_path)
    (repo / "tracked_key.txt").write_text("api_key=very-secret-value-123\n")
    archive = tmp_path / "archive"
    r = _run_archive(repo, target, archive,
                     ("--secret-allowlist", "tracked_key.txt"))
    assert r.returncode == 0, r.stderr
    inventory = (archive / "ENV_INVENTORY.md").read_text(encoding="utf-8")
    # NAMES only — values never reach the archive
    assert "OPENAI_API_KEY" in inventory
    assert "sk-secret123456" not in inventory
    assert "sk.token" in inventory and "tracked_key.txt" in inventory
    assert "very-secret-value-123" not in inventory
    # the archival branch must NOT contain any secret file
    clone = next(archive.glob("parent-clone-*"))
    tracked = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"],
        cwd=clone, capture_output=True, text=True).stdout
    # HEAD of the clone is the archival branch (checked out at capture)
    assert "sk.token" not in tracked
    assert "rebase_logs/run.log" in tracked  # runtime state captured
    # bundle + db + tarball + docs exist
    assert list(archive.glob("parent-*.bundle"))
    assert list(archive.glob("debug_memory-*.db"))
    tarball = next(archive.glob("rebase_logs-*.tar.gz"))
    assert (archive / "RESTORE.md").exists()
    # the secret policy governs the TARBALL too (hook finding): the
    # token-bearing log is inventoried by NAME, never archived
    import tarfile as _tarfile
    with _tarfile.open(tarball) as tar:
        names = tar.getnames()
    assert "rebase_logs/run.log" in names
    assert all("env-dump.log" not in n for n in names)
    assert all("deep.log" not in n for n in names)  # whole-file scan
    assert "rebase_logs/env-dump.log" in inventory
    assert "rebase_logs/deep.log" in inventory
    assert "leaked-in-a-log-000111" not in inventory
    assert "deep-secret-abcdef123456" not in inventory
    # db copy is a REAL consistent copy
    db_copy = next(archive.glob("debug_memory-*.db"))
    n = sqlite3.connect(db_copy).execute(
        "SELECT count(*) FROM debug_entries").fetchone()[0]
    assert n == 1


def test_prestaged_secret_never_reaches_the_archive(tmp_path):
    """Hook iteration-2 finding: a secret STAGED before the script ran
    would survive classification in the index and ride into the
    pathspec-free commit/clone/bundle — the index reset must strip it."""
    repo, target = _parent_fixture(tmp_path)
    (repo / "tracked_key.txt").write_text("api_key=very-secret-value-123\n")
    _git(repo, "add", "tracked_key.txt")  # pre-staged BEFORE archiving
    archive = tmp_path / "archive"
    r = _run_archive(repo, target, archive,
                     ("--secret-allowlist", "tracked_key.txt"))
    assert r.returncode == 0, r.stderr
    clone = next(archive.glob("parent-clone-*"))
    shown = subprocess.run(
        ["git", "show", "HEAD:tracked_key.txt"],
        cwd=clone, capture_output=True, text=True).stdout
    assert "very-secret-value-123" not in shown
    assert shown == "clean for now\n"  # the OLD committed content only


def test_archive_refuses_while_lock_held(tmp_path):
    import fcntl
    import os as _os

    repo, target = _parent_fixture(tmp_path)
    lock = target / "locks" / "omni.lock"
    fd = _os.open(lock, _os.O_RDWR | _os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        r = _run_archive(repo, target, tmp_path / "archive")
        assert r.returncode != 0 and "HELD" in (r.stderr + r.stdout)
    finally:
        _os.close(fd)


def test_archive_refuses_fake_or_missing_target(tmp_path):
    """PR-boundary F20: a typo'd/fake target must REFUSE (not-contention
    setup failure through the shared hardened CheckoutLock), never let
    the archive proceed while the real lock lives elsewhere."""
    repo, target = _parent_fixture(tmp_path)
    r = _run_archive(repo, tmp_path / "no-such-checkout",
                     tmp_path / "archive")
    assert r.returncode != 0
    assert "REFUSED (not contention)" in (r.stderr + r.stdout)


def test_archive_requires_db_and_tag_fail_closed(tmp_path):
    """PR-boundary F21: a missing debug DB aborts without the explicit
    waiver, and a supplied --copilot-repo without the pre-pr7-retirement
    tag aborts instead of noting."""
    repo, target = _parent_fixture(tmp_path)
    (repo / "agent" / "store" / "debug_memory.db").unlink()
    r = _run_archive(repo, target, tmp_path / "archive")
    assert r.returncode == 6 and "--allow-missing-db" in r.stderr
    r = _run_archive(repo, target, tmp_path / "archive2",
                     ("--allow-missing-db",))
    assert r.returncode == 0, r.stderr
    # tag fail-closed: an un-tagged copilot repo aborts
    copilot = tmp_path / "copilot"
    copilot.mkdir()
    _git(copilot, "init", "-q")
    r = _run_archive(repo, target, tmp_path / "archive3",
                     ("--allow-missing-db", "--copilot-repo",
                      str(copilot)))
    assert r.returncode == 7 and "pre-pr7-retirement" in r.stderr


def test_restore_sh_round_trips(tmp_path):
    """PR-boundary F21: the generated restore.sh actually restores the
    parent world into a scratch path — clone at the archival branch,
    logs unpacked, debug DB in place."""
    repo, target = _parent_fixture(tmp_path)
    archive = tmp_path / "archive"
    r = _run_archive(repo, target, archive)
    assert r.returncode == 0, r.stderr
    restore_sh = archive / "restore.sh"
    assert restore_sh.exists() and restore_sh.stat().st_mode & 0o111
    dest = tmp_path / "restored"
    rr = subprocess.run(["bash", str(restore_sh), str(dest)],
                        capture_output=True, text=True)
    assert rr.returncode == 0, rr.stderr
    assert (dest / "code.py").read_text() == "print('changed')\n"
    assert (dest / "rebase_logs" / "run.log").exists()
    n = sqlite3.connect(dest / "agent" / "store" / "debug_memory.db"
                        ).execute("SELECT count(*) FROM debug_entries"
                                  ).fetchone()[0]
    assert n == 1


def test_archive_aborts_on_clean_committed_secret(tmp_path):
    """PR-boundary F19: a secret committed CLEAN (no dirty status entry)
    still reaches the archival branch's HEAD tree — the tree scan aborts
    unless the path is allowlisted (history itself is a recorded owner
    position, not scanned)."""
    repo, target = _parent_fixture(tmp_path)
    (repo / "committed_cred.txt").write_text(
        "password=committed-long-ago-123\n")
    _git(repo, "add", "committed_cred.txt")
    _git(repo, "commit", "-qm", "old secret, clean tree")
    r = _run_archive(repo, target, tmp_path / "archive")
    assert r.returncode == 5
    assert "committed_cred.txt" in r.stderr
    r = _run_archive(repo, target, tmp_path / "archive2",
                     ("--secret-allowlist", "committed_cred.txt"))
    assert r.returncode == 0, r.stderr


def test_knowledge_digest_cli_roundtrip(tmp_path):
    db = tmp_path / "m.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY, symptom TEXT)")
    c.execute("INSERT INTO entries (symptom) VALUES ('s')")
    c.commit()
    c.close()
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "knowledge_digest.py"), "digest",
         "--db", str(db)], capture_output=True, text=True)
    assert r.returncode == 0 and "debug_db" in r.stdout
    digest = r.stdout.split()[-1]
    snap = tmp_path / "snap.db"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "knowledge_digest.py"), "snapshot",
         "--db", str(db), "--dest", str(snap)],
        capture_output=True, text=True)
    assert r.returncode == 0 and digest in r.stdout
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "knowledge_digest.py"), "restore",
         "--snapshot", str(snap), "--target", str(db)],
        capture_output=True, text=True)
    assert r.returncode == 0 and digest in r.stdout
    assert ka.debug_db_digest(db) == digest
