"""Curator + curate/knowledge_prep steps (design D5, Rev 8 §5).

Pins the recorded divergences from the parent curator (retire-never-delete
with immutable lineage, repo scoping, retired rows excluded from every
input, second-pass no-op) and the exactly-once watchdog harvest the curate
step owns. Also pins the sanctioned `ensure_schema_v2()` entry-point census
— exactly three call sites may upgrade an existing store's schema.
"""

import asyncio
import json
from pathlib import Path

import pytest

from infermatrix_copilot.memory.curator import DebugMemoryCurator
from infermatrix_copilot.memory.debug_memory import DebugMemory
from infermatrix_copilot.memory.skills import SkillStore
from infermatrix_copilot.testing import watchdog_learn

REPO_ROOT = Path(__file__).resolve().parents[1]


def _store(tmp_path, rows):
    dm = DebugMemory(tmp_path / "m.db")
    for r in rows:
        base = dict(repo="repo-x", module="core", run_id="run-1",
                    symptom="s", root_cause="rc", fix_summary="fs",
                    files=["a.py"], verification="v", run_count=1)
        base.update(r)
        dm.record(**base)
    return dm


def _curator(dm, **kw):
    return DebugMemoryCurator(dm, repo="repo-x", **kw)


def test_merge_retires_with_lineage_never_deletes(tmp_path):
    dm = _store(tmp_path, [
        {"key": "import-moved", "symptom": "ImportError SchedulerOutput "
         "moved to core", "root_cause": "upstream moved SchedulerOutput",
         "run_count": 2},
        {"key": "import-moved-again", "symptom": "ImportError "
         "SchedulerOutput moved to core", "root_cause": "upstream moved "
         "SchedulerOutput", "tags": "import", "run_count": 3},
        {"key": "unrelated", "symptom": "CUDA OOM in warmup",
         "root_cause": "batch too large"},
    ])
    report = _curator(dm).curate()
    assert report.merged == 1
    rows = {r["key"]: r for r in dm.entries(
        repo="repo-x", statuses=("active", "candidate", "stale", "retired"))}
    survivor = rows["import-moved-again"]      # newest id wins
    retired = rows["import-moved"]
    assert retired["status"] == "retired"
    assert retired["derived_from"] == str(survivor["id"])
    assert survivor["run_count"] == 5          # summed THIS pass only
    assert dm.count() == 3                     # nothing deleted
    # retired rows are invisible to search
    assert all(h["id"] != retired["id"]
               for h in dm.search("ImportError SchedulerOutput"))


def test_second_curation_is_a_strict_noop(tmp_path):
    dm = _store(tmp_path, [
        {"key": "k1", "symptom": "same symptom text here",
         "root_cause": "same root cause", "run_count": 2},
        {"key": "k2", "symptom": "same symptom text here",
         "root_cause": "same root cause", "run_count": 3},
    ])
    runtime = SkillStore(tmp_path / "runtime")
    _curator(dm, propose_to=runtime).curate()
    before = [dict(r) for r in dm.entries(
        repo="repo-x", statuses=("active", "candidate", "stale", "retired"))]
    cands_before = runtime.candidates_file.read_text(encoding="utf-8")
    report2 = _curator(dm, propose_to=runtime).curate()
    after = [dict(r) for r in dm.entries(
        repo="repo-x", statuses=("active", "candidate", "stale", "retired"))]
    assert report2.merged == 0
    assert before == after  # run_count not re-summed, lineage untouched
    # a pending candidate is never re-proposed (file byte-identical)
    assert runtime.candidates_file.read_text(
        encoding="utf-8") == cands_before


def test_foreign_repo_rows_untouched(tmp_path):
    dm = _store(tmp_path, [
        {"key": "k1", "symptom": "dup symptom", "root_cause": "dup rc"},
        {"key": "k2", "symptom": "dup symptom", "root_cause": "dup rc"},
        {"key": "other-repo", "repo": "repo-y", "symptom": "dup symptom",
         "root_cause": "dup rc"},
    ])
    _curator(dm).curate()
    other = [r for r in dm.entries(repo="repo-y",
                                   statuses=("active", "candidate",
                                             "stale", "retired"))]
    assert len(other) == 1 and other[0]["status"] == "active"


