"""Unit-A knowledge foundation (design: rebase-completion, GPT-approved).

Pins: KnowledgePaths byte-identity with the pre-resolver wiring (a pure
refactor — any drift here silently changes what PR6 validates), DebugMemory's
no-DDL-on-open / explicit-upgrade schema contract, the read-only open the
report-only prelude relies on, the shared/exclusive knowledge run-lock, the
crash-safe SkillStore rewrites, and the watchdog decision log's torn-tail
repair (a resumed writer must never fuse its record onto a crash fragment).
"""

import json
import sqlite3
from pathlib import Path

import pytest

from infermatrix_copilot.memory.debug_memory import (ADDITIVE_COLUMNS,
                                                     DebugMemory)
from infermatrix_copilot.memory.paths import (KnowledgeLockHeld,
                                              KnowledgePaths,
                                              KnowledgeRunLock)
from infermatrix_copilot.memory.skills import SkillStore
from infermatrix_copilot.testing import watchdog_learn


class _Settings:
    def __init__(self, home: Path):
        self.memory_db = home / "debug_memory.db"
        self.skills_dir = home / "shared-skills"


def _entry(**overrides):
    base = dict(
        repo="repo-x", module="core", run_id="run-1",
        symptom="ImportError: moved", root_cause="upstream moved it",
        fix_summary="update import", files=["a.py"],
        verification="pytest passed",
    )
    base.update(overrides)
    return base


# ── KnowledgePaths: byte-identity with the pre-resolver wiring ──────────────

def test_paths_byte_identity_with_adapter(tmp_path):
    s = _Settings(tmp_path / "home")
    adapter_root = tmp_path / "adapters" / "repo_x"
    p = KnowledgePaths.resolve(s, "repo-x", adapter_root=adapter_root)
    state = s.memory_db.parent / "state" / "repo-x"
    # each member must equal the exact expression its consumer used before
    assert p.rebase_backend_db == s.memory_db
    assert p.shared_write_db == adapter_root / "store" / "debug_memory.db"
    assert p.debug_read_layers == (
        adapter_root / "store" / "debug_memory.db", s.memory_db)
    assert p.skills_seed_dir == adapter_root / "skills"
    assert p.skills_runtime_dir == state / "skills_runtime"
    assert p.repo_map_cache_dir == adapter_root / "repo_map"
    assert p.watchdog_overlay == state / "watchdog_overlay.yaml"
    assert p.watchdog_decisions == state / "watchdog_decisions.jsonl"
    assert p.backups_dir == state / "backups"


def test_paths_byte_identity_without_adapter(tmp_path):
    s = _Settings(tmp_path / "home")
    p = KnowledgePaths.resolve(s, "repo-x")
    assert p.rebase_backend_db == s.memory_db
    assert p.shared_write_db == s.memory_db          # no-adapter fallback
    assert p.debug_read_layers == (s.memory_db,)
    assert p.skills_seed_dir == Path(s.skills_dir)   # shared pool
    assert p.repo_map_cache_dir is None              # caller's run-dir fallback


# ── DebugMemory schema contract ─────────────────────────────────────────────

def _legacy_db(path: Path) -> None:
    """A v1-schema db exactly as the pre-slice code created it."""
    c = sqlite3.connect(path)
    c.execute("""CREATE TABLE entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT, module TEXT, run_id TEXT,
        symptom TEXT, root_cause TEXT, fix_summary TEXT,
        files TEXT, verification TEXT,
        status TEXT DEFAULT 'active', created_at REAL)""")
    c.execute("""CREATE VIRTUAL TABLE entries_fts USING fts5(
        symptom, root_cause, fix_summary, module, repo,
        content='entries', content_rowid='id')""")
    c.commit()
    c.close()


def test_new_db_created_with_v2_columns(tmp_path):
    dm = DebugMemory(tmp_path / "m.db")
    assert dm.schema_v2
    rid = dm.record(**_entry(key="import-moved", tags=["import", "port"],
                             watch_outs="also check __init__",
                             upstream_commit="abc123", source="test"))
    row = dm.get(rid)
    assert row["key"] == "import-moved"
    assert row["tags"] == "import,port"
    assert row["upstream_commit"] == "abc123"
    assert row["run_count"] == 1
    # new-schema FTS indexes the additive text columns
    assert any(h["id"] == rid for h in dm.search("import-moved"))


