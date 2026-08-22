"""D2 read-compat wiring: prelude fail-closed + provenance, backend union.

The prelude must BLOCK on any declared-but-broken parent layer (including a
declared path whose env var did not expand — the silent knowledge-bare run
the §8 fairness gate can never allow) and record the opening provenance
block; the v3 backends must union parent layers LAST and degrade OPEN with
a trace once the prelude has passed.
"""

import asyncio
import sqlite3
from pathlib import Path

import yaml

from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import StepContext
from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.engine.steps.rebase_v3 import (_build_backends,
                                                        _substate)
from test_parent_compat import _parent_db  # parent-schema fixture builder


def _adapter(settings, tmp_path, repo, knowledge=None) -> dict:
    adir = Path(settings.adapters_dir) / "widget_repo"
    adir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "widget_repo", "status": "active",
        "repo": {"path": str(repo), "default_branch": "main"},
        "modules": {"core": {"local_paths": ["core/"]}},
        "rebase": {"lock_name": "widget"},
    }
    if knowledge:
        manifest["rebase"]["knowledge"] = knowledge
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    return manifest


def _repo(tmp_path) -> Path:
    import subprocess
    repo = tmp_path / "widget"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "a.txt").write_text("a")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qm", "init"], cwd=repo, check=True)
    return repo


def _prelude_ctx(settings, trace, repo, run_dir, mode="report_only"):
    return StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"kind": "repo_rebase", "repo": "widget-repo",
                             "params": {"rebase_mode": mode}},
               "repo_path": str(repo), "run_id": run_dir.name})


def _run_prelude(settings, trace, repo, run_dir):
    registry = register_builtin_steps(StepRegistry())
    prelude = registry.get("rebase.v3_prelude")
    return asyncio.run(prelude.handler(
        _prelude_ctx(settings, trace, repo, run_dir)))


def test_prelude_blocks_on_unreadable_declared_layer(settings, trace,
                                                     tmp_path):
    repo = _repo(tmp_path)
    _adapter(settings, tmp_path, repo,
             knowledge={"parent_debug_db": str(tmp_path / "missing.db")})
    run_dir = tmp_path / "run-a"
    run_dir.mkdir()
    r = _run_prelude(settings, trace, repo, run_dir)
    assert not r.ok and "unreadable" in r.summary


def test_prelude_blocks_on_unexpanded_env_var(settings, trace, tmp_path,
                                              monkeypatch):
    monkeypatch.delenv("NO_SUCH_PARENT_ROOT", raising=False)
    repo = _repo(tmp_path)
    _adapter(settings, tmp_path, repo,
             knowledge={"parent_debug_db":
                        "${NO_SUCH_PARENT_ROOT}/store/debug_memory.db"})
    run_dir = tmp_path / "run-b"
    run_dir.mkdir()
    r = _run_prelude(settings, trace, repo, run_dir)
    assert not r.ok and "did not expand" in r.summary


def test_manifest_expansion_reads_adapter_declared_env_keys(
        tmp_path, monkeypatch):
    """Live-launch finding (2026-08-23): adapter-declared variables
    (VLLM_OMNI_VENV-class) are NOT Settings fields — `extra="ignore"`
    drops them at load — yet the manifest contract says `.env` is where
    they live. `expansion_env` must re-read the raw env files for them:
    same secret filter, Settings fields winning on a name collision."""
    from infermatrix_copilot.adapters.base import expand_path
    from infermatrix_copilot.config import Settings

    env_file = tmp_path / "adapter.env"
    env_file.write_text(
        'TARGET_REPO_VENV="/ws/venv"\n'
        'TARGET_SECRET_TOKEN="never-this"\n'
        # indirection must not smuggle the secret through a benign name
        'TARGET_INDIRECT="${TARGET_SECRET_TOKEN}"\n'
        'REBASE_AGENT_ROOT="/from/the/file"\n', encoding="utf-8")

    class FileSettings(Settings):
        model_config = dict(Settings.model_config,
                            env_file=(str(env_file),))

    # pydantic's canonical single-path forms (bare str / Path) must load
    # identically - never be iterated character-by-character
    class StrFileSettings(Settings):
        model_config = dict(Settings.model_config, env_file=str(env_file))

    class PathFileSettings(Settings):
        model_config = dict(Settings.model_config, env_file=env_file)

    monkeypatch.delenv("TARGET_REPO_VENV", raising=False)
    monkeypatch.delenv("REBASE_AGENT_ROOT", raising=False)
    extra = FileSettings().expansion_env()
    assert extra["TARGET_REPO_VENV"] == "/ws/venv"
    assert "TARGET_SECRET_TOKEN" not in extra      # secret filter holds
    # interpolation stays OFF: the reference is literal, never the secret
    assert extra["TARGET_INDIRECT"] == "${TARGET_SECRET_TOKEN}"
    for single_form in (StrFileSettings, PathFileSettings):
        single = single_form().expansion_env()
        assert single["TARGET_REPO_VENV"] == "/ws/venv"
        assert "TARGET_SECRET_TOKEN" not in single
    # a name that IS a Settings field resolves through the field (one
    # source of truth for anything Settings owns)
    assert extra["REBASE_AGENT_ROOT"] == "/from/the/file"
    assert expand_path("${TARGET_REPO_VENV}/bin",
                       extra=extra) == "/ws/venv/bin"


