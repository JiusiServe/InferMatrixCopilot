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


def test_parent_probe_rejects_column_incomplete_fts(tmp_path):
    """PR-boundary round-2 F4: a symptom-only FTS answers the join probe
    but silently misses key/tag/root-cause/fix terms — the open must
    refuse it."""
    db = tmp_path / "thin.db"
    c = sqlite3.connect(db)
    c.executescript("""
CREATE TABLE debug_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL, key TEXT NOT NULL,
    tags TEXT DEFAULT '', files TEXT DEFAULT '',
    run_id TEXT DEFAULT '', timestamp TEXT DEFAULT '',
    symptom TEXT DEFAULT '', root_cause TEXT DEFAULT '',
    fix TEXT DEFAULT '', watch_outs TEXT DEFAULT '',
    status TEXT DEFAULT 'active');
CREATE VIRTUAL TABLE debug_entries_fts USING fts5(
    symptom, content='debug_entries', content_rowid='id');""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="retrieval probe"):
        ParentDebugMemory(db)


def test_restore_guard_rejects_planted_symlink(tmp_path):
    """PR-boundary round-2 F10: a planted symlink at the predictable
    guard name is neither followed at creation (unique tmp + atomic
    replace) nor consumed at self-heal."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    victim = tmp_path / "victim.txt"
    victim.write_text("do not overwrite", encoding="utf-8")
    guard = tmp_path / "p.db.pre-restore-guard.db"
    guard.symlink_to(victim)
    with pytest.raises(OSError, match="not a regular file"):
        ka.restore_debug_db(snap, db)
    assert victim.read_text(encoding="utf-8") == "do not overwrite"
    assert ka.debug_db_digest(db)  # target untouched and readable


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


def test_parent_open_rejects_symptom_only_fts(tmp_path):
    """Round-2 F4: an FTS index missing required columns (symptom-only)
    would answer the join probe yet silently miss key/tag/root-cause/
    fix/watch-out searches — the schema-validating open must refuse."""
    db = tmp_path / "narrow.db"
    c = sqlite3.connect(db)
    c.executescript("""
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
    symptom, content='debug_entries', content_rowid='id');
""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="retrieval probe"):
        ParentDebugMemory(db)


def test_restore_guard_failure_on_readable_target_aborts(tmp_path,
                                                         monkeypatch):
    """Round-2 F9: when the pre-restore guard cannot be created for a
    READABLE target, the restore ABORTS — swapping without crash
    protection was the fail-open."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()  # keep open: WAL alive + uncheckpointable via busy? no —
    # force the uncheckpointable path by holding a read txn open
    c.execute("BEGIN")
    c.execute("SELECT count(*) FROM debug_entries")
    before = ka.debug_db_digest(db)
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    # fail exactly the GUARD's source open (the first ro open of the
    # TARGET inside restore); the later integrity re-probe must succeed
    # so the "readable target ⇒ abort" branch is exercised
    real_uri = ka.readonly_uri
    fails = {"armed": True}

    def flaky_uri(path):
        if fails["armed"] and str(path) == str(db):
            fails["armed"] = False
            return "file:/nonexistent-guard-source?mode=ro"
        return real_uri(path)

    monkeypatch.setattr(ka, "readonly_uri", flaky_uri)
    with pytest.raises(sqlite3.DatabaseError, match="without crash "
                                                    "protection"):
        ka.restore_debug_db(snap, db)
    monkeypatch.setattr(ka, "readonly_uri", real_uri)
    c.close()
    assert ka.debug_db_digest(db) == before  # target untouched


def test_restore_refuses_planted_guard_symlink(tmp_path):
    """Round-2 F10: a planted symlink at the predictable guard name must
    never be consumed as the self-heal source (or followed as a write
    target — guards are built at unique temps and renamed over)."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    victim = tmp_path / "victim.db"
    victim.write_text("attacker data", encoding="utf-8")
    guard = tmp_path / "p.db.pre-restore-guard.db"
    guard.symlink_to(victim)
    with pytest.raises(OSError, match="not a regular file"):
        ka.restore_debug_db(snap, db)
    assert victim.read_text(encoding="utf-8") == "attacker data"
    assert guard.is_symlink()  # untouched


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


def test_parent_probe_rejects_inexact_upstream_column(tmp_path):
    """Round-3 F5: a bare SELECT accepts rowid/oid aliases and case
    variants of the declared upstream column, but get()'s dict pop is
    exact — such rows would silently map upstream_commit to ''."""
    db = _parent_db(tmp_path / "c.db", [])
    for alias in ("ROWID", "oid", "VLLM_COMMIT"):
        with pytest.raises(sqlite3.DatabaseError, match="exact column"):
            ParentDebugMemory(db, upstream_column=alias)
    assert ParentDebugMemory(db, upstream_column="vllm_commit").count() == 0


_FULL_ENTRIES_DDL = """
CREATE TABLE debug_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL, key TEXT NOT NULL,
    tags TEXT DEFAULT '', files TEXT DEFAULT '',
    run_id TEXT DEFAULT '', timestamp TEXT DEFAULT '',
    symptom TEXT DEFAULT '', root_cause TEXT DEFAULT '',
    fix TEXT DEFAULT '', watch_outs TEXT DEFAULT '',
    status TEXT DEFAULT 'active');
"""


def test_parent_probe_rejects_fts4_index(tmp_path):
    """Round-3 F4: an FTS4 table with the full column set answers every
    name-based probe yet lacks FTS5's rank/integrity-check semantics
    the reader and attestation rely on — the open must refuse it."""
    db = tmp_path / "f4.db"
    c = sqlite3.connect(db)
    c.executescript(_FULL_ENTRIES_DDL + """
CREATE VIRTUAL TABLE debug_entries_fts USING fts4(
    module, key, tags, symptom, root_cause, fix, watch_outs);""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="not an FTS5"):
        ParentDebugMemory(db)