def test_non_actionable_rows_make_no_candidates(tmp_path):
    dm = _store(tmp_path, [
        {"key": "clean-module", "symptom": "module already compatible",
         "run_count": 5},
        {"key": "real-fix", "symptom": "watchdog kill on OOM growth",
         "root_cause": "leaked pin buffers", "run_count": 5},
    ])
    runtime = SkillStore(tmp_path / "runtime")
    report = _curator(dm, propose_to=runtime).curate()
    keys = {c.key for c in report.candidates}
    assert "clean-module" not in keys and "real-fix" in keys
    assert set(runtime.candidates())  # proposal landed as a CANDIDATE


def test_candidate_covered_by_existing_skill_is_skipped(tmp_path):
    dm = _store(tmp_path, [
        {"key": "watchdog-oom", "symptom": "watchdog kill on OOM growth "
         "in warmup", "root_cause": "leaked pin buffers", "run_count": 5},
    ])
    seed = SkillStore(tmp_path / "seed")
    seed.propose(name="watchdog-oom-lore",
                 description="watchdog kill OOM growth warmup leaked pin "
                             "buffers", body="handled")
    seed.promote("watchdog-oom-lore")
    report = _curator(dm, skill_layers=(seed,)).curate()
    assert report.candidates == []


def test_dormancy_marks_stale_with_window(tmp_path):
    dm = _store(tmp_path, [
        {"key": "old", "last_seen_run": "run-000"},
        {"key": "fresh", "last_seen_run": "run-990"},
    ])
    report = _curator(dm).curate(
        recent_runs=[f"run-9{i:02d}" for i in range(11)] + ["run-990"])
    assert report.dormant == 1
    rows = {r["key"]: r["status"] for r in dm.entries(
        repo="repo-x", statuses=("active", "candidate", "stale", "retired"))}
    assert rows["old"] == "stale" and rows["fresh"] == "active"


def test_curator_requires_schema_v2(tmp_path):
    import sqlite3
    db = tmp_path / "legacy.db"
    c = sqlite3.connect(db)
    c.executescript("""CREATE TABLE entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT, module TEXT, run_id TEXT, symptom TEXT, root_cause TEXT,
        fix_summary TEXT, files TEXT, verification TEXT,
        status TEXT DEFAULT 'active', created_at REAL);
        CREATE VIRTUAL TABLE entries_fts USING fts5(
        symptom, root_cause, fix_summary, module, repo,
        content='entries', content_rowid='id');""")
    c.close()
    with pytest.raises(RuntimeError, match="ensure_schema_v2"):
        DebugMemoryCurator(DebugMemory(db), repo="repo-x")


# ── exactly-once harvest ────────────────────────────────────────────────────

def test_harvest_exactly_once_across_crash_windows(tmp_path):
    state_log = tmp_path / "state" / "watchdog_decisions.jsonl"
    checkpoint = tmp_path / "state" / "harvested.json"
    lock = tmp_path / "state" / "locks" / "state.lock"
    src = tmp_path / "run" / "watchdog_decisions.jsonl"
    for seq in (1, 2):
        watchdog_learn.record(src, pattern=f"pat-{seq}", verdict="CONTINUE",
                              test="t", run="r1", attempt="a", seq=seq)
    assert watchdog_learn.harvest(state_log, checkpoint, [src],
                                  lock_path=lock) == 2
    # crash window: checkpoint lost after append — the LOG dedups
    checkpoint.unlink()
    assert watchdog_learn.harvest(state_log, checkpoint, [src],
                                  lock_path=lock) == 0
    # unchanged source short-circuits by digest
    assert watchdog_learn.harvest(state_log, checkpoint, [src],
                                  lock_path=lock) == 0
    # a NEW decision in the same file is picked up exactly once
    watchdog_learn.record(src, pattern="pat-3", verdict="CONTINUE",
                          test="t", run="r1", attempt="a", seq=3)
    assert watchdog_learn.harvest(state_log, checkpoint, [src],
                                  lock_path=lock) == 1
    assert len(watchdog_learn.read_decisions(state_log)) == 3
    # torn STATE tail is repaired before appending
    with open(state_log, "ab") as fh:
        fh.write(b'{"torn": "frag')
    watchdog_learn.record(src, pattern="pat-4", verdict="CONTINUE",
                          test="t", run="r1", attempt="a", seq=4)
    assert watchdog_learn.harvest(state_log, checkpoint, [src],
                                  lock_path=lock) == 1
    assert len(watchdog_learn.read_decisions(state_log)) == 4


