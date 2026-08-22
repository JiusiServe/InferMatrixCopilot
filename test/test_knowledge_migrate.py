"""Unit B — the PR4d migration machinery + repo-scoped activation.

Pins the design's D1/D3/D6/D7/D8 contracts: dormancy (flag off ⇒
byte-identical resolution; flag on ⇒ marker-gated state-dir paths),
migration correctness (complete mapping for both schema families, source
identity idempotency, changed-row versioning, WAL sources, dedup with
lineage, preserved runtime state, journaled crash redo, dry run), the
lock exclusions, and Unit-A independence (no Unit-A module imports the
migration module).
"""

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from infermatrix_copilot.memory.debug_memory import DebugMemory
from infermatrix_copilot.memory.paths import (KnowledgeLockHeld,
                                              KnowledgePaths,
                                              KnowledgeRunLock,
                                              KnowledgeStateError)
from infermatrix_copilot.rebase_engine.knowledge_migrate import (
    MigrationError, migrate_knowledge)
from test_parent_compat import _parent_db

REPO_ROOT = Path(__file__).resolve().parents[1]


def _world(settings, tmp_path, parent_rows=(), with_skills=True):
    """A migration world: adapter + git-less repo + parent stores."""
    repo = tmp_path / "widget"
    (repo / "locks").mkdir(parents=True, exist_ok=True)
    parent_root = tmp_path / "parent"
    (parent_root / "agent" / "store").mkdir(parents=True, exist_ok=True)
    db = _parent_db(parent_root / "agent" / "store" / "debug_memory.db",
                    list(parent_rows))
    skills = parent_root / "agent" / "skills"
    if with_skills:
        (skills / "parent-skill").mkdir(parents=True, exist_ok=True)
        (skills / "parent-skill" / "SKILL.md").write_text(
            "---\nname: parent-skill\ndescription: lore\n---\nbody\n",
            encoding="utf-8")
        (skills / "_candidates.json").write_text(json.dumps(
            {"cand-1": {"description": "d", "body": "b", "modules": []}}),
            encoding="utf-8")
    adir = Path(settings.adapters_dir) / "widget_repo"
    (adir / "skills").mkdir(parents=True, exist_ok=True)
    (adir / "manifest.yaml").write_text(yaml.safe_dump({
        "name": "widget_repo", "status": "active",
        "repo": {"path": str(repo)}, "modules": {},
        "rebase": {"lock_name": "widget",
                   "knowledge": {
                       "parent_debug_db": str(db),
                       "parent_skills_dir": str(skills),
                       "parent_upstream_column": "vllm_commit"}}}))
    return repo, db, skills, adir


PARENT_ROWS = [
    {"key": "caplog-empty", "symptom": "caplog empty assertion",
     "root_cause": "propagate False", "fix": "capture at emitter",
     "vllm_commit": "abc123"},
    {"key": "import-moved", "symptom": "ImportError moved",
     "root_cause": "moved", "fix": "fix import", "status": "inactive"},
]


