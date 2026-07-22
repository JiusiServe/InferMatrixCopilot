"""Repo-specific skills live in the ADAPTER store, not the shared pool.

`model-adaptation-review` (model/checkpoint/stage-topology review for the
vllm_omni adapter's repo) was mis-filed in the shared cross-repo pool; it now
lives under `adapters/vllm_omni/skills/`. `_knowledge_stores` searches the
adapter store before the shared pool, so runs against that repo still retrieve
it (with repo priority) while other repos no longer see it — and retrieval
degrades gracefully to the shared pool when no adapter resolves.
"""

from __future__ import annotations

import types
from pathlib import Path

from infermatrix_copilot.config import Settings
from infermatrix_copilot.engine.agent_runtime.knowledge import _knowledge_stores
from infermatrix_copilot.memory.skills import SkillStore

_REPO_ROOT = Path(__file__).resolve().parents[1]
_QUERY = "model adaptation review new checkpoint pipeline stage"


def _ctx(state: dict):
    return types.SimpleNamespace(settings=Settings(), state=state)


def test_skill_lives_in_adapter_store_not_shared_pool():
    shared = [s.name for s in SkillStore(Settings().skills_dir).load_all()]
    assert "model-adaptation-review" not in shared
    adapter = [s.name for s in
               SkillStore(_REPO_ROOT / "adapters" / "vllm_omni" / "skills").load_all()]
    assert "model-adaptation-review" in adapter


def test_repo_run_retrieves_skill_with_repo_priority():
    store = _knowledge_stores(_ctx({"task_spec": {"repo": "vllm-omni"}}))
    assert len(store.stores) == 2  # adapter store first, shared pool second
    hits = [s.name for s in store.find(query=_QUERY, k=5)]
    assert "model-adaptation-review" in hits


def test_no_adapter_degrades_gracefully_without_cross_repo_bleed():
    store = _knowledge_stores(_ctx({}))
    assert len(store.stores) == 1  # shared pool only — no crash without adapter
    hits = [s.name for s in store.find(query=_QUERY, k=5)]
    assert "model-adaptation-review" not in hits
