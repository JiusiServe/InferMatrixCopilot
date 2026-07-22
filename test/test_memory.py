import pytest

from infermatrix_copilot.memory.debug_memory import DebugMemory
from infermatrix_copilot.memory.skills import SkillStore


def _entry(**overrides):
    base = dict(
        repo="vllm-omni", module="scheduler", run_id="run-1",
        symptom="ImportError: SchedulerOutput moved",
        root_cause="upstream moved SchedulerOutput to vllm.v2.core",
        fix_summary="update import path in omni scheduler shim",
        files=["vllm_omni/core/sched.py"],
        verification="pytest tests/core/test_sched.py passed",
    )
    base.update(overrides)
    return base


def test_debug_memory_write_contract(tmp_path):
    dm = DebugMemory(tmp_path / "m.db")
    with pytest.raises(ValueError, match="missing required fields.*root_cause"):
        dm.record(**{**_entry(), "root_cause": ""})
    rowid = dm.record(**_entry())
    assert rowid == 1 and dm.count() == 1


def test_debug_memory_search_returns_summaries(tmp_path):
    dm = DebugMemory(tmp_path / "m.db")
    dm.record(**_entry())
    dm.record(**_entry(module="platform", symptom="CUDA OOM in warmup",
                       root_cause="batch too large", fix_summary="cap warmup batch"))
    hits = dm.search("SchedulerOutput import moved")
    assert len(hits) >= 1
    top = hits[0]
    assert top["module"] == "scheduler"
    assert set(top) == {"id", "repo", "module", "symptom", "fix_summary"}  # summaries only
    full = dm.get(top["id"])
    assert full["verification"].startswith("pytest")
    assert full["files"] == ["vllm_omni/core/sched.py"]


def test_skill_propose_is_gated(tmp_path):
    store = SkillStore(tmp_path / "skills")
    store.propose(name="fix-import-drift", description="how to fix import drift",
                  body="## Fix\nupdate the shim", modules=["scheduler"])
    # candidate exists, but NOT as an active SKILL.md
    assert "fix-import-drift" in store.candidates()
    assert store.load_all() == []
    # promotion (curator/human) materializes it
    path = store.promote("fix-import-drift")
    assert path.exists()
    skills = store.load_all()
    assert len(skills) == 1 and skills[0].name == "fix-import-drift"
    assert store.candidates() == {}


def test_skill_find_ranks_module_match(tmp_path):
    store = SkillStore(tmp_path / "skills")
    for name, mods in [("sched-skill", ["scheduler"]), ("plat-skill", ["platform"])]:
        store.propose(name=name, description=f"skill for {mods[0]}", body="b", modules=mods)
        store.promote(name)
    found = store.find(module="scheduler", k=1)
    assert found and found[0].name == "sched-skill"
    assert "sched-skill" in store.render_for_prompt(found)


def test_skill_touch_increments_usage(tmp_path):
    """SkillStore.touch bumps run_count + stamps last_used_at, preserving the
    body; unknown names return False instead of raising."""
    from infermatrix_copilot.memory.skills import SkillStore

    store = SkillStore(tmp_path)
    d = tmp_path / "my-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: d\ntrigger: t\nmodules: []\n"
        "status: active\nrun_count: 2\n---\n\n## Fix\nbody text\n")
    assert store.touch("my-skill")
    s = store.load_all()[0]
    assert s.run_count == 3 and "body text" in s.body
    assert not store.touch("nope")


def test_debug_memory_recorded_from_step_helper(tmp_path):
    """record_debug_memory writes a contract-complete entry into the shared
    pool and never raises on failure."""
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps._common import record_debug_memory
    from infermatrix_copilot.memory.debug_memory import DebugMemory
    from infermatrix_copilot.run_trace import RunTrace

    settings = Settings(_env_file=None, adapters_dir=tmp_path / "adapters",
                        memory_db=tmp_path / "mem.db")
    ctx = StepContext(settings=settings,
                      state={"task_spec": {"repo": "r1"}}, params={},
                      run_dir=tmp_path / "run-x", trace=RunTrace(tmp_path / "t.jsonl"),
                      llm=None)
    ok = record_debug_memory(ctx, module="ci", symptom="s", root_cause="rc",
                             fix_summary="fs", files=["a.py"], verification="v")
    assert ok
    hits = DebugMemory(tmp_path / "mem.db").search("rc")
    assert hits and hits[0]["module"] == "ci"
