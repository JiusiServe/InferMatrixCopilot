"""Parent-store read-compat + knowledge attestation (Unit A, design D2).

The parent-schema fixture mirrors the real store's DDL (verified against the
deployed instance's `.schema`): `debug_entries` + external-content
`debug_entries_fts`. Read-compat must never write; digests must be LOGICAL
(WAL-committed rows count; file-copy artifacts don't).
"""

import sqlite3
from pathlib import Path

import pytest

from infermatrix_copilot.rebase_engine import knowledge_attest as ka
from infermatrix_copilot.rebase_engine.parent_compat import ParentDebugMemory

PARENT_DDL = """
CREATE TABLE debug_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL, key TEXT NOT NULL,
    tags TEXT DEFAULT '', files TEXT DEFAULT '',
    run_id TEXT DEFAULT '', timestamp TEXT DEFAULT '',
    symptom TEXT DEFAULT '', root_cause TEXT DEFAULT '',
    fix TEXT DEFAULT '', watch_outs TEXT DEFAULT '',
    status TEXT DEFAULT 'active', run_count INTEGER DEFAULT 1,
    last_seen_run TEXT DEFAULT '', vllm_commit TEXT DEFAULT '',
    derived_from TEXT DEFAULT '');
CREATE VIRTUAL TABLE debug_entries_fts USING fts5(
    module, key, tags, symptom, root_cause, fix, watch_outs,
    content='debug_entries', content_rowid='id');
"""


def _parent_db(path: Path, rows=()) -> Path:
    c = sqlite3.connect(path)
    c.executescript(PARENT_DDL)
    for r in rows:
        cur = c.execute(
            "INSERT INTO debug_entries (module, key, symptom, root_cause, "
            "fix, status, vllm_commit) VALUES (?,?,?,?,?,?,?)",
            (r.get("module", "m"), r["key"], r.get("symptom", ""),
             r.get("root_cause", ""), r.get("fix", ""),
             r.get("status", "active"), r.get("vllm_commit", "")))
        c.execute(
            "INSERT INTO debug_entries_fts (rowid, module, key, tags, "
            "symptom, root_cause, fix, watch_outs) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cur.lastrowid, r.get("module", "m"), r["key"], "",
             r.get("symptom", ""), r.get("root_cause", ""),
             r.get("fix", ""), ""))
    c.commit()
    c.close()
    return path


def test_parent_search_maps_fields_and_filters_status(tmp_path):
    db = _parent_db(tmp_path / "p.db", [
        {"key": "caplog-empty", "symptom": "caplog.text empty assertion",
         "fix": "capture at the emitting logger", "vllm_commit": "abc"},
        {"key": "dead-entry", "symptom": "caplog something",
         "fix": "old", "status": "stale"},
    ])
    pm = ParentDebugMemory(db, upstream_column="vllm_commit")
    hits = pm.search("caplog empty assertion")
    assert [h["key"] for h in hits] == ["caplog-empty"]  # stale filtered
    assert hits[0]["fix_summary"] == "capture at the emitting logger"
    full = pm.get(hits[0]["id"])
    assert full["upstream_commit"] == "abc"
    assert "fix" not in full and "vllm_commit" not in full
    # an UNDECLARED upstream column maps to "" (repo-neutral default)
    assert ParentDebugMemory(db).get(1)["upstream_commit"] == ""
    # a declared-but-absent column fails the schema probe at the gate
    import pytest as _pytest
    with _pytest.raises(sqlite3.DatabaseError):
        ParentDebugMemory(db, upstream_column="no_such_column")


def test_parent_open_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        ParentDebugMemory(tmp_path / "missing.db")
    bad = tmp_path / "bad.db"
    bad.write_bytes(b"garbage")
    with pytest.raises(sqlite3.DatabaseError):
        ParentDebugMemory(bad)
    # a valid sqlite file with the WRONG schema is also refused
    other = tmp_path / "other.db"
    sqlite3.connect(other).executescript("CREATE TABLE t (x);")
    with pytest.raises(sqlite3.DatabaseError):
        ParentDebugMemory(other)


def test_parent_store_never_written(tmp_path):
    db = _parent_db(tmp_path / "p.db", [{"key": "k", "symptom": "s"}])
    before = db.stat().st_mtime_ns
    pm = ParentDebugMemory(db)
    pm.search("s")
    pm.get(1)
    assert db.stat().st_mtime_ns == before


def test_logical_digest_sees_wal_only_rows(tmp_path):
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    d1 = ka.debug_db_digest(db)
    # commit a row in WAL mode and DON'T checkpoint: the main file bytes may
    # not contain it, the logical digest must
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()
    d2 = ka.debug_db_digest(db)
    assert d2 != d1
    assert (tmp_path / "p.db-wal").exists()  # rows really were in the WAL
    c.close()