def test_migration_full_pass_and_idempotency(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    report = migrate_knowledge(settings, "widget-repo")
    assert report.ingested == 2 and report.skipped_unchanged == 0
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    assert (state_dir / "MIGRATION_COMPLETE.json").exists()
    assert (state_dir / "MIGRATION_REPORT.md").exists()
    target = DebugMemory(state_dir / "debug_memory.db")
    rows = {r["key"]: r for r in target.entries(
        repo="widget-repo",
        statuses=("active", "candidate", "stale", "retired"))}
    # complete mapping: fix→fix_summary, vllm_commit→upstream_commit,
    # inactive→stale, verification synthesized, source self-contained
    assert rows["caplog-empty"]["fix_summary"] == "capture at emitter"
    assert rows["caplog-empty"]["upstream_commit"] == "abc123"
    assert rows["caplog-empty"]["source"].startswith("parent-db#1@")
    assert rows["caplog-empty"]["verification"].startswith(
        "migrated from parent store")
    assert rows["import-moved"]["status"] == "stale"
    # seed skill installed as a git-visible adapter add + candidate merged
    assert (adir / "skills" / "parent-skill" / "SKILL.md").exists()
    assert report.candidates_merged == 1
    # strict no-op on identical frozen inputs
    report2 = migrate_knowledge(settings, "widget-repo")
    assert (report2.ingested, report2.reversioned) == (0, 0)
    assert report2.skipped_unchanged == 2


def test_changed_source_row_versions_only_itself(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    migrate_knowledge(settings, "widget-repo")
    c = sqlite3.connect(db)
    c.execute("UPDATE debug_entries SET fix='capture at the RIGHT emitter' "
              "WHERE key='caplog-empty'")
    c.commit()
    c.close()
    report = migrate_knowledge(settings, "widget-repo")
    assert report.reversioned == 1
    assert report.skipped_unchanged == 1  # the untouched row skips
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    target = DebugMemory(state_dir / "debug_memory.db")
    versions = [r for r in target.entries(
        repo="widget-repo",
        statuses=("active", "candidate", "stale", "retired"))
        if r["key"] == "caplog-empty"]
    live = [r for r in versions if r["status"] != "retired"]
    old = [r for r in versions if r["status"] == "retired"]
    assert len(live) == 1 and len(old) == 1
    assert live[0]["fix_summary"] == "capture at the RIGHT emitter"
    assert old[0]["derived_from"] == str(live[0]["id"])


def test_wal_only_rows_are_migrated(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS[:1])
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO debug_entries (module, key, symptom) "
              "VALUES ('m','wal-only','committed in wal')")
    c.commit()  # no checkpoint — lives in -wal
    report = migrate_knowledge(settings, "widget-repo")
    c.close()
    assert report.ingested == 2
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    target = DebugMemory(state_dir / "debug_memory.db")
    keys = {r["key"] for r in target.entries(repo="widget-repo")}
    assert "wal-only" in keys


def test_preserved_runtime_state_and_legacy_sources(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS[:1])
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    # pre-existing runtime state that migration must NOT touch
    overlay = state_dir / "watchdog_overlay.yaml"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_text("noise: [x]\n", encoding="utf-8")
    runtime_skill = state_dir / "skills_runtime" / "learned" / "SKILL.md"
    runtime_skill.parent.mkdir(parents=True, exist_ok=True)
    runtime_skill.write_text("---\nname: learned\n---\nbody\n",
                             encoding="utf-8")
    # legacy copilot source rows (global store)
    legacy = DebugMemory(settings.memory_db)
    legacy.record(repo="widget-repo", module="core", run_id="r",
                  symptom="legacy row without key", root_cause="rc",
                  fix_summary="fs", files=["a.py"], verification="v")
    # a FOREIGN repo's row in the shared global store must never migrate
    # into this repo's state DB (hook finding)
    legacy.record(repo="other-repo", module="m", run_id="r",
                  symptom="foreign knowledge", root_cause="rc",
                  fix_summary="fs", files=["z.py"], verification="v")
    report = migrate_knowledge(settings, "widget-repo")
    assert report.ingested == 2  # parent + THIS repo's legacy row only
    assert overlay.read_text(encoding="utf-8") == "noise: [x]\n"
    assert runtime_skill.exists()
    target = DebugMemory(state_dir / "debug_memory.db")
    all_rows = target.entries(
        repo=None, statuses=("active", "candidate", "stale", "retired"))
    assert all(r["repo"] == "widget-repo" for r in all_rows)
    legacy_row = [r for r in target.entries(repo="widget-repo")
                  if r["source"].startswith("copilot-global#")][0]
    assert legacy_row["key"] == "legacy-row-without-key"  # synthesized


def test_dedup_retires_with_lineage_across_sources(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, [
        {"key": "same-key", "symptom": "s", "fix": "parent fix"}])
    legacy = DebugMemory(settings.memory_db)
    legacy.record(repo="widget-repo", module="m", run_id="r",
                  symptom="s", root_cause="rc", fix_summary="copilot fix",
                  files=["a.py"], verification="v", key="same-key")
    report = migrate_knowledge(settings, "widget-repo")
    assert report.retired_by_dedup >= 1
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    target = DebugMemory(state_dir / "debug_memory.db")
    rows = [r for r in target.entries(
        repo="widget-repo",
        statuses=("active", "candidate", "stale", "retired"))
        if r["key"] == "same-key"]
    live = [r for r in rows if r["status"] != "retired"]
    assert len(live) == 1
    # precedence: copilot-global beats parent-db
    assert live[0]["source"].startswith("copilot-global#")


def test_near_dup_dedup_honors_source_precedence(settings, tmp_path):
    """PR-boundary F11: a freshly imported parent near-duplicate (with a
    DIFFERENT key, so only the Jaccard pass sees it) must never retire
    higher-priority runtime knowledge, even though it is newer."""
    repo, db, skills, adir = _world(settings, tmp_path, [
        {"key": "parent-flavor", "symptom": "watchdog kill on OOM growth "
         "in warmup", "root_cause": "leaked pin buffers",
         "fix": "parent fix"}])
    legacy = DebugMemory(settings.memory_db)
    legacy.record(repo="widget-repo", module="m",
                  run_id="r", key="runtime-flavor",
                  symptom="watchdog kill on OOM growth in warmup",
                  root_cause="leaked pin buffers",
                  fix_summary="runtime fix", files=["a.py"],
                  verification="v", source="v3-agent")
    migrate_knowledge(settings, "widget-repo")
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    target = DebugMemory(state_dir / "debug_memory.db")
    rows = {r["key"]: r for r in target.entries(
        repo="widget-repo",
        statuses=("active", "candidate", "stale", "retired"))}
    live = [k for k, r in rows.items() if r["status"] != "retired"
            and k in ("parent-flavor", "runtime-flavor")]
    # the runtime-sourced row survives; the parent near-dup retires
    assert live == ["runtime-flavor"], rows
    assert rows["parent-flavor"]["status"] == "retired"


def test_migrated_rows_exempt_from_dormancy(settings, tmp_path):
    """PR-boundary F12: the first post-activation curate must not mark
    freshly migrated parent facts stale — their run ids live in a foreign
    id space that can never appear in the copilot's run window."""
    from infermatrix_copilot.memory.curator import DebugMemoryCurator

    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS[:1])
    migrate_knowledge(settings, "widget-repo")
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    target = DebugMemory(state_dir / "debug_memory.db")
    report = DebugMemoryCurator(target, repo="widget-repo").curate(
        recent_runs=[f"run-2026{i:04d}" for i in range(12)])
    assert report.dormant == 0
    rows = {r["key"]: r["status"] for r in target.entries(
        repo="widget-repo",
        statuses=("active", "candidate", "stale", "retired"))}
    assert rows["caplog-empty"] == "active"