def test_manifest_expansion_falls_back_to_settings(settings, tmp_path,
                                                   monkeypatch):
    """Live-smoke finding (2026-08-20): `.env` keys load into Settings
    fields without being exported, so `${REBASE_AGENT_ROOT}`-style
    manifest paths expanded to nothing unless the shell happened to
    export them. Expansion now falls back to Settings-derived values —
    process env still wins, secrets never substitute."""
    from infermatrix_copilot.adapters.base import expand_path

    monkeypatch.delenv("REBASE_AGENT_ROOT", raising=False)
    extra = settings.expansion_env()
    assert extra["REBASE_AGENT_ROOT"] == str(settings.rebase_agent_root)
    got = expand_path("${REBASE_AGENT_ROOT}/agent/skills", extra=extra)
    assert got == f"{settings.rebase_agent_root}/agent/skills"
    # the process env WINS over the fallback
    monkeypatch.setenv("REBASE_AGENT_ROOT", "/from/the/shell")
    assert expand_path("${REBASE_AGENT_ROOT}/x",
                       extra=extra) == "/from/the/shell/x"
    # secret-bearing fields are never available to manifest paths
    assert not any("key" in k.lower() or "token" in k.lower()
                   for k in extra)
    # a variable that exists nowhere still yields "" (fail-closed callers
    # keep blocking)
    monkeypatch.delenv("NO_SUCH_VAR_ANYWHERE", raising=False)
    assert expand_path("${NO_SUCH_VAR_ANYWHERE}/x", extra=extra) == ""
    # token-aware fallback (hook finding): a known name must never
    # rewrite the HEAD of a longer unknown one — $REBASE_AGENT_ROOT_V2
    # stays unresolved and fails closed, in braced and unbraced forms
    monkeypatch.delenv("REBASE_AGENT_ROOT_V2", raising=False)
    monkeypatch.delenv("REBASE_AGENT_ROOT", raising=False)
    assert expand_path("${REBASE_AGENT_ROOT_V2}/x", extra=extra) == ""
    assert expand_path("$REBASE_AGENT_ROOT_V2/x", extra=extra) == ""


def test_prelude_records_open_provenance(settings, trace, tmp_path):
    repo = _repo(tmp_path)
    parent_db = _parent_db(tmp_path / "parent.db",
                           [{"key": "k1", "symptom": "s1"}])
    skills = tmp_path / "pskills"
    (skills / "ps1").mkdir(parents=True)
    (skills / "ps1" / "SKILL.md").write_text(
        "---\nname: ps1\ndescription: parent skill\n---\nbody\n",
        encoding="utf-8")
    _adapter(settings, tmp_path, repo,
             knowledge={"parent_debug_db": str(parent_db),
                        "parent_skills_dir": str(skills)})
    run_dir = tmp_path / "run-c"
    run_dir.mkdir()
    r = _run_prelude(settings, trace, repo, run_dir)
    assert r.ok, r.summary
    ctx = _prelude_ctx(settings, trace, repo, run_dir)
    kn = _substate(ctx).read().get("knowledge") or {}
    assert len(kn["open"]["parent_debug_db"]["digest"]) == 64
    assert kn["open"]["parent_skills_dir"]["skills"] == 1
    assert kn["skill_union"]["ps1"] == "parent"  # collision table


