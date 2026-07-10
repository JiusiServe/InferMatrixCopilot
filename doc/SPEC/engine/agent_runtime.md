# engine/agent_runtime.py — spec

`LOC ~685 · engine (governed agent runtime) · refactor-status: split-candidate`

## Responsibility
The single governed entry for every `kind == "agent"` step, plus the
review-quality ensemble. The densest, highest-leverage file in the repo.

## Functionality
`run_agent_step`: builds `AgentDispatchContext` (task/step/repo/briefing/
evidence/permissions/skills/memories/output-contract), packs+archives+fences
evidence, retrieves scoped knowledge + tools, runs the tool loop, coerces
output to the contract (one repair round), maps status→FailureKind, traces
everything. `run_agent_step_ensemble`: perspective-diverse lens fan-out +
verify-and-merge reduction. Helpers: `_resolve_plugin`, `_ScopedKnowledge`,
`_knowledge_tools`, `_repo_map_tool`, `_build_evidence`, `_coerce_output`,
`_to_step_result`, `_permissions_view`.

## Public contract
`run_agent_step(...) -> (StepResult, output)`; `run_agent_step_ensemble(...)`;
`AgentDispatchContext`; `BASE_OUTPUT_SCHEMA`; `_resolve_plugin` (used by steps).

## Invariants (**B4**)
- Single entry: agent steps do agentic work only through here — no ad-hoc
  `ctx.llm.create()` for investigation.
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

## Scope — not here
No task/planning logic; no repo literals (system prompt repo-neutral). Step-
specific prompts/lenses live in the step file (e.g. `steps/review.py`).

## Dependencies (allowed)
`agent_loop`, `llm`, `memory/*`, `plugins/base`, `profiles/repo_map`, `scopes`,
`tools`, `engine/step`.

## Extension points
A new list-output agent step adopts the ensemble by passing lenses +
merge_guidance; a new knowledge source → extend `_ScopedKnowledge`/
`_knowledge_tools`.

## Tests
`test_agent_runtime.py`, `test_agent_ensemble.py`, `test_review_step.py`.

## Refactor notes
**Highest-priority split target.** Four cohesive clusters could become files
under an `agent/` subpackage: (1) `dispatch.py` — `AgentDispatchContext`,
`_build_evidence`, `_permissions_view`, `_coerce_output`, `_to_step_result`,
`run_agent_step`; (2) `ensemble.py` — `run_agent_step_ensemble` + reducer;
(3) `knowledge.py` — `_resolve_plugin`, `_ScopedKnowledge`, `_knowledge_tools`,
`_repo_map_tool`; (4) `BASE_OUTPUT_SCHEMA` as a small constants module. Keep
`run_agent_step`/`run_agent_step_ensemble` as the two public entries. The
inline eval-citation comments are institutional memory — move them WITH their
code, never drop them.
