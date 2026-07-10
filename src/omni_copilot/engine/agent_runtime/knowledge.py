"""Repo-scoped knowledge for agent steps: plugin resolution, skill/debug-memory
retrieval, and the read-only tools an agent uses to pull more on demand.

Retrieval is scoped per repo — the active plugin's own store ranks before the
shared pool, and skill-update *candidates* land in the repo's namespace (agents
never edit active skills). `_repo_map_tool` exposes goal-ranked structure as a
tool (design §V2.3.4 channel 3: structure is pulled, never injected wholesale).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...memory.debug_memory import DebugMemory
from ...memory.skills import SkillStore
from ...tools import ToolDef
from ..step import StepContext


def _resolve_plugin(ctx: StepContext):
    """The active repo's plugin, when one is registered (never raises)."""
    from ...plugins.base import PluginRegistry

    registry = PluginRegistry(ctx.settings.plugins_dir)
    spec = ctx.state.get("task_spec") or {}
    try:
        plugin = registry.resolve(repo_path=ctx.state.get("repo_path") or None)
        if plugin is None and spec.get("repo"):
            plugin = registry.resolve(name=str(spec["repo"]).replace("-", "_"))
        return plugin
    except Exception:
        return None


class _ScopedKnowledge:
    """Skill retrieval scoped per repo: the repo plugin's own store first, the
    shared pool second (v2 P0 — the per-repo dirs existed on RepoPlugin but
    were never wired in). Proposals land in the repo's namespace when one
    exists, so knowledge never leaks across repos."""

    def __init__(self, stores: list[SkillStore]):
        self.stores = stores  # ordered: repo store first, shared pool last

    def find(self, query: str = "", module: str = "", k: int = 3):
        out, seen = [], set()
        for store in self.stores:
            for s in store.find(query=query, module=module, k=k):
                if s.name not in seen:
                    seen.add(s.name)
                    out.append(s)
        return out[:k]

    def propose(self, **kwargs) -> None:
        self.stores[0].propose(**kwargs)


def _knowledge_stores(ctx: StepContext) -> _ScopedKnowledge:
    stores: list[SkillStore] = []
    plugin = _resolve_plugin(ctx)
    if plugin is not None and plugin.skills_dir != Path(ctx.settings.skills_dir):
        stores.append(SkillStore(plugin.skills_dir))
    stores.append(SkillStore(ctx.settings.skills_dir))
    return _ScopedKnowledge(stores)


def _retrieve_skills(ctx: StepContext, query: str) -> tuple[list[dict], "_ScopedKnowledge"]:
    store = _knowledge_stores(ctx)
    hits = store.find(query=query, k=ctx.settings.skills_top_k)
    summaries = [{"name": s.name, "summary": s.description or s.body[:200]}
                 for s in hits]
    return summaries, store


def _retrieve_memories(ctx: StepContext, query: str) -> list[str]:
    dbs: list[Path] = []
    plugin = _resolve_plugin(ctx)
    if plugin is not None:
        dbs.append(Path(plugin.debug_memory_db))
    dbs.append(Path(ctx.settings.memory_db))
    hits: list[str] = []
    seen: set[str] = set()
    for db in dbs:  # repo-scoped memories rank before the shared pool's
        try:
            if not db.exists():
                continue
            for h in DebugMemory(db).search(query, k=3):
                line = f"[{h['module']}] {h['symptom']} -> {h['fix_summary']}"
                if line not in seen:
                    seen.add(line)
                    hits.append(line)
        except Exception:
            continue
    return hits[:3]


def _knowledge_tools(store: "_ScopedKnowledge", ctx: StepContext) -> dict[str, ToolDef]:
    """Read-only knowledge tools + governed skill-candidate proposals."""

    def skill_search(query: str, **_: Any) -> str:
        hits = store.find(query=query, k=5)
        if not hits:
            return "(no matching skills)"
        return "\n\n".join(f"# {s.name}\n{s.description}\n{s.body[:1500]}"
                           for s in hits)

    def memory_search(query: str, **_: Any) -> str:
        hits = _retrieve_memories(ctx, query)
        return "\n".join(hits) or "(no matching debug memories)"

    def skill_update_candidate(name: str, description: str, body: str,
                               **_: Any) -> str:
        store.propose(name=name, description=description, body=body)
        ctx.trace.record("skill_candidate_proposed", name=name)
        return (f"candidate '{name}' recorded for curator review — active skills "
                "are never modified directly")

    s = {"type": "string"}
    return {
        "skill_search": ToolDef("skill_search", "Search procedural skills.",
                                {"type": "object", "properties": {"query": s},
                                 "required": ["query"]}, skill_search),
        "memory_search": ToolDef("memory_search", "Search debug memories.",
                                 {"type": "object", "properties": {"query": s},
                                  "required": ["query"]}, memory_search),
        "skill_update_candidate": ToolDef(
            "skill_update_candidate",
            "Propose a new/updated skill (candidate only; curator-gated).",
            {"type": "object", "properties": {"name": s, "description": s,
                                              "body": s},
             "required": ["name", "description", "body"]}, skill_update_candidate),
    }


def _repo_map_tool(ctx: StepContext, plugin) -> dict[str, ToolDef]:
    """`repo_map` — goal-ranked, budgeted structure queries (design §V2.3.4
    channel 3: structure is pulled on demand, never injected as an overview)."""
    from ...profiles.repo_map import RepoMap

    repo = ctx.state.get("repo_path") or (plugin.repo_path if plugin else "")
    if not repo or not Path(repo).exists():
        return {}
    language = "python"
    cache_dir = ctx.run_dir / "repo_map"
    if plugin is not None:
        language = str(plugin.manifest.get("repo", {}).get("language")
                       or "python")
        cache_dir = plugin.root / "repo_map"
    rmap = RepoMap(repo, language, cache_dir=cache_dir)
    if not rmap.supported:
        ctx.trace.record("capability_gap", capability=f"repo_map.{language}",
                         step="agent_runtime",
                         effect="repo_map tool unavailable; agent uses grep")
        return {}

    def repo_map(query: str, **_: Any) -> str:
        return rmap.render(str(query))

    return {"repo_map": ToolDef(
        "repo_map",
        "Goal-ranked map of the repo's files and symbol signatures for a "
        "query (budgeted). Use it to LOCATE where something lives before "
        "reading files; it is not a substitute for reading them.",
        {"type": "object", "properties": {"query": {"type": "string"}},
         "required": ["query"]}, repo_map)}