def test_migration_validates_upstream_column_and_skills(settings,
                                                        tmp_path):
    """Round-2 F6/F7: a mistyped declared upstream column and a malformed
    declared parent skill each REFUSE before any mutation — silently
    mapping commits to "" or copying files retrieval skips would stamp a
    completion that strands knowledge."""
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    manifest_path = adir / "manifest.yaml"
    doc = yaml.safe_load(manifest_path.read_text())
    doc["rebase"]["knowledge"]["parent_upstream_column"] = "no_such_col"
    manifest_path.write_text(yaml.safe_dump(doc))
    with pytest.raises(MigrationError, match="retrieval-schema probe"):
        migrate_knowledge(settings, "widget-repo")
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    assert not (state_dir / "MIGRATION_COMPLETE.json").exists()
    # restore the column; break a skill instead
    doc["rebase"]["knowledge"]["parent_upstream_column"] = "vllm_commit"
    manifest_path.write_text(yaml.safe_dump(doc))
    (skills / "broken").mkdir()
    (skills / "broken" / "SKILL.md").write_text("no frontmatter\n",
                                                encoding="utf-8")
    with pytest.raises(MigrationError, match="skills invalid"):
        migrate_knowledge(settings, "widget-repo")
    assert not (state_dir / "MIGRATION_COMPLETE.json").exists()