# ── sanctioned ensure_schema_v2 census ──────────────────────────────────────

def test_sanctioned_schema_upgrade_entry_points():
    """Exactly three production call SITES may upgrade an existing store:
    the migration CLI, rebase.v3_knowledge_prep, and rebase.v3_curate
    (design round-5 F2) — pinned by EXACT per-file counts, so neither a
    dropped sanctioned caller nor an extra call inside an allowed file
    can slip through."""
    import re
    src_root = REPO_ROOT / "src" / "infermatrix_copilot"
    counts: dict[str, int] = {}
    for path in src_root.rglob("*.py"):
        rel = path.relative_to(src_root).as_posix()
        if rel == "memory/debug_memory.py":  # the definition itself
            continue
        n = len(re.findall(r"\.ensure_schema_v2\(",
                           path.read_text(encoding="utf-8")))
        if n:
            counts[rel] = n
    expected = {"engine/steps/rebase_knowledge.py": 2}  # prep + curate
    if (src_root / "rebase_engine" / "knowledge_migrate.py").exists():
        expected["rebase_engine/knowledge_migrate.py"] = 1  # Unit B
    assert counts == expected, counts


def test_slug_colliding_candidates_both_survive(tmp_path):
    """Two distinct patterns whose (module, key) normalize to the same
    slug must both be proposed (collision-safe suffix), while the SAME
    pending candidate is still never re-proposed (iteration-2 F3)."""
    dm = _store(tmp_path, [
        {"key": "oom.kill", "module": "core",
         "symptom": "first distinct pattern watchdog", "run_count": 3},
        {"key": "oom_kill", "module": "core",
         "symptom": "second unrelated growth issue entirely",
         "root_cause": "different cause entirely", "run_count": 3},
    ])
    runtime = SkillStore(tmp_path / "runtime")
    _curator(dm, propose_to=runtime).curate()
    names = set(runtime.candidates())
    assert len(names) == 2, names  # no silent mutual suppression
    before = runtime.candidates_file.read_text(encoding="utf-8")
    _curator(dm, propose_to=runtime).curate()
    assert runtime.candidates_file.read_text(encoding="utf-8") == before
    # identity decides, not prose (iteration-3 F2): the SAME (module,key)
    # with a CHANGED trigger is still never re-proposed
    dm.apply_curation({1: {"symptom": "first distinct pattern watchdog "
                           "with a brand new trigger line"}})
    _curator(dm, propose_to=runtime).curate()
    assert set(runtime.candidates()) == names  # no third candidate
    assert runtime.candidates_file.read_text(encoding="utf-8") == before