def test_backend_writes_never_touch_seed_or_parent_trees(settings, trace,
                                                         tmp_path):
    """Seed immutability (design round-2/round-4 F4): the rebase backends'
    write surfaces (skill proposals, debug recordings) land in runtime/
    copilot stores only — the adapter seed tree and the parent stores stay
    byte-identical through them."""
    import hashlib

    repo = _repo(tmp_path)
    parent_db = _parent_db(tmp_path / "parent.db", [{"key": "k"}])
    skills = tmp_path / "pskills"
    (skills / "ps1").mkdir(parents=True)
    (skills / "ps1" / "SKILL.md").write_text(
        "---\nname: ps1\ndescription: d\n---\nbody\n", encoding="utf-8")
    manifest = _adapter(settings, tmp_path, repo,
                        knowledge={"parent_debug_db": str(parent_db),
                                   "parent_skills_dir": str(skills)})
    adapter_dir = Path(settings.adapters_dir) / "widget_repo"
    (adapter_dir / "skills" / "seed1").mkdir(parents=True)
    (adapter_dir / "skills" / "seed1" / "SKILL.md").write_text(
        "---\nname: seed1\ndescription: s\n---\nseed\n", encoding="utf-8")

    def tree_digest(root: Path) -> str:
        h = hashlib.sha256()
        for p in sorted(root.rglob("*")):
            if p.is_file():
                h.update(str(p.relative_to(root)).encode())
                h.update(p.read_bytes())
        return h.hexdigest()

    seed_before = tree_digest(adapter_dir)
    parent_before = (parent_db.read_bytes(), tree_digest(skills))
    run_dir = tmp_path / "run-w"
    run_dir.mkdir()

    class _Target:
        model = "m"
        api_key = "k"
        base_url = ""

    ctx = StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"kind": "repo_rebase", "repo": "widget-repo",
                             "params": {"rebase_mode": "full"}},
               "repo_path": str(repo), "run_id": run_dir.name})
    backends = _build_backends(ctx, manifest, str(repo), _Target())
    backends.skill_manage(action="propose", name="learned-x",
                          description="d", body="b")
    backends.record_debug_memory(module="m", symptom="s",
                                 root_cause="rc", fix="f", key="k2")
    backends.search_skills(keyword="seed")
    backends.search_debug_memory(keyword="k")
    assert tree_digest(adapter_dir) == seed_before
    assert (parent_db.read_bytes(), tree_digest(skills)) == parent_before


def test_report_only_prelude_never_writes_stores(settings, trace,
                                                 tmp_path):
    """D10: report_only's knowledge pre-flight opens every declared store
    strictly read-only — content and mtime byte-stable (WAL-mode parent
    stores keep their live sidecars; the main file must not change)."""
    repo = _repo(tmp_path)
    parent_db = _parent_db(tmp_path / "parent.db",
                           [{"key": "k1", "symptom": "s1"}])
    skills = tmp_path / "pskills"
    (skills / "ps1").mkdir(parents=True)
    skill_md = skills / "ps1" / "SKILL.md"
    skill_md.write_text("---\nname: ps1\ndescription: d\n---\nbody\n",
                        encoding="utf-8")
    _adapter(settings, tmp_path, repo,
             knowledge={"parent_debug_db": str(parent_db),
                        "parent_skills_dir": str(skills)})
    run_dir = tmp_path / "run-ro"
    run_dir.mkdir()
    before = (parent_db.stat().st_mtime_ns, parent_db.read_bytes(),
              skill_md.stat().st_mtime_ns)
    r = _run_prelude(settings, trace, repo, run_dir)
    assert r.ok, r.summary
    assert (parent_db.stat().st_mtime_ns, parent_db.read_bytes(),
            skill_md.stat().st_mtime_ns) == before