def test_snapshot_and_restore_are_wal_safe(tmp_path):
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()  # k2 lives in the WAL
    live_digest = ka.debug_db_digest(db)
    snap = tmp_path / "backups" / "p.snapshot.db"
    assert ka.snapshot_debug_db(db, snap) == live_digest  # WAL row captured
    # mutate the live db, then restore: stale sidecars must not survive
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k3')")
    c.commit()
    c.close()
    restored = ka.restore_debug_db(snap, db)
    assert restored == live_digest
    assert not (tmp_path / "p.db-wal").exists()
    names = {r[0] for r in sqlite3.connect(db).execute(
        "SELECT key FROM debug_entries")}
    assert names == {"k1", "k2"}


def test_attest_rejects_stale_or_empty_fts_index(tmp_path):
    """Commit-hook finding (2026-08-20): a populated store whose
    external-content FTS index was never built (or went stale) must fail
    the attestation — retrieval would silently answer nothing while the
    digests look healthy."""
    db = tmp_path / "stale.db"
    c = sqlite3.connect(db)
    c.executescript(PARENT_DDL)
    # rows land in the CONTENT table only — the index never hears of them
    c.execute("INSERT INTO debug_entries (module, key, symptom) "
              "VALUES ('m', 'unindexed-key', 'unindexed symptom words')")
    c.commit()
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="stale"):
        ka.attest_layers(parent_debug_db=str(db))
    # an EMPTY store still attests fine (nothing to be unsearchable)
    empty = _parent_db(tmp_path / "empty.db", [])
    assert "parent_debug_db" in ka.attest_layers(
        parent_debug_db=str(empty))
    # PARTIAL corruption (hook iteration-3 finding): every active row is
    # probed, so an index stale for just ONE row — while others still
    # answer — is caught too
    partial = _parent_db(tmp_path / "partial.db", [
        {"key": "indexed-row", "symptom": "healthy indexed words"}])
    c = sqlite3.connect(partial)
    c.execute("INSERT INTO debug_entries (module, key, symptom) "
              "VALUES ('m', 'ghost-row', 'never reached the index')")
    c.commit()
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="stale"):
        ka.attest_layers(parent_debug_db=str(partial))
    # unicode + single-character content attests fine: the probe is the
    # tokenizer's own whole-field phrase, never an ASCII regex
    unicode_db = _parent_db(tmp_path / "uni.db", [
        {"key": "é", "symptom": "éclair déjà-vu 修复 x"}])
    assert "parent_debug_db" in ka.attest_layers(
        parent_debug_db=str(unicode_db))
    # PER-FIELD staleness (hook finding): update ONE column of an indexed
    # row without re-indexing — the still-searchable key must not carry a
    # stale symptom column past the gate
    field_stale = _parent_db(tmp_path / "field.db", [
        {"key": "stable-key", "symptom": "original symptom words",
         "fix": "original fix"}])
    c = sqlite3.connect(field_stale)
    c.execute("UPDATE debug_entries SET symptom='rewritten symptom text' "
              "WHERE key='stable-key'")
    c.commit()
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="does not match"):
        ka.attest_layers(parent_debug_db=str(field_stale))
    # SHORTENED content (hook iteration-3 finding): phrase matching
    # accepts subsequences, so only a full token-stream comparison
    # catches "alpha beta gamma" indexed vs "alpha beta" stored
    shortened = _parent_db(tmp_path / "short.db", [
        {"key": "sk", "symptom": "alpha beta gamma"}])
    c = sqlite3.connect(shortened)
    c.execute("UPDATE debug_entries SET symptom='alpha beta' "
              "WHERE key='sk'")
    c.commit()
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="does not match"):
        ka.attest_layers(parent_debug_db=str(shortened))


def test_attest_rejects_wrong_schema_as_parent_layer(tmp_path):
    """A copilot-schema DB (or any non-parent store) must fail the
    attestation at the GATE — a green attest followed by silent mid-run
    degradation is the exact unfairness the prelude exists to stop."""
    from infermatrix_copilot.memory.debug_memory import DebugMemory

    copilot_db = tmp_path / "copilot.db"
    DebugMemory(copilot_db)
    with pytest.raises(sqlite3.DatabaseError):
        ka.attest_layers(parent_debug_db=str(copilot_db))


def test_restore_leaves_target_intact_on_bad_snapshot(tmp_path):
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()  # k2 committed, WAL-resident
    before = ka.debug_db_digest(db)
    bad = tmp_path / "bad-snapshot.db"
    bad.write_bytes(b"definitely not sqlite")
    with pytest.raises(Exception):
        ka.restore_debug_db(bad, db)
    c.close()
    # the target — INCLUDING its WAL-resident committed row — survived
    assert ka.debug_db_digest(db) == before