def test_parent_probe_rejects_unindexed_required_column(tmp_path):
    """Round-3 F4: an UNINDEXED required column exists by name and
    answers a column-filtered MATCH with silent emptiness — searches
    would miss every term in it; the open must refuse."""
    db = tmp_path / "unidx.db"
    c = sqlite3.connect(db)
    c.executescript(_FULL_ENTRIES_DDL + """
CREATE VIRTUAL TABLE debug_entries_fts USING fts5(
    module, key UNINDEXED, tags, symptom, root_cause, fix, watch_outs,
    content='debug_entries', content_rowid='id');""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="UNINDEXED"):
        ParentDebugMemory(db)


def test_skills_catalog_validates_types_and_uniqueness(tmp_path):
    """Round-3 F6: `name: [broken]` parses as YAML but is unhashable at
    retrieval (SkillStore.find crashes on it); two skills sharing an
    effective name collide silently. validate=True refuses both."""
    root = tmp_path / "skills"
    (root / "a").mkdir(parents=True)
    (root / "a" / "SKILL.md").write_text(
        "---\nname: [broken]\ndescription: d\n---\nbody\n",
        encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty string"):
        ka.skills_catalog(root, validate=True)
    (root / "a" / "SKILL.md").write_text(
        "---\nname: same\ndescription: d\n---\nbody\n",
        encoding="utf-8")
    (root / "b").mkdir()
    (root / "b" / "SKILL.md").write_text(
        "---\nname: same\ndescription: d\n---\nbody\n",
        encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate effective"):
        ka.skills_catalog(root, validate=True)
    # the pure digest path (validate=False) still hashes both files
    assert len(ka.skills_catalog(root)) == 2


@pytest.mark.parametrize("probe_exc", [
    sqlite3.OperationalError("disk I/O error"),
    # round-4 F4: an exact base DatabaseError WITHOUT a corruption
    # errorcode is ambiguous, not a corruption verdict — abort too
    sqlite3.DatabaseError("ambiguous failure, no errorcode"),
])
def test_restore_aborts_when_target_state_unknown(tmp_path, monkeypatch,
                                                  probe_exc):
    """Round-3 F8 + round-4 F4: when the pre-restore guard fails AND the
    corruption re-probe itself errors WITHOUT a definitive
    SQLITE_CORRUPT/SQLITE_NOTADB code (transient IO, locked, or an
    uncoded base DatabaseError), the target's state is UNKNOWN: the
    restore must abort BEFORE touching any sidecar, never proceed
    guardless."""
    db = _parent_db(tmp_path / "p.db", [{"key": "k1", "symptom": "s1"}])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','k2')")
    c.commit()
    wal = tmp_path / "p.db-wal"
    assert wal.exists()
    wal_bytes = wal.read_bytes()
    snap = tmp_path / "snap.db"
    ka.snapshot_debug_db(db, snap)
    real_connect = sqlite3.connect

    def flaky_connect(database, *a, **kw):
        s = str(database)
        # every open of the TARGET errors like a flaky disk; the staged
        # `p.db.restore-*.tmp` copy stays reachable
        if s.endswith("p.db") or "p.db?" in s:
            raise probe_exc
        return real_connect(database, *a, **kw)

    monkeypatch.setattr(sqlite3, "connect", flaky_connect)
    try:
        with pytest.raises(sqlite3.DatabaseError, match="UNKNOWN"):
            ka.restore_debug_db(snap, db)
    finally:
        monkeypatch.undo()
    # nothing moved: live WAL intact at its true name, no aside copies,
    # no leftover guard (checked before closing `c` — its close would
    # checkpoint the WAL away)
    assert wal.exists() and wal.read_bytes() == wal_bytes
    assert not (tmp_path / "p.db-wal.pre-restore").exists()
    assert not list(tmp_path.glob("*pre-restore-guard*"))
    c.close()


def test_parent_probe_rejects_unindexed_despite_formatting(tmp_path):
    """Round-3 F4 hook iteration: UNINDEXED detection must survive DDL
    formatting — extra whitespace, an interleaved comment, a quoted
    column name — because sqlite_master stores the CREATE text verbatim."""
    # (no comment/tab/newline variants: FTS5's own argument parser
    # refuses those, so such DDL cannot exist in sqlite_master)
    for i, coldef in enumerate((
            "key     UNINDEXED",
            "key unindexed",
            '"key" UNINDEXED',
            "[key] UNINDEXED",
            "KEY UNINDEXED",
            '"Key" UNINDEXED')):
        db = tmp_path / f"fmt{i}.db"
        c = sqlite3.connect(db)
        c.executescript(_FULL_ENTRIES_DDL + f"""
CREATE VIRTUAL TABLE debug_entries_fts USING fts5(
    module, {coldef}, tags, symptom, root_cause, fix, watch_outs,
    content='debug_entries', content_rowid='id');""")
        c.close()
        with pytest.raises(sqlite3.DatabaseError, match="UNINDEXED"):
            ParentDebugMemory(db)


def test_parent_probe_strips_comments_before_fts5_check(tmp_path):
    """Hook iteration-2: sqlite_master stores CREATE text verbatim, so
    `/* USING fts5( */ USING fts4(...)` fools a raw-text regex — the
    FTS5-ness check must run on comment-stripped SQL."""
    db = tmp_path / "trick.db"
    c = sqlite3.connect(db)
    c.executescript(_FULL_ENTRIES_DDL + """
CREATE VIRTUAL TABLE debug_entries_fts /* USING fts5( */ USING fts4(
    module, key, tags, symptom, root_cause, fix, watch_outs);""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="not an FTS5"):
        ParentDebugMemory(db)