def test_backend_union_parent_last_and_degrade_open(settings, trace,
                                                    tmp_path):
    repo = _repo(tmp_path)
    parent_db = _parent_db(tmp_path / "parent.db", [
        {"key": "parent-fact", "symptom": "watchdog kill on OOM pattern",
         "fix": "raise shm"}])
    skills = tmp_path / "pskills"
    (skills / "parent-skill").mkdir(parents=True)
    (skills / "parent-skill" / "SKILL.md").write_text(
        "---\nname: parent-skill\ndescription: watchdog lore\n---\nbody\n",
        encoding="utf-8")
    manifest = _adapter(settings, tmp_path, repo,
                        knowledge={"parent_debug_db": str(parent_db),
                                   "parent_skills_dir": str(skills)})
    run_dir = tmp_path / "run-d"
    run_dir.mkdir()

    class _Target:
        model = "m"
        api_key = "k"
        base_url = ""

    ctx = StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"kind": "repo_rebase", "repo": "widget-repo",
                             "params": {"rebase_mode": "full"}},
               "repo_path": str(repo), "run_id": run_dir.name})
    backends = _build_backends(ctx, manifest, str(repo), _Target())
    # copilot store is empty: the parent layer answers, labeled
    hits = backends.search_debug_memory(keyword="watchdog OOM pattern")
    assert [h["key"] for h in hits["results"]] == ["parent-fact"]
    assert hits["results"][0]["source_layer"] == "parent"
    skills_out = backends.search_skills(keyword="watchdog")
    assert [s["name"] for s in skills_out["skills"]] == ["parent-skill"]
    # cross-layer collisions must not starve distinct parent hits ranked
    # beyond k (iteration-2 F4): the copilot layer holds the same fact,
    # the parent's top hits duplicate it, and a distinct parent fact
    # exists further down — the union must still fill up to k
    rec = backends.record_debug_memory(
        module="m", symptom="watchdog OOM in warmup xyz",
        root_cause="rc", fix="known", files="a.py")
    assert rec.get("ok"), rec  # a swallowed write would blind the test
    import sqlite3 as _sq
    c = _sq.connect(parent_db)
    for fix in ("dupA", "dupB"):  # same (module, symptom-head) signature
        cur = c.execute(
            "INSERT INTO debug_entries (module, key, symptom, fix) "
            "VALUES ('m', ?, 'watchdog OOM in warmup xyz', ?)",
            (f"dup-{fix}", fix))
        c.execute(
            "INSERT INTO debug_entries_fts (rowid, module, key, tags, "
            "symptom, root_cause, fix, watch_outs) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cur.lastrowid, "m", f"dup-{fix}", "",
             "watchdog OOM in warmup xyz", "", fix, ""))
    cur = c.execute(
        "INSERT INTO debug_entries (module, key, symptom, fix) "
        "VALUES ('m', 'distinct-fact', 'watchdog OOM growth pattern', "
        "'raise shm')")
    c.execute(
        "INSERT INTO debug_entries_fts (rowid, module, key, tags, "
        "symptom, root_cause, fix, watch_outs) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (cur.lastrowid, "m", "distinct-fact",
         "", "watchdog OOM growth pattern", "", "raise shm", ""))
    c.commit()
    c.close()
    out = backends.search_debug_memory(
        keyword="watchdog OOM warmup xyz", max_results=2)["results"]
    assert len(out) == 2, out
    assert any(h.get("key") == "distinct-fact" or
               "growth" in str(h.get("symptom", "")) for h in out)
    # DEEP starvation (iteration-3 F3): pile 6 more duplicate-signature
    # rows above the distinct one — exhaustion-widening must still find it
    c = _sq.connect(parent_db)
    for i in range(6):
        cur = c.execute(
            "INSERT INTO debug_entries (module, key, symptom, fix) "
            "VALUES ('m', ?, 'watchdog OOM in warmup xyz', 'dup')",
            (f"deep-dup-{i}",))
        c.execute(
            "INSERT INTO debug_entries_fts (rowid, module, key, tags, "
            "symptom, root_cause, fix, watch_outs) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cur.lastrowid, "m", f"deep-dup-{i}", "",
             "watchdog OOM in warmup xyz", "", "dup", ""))
    c.commit()
    c.close()
    out = backends.search_debug_memory(
        keyword="watchdog OOM warmup xyz", max_results=2)["results"]
    assert len(out) == 2, out

    # runtime-layer duplicates must not mask the parent (verification
    # finding): k copilot rows sharing one signature collapse to one and
    # the parent still fills the union
    rec = backends.record_debug_memory(
        module="m", symptom="watchdog OOM in warmup xyz",
        root_cause="rc2", fix="known-dup", files="b.py")
    assert rec.get("ok"), rec
    out = backends.search_debug_memory(
        keyword="watchdog OOM warmup xyz", max_results=2)["results"]
    assert len(out) == 2, out
    assert any(h.get("source_layer") == "parent" for h in out)

    # degrade OPEN mid-run: break the parent db AFTER the backends exist
    parent_db.write_bytes(b"corrupt now")
    hits = backends.search_debug_memory(keyword="watchdog OOM pattern")
    # the copilot layers still answer; the parent layer contributes
    # nothing and the failure is traced, never raised
    assert all(h.get("source_layer") != "parent" for h in hits["results"])
    import json
    events = [json.loads(ln) for ln in Path(trace.path).read_text(
        encoding="utf-8").splitlines()]
    assert any(e.get("kind") == "capability_note" and
               "parent layer degraded" in str(e)
               for e in events)
