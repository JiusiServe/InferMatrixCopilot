"""Repo-scoped knowledge for agent steps: adapter resolution, skill/debug-memory
retrieval, and the read-only tools an agent uses to pull more on demand.

Retrieval is scoped per repo — the active adapter's own store ranks before the
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


def _resolve_adapter(ctx: StepContext):
    """The active repo's adapter, when one is registered (never raises)."""
    from ...adapters.base import AdapterRegistry

    registry = AdapterRegistry(ctx.settings.adapters_dir)
    spec = ctx.state.get("task_spec") or {}
    try:
        adapter = registry.resolve(repo_path=ctx.state.get("repo_path") or None)
        if adapter is None and spec.get("repo"):
            adapter = registry.resolve(name=str(spec["repo"]).replace("-", "_"))
        return adapter
    except Exception:
        return None


class _ScopedKnowledge:
    """Skill retrieval scoped per repo: the repo adapter's own store first, the
    shared pool second (v2 P0 — the per-repo dirs existed on RepoAdapter but
    were never wired in). Proposals land in the repo's namespace when one
    exists, so knowledge never leaks across repos."""

    def __init__(self, stores: list[SkillStore]):
        """Hold the ordered skill stores — repo store first, shared pool last —
        so retrieval and proposals honor the per-repo scoping."""
        self.stores = stores  # ordered: repo store first, shared pool last

    def find(self, query: str = "", module: str = "", k: int = 3):
        """Search the stores in priority order and return up to `k` skills,
        deduped by name (first store wins on a tie, so the repo's own skill
        outranks a same-named shared one). `query`/`module` are passed through
        to each store's own ranking."""
        out, seen = [], set()
        for store in self.stores:
            for s in store.find(query=query, module=module, k=k):
                if s.name not in seen:
                    seen.add(s.name)
                    out.append(s)
        return out[:k]

    def propose(self, **kwargs) -> None:
        """Record a skill-update candidate in the highest-priority store (the
        repo's namespace when one exists), so proposals never leak across repos
        and never touch active skills."""
        self.stores[0].propose(**kwargs)

    def touch(self, name: str) -> None:
        """Record one use of skill `name` in whichever store owns it — the
        usage prior (`run_count`) that breaks retrieval ties toward proven
        skills was a dead field until steps actually stamped it."""
        for store in self.stores:
            if store.touch(name):
                return


def _knowledge_stores(ctx: StepContext) -> _ScopedKnowledge:
    """Build the per-repo `_ScopedKnowledge`: the active adapter's own skill
    store first (when it differs from the shared dir), then the shared pool —
    the ordering that gives repo skills retrieval and proposal priority."""
    stores: list[SkillStore] = []
    adapter = _resolve_adapter(ctx)
    if adapter is not None and adapter.skills_dir != Path(ctx.settings.skills_dir):
        stores.append(SkillStore(adapter.skills_dir))
    stores.append(SkillStore(ctx.settings.skills_dir))
    return _ScopedKnowledge(stores)


def _retrieve_skills(ctx: StepContext, query: str) -> tuple[list[dict], "_ScopedKnowledge"]:
    """Pre-retrieve the top-k skills for `query` to seed the dispatch context.
    Returns light `{name, summary}` dicts (summary falls back to the skill body
    head when it has no description) plus the live `_ScopedKnowledge` store, so
    the caller can also hand the agent its on-demand `skill_search` tool."""
    store = _knowledge_stores(ctx)
    hits = store.find(query=query, k=ctx.settings.skills_top_k)
    summaries = [{"name": s.name, "summary": s.description or s.body[:200]}
                 for s in hits]
    return summaries, store


def _retrieve_memories(ctx: StepContext, query: str) -> list[str]:
    """Search the debug-memory stores for `query` and return up to 3 one-line
    `[module] symptom -> fix` hits. The repo adapter's DB is searched before the
    shared one so repo-scoped memories rank first; duplicate lines are dropped
    and any DB error is swallowed (retrieval never fails a step)."""
    dbs: list[Path] = []
    adapter = _resolve_adapter(ctx)
    if adapter is not None:
        dbs.append(Path(adapter.debug_memory_db))
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
        """Tool: return up to 5 matching skills rendered as name + description +
        body head, or a `(no matching skills)` sentinel."""
        hits = store.find(query=query, k=5)
        if not hits:
            return "(no matching skills)"
        return "\n\n".join(f"# {s.name}\n{s.description}\n{s.body[:1500]}"
                           for s in hits)

    def memory_search(query: str, **_: Any) -> str:
        """Tool: return the debug-memory hits for `query` as newline-joined
        lines, or a `(no matching debug memories)` sentinel."""
        hits = _retrieve_memories(ctx, query)
        return "\n".join(hits) or "(no matching debug memories)"

    def skill_update_candidate(name: str, description: str, body: str,
                               **_: Any) -> str:
        """Tool: record a proposed skill as a curator-gated candidate (active
        skills are never edited by an agent), trace it, and confirm to the
        agent."""
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


def _repo_map_tool(ctx: StepContext, adapter) -> dict[str, ToolDef]:
    """`repo_map` — goal-ranked, budgeted structure queries (design §V2.3.4
    channel 3: structure is pulled on demand, never injected as an overview)."""
    from ...profiles.repo_map import RepoMap

    repo = ctx.state.get("repo_path") or (adapter.repo_path if adapter else "")
    if not repo or not Path(repo).exists():
        return {}
    language = "python"
    cache_dir = ctx.run_dir / "repo_map"
    if adapter is not None:
        language = str(adapter.manifest.get("repo", {}).get("language")
                       or "python")
        cache_dir = adapter.root / "repo_map"
    rmap = RepoMap(repo, language, cache_dir=cache_dir)
    if not rmap.supported:
        ctx.trace.record("capability_gap", capability=f"repo_map.{language}",
                         step="agent_runtime",
                         effect="repo_map tool unavailable; agent uses grep")
        return {}

    def repo_map(query: str, **_: Any) -> str:
        """Tool: render the goal-ranked, budgeted repo map for `query`."""
        return rmap.render(str(query))

    return {"repo_map": ToolDef(
        "repo_map",
        "Goal-ranked map of the repo's files and symbol signatures for a "
        "query (budgeted). Use it to LOCATE where something lives before "
        "reading files; it is not a substitute for reading them.",
        {"type": "object", "properties": {"query": {"type": "string"}},
         "required": ["query"]}, repo_map)}