def test_activation_refuses_masquerading_fts_table(settings, tmp_path):
    """Hook iteration-2 finding: a PLAIN table named entries_fts with the
    right column names satisfies introspection but fails every MATCH —
    the usability probe must keep it from activating."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "debug_memory.db"
    dm = DebugMemory(db_path)
    dm._conn.execute("DROP TABLE entries_fts")
    dm._conn.execute(
        "CREATE TABLE entries_fts (symptom, root_cause, fix_summary, "
        "module, repo, key, tags, watch_outs)")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError,
                       match="fully-indexed FTS5"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_activation_refuses_legacy_fts_mirror(settings, tmp_path):
    """Round-2 F5: a store whose entries are v2 but whose FTS mirror is
    the LEGACY column set must not activate — retrieval would silently
    miss key/tags/watch_outs terms."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "debug_memory.db"
    dm = DebugMemory(db_path)  # fresh v2 store (v2 mirror)
    # downgrade the MIRROR only
    dm._conn.execute("DROP TABLE entries_fts")
    dm._conn.execute(
        """CREATE VIRTUAL TABLE entries_fts USING fts5(
            symptom, root_cause, fix_summary, module, repo,
            content='entries', content_rowid='id')""")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError, match="FTS mirror lacks"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_dry_run_writes_only_the_report(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    report = migrate_knowledge(settings, "widget-repo", dry_run=True)
    assert report.ingested == 2
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    assert (state_dir / "MIGRATION_REPORT.md").exists()
    assert not (state_dir / "MIGRATION_COMPLETE.json").exists()
    assert not (state_dir / "debug_memory.db").exists()
    assert not (adir / "skills" / "parent-skill").exists()


def test_migration_refused_while_run_lock_shared(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    kp = KnowledgePaths.resolve(settings, "widget-repo")
    held = KnowledgeRunLock(kp.knowledge_run_lock).acquire_shared()
    try:
        with pytest.raises(KnowledgeLockHeld):
            migrate_knowledge(settings, "widget-repo")
    finally:
        held.release()


def test_pre_existing_seed_skill_is_a_collision_not_overwritten(
        settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    dest = adir / "skills" / "parent-skill"
    dest.mkdir(parents=True)
    original = "---\nname: parent-skill\ndescription: mine\n---\nlocal\n"
    (dest / "SKILL.md").write_text(original, encoding="utf-8")
    report = migrate_knowledge(settings, "widget-repo")
    # existing adapter skill wins; the parent copy is reported only
    assert "parent-skill" in report.skills_collisions
    assert (dest / "SKILL.md").read_text(encoding="utf-8") == original


def test_seed_redo_digest_matching_after_crash(settings, tmp_path,
                                               monkeypatch):
    """Round-3 F6: after a crash left a journal, a file that APPEARED at a
    planned seed path is adopted only on an exact digest match; different
    content fails closed — never silently re-classified as a collision."""
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    import infermatrix_copilot.rebase_engine.knowledge_migrate as km
    real_replace = km.os.replace
    calls = []

    def crashing_replace(src, dst):
        if str(dst).endswith("debug_memory.db") and not calls:
            calls.append(1)
            raise OSError("simulated crash before seed install")
        return real_replace(src, dst)

    monkeypatch.setattr(km.os, "replace", crashing_replace)
    with pytest.raises(OSError):
        migrate_knowledge(settings, "widget-repo")
    monkeypatch.setattr(km.os, "replace", real_replace)
    # someone else's file appears at the JOURNALED planned path
    dest = adir / "skills" / "parent-skill"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("---\nname: unrelated\n---\nother\n",
                                   encoding="utf-8")
    with pytest.raises(MigrationError, match="DIFFERENT"):
        migrate_knowledge(settings, "widget-repo")
    # with the EXACT planned content in place instead, redo converges
    (dest / "SKILL.md").write_text(
        (skills / "parent-skill" / "SKILL.md").read_text(encoding="utf-8"),
        encoding="utf-8")
    report = migrate_knowledge(settings, "widget-repo")
    assert (Path(settings.memory_db).parent / "state" / "widget-repo"
            / "MIGRATION_COMPLETE.json").exists()
    assert "parent-skill" not in report.skills_collisions


def test_crash_between_journal_and_replace_redoes(settings, tmp_path,
                                                  monkeypatch):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    import infermatrix_copilot.rebase_engine.knowledge_migrate as km
    real_replace = km.os.replace
    calls = []

    def crashing_replace(src, dst):
        if str(dst).endswith("debug_memory.db") and not calls:
            calls.append(1)
            raise OSError("simulated crash at the DB replace")
        return real_replace(src, dst)

    monkeypatch.setattr(km.os, "replace", crashing_replace)
    with pytest.raises(OSError):
        migrate_knowledge(settings, "widget-repo")
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    assert (state_dir / ".migration-journal.json").exists()  # redo signal
    assert not (state_dir / "MIGRATION_COMPLETE.json").exists()
    monkeypatch.setattr(km.os, "replace", real_replace)
    report = migrate_knowledge(settings, "widget-repo")  # redo converges
    assert report.ingested == 2
    assert (state_dir / "MIGRATION_COMPLETE.json").exists()
    assert not (state_dir / ".migration-journal.json").exists()


def test_target_wal_rows_survive_failed_swap(settings, tmp_path,
                                             monkeypatch):
    """Hook iteration-2 finding: committed rows living only in the
    TARGET's WAL must survive a failure at the final replace — the swap
    checkpoints the old target before touching sidecars and rolls back
    on failure, so the redo re-snapshots an undamaged store."""
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS[:1])
    migrate_knowledge(settings, "widget-repo")
    state_db = Path(settings.memory_db).parent / "state" / "widget-repo" \
        / "debug_memory.db"
    # a post-migration runtime write, committed but WAL-resident
    c = sqlite3.connect(state_db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("INSERT INTO entries (repo, module, run_id, symptom, "
              "root_cause, fix_summary, files, verification, status, key) "
              "VALUES ('widget-repo','m','r','wal resident row','rc','fs',"
              "'[]','v','active','wal-resident')")
    c.commit()  # no checkpoint; keep the connection open so the WAL lives
    # force re-migration work so the swap actually runs
    pc = sqlite3.connect(db)
    pc.execute("UPDATE debug_entries SET fix='changed' "
               "WHERE key='caplog-empty'")
    pc.commit()
    pc.close()
    import infermatrix_copilot.rebase_engine.knowledge_migrate as km
    real_replace = km.os.replace
    calls = []

    def failing_replace(src, dst):
        if str(dst).endswith("debug_memory.db") and \
                "state" in str(dst) and not calls:
            calls.append(1)
            raise OSError("simulated swap failure")
        return real_replace(src, dst)

    monkeypatch.setattr(km.os, "replace", failing_replace)
    with pytest.raises(OSError, match="simulated swap"):
        migrate_knowledge(settings, "widget-repo")
    monkeypatch.setattr(km.os, "replace", real_replace)
    c.close()
    # marker-invalid-first (hook iteration-3 finding): the crashed rerun
    # must have taken the old MIGRATION_COMPLETE with it — an activated
    # runtime now fails CLOSED instead of starting against a
    # half-migrated world
    state_dir = state_db.parent
    assert not (state_dir / "MIGRATION_COMPLETE.json").exists()
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError):
        KnowledgePaths.resolve(settings, "widget-repo")
    settings.imx_knowledge_runtime = ""
    # the WAL-resident row is still there, and the redo keeps it — and
    # restores the marker as its final act
    keys = {r["key"] for r in DebugMemory(state_db).entries(
        repo="widget-repo")}
    assert "wal-resident" in keys
    migrate_knowledge(settings, "widget-repo")
    keys = {r["key"] for r in DebugMemory(state_db).entries(
        repo="widget-repo")}
    assert "wal-resident" in keys
    assert (state_dir / "MIGRATION_COMPLETE.json").exists()


# ── activation flag (D1/D3) ─────────────────────────────────────────────────

def test_flag_off_is_byte_identical(settings, tmp_path):
    adapter_root = tmp_path / "adapters" / "widget_repo"
    p_off = KnowledgePaths.resolve(settings, "widget-repo",
                                   adapter_root=adapter_root)
    assert p_off.rebase_backend_db == Path(settings.memory_db)
    assert p_off.shared_write_db == adapter_root / "store" / \
        "debug_memory.db"


def test_flag_on_requires_marker_and_is_repo_scoped(settings, tmp_path):
    settings.imx_knowledge_runtime = "widget-repo"
    # listed repo without a marker: FAIL CLOSED
    with pytest.raises(KnowledgeStateError, match="migrate-knowledge"):
        KnowledgePaths.resolve(settings, "widget-repo")
    # a DIFFERENT repo is untouched by the activation (round-4 F2)
    other = KnowledgePaths.resolve(settings, "other-repo")
    assert other.rebase_backend_db == Path(settings.memory_db)
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    marker = state_dir / "MIGRATION_COMPLETE.json"
    # a marker COPIED from another repo never activates
    marker.write_text(json.dumps(
        {"schema": "v2", "repo": "someone-else",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    with pytest.raises(KnowledgeStateError, match="copied/stale"):
        KnowledgePaths.resolve(settings, "widget-repo")
    # an unknown schema version never activates
    marker.write_text(json.dumps(
        {"schema": "v9", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    with pytest.raises(KnowledgeStateError, match="unknown schema"):
        KnowledgePaths.resolve(settings, "widget-repo")
    # a valid marker with a MISSING target store never activates
    marker.write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    with pytest.raises(KnowledgeStateError, match="missing, unreadable"):
        KnowledgePaths.resolve(settings, "widget-repo")
    # with a marker AND a real store the debug members converge on it
    DebugMemory(state_dir / "debug_memory.db")
    p_on = KnowledgePaths.resolve(settings, "widget-repo",
                                  adapter_root=tmp_path / "a")
    assert p_on.rebase_backend_db == state_dir / "debug_memory.db"
    assert p_on.shared_write_db == state_dir / "debug_memory.db"
    assert p_on.debug_read_layers == (state_dir / "debug_memory.db",)
    assert p_on.repo_map_cache_dir == state_dir / "repo_map"
    # seed dir stays the adapter tree — read-only knowledge is not moved
    assert p_on.skills_seed_dir == tmp_path / "a" / "skills"


def test_activation_rejects_legacy_or_thin_fts_store(settings, tmp_path):
    """PR-boundary round-2 F5: the marker gate verifies the STORE — a
    legacy-schema db or a v2 db whose FTS mirror lacks the v2 columns
    never activates, whatever the marker claims."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    # legacy-schema store: refuses
    c = sqlite3.connect(state_dir / "debug_memory.db")
    c.executescript("""CREATE TABLE entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT, module TEXT, run_id TEXT, symptom TEXT, root_cause TEXT,
        fix_summary TEXT, files TEXT, verification TEXT,
        status TEXT DEFAULT 'active', created_at REAL);
        CREATE VIRTUAL TABLE entries_fts USING fts5(
        symptom, root_cause, fix_summary, module, repo,
        content='entries', content_rowid='id');""")
    c.close()
    with pytest.raises(KnowledgeStateError, match="not schema v2"):
        KnowledgePaths.resolve(settings, "widget-repo")
    # v2 columns but a THIN mirror: refuses too
    (state_dir / "debug_memory.db").unlink()
    dm = DebugMemory(state_dir / "debug_memory.db")
    dm._conn.executescript(
        "DROP TABLE entries_fts;"
        "CREATE VIRTUAL TABLE entries_fts USING fts5("
        "symptom, content='entries', content_rowid='id');")
    with pytest.raises(KnowledgeStateError, match="FTS mirror lacks"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_migration_validates_column_and_skills(settings, tmp_path):
    """PR-boundary round-2 F6/F7: a mistyped parent_upstream_column and a
    malformed declared skill each refuse the migration up front."""
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    manifest = yaml.safe_load((adir / "manifest.yaml").read_text())
    manifest["rebase"]["knowledge"]["parent_upstream_column"] = "no_such"
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    with pytest.raises(MigrationError, match="retrieval-schema probe"):
        migrate_knowledge(settings, "widget-repo")
    manifest["rebase"]["knowledge"]["parent_upstream_column"] = \
        "vllm_commit"
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    (skills / "broken").mkdir()
    (skills / "broken" / "SKILL.md").write_text("no frontmatter\n",
                                                encoding="utf-8")
    with pytest.raises(MigrationError, match="skills invalid"):
        migrate_knowledge(settings, "widget-repo")


def test_full_cycle_migrate_then_activate(settings, tmp_path):
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    migrate_knowledge(settings, "widget-repo")
    settings.imx_knowledge_runtime = "widget-repo"
    kp = KnowledgePaths.resolve(settings, "widget-repo",
                                adapter_root=adir)
    dm = DebugMemory.open_readonly(kp.rebase_backend_db)
    assert dm.count() == 2  # the migrated knowledge is what runs now see


def test_activation_error_exits_blocked_and_releases_run_lock(
        settings, tmp_path, git_repo, capsys):
    """PR-boundary F4: an invalid activation marker raised during the
    knowledge-lock acquisition must exit blocked/3 with the RUN LOCK
    released — never a traceback that leaves it held in a long-lived
    process."""
    import shutil

    from infermatrix_copilot.cli import Copilot
    from infermatrix_copilot.config import _REPO_ROOT
    from infermatrix_copilot.engine.lifecycle import RunLock
    from infermatrix_copilot.notify import BLOCKED_EXIT
    from infermatrix_copilot.task_spec import TaskSpec

    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(_REPO_ROOT / "playbooks" / "repo-rebase.yaml",
                settings.playbooks_dir / "repo-rebase.yaml")
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    settings.imx_knowledge_runtime = "vllm-omni"  # activated, NO marker
    copilot = Copilot(settings)
    spec = TaskSpec(kind="repo_rebase", repo="vllm-omni")
    res = copilot.resolve(spec)
    run_dir = Path(settings.run_root) / "run-actblocked"
    run_dir.mkdir(parents=True)
    code = copilot._execute(res.playbook, spec, run_dir)
    assert code == BLOCKED_EXIT
    out = capsys.readouterr().out
    assert "migrate-knowledge" in out  # the KnowledgeStateError surfaced
    # the run lock is reacquirable — nothing leaked
    relock = RunLock(run_dir).acquire()
    relock.release()


# ── Unit-A independence (round-2 F1) ────────────────────────────────────────

def test_unit_a_never_imports_unit_b():
    """Reverting Unit B (knowledge_migrate + the flag branch) must leave
    Unit A whole: no Unit-A module may import the migration module."""
    src = REPO_ROOT / "src" / "infermatrix_copilot"
    offenders = []
    for path in src.rglob("*.py"):
        if path.name == "knowledge_migrate.py":
            continue
        if path.relative_to(src).as_posix().startswith("cli/entry"):
            continue  # the CLI dispatch line is part of Unit B's commit
        if "knowledge_migrate" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(src).as_posix())
    assert offenders == [], offenders


def test_migration_rejects_pseudo_column_upstream(settings, tmp_path):
    """Round-3 F5: `rowid` SELECTs fine on any rowid table, so the bare
    probe accepted it — yet it is not a real debug_entries column and
    every later dict lookup would miss. Exact table_xinfo membership
    must refuse it."""
    repo, db, skills, adir = _world(settings, tmp_path, PARENT_ROWS)
    manifest = yaml.safe_load((adir / "manifest.yaml").read_text())
    manifest["rebase"]["knowledge"]["parent_upstream_column"] = "rowid"
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    with pytest.raises(MigrationError, match="not an exact column"):
        migrate_knowledge(settings, "widget-repo")


def test_activation_refuses_fts4_with_fts5_named_column(settings,
                                                        tmp_path):
    """Commit-review hardening: an FTS4 mirror with an extra column
    literally NAMED `fts5` defeated a substring engine check — the
    activation gate must verify `USING fts5(` structurally."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    dm = DebugMemory(state_dir / "debug_memory.db")
    dm._conn.executescript(
        "DROP TABLE entries_fts;"
        "CREATE VIRTUAL TABLE entries_fts USING fts4("
        "symptom, root_cause, fix_summary, module, repo, key, tags, "
        "watch_outs, fts5);")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError, match="fully-indexed FTS5"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_activation_refuses_unindexed_mirror_column(settings, tmp_path):
    """Round-3 F4 (marker side): a v2 store whose FTS5 mirror declares a
    required column UNINDEXED has the right names but silently misses
    every term in that column — activation must refuse."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    dm = DebugMemory(state_dir / "debug_memory.db")
    dm._conn.executescript(
        "DROP TABLE entries_fts;"
        "CREATE VIRTUAL TABLE entries_fts USING fts5("
        "symptom, root_cause, fix_summary, module, repo, key, tags, "
        "watch_outs UNINDEXED, content='entries', content_rowid='id');")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError, match="fully-indexed FTS5"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_activation_strips_comments_before_fts5_check(settings, tmp_path):
    """Hook iteration-2 (marker side): a comment carrying `USING fts5(`
    ahead of the real `USING fts4` must not pass the mirror check."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    dm = DebugMemory(state_dir / "debug_memory.db")
    dm._conn.executescript(
        "DROP TABLE entries_fts;"
        "CREATE VIRTUAL TABLE entries_fts /* USING fts5( */ USING fts4("
        "symptom, root_cause, fix_summary, module, repo, key, tags, "
        "watch_outs);")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError, match="fully-indexed FTS5"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_activation_rejects_quoted_identifier_fts5_spoof(settings,
                                                         tmp_path):
    """Hook iteration-3 (marker side): the quoted-identifier spoof —
    an FTS4 mirror whose first column is named `[USING fts5(]` — must
    not activate."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    dm = DebugMemory(state_dir / "debug_memory.db")
    dm._conn.executescript(
        "DROP TABLE entries_fts;"
        "CREATE VIRTUAL TABLE entries_fts USING fts4([USING fts5(], "
        "symptom, root_cause, fix_summary, module, repo, key, tags, "
        "watch_outs);")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError, match="fully-indexed FTS5"):
        KnowledgePaths.resolve(settings, "widget-repo")


def test_activation_quoted_paren_cannot_hide_unindexed(settings,
                                                       tmp_path):
    """Hook iteration (marker side): the quoted-`)` early-termination
    spoof must not let an UNINDEXED mirror column activate."""
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    state_dir.mkdir(parents=True, exist_ok=True)
    dm = DebugMemory(state_dir / "debug_memory.db")
    dm._conn.executescript(
        "DROP TABLE entries_fts;"
        'CREATE VIRTUAL TABLE entries_fts USING fts5("x)", '
        "repo UNINDEXED, symptom, root_cause, fix_summary, module, key, "
        "tags, watch_outs);")
    dm._conn.commit()
    (state_dir / "MIGRATION_COMPLETE.json").write_text(json.dumps(
        {"schema": "v2", "repo": "widget-repo",
         "digests": {"target_db": "x"}}), encoding="utf-8")
    settings.imx_knowledge_runtime = "widget-repo"
    with pytest.raises(KnowledgeStateError, match="fully-indexed FTS5"):
        KnowledgePaths.resolve(settings, "widget-repo")