def test_parent_probe_rejects_quoted_identifier_fts5_spoof(tmp_path):
    """Hook iteration-3: a quoted FTS4 column literally named
    `[USING fts5(]` puts the magic text into the DDL — the module check
    must tokenize (quoted identifiers are single tokens), not regex the
    raw statement."""
    db = tmp_path / "spoof.db"
    c = sqlite3.connect(db)
    c.executescript(_FULL_ENTRIES_DDL + """
CREATE VIRTUAL TABLE debug_entries_fts USING fts4([USING fts5(],
    module, key, tags, symptom, root_cause, fix, watch_outs);""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError, match="not an FTS5"):
        ParentDebugMemory(db)


def test_upstream_column_rejects_hidden_virtual_columns(tmp_path):
    """Round-4 F2: PRAGMA table_xinfo lists a virtual table's HIDDEN
    columns (`rank`, the table-name column) that `SELECT *` omits — a
    parent whose debug_entries is itself an FTS5 table must not accept
    `rank` as the upstream column (get() would emit "" forever)."""
    db = tmp_path / "vt.db"
    c = sqlite3.connect(db)
    c.executescript("""
CREATE VIRTUAL TABLE debug_entries USING fts5(
    id, module, key, tags, files, run_id, timestamp,
    symptom, root_cause, fix, watch_outs, status);
CREATE VIRTUAL TABLE debug_entries_fts USING fts5(
    module, key, tags, symptom, root_cause, fix, watch_outs);""")
    c.close()
    with pytest.raises(sqlite3.DatabaseError,
                       match="not an exact column"):
        ParentDebugMemory(db, upstream_column="rank")


def test_unindexed_parser_survives_quoted_comment_openers(tmp_path):
    """Round-4 F1: a comment-opener INSIDE a quoted column name must not
    blank a span of real DDL — the crafted names below would otherwise
    swallow the UNINDEXED declaration between them."""
    from infermatrix_copilot.memory.debug_memory import (
        fts5_unindexed_columns, is_fts5_table)
    ddl = ('CREATE VIRTUAL TABLE t USING fts5('
           '"a /*", key UNINDEXED, "*/ c")')
    assert is_fts5_table(ddl)
    assert "key" in fts5_unindexed_columns(ddl)
    # and a REAL comment before the module clause still cannot spoof
    spoof = ("CREATE VIRTUAL TABLE t /* USING fts5( */ "
             "USING fts4(a, b)")
    assert not is_fts5_table(spoof)
    # quoted PUNCTUATION is payload, not structure: a column named ")"
    # (or "(", or "a,b") must not terminate/split the scan before a
    # later UNINDEXED declaration (hook round-4 iteration finding)
    tricky = ('CREATE VIRTUAL TABLE t USING fts5('
              '")", key UNINDEXED, "(", "a,b", module unindexed)')
    assert fts5_unindexed_columns(tricky) == {"key", "module"}


def test_skills_catalog_rejects_falsey_laundering(tmp_path):
    """Round-4 F3: `or {}`/`or []` laundering accepted falsey
    non-mappings — `status: false` would load, stringify to "False" and
    be silently dropped by SkillStore.load_all; `modules: false` loses
    module targeting; a non-mapping frontmatter has no fields at all."""
    root = tmp_path / "skills"
    (root / "a").mkdir(parents=True)
    skill = root / "a" / "SKILL.md"
    skill.write_text("---\nname: a\nstatus: false\n---\nbody\n",
                     encoding="utf-8")
    with pytest.raises(ValueError, match="status must be a scalar"):
        ka.skills_catalog(root, validate=True)
    skill.write_text("---\nname: a\nmodules: false\n---\nbody\n",
                     encoding="utf-8")
    with pytest.raises(ValueError, match="list of strings"):
        ka.skills_catalog(root, validate=True)
    skill.write_text("---\n- just\n- a-list\n---\nbody\n",
                     encoding="utf-8")
    with pytest.raises(ValueError, match="does not parse as a skill"):
        ka.skills_catalog(root, validate=True)
    # a plain healthy skill still validates
    skill.write_text("---\nname: a\ndescription: d\nmodules: [m]\n"
                     "---\nbody\n", encoding="utf-8")
    assert ka.skills_catalog(root, validate=True)
