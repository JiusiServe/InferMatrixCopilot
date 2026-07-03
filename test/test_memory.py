import pytest

from omni_copilot.memory.debug_memory import DebugMemory
from omni_copilot.memory.skills import SkillStore


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