def test_plan_review_gets_resolved_mode_context():
    """Live-smoke finding (2026-08-20): the plan reviewer sees the v3
    yaml's FULL step list but not the resolved mode, so a report_only
    plan looked like it runs its write/push steps and was spuriously
    blocked. The review context must carry the mode and the exact
    active-step set the `when:` gates produce — and nothing for
    non-mode-aware playbooks."""
    from types import SimpleNamespace

    import yaml

    from infermatrix_copilot.cli.copilot import _mode_review_context
    from infermatrix_copilot.playbooks.store import parse_playbook

    doc = (REPO_ROOT / "playbooks" / "repo-rebase-v3.yaml").read_text(
        encoding="utf-8")
    pb = parse_playbook(yaml.safe_load(doc), "repo-rebase-v3.yaml")
    spec = SimpleNamespace(params={"rebase_mode": "report_only"})
    ctx = _mode_review_context(pb, spec)
    assert "rebase_mode=report_only" in ctx
    assert "'scan'" in ctx and "'prelude'" in ctx
    for gated_off in ("'curate'", "'ci'", "'wave1'", "'knowledge_prep'"):
        assert gated_off not in ctx
    # full mode lists the whole pipeline
    ctx_full = _mode_review_context(
        pb, SimpleNamespace(params={"rebase_mode": "full"}))
    assert "'curate'" in ctx_full and "'compare'" in ctx_full
    # non-mode-aware playbooks add nothing
    pb2 = parse_playbook(yaml.safe_load(doc) | {"mode_aware": False},
                         "x.yaml")
    assert _mode_review_context(
        pb2, SimpleNamespace(params={"rebase_mode": "full"})) == ""


def test_candidate_never_shadows_a_promoted_skill(tmp_path):
    """Commit-hook finding (2026-08-20): a candidate whose allocated name
    matches an already-PROMOTED skill would let a later promote()
    overwrite the active SKILL.md — the allocator must treat promoted
    names as taken and fall to the digest suffix."""
    runtime = SkillStore(tmp_path / "runtime")
    runtime.propose(name="core-oom-kill", description="old", body="b")
    promoted_path = runtime.promote("core-oom-kill")
    promoted = promoted_path.read_text(encoding="utf-8")
    name = runtime.propose_if_new_identity(
        base_name="core-oom-kill", identity="core\0oom.kill",
        description="new pattern", body="body")
    assert name is not None and name != "core-oom-kill"
    assert name.startswith("core-oom-kill-")
    # the active skill is untouched, and promoting the new candidate
    # cannot overwrite it either
    assert promoted_path.read_text(encoding="utf-8") == promoted
    runtime.promote(name)
    assert promoted_path.read_text(encoding="utf-8") == promoted


def test_recent_repo_runs_filters_by_repo(settings, trace, tmp_path):
    """The dormancy window is built from THIS repo's runs only — unrelated
    repos' runs must not evict the target's recent ids (review F6)."""
    from types import SimpleNamespace

    from infermatrix_copilot.engine.steps.rebase_knowledge import \
        _recent_repo_runs

    run_root = Path(settings.run_root)
    for i, repo in enumerate(["widget-repo"] * 3 + ["other-repo"] * 15):
        rd = run_root / f"run-{i:03d}"
        rd.mkdir(parents=True)
        (rd / "task.json").write_text(json.dumps(
            {"spec": {"repo": repo}}), encoding="utf-8")
    ctx = SimpleNamespace(settings=settings)
    recent = _recent_repo_runs(ctx, "widget-repo", limit=12)
    assert recent == ["run-000", "run-001", "run-002"]


# ── the steps ───────────────────────────────────────────────────────────────

