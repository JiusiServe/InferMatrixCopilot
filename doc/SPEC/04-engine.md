# 04 — Engine Substrate & Governed Agent Runtime

Modules: `engine/step.py`, `engine/registry.py`, `engine/executor.py`,
`engine/agent_runtime.py`, `agent_loop.py`, `tools.py`, `scopes.py`, `llm.py`.

---

## `engine/step.py`

- **Responsibility** — the base execution vocabulary.
- **Public contract** — `FailureKind` (RETRYABLE, REPLAN, TEST_FAILURE, BLOCKED,
  FORBIDDEN, ESCALATE); `StepResult(ok, failure?, summary, outputs,
  changed_files)`; `StepContext` (settings, state, params, run_dir, trace, llm?,
  notifier?, item?); `StepSpec(name, kind, risk, handler, description,
  tool_scope?, patch_review_triggers)`. `Kind ∈ {deterministic, script, agent,
  validation, report}`; `Risk ∈ {read, write_workspace, push, knowledge,
  report}`.
- **Invariants** — the base vocabulary is repo- and task-agnostic. `StepSpec` is
  frozen. **Depends on** only `run_trace`, `scopes` (**A3/§00.4.3**).
- **Scope** — types only. No behavior.

## `engine/registry.py`

- **Responsibility** — `StepRegistry`: a name→`StepSpec` map.
- **Public contract** — `register(spec)`, `get(name)`, `__contains__`, `names`,
  `read_only_names`.
- **Invariants** — duplicate registration raises; `get` on an unknown name raises
  with the registered set (fail loudly). The registry is the single place a name
  string resolves to a handler.
- **Scope** — storage/lookup only. No execution, no policy.

## `engine/executor.py`

- **Responsibility** — run a playbook's steps with task-agnostic guarantees.
- **Public contract** — `Executor(registry, settings, run_dir, trace, llm?,
  notifier?)`; `run(playbook, state) -> RunOutcome(status, step_results,
  blocked_reason)`. Helpers `_eval_when`, `_merge`.
- **Invariants**
  - **Checkpoint/resume** — completed steps recorded in `progress.json`; on
    resume, cached `outputs.state_updates` are re-applied to state before
    skipping (**B2**).
  - **foreach** — fans out over a state list via `asyncio.gather`; `_merge`
    keeps outputs by index AND lifts each item's `state_updates` (last-writer
    wins) to the top level.
  - **`when:`** — TaskSpec fields then state keys; unknown key → blocked, not
    silent (**B3**).
  - **Typed routing** — BLOCKED/ESCALATE/FORBIDDEN → notifier.escalate + return
    blocked; RETRYABLE → bounded retry; others → failed. Unhandled exception →
    BLOCKED (never swallowed, **B1**).
  - **Success recording** — on ok, persist checkpoint, then
    `state.update(outputs.state_updates)` and index outputs by step id.
- **Scope** — execution guarantees only. No step logic, no repo knowledge, no
  planning, no LLM prompts.
- **Depends on** — `engine/{step,registry}`, and (typing) config/llm/notifier/
  playbook/run_trace.
- **Tests** — `test_engine.py`, `test_v2_p0.py` (resume/foreach/when).

## `engine/agent_runtime.py` — the heart

- **Responsibility** — the single governed entry for every `kind == "agent"`
  step: dispatch context, evidence pack, scoped knowledge + tools, output
  contract, full trace; plus the review-quality ensemble.
- **Public contract** — `run_agent_step(ctx, *, step_name, purpose, evidence,
  guidance?, expected?, output_extension?, scope?, extra_tools?, max_iters?)
  -> (StepResult, output_dict)`; `run_agent_step_ensemble(...)` adds lenses +
  merge. `AgentDispatchContext`, `BASE_OUTPUT_SCHEMA`.
