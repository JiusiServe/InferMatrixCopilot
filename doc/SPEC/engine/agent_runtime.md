# engine/agent_runtime/ — spec

`LOC ~620 across 6 files · engine (governed agent runtime) · refactor-status: split-applied (2026-07-10)`

## Responsibility
The single governed entry for every `kind == "agent"` step, plus the
review-quality ensemble. The densest, highest-leverage subsystem in the repo —
formerly one 685-line module, now a package whose substrate (dispatch/knowledge/
utils) is separated from its two entry points (runner/ensemble).

## Package layout (one concern per file)
- `__init__.py` — public re-exports only (surface below); no logic.
- `dispatch.py` — the agent **input contract**: `AgentDispatchContext` (+ its
  `render()`) and `BASE_OUTPUT_SCHEMA`. Prompt shape, isolated from control flow.
- `knowledge.py` — repo-scoped knowledge: `_resolve_adapter`, `_ScopedKnowledge`,
  `_knowledge_stores`, `_retrieve_skills`, `_retrieve_memories`,
  `_knowledge_tools`, `_repo_map_tool`.
- `utils.py` — stateless helpers: `_build_evidence`, `_permissions_view`,
  `_coerce_output`, `_to_step_result` (+ the status→FailureKind maps).
- `runner.py` — `run_agent_step`: assembles dispatch context, packs evidence,
  retrieves knowledge, runs the tool loop, coerces output, traces everything.
- `ensemble.py` — `run_agent_step_ensemble`: perspective-diverse lens fan-out +
  verify-and-merge reduction.

## Public contract (importable from `engine.agent_runtime`)
`run_agent_step(...) -> (StepResult, output)`; `run_agent_step_ensemble(...)`;
`AgentDispatchContext`; `BASE_OUTPUT_SCHEMA`; `_resolve_adapter`,
`_retrieve_skills` (used by steps/tests). The re-exporting `__init__` keeps the
pre-split import paths (`from ..agent_runtime import X`) unchanged.

## Invariants (**B4**)
- Single entry: agent steps do agentic work only through `run_agent_step` — no
  ad-hoc `ctx.llm.create()` for investigation.
- Evidence capped per item + archived + fenced `<untrusted_data>` (**C7**).
- `_ScopedKnowledge`: repo skills+memory before shared pool; proposals land in
  repo namespace, candidates only (**D1/D2**).
- `_repo_map_tool`: on-demand, never injected as prose; unsupported language →
  `capability_gap`.
- Briefing enters prompt only when `profile_briefing_enabled` (ablation switch).
- Output: base+extension schema, one repair round, status→FailureKind; budget
  exhaustion forces a final answer. Full trace (`agent_dispatch`/`agent_output`).
- Ensemble reducer: per-numbered-candidate keep/drop/dup, deterministic
  assembly, unmentioned kept (fail-open), consensus-gated fast path.

## Internal dependency rule
`runner`/`ensemble` depend on `dispatch`/`knowledge`/`utils`, never the reverse;
`ensemble` depends on `runner` (not vice-versa). The substrate files import no
sibling entry point, so there is no cycle.

## Scope — not here
No task/planning logic; no repo literals (system prompt repo-neutral). Step-
specific prompts/lenses live in the step file (e.g. `steps/review/prompts.py`).

## Dependencies (allowed)
`agent_loop`, `llm`, `memory/*`, `adapters/base`, `profiles/repo_map`, `scopes`,
`tools`, `engine/step`.

## Extension points
A new list-output agent step adopts the ensemble by passing lenses +
merge_guidance; a new knowledge source → extend `_ScopedKnowledge`/
`_knowledge_tools` in `knowledge.py`.

## Tests
`test_agent_runtime.py`, `test_agent_ensemble.py`, `test_review_step.py`.

## Refactor notes
Split **applied** (was the highest-priority cohesion target). The inline
eval-citation comments are institutional memory — they moved WITH their code
into the sibling files, never dropped. `ensemble.py` (~290 LOC) remains the
largest file; its reducer is a single cohesive algorithm and is not a further
split target.