def test_knowledge_prep_and_curate_steps(settings, trace, tmp_path):
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.rebase_engine.substate import Substate

    import subprocess
    import yaml
    repo = tmp_path / "widget"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    adir = Path(settings.adapters_dir) / "widget_repo"
    adir.mkdir(parents=True)
    (adir / "manifest.yaml").write_text(yaml.safe_dump({
        "name": "widget_repo", "status": "active",
        "repo": {"path": str(repo)}, "modules": {},
        "rebase": {"lock_name": "widget"}}))

    registry = register_builtin_steps(StepRegistry())
    run_dir = tmp_path / "run-k"
    run_dir.mkdir()

    def ctx():
        return StepContext(
            settings=settings, params={}, run_dir=run_dir, trace=trace,
            state={"task_spec": {"kind": "repo_rebase",
                                 "repo": "widget-repo",
                                 "params": {"rebase_mode": "full"}},
                   "repo_path": str(repo), "run_id": "run-k"})

    # legacy store: prep upgrades it BEFORE any agent write
    legacy = DebugMemory(settings.memory_db)
    assert legacy.schema_v2  # fresh fixture store is v2 already
    prep = registry.get("rebase.v3_knowledge_prep")
    r = asyncio.run(prep.handler(ctx()))
    assert r.ok and r.outputs["state_updates"]["knowledge_prepped"] is True

    # seed a duplicate pair + a run-dir watchdog decision, then curate
    for key in ("k1", "k2"):
        legacy.record(repo="widget-repo", module="core", run_id="run-k",
                      symptom="same symptom words", root_cause="same rc",
                      fix_summary="fs", files=["a.py"], verification="v",
                      key=key)
    watchdog_learn.record(run_dir / "watchdog_decisions.jsonl",
                          pattern="noise line", verdict="CONTINUE",
                          test="t", run="run-k", attempt="a", seq=1)
    Substate(run_dir, "run-k").update({"phase": "reporting"})
    curate = registry.get("rebase.v3_curate")
    r = asyncio.run(curate.handler(ctx()))
    assert r.ok, r.summary
    state_dir = Path(settings.memory_db).parent / "state" / "widget-repo"
    assert (state_dir / "PROMOTION.md").exists()
    harvested = watchdog_learn.read_decisions(
        state_dir / "watchdog_decisions.jsonl")
    assert len(harvested) == 1
    # re-run: strict no-op harvest, no re-merge
    r2 = asyncio.run(curate.handler(ctx()))
    assert r2.ok and "0 harvested" in r2.summary
    # the harvest SWEEPS other run dirs too (review F3): a local_ci run
    # that never curated still gets its decisions into the state log
    other_run = Path(settings.run_root) / "run-lci"
    other_run.mkdir(parents=True, exist_ok=True)
    (other_run / "task.json").write_text(json.dumps(
        {"spec": {"repo": "widget-repo"}}), encoding="utf-8")
    watchdog_learn.record(other_run / "watchdog_decisions.jsonl",
                          pattern="lci noise", verdict="CONTINUE",
                          test="t2", run="run-lci", attempt="b", seq=1)
    # …while ANOTHER repo's run must stay out of this repo's state log
    foreign_run = Path(settings.run_root) / "run-foreign"
    foreign_run.mkdir(parents=True, exist_ok=True)
    (foreign_run / "task.json").write_text(json.dumps(
        {"spec": {"repo": "other-repo"}}), encoding="utf-8")
    watchdog_learn.record(foreign_run / "watchdog_decisions.jsonl",
                          pattern="foreign noise", verdict="CONTINUE",
                          test="t3", run="run-foreign", attempt="c", seq=1)
    r3 = asyncio.run(curate.handler(ctx()))
    assert r3.ok, r3.summary
    harvested = watchdog_learn.read_decisions(
        state_dir / "watchdog_decisions.jsonl")
    assert len(harvested) == 2
    assert all(d["run"] != "run-foreign" for d in harvested)