def test_existing_db_untouched_at_open(tmp_path):
    db = tmp_path / "legacy.db"
    _legacy_db(db)
    dm = DebugMemory(db)
    assert not dm.schema_v2
    cols = {r[1] for r in dm._conn.execute("PRAGMA table_info(entries)")}
    assert set(ADDITIVE_COLUMNS).isdisjoint(cols)  # open performed no DDL
    # additive fields are dropped, never an SQL error
    rid = dm.record(**_entry(key="k1", tags=["t"]))
    row = dm._conn.execute("SELECT * FROM entries WHERE id=?",
                           (rid,)).fetchone()
    assert "key" not in row.keys()


def test_ensure_schema_v2_upgrades_and_reindexes(tmp_path):
    db = tmp_path / "legacy.db"
    _legacy_db(db)
    dm = DebugMemory(db)
    dm.record(**_entry())
    assert dm.ensure_schema_v2() is True
    assert dm.schema_v2
    assert dm.ensure_schema_v2() is False  # idempotent
    rid = dm.record(**_entry(key="fresh-key", symptom="other symptom",
                             root_cause="rc", fix_summary="fs"))
    assert any(h["id"] == rid for h in dm.search("fresh-key"))
    # pre-upgrade row survived with defaults
    assert dm.count() == 2
    assert dm.get(1)["run_count"] == 1


def test_open_readonly_contract(tmp_path):
    with pytest.raises(FileNotFoundError):
        DebugMemory.open_readonly(tmp_path / "absent" / "m.db")
    assert not (tmp_path / "absent").exists()  # no mkdir side effect
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"not a database at all")
    with pytest.raises(sqlite3.DatabaseError):
        DebugMemory.open_readonly(corrupt)
    db = tmp_path / "m.db"
    DebugMemory(db).record(**_entry())
    before = db.stat().st_mtime_ns
    ro = DebugMemory.open_readonly(db)
    assert ro.search("ImportError")
    with pytest.raises(sqlite3.OperationalError):
        ro.ensure_schema_v2()
    assert db.stat().st_mtime_ns == before  # provably no write


def test_unrelated_existing_db_is_refused(tmp_path):
    other = tmp_path / "other.db"
    sqlite3.connect(other).executescript("CREATE TABLE t (x);")
    with pytest.raises(sqlite3.DatabaseError, match="not a debug memory"):
        DebugMemory(other)
    # …and it was not mutated into a debug store
    tables = {r[0] for r in sqlite3.connect(other).execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"t"}


def test_empty_file_initializes_as_new_store(tmp_path):
    db = tmp_path / "empty.db"
    db.touch()  # 0-byte pre-created file: sqlite's own "new database" shape
    dm = DebugMemory(db)
    assert dm.schema_v2


def test_half_created_db_is_repaired_on_open(tmp_path):
    db = tmp_path / "half.db"
    c = sqlite3.connect(db)
    c.execute("""CREATE TABLE entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT, module TEXT, run_id TEXT,
        symptom TEXT, root_cause TEXT, fix_summary TEXT,
        files TEXT, verification TEXT,
        status TEXT DEFAULT 'active', created_at REAL)""")
    c.execute(
        "INSERT INTO entries (repo, module, run_id, symptom, root_cause, "
        "fix_summary, files, verification, status) "
        "VALUES ('r','m','run-0','pre-repair OOM symptom','rc','fs','[]',"
        "'v','active')")
    c.commit()
    c.close()  # crash window: entries landed (with a row), mirror did not
    dm = DebugMemory(db)
    # the repair BACKFILLS the mirror: the pre-repair row is searchable
    assert any(h["id"] == 1 for h in dm.search("pre-repair OOM"))
    rid = dm.record(**_entry())
    assert any(h["id"] == rid for h in dm.search("ImportError"))
    # the repaired legacy mirror indexes only the columns entries HAS
    fts_cols = {r[1] for r in dm._conn.execute(
        "PRAGMA table_info(entries_fts)")}
    assert "key" not in fts_cols


def test_readonly_uri_handles_hostile_filenames(tmp_path):
    weird = tmp_path / "a?b%c#d.db"
    DebugMemory(weird).record(**_entry())
    ro = DebugMemory.open_readonly(weird)
    assert ro.count() == 1