- **Invariants** (**B4**)
  - Single entry: an agent step does agentic work only through this function.
  - Evidence is capped per item, full text archived to the run dir, fenced in
    `<untrusted_data>` with a not-instructions preamble (**C7**).
  - Knowledge via `_ScopedKnowledge`: the active repo's `skills/` +
    `debug_memory.db` before the shared pool; agent proposals land in the repo
    namespace, candidates only (**D1/D2**).
  - `_repo_map_tool`: goal-ranked structure on demand; never injected as prose.
  - Briefing: only the profile's word-budgeted briefing slice enters the prompt,
    and only when `profile_briefing_enabled` (the ablation switch).
  - Output: base schema + extension, one repair round, status → FailureKind;
    budget exhaustion forces a final answer. Full RunTrace (`agent_dispatch`,
    `agent_output`, token cost).
  - Ensemble reducer: per-numbered-candidate keep/drop/dup, deterministic
    assembly, unmentioned kept (fail-open), consensus-gated fast path. The
    inline eval citations are load-bearing rationale — keep them with the code.
- **Scope** — agent governance + review ensemble. No task/planning logic; no
  repo literals (its system prompt is repo-neutral).
- **Depends on** — `agent_loop`, `llm`, `memory/*`, `plugins/base`,
  `profiles/repo_map`, `scopes`, `tools`, `engine/step`.
- **Tests** — `test_agent_runtime.py`, `test_agent_ensemble.py`,
  `test_review_step.py`.

## `agent_loop.py`

- **Responsibility** — the minimal tool-use loop, ToolScope-constrained and
  trace-audited.
- **Public contract** — `run_agent(llm, *, system, prompt, scope, trace?,
  model?, max_iters, extra_tools?) -> AgentOutcome`.
- **Invariants** — the loop only ever sees tools its scope allows; every call
  goes through `tools.dispatch`; budget exhaustion forces a final answer instead
  of discarding the investigation. No planning/step semantics here.
- **Depends on** — `llm`, `run_trace`, `scopes`, `tools`.
- **Tests** — `test_agent_loop.py`.

## `tools.py`

- **Responsibility** — atomic capabilities + the single scope-enforcing dispatch
  choke point.
- **Public contract** — `ToolDef`; `TOOLS` (read_file, write_file, edit_file,
  list_dir, grep, run_shell); `tool_definitions_for(scope, extra?)`;
  `dispatch(name, args, *, scope?, trace?, extra?) -> {ok, result|error,
  out_of_scope}`.
- **Invariants** (**C3**) — every builtin call is scope-checked; refused calls
  return an error (never raise); out-of-scope writes execute but emit
  `out_of_scope_edit`; full-file `.py` writes emit `full_file_write`; errors are
  observations, not crashes. Extra (step-provided) tools bypass the builtin
  allowlist but are still traced.
- **Scope** — "what can be done". Tools express capability, not engineering
  semantics (that is a step). MUST NOT contain task/repo logic.
- **Tests** — `test_scopes_tools.py`.

## `scopes.py`

- **Responsibility** — path-level tool permissions.
- **Public contract** — `ToolScope(name, allowed_tools, path_scope?, read_only)`
  with `check`; `PathScope(writable, primary)` with `check_write`;
  `read_only_scope`, `pre_plan_scope`, `post_plan_scope`.
- **Invariants** — three outcomes: allowed / refused (tool not in set, or write
  outside `writable`, or read-only scope) / out-of-scope (inside `writable` but
  outside `primary` — allowed + recorded). `writable` is a hard wall; `primary`
  is the module's owned files.
- **Scope** — permission decisions only; no execution.
- **Tests** — `test_scopes_tools.py`.

## `llm.py`

- **Responsibility** — the Anthropic-SDK-compatible client wrapper.
- **Public contract** — `LLM(settings)` with `available`, `create(...)`;
  `Reply`, `Block`, `parse_json_reply`.
- **Invariants** — `available` is false without a key/endpoint; callers must
  degrade (a `capability_gap`), not crash. Untrusted content is fenced by
  callers, not here.
- **Scope** — transport + parsing only. No prompts, no policy.