def test_restore_replace_failure_loses_no_wal_rows(tmp_path, monkeypatch):
    """Iteration-2 F1: the target is CHECKPOINTED before its sidecars are
    touched, so even a failure at the final replace leaves every committed
    row (WAL-resident included) readable."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()
    c.close()
    before = ka.debug_db_digest(db)
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    import os as _os
    real_replace = _os.replace

    def failing_replace(src, dst):
        if str(dst).endswith("p.db"):
            raise OSError("simulated replace failure")
        return real_replace(src, dst)

    monkeypatch.setattr(_os, "replace", failing_replace)
    with pytest.raises(OSError):
        ka.restore_debug_db(snap, db)
    monkeypatch.undo()
    assert ka.debug_db_digest(db) == before  # k2 survived the failure


def test_restore_failure_restores_preserved_sidecars(tmp_path,
                                                     monkeypatch):
    """Iteration-3 F1: an UNCHECKPOINTABLE target's sidecars are moved
    aside, and a failure at the final replace moves them BACK — the old
    target stays attached to its WAL."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()
    # keep `c` OPEN: the last connection's close would checkpoint and
    # delete the WAL — this test needs a live WAL to protect
    wal = tmp_path / "p.db-wal"
    assert wal.exists()
    wal_bytes = wal.read_bytes()
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    # make the MAIN file uncheckpointable while its sidecars live on
    db.write_bytes(b"corrupted main file --------")
    import os as _os
    real_replace = _os.replace

    def failing_replace(src, dst):
        if str(dst).endswith("p.db"):
            raise OSError("simulated replace failure")
        return real_replace(src, dst)

    monkeypatch.setattr(_os, "replace", failing_replace)
    try:
        with pytest.raises(OSError, match="simulated replace"):
            ka.restore_debug_db(snap, db)
        # the sidecar is back at its real name, byte-identical (checked
        # BEFORE closing `c` — the close of a connection to the corrupt
        # main deletes sidecars as its own cleanup)
        assert wal.exists() and wal.read_bytes() == wal_bytes
        assert not (tmp_path / "p.db-wal.pre-restore").exists()
    finally:
        monkeypatch.undo()
        c.close()
    # and a subsequent (unimpeded) restore succeeds
    restored = ka.restore_debug_db(snap, db)
    assert restored == ka.debug_db_digest(db)


def test_restore_ignores_planted_staging_symlink(tmp_path):
    """PR-boundary F14: a pre-planted symlink at the old predictable
    staging name must neither redirect the staged write nor become the
    target — staging is a unique O_EXCL temp file now."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    victim = tmp_path / "victim.txt"
    victim.write_text("do not overwrite", encoding="utf-8")
    planted = tmp_path / "p.db.restore-tmp"  # the OLD predictable name
    planted.symlink_to(victim)
    restored = ka.restore_debug_db(snap, db)
    assert restored == ka.debug_db_digest(db)
    assert victim.read_text(encoding="utf-8") == "do not overwrite"
    assert planted.is_symlink()  # untouched, and never installed


def test_restore_self_heals_after_simulated_sigkill(tmp_path,
                                                    monkeypatch):
    """PR-boundary F15: a process death between sidecar-aside and replace
    leaves the durable pre-restore GUARD on disk; the next restore call
    self-heals the unreadable target from it before proceeding."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()  # k2 is WAL-resident; keep the connection open
    live_digest = ka.debug_db_digest(db)
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    # simulate the SIGKILL aftermath: guard written, sidecars gone, main
    # left truncated mid-swap (no in-process rollback ran)
    guard = tmp_path / "p.db.pre-restore-guard.db"
    ka.snapshot_debug_db(db, guard)
    c.close()
    for side in (tmp_path / "p.db-wal", tmp_path / "p.db-shm"):
        side.unlink(missing_ok=True)
    db.write_bytes(b"truncated mid-swap")
    # a FRESH restore call self-heals from the guard, then restores
    restored = ka.restore_debug_db(snap, db)
    assert restored == live_digest
    keys = {r[0] for r in sqlite3.connect(db).execute(
        "SELECT key FROM debug_entries")}
    assert keys == {"k1", "k2"}  # the WAL-resident row survived the kill
    assert not guard.exists()    # consumed/cleaned by the healed restore


def test_attest_rejects_malformed_declared_skill(tmp_path):
    """PR-boundary F2: a declared parent skill that does not PARSE would
    be silently skipped at retrieval while its bytes attest — the gate
    must refuse instead."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k"}])
    skills = tmp_path / "skills"
    (skills / "broken").mkdir(parents=True)
    (skills / "broken" / "SKILL.md").write_text("no frontmatter at all\n",
                                                encoding="utf-8")
    with pytest.raises(ValueError, match="does not parse"):
        ka.attest_layers(parent_debug_db=str(db),
                         parent_skills_dir=str(skills))


def test_attest_layers_fail_closed_and_catalog(tmp_path):
    skills = tmp_path / "skills"
    (skills / "s1").mkdir(parents=True)
    (skills / "s1" / "SKILL.md").write_text(
        "---\nname: s1\ndescription: d\n---\nbody\n", encoding="utf-8")
    db = _parent_db(tmp_path / "p.db", [{"key": "k"}])
    block = ka.attest_layers(parent_debug_db=str(db),
                             parent_skills_dir=str(skills))
    assert block["parent_skills_dir"]["skills"] == 1
    assert len(block["parent_debug_db"]["digest"]) == 64
    with pytest.raises(FileNotFoundError):
        ka.attest_layers(parent_skills_dir=str(tmp_path / "nope"))
    with pytest.raises(Exception):
        ka.attest_layers(parent_debug_db=str(tmp_path / "nope.db"))
    assert ka.attest_layers() == {}  # nothing declared, nothing attested