def test_phase5_report_and_compare_steps(settings, trace, tmp_path):
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.rebase_engine.substate import Substate

    import subprocess
    import yaml
    repo = tmp_path / "widget"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    adir = Path(settings.adapters_dir) / "widget_repo"
    adir.mkdir(parents=True)
    (adir / "manifest.yaml").write_text(yaml.safe_dump({
        "name": "widget_repo", "status": "active",
        "repo": {"path": str(repo)}, "modules": {},
        "rebase": {"lock_name": "widget"}}))
    registry = register_builtin_steps(StepRegistry())
    run_dir = tmp_path / "run-p"
    run_dir.mkdir()
    sub = Substate(run_dir, "run-p")
    sub.update({"modules": {"core": {"status": "done"},
                            "worker": {"status": "failed"}},
                "tests": {"pipeline": {"passed": 3, "failed": 1,
                                       "failed_tests": ["t_x"]}}})

    def ctx(params=None):
        return StepContext(
            settings=settings, params=params or {}, run_dir=run_dir,
            trace=trace,
            state={"task_spec": {"kind": "repo_rebase",
                                 "repo": "widget-repo",
                                 "params": {"rebase_mode": "full",
                                            **(params or {})}},
                   "repo_path": str(repo), "run_id": "run-p"})

    r = asyncio.run(registry.get("rebase.v3_phase5_report").handler(ctx()))
    assert r.ok
    summary = (run_dir / "FINAL_SUMMARY.md").read_text(encoding="utf-8")
    assert "worker: failed" in summary and "failed: t_x" in summary

    # compare with no baseline and no declared knowledge: artifact +
    # explicit no-baseline note, no drift machinery
    r = asyncio.run(registry.get("rebase.v3_compare").handler(ctx()))
    assert r.ok and "no drift" in r.summary
    comparison = (run_dir / "COMPARISON.md").read_text(encoding="utf-8")
    assert "no baseline supplied" in comparison

    # with a baseline status file, the side-by-side lands — and RULES
    # (PR-boundary F6): matching modules pass…
    baseline = tmp_path / "ext_status.json"
    baseline.write_text(json.dumps(
        {"modules": {"core": {"status": "done"}}}), encoding="utf-8")
    r = asyncio.run(registry.get("rebase.v3_compare").handler(
        ctx({"baseline_status": str(baseline)})))
    assert r.ok
    comparison = (run_dir / "COMPARISON.md").read_text(encoding="utf-8")
    assert "## Baseline" in comparison and "core: done" in comparison
    # …a module the baseline had green but this run failed BLOCKS
    # (needs-human, the soak's investigate-don't-average contract)
    baseline.write_text(json.dumps(
        {"modules": {"worker": {"status": "done"}}}), encoding="utf-8")
    r = asyncio.run(registry.get("rebase.v3_compare").handler(
        ctx({"baseline_status": str(baseline)})))
    assert not r.ok and "worse-than-baseline" in r.summary
    # …and an unreadable baseline is a typed failure, never prose
    baseline.write_text("not json", encoding="utf-8")
    r = asyncio.run(registry.get("rebase.v3_compare").handler(
        ctx({"baseline_status": str(baseline)})))
    assert not r.ok and "unreadable" in r.summary


def test_compare_detects_parent_layer_drift(settings, trace, tmp_path):
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.rebase_engine.substate import Substate
    from test_parent_compat import _parent_db

    import subprocess
    import sqlite3
    import yaml
    repo = tmp_path / "widget"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    parent_db = _parent_db(tmp_path / "parent.db", [{"key": "k"}])
    adir = Path(settings.adapters_dir) / "widget_repo"
    adir.mkdir(parents=True)
    (adir / "manifest.yaml").write_text(yaml.safe_dump({
        "name": "widget_repo", "status": "active",
        "repo": {"path": str(repo)}, "modules": {},
        "rebase": {"lock_name": "widget",
                   "knowledge": {"parent_debug_db": str(parent_db)}}}))
    registry = register_builtin_steps(StepRegistry())
    run_dir = tmp_path / "run-d"
    run_dir.mkdir()

    def ctx(mode="full"):
        return StepContext(
            settings=settings, params={}, run_dir=run_dir, trace=trace,
            state={"task_spec": {"kind": "repo_rebase",
                                 "repo": "widget-repo",
                                 "params": {"rebase_mode": mode}},
                   "repo_path": str(repo), "run_id": "run-d"})

    # prelude records the OPEN attestation (report_only: no world init
    # needed — the attestation runs in every mode)
    r = asyncio.run(registry.get("rebase.v3_prelude").handler(
        ctx("report_only")))
    assert r.ok, r.summary
    # an outside writer mutates the parent store mid-run
    c = sqlite3.connect(parent_db)
    c.execute("INSERT INTO debug_entries (module, key) VALUES ('m','new')")
    c.commit()
    c.close()
    r = asyncio.run(registry.get("rebase.v3_compare").handler(ctx()))
    assert r.ok and "DRIFT" in r.summary
    sub = Substate(run_dir, "run-d")
    assert sub.read()["knowledge"]["drift"] is True
    comparison = (run_dir / "COMPARISON.md").read_text(encoding="utf-8")
    assert "gate-ineligible" in comparison