def test_concurrent_proposes_lose_nothing(tmp_path):
    import threading

    store = SkillStore(tmp_path / "skills")
    names = [f"s{i}" for i in range(16)]
    threads = [threading.Thread(
        target=lambda n=n: SkillStore(tmp_path / "skills").propose(
            name=n, description="d", body="b")) for n in names]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert set(store.candidates()) == set(names)  # no lost update


# ── Knowledge run-lock ──────────────────────────────────────────────────────

def test_knowledge_lock_shared_and_exclusive(tmp_path):
    lock_path = tmp_path / "locks" / "knowledge.lock"
    a = KnowledgeRunLock(lock_path).acquire_shared()
    b = KnowledgeRunLock(lock_path).acquire_shared()  # runs never contend
    with pytest.raises(KnowledgeLockHeld, match="run for this repo is active"):
        KnowledgeRunLock(lock_path).acquire_exclusive()
    a.release()
    b.release()
    excl = KnowledgeRunLock(lock_path).acquire_exclusive()
    with pytest.raises(KnowledgeLockHeld, match="migration is in progress"):
        KnowledgeRunLock(lock_path).acquire_shared()
    excl.release()
    KnowledgeRunLock(lock_path).acquire_shared().release()


# ── SkillStore crash-safe rewrites ──────────────────────────────────────────

def test_candidates_rewrite_is_atomic_under_crash(tmp_path, monkeypatch):
    store = SkillStore(tmp_path / "skills")
    store.propose(name="s1", description="d", body="b")
    good = store.candidates_file.read_text(encoding="utf-8")

    import infermatrix_copilot.memory.skills as skills_mod
    real_replace = skills_mod.os.replace

    def crash_replace(src, dst):  # crash BEFORE the atomic rename lands
        raise OSError("simulated crash at rename")

    monkeypatch.setattr(skills_mod.os, "replace", crash_replace)
    with pytest.raises(OSError):
        store.propose(name="s2", description="d2", body="b2")
    monkeypatch.setattr(skills_mod.os, "replace", real_replace)
    # the old content is intact and parseable — never truncated
    assert store.candidates_file.read_text(encoding="utf-8") == good
    assert set(store.candidates()) == {"s1"}


def test_touch_preserves_file_on_crash(tmp_path, monkeypatch):
    store = SkillStore(tmp_path / "skills")
    store.propose(name="s1", description="d", body="body text")
    store.promote("s1")
    path = tmp_path / "skills" / "s1" / "SKILL.md"
    good = path.read_text(encoding="utf-8")

    import infermatrix_copilot.memory.skills as skills_mod

    monkeypatch.setattr(skills_mod.os, "replace",
                        lambda s, d: (_ for _ in ()).throw(OSError("crash")))
    assert store.touch("s1") is False  # touch never raises
    assert path.read_text(encoding="utf-8") == good


# ── Watchdog decision log: identity + torn-tail repair ──────────────────────

def test_record_carries_identity_fields(tmp_path):
    log = tmp_path / "d.jsonl"
    watchdog_learn.record(log, pattern="CUDA error: device-side assert",
                          verdict="KILL", test="t1", run="run-9",
                          attempt="a1", job_key="job-x", seq=3)
    entry = json.loads(log.read_text(encoding="utf-8").strip())
    assert (entry["run"], entry["attempt"], entry["job_key"], entry["seq"]) \
        == ("run-9", "a1", "job-x", 3)


def test_resumed_record_never_fuses_onto_torn_tail(tmp_path):
    log = tmp_path / "d.jsonl"
    watchdog_learn.record(log, pattern="first line pattern", verdict="CONTINUE",
                          test="t0", run="r", seq=1)
    with open(log, "ab") as fh:      # crash fragment: no trailing newline
        fh.write(b'{"ts": "2026-01-01 00:00:00", "pattern": "torn frag')
    watchdog_learn.record(log, pattern="resumed pattern", verdict="CONTINUE",
                          test="t1", run="r", seq=2)
    lines = log.read_text(encoding="utf-8").splitlines()
    parsed = [json.loads(ln) for ln in lines]  # every line parses
    assert [p["seq"] for p in parsed] == [1, 2]
    assert all("torn frag" not in ln for ln in lines)
    # and read_decisions sees exactly both real records
    assert len(watchdog_learn.read_decisions(log)) == 2
