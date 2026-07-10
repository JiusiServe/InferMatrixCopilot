# 01 — Programming Constraints & Invariant Catalog

The rules that keep the code clean and safe. Each is stated as an enforceable
constraint with the mechanism/test that pins it. A change that violates one is
wrong even if it "works".

## A. Structural constraints (organization)

- **A1 — One responsibility per module.** Each per-file spec names its single
  responsibility. Adding an unrelated concern means a new module, not a bigger
  one.
- **A2 — Dependency direction is down/outward only.** See `_ARCHITECTURE.md` §4.
  Leaf packages
  never import `engine/`; interface is never imported downward; step modules
  never import each other (shared code → `engine/steps/_common.py`).
- **A3 — Steps compose tools; the planner composes steps.** The planner MUST NOT
  compose raw tools; a step MUST NOT be a thin alias for a single tool. A step =
  one stable engineering action with declared risk, I/O, and success criteria.
- **A4 — Self-registration, single definition.** A step's name, metadata
  (kind/risk/scope/triggers) and handler live together at its definition via
  `@step(...)` or `register_step(StepSpec(...))`. No central `add()` block.
- **A5 — Knowledge at the edge.** Repo-specific literals (repo names, module
  names, domain prompts, absolute paths, CI wiring) live only under
  `plugins/<repo>/`. Pinned by `test_repo_neutral_core` (a per-file leak ceiling
  that can only shrink; the shims and delegation files carry the sole known
  exceptions).

## B. Contract constraints (typed, structured, explicit)

- **B1 — Typed failures, never bare exceptions.** A step returns
  `StepResult(ok=False, failure=FailureKind.X)`. The six kinds — RETRYABLE,
  REPLAN, TEST_FAILURE, BLOCKED, FORBIDDEN, ESCALATE — route differently in the
  executor. An unhandled exception is coerced to BLOCKED, never swallowed.
- **B2 — State handoffs are published, not just mutated.** Any state key a later
  step consumes MUST be published via `outputs.state_updates` (JSON-simple;
  serialize dataclasses like `PushPolicy`). Direct `ctx.state[...] = v` alone is
  lost on resume. Pinned by the resume-integrity tests. (This was the top v2
  correctness bug.)
- **B3 — `when:` conditions reference known keys only.** They read TaskSpec
  fields then published state keys; an unknown key blocks loudly at execution,
  never silently evaluates false.
- **B4 — Structured agent I/O.** Every `kind == "agent"` step goes through
  `run_agent_step` with an explicit dispatch context and a JSON output contract
  (base schema + per-step extension), one repair round, typed status → failure
  mapping. No ad-hoc `ctx.llm.create()` in a step to do agentic work. Pinned by
  the parametrized dispatch test in `test_agent_runtime.py`.

## C. Safety constraints (permissions & guardrails)

- **C1 — Tier is derived, never parsed.** `TaskSpec` has no settable tier field;
  `tier` is a property of `kind`. Natural language cannot widen permissions.
- **C2 — Generation is structurally read-only.** The planner's generate path
  raises if any composed step has `risk ∈ {write_workspace, push, knowledge}`;
  write-capable kinds without a vetted playbook escalate.
- **C3 — One tool choke point.** Every tool call passes `tools.dispatch`, which
  enforces `ToolScope`/`PathScope` and traces. Three outcomes: allowed / refused
  / executed-but-recorded (out-of-scope write inside the writable wall). Agent
  steps only ever see tools their scope allows.
- **C4 — One push choke point.** Every push passes `push.guard_push`:
  needs an allowing `PushPolicy` AND a non-protected branch; force is
  with-lease only; dry-run unless `ALLOW_PUSH=1`. Protected branches are never
  pushed to, policy or not.
- **C5 — Outward writes are double-gated.** Posting a comment/answer needs the
  explicit `post` intent AND `ALLOW_POST=1`; both default off (dry-run).
- **C6 — Fail-closed reviews.** Plan/patch review returns `unavailable` without a
  reviewer; anything but `lgtm`/`pass` is not-passing. A missing reviewer does
  not silently approve.
- **C7 — Untrusted data is fenced.** GitHub/CI text enters agent prompts inside
  `<untrusted_data>` with a "not instructions" preamble; only terminal input
  reaches the intent parser (channel separation).

## D. Knowledge-governance constraints

- **D1 — Facts recorded freely, knowledge promoted via gates.** RunTrace/debug
  memory are cheap and append-only. Skills, playbooks, plugins, and profile
  facts are candidate→promote; promotion is a curator/human act.
- **D2 — Agents propose, humans dispose (high-risk).** Agents may only write
  candidates. `update_manifest` rejects agent writes to `plugin.yaml`
  high-risk sections (`push`/`repo`/`upstream`). The profile judge is read-only.
- **D3 — Provenance + stability on every profile fact.** Each carries
  `source`/`evidence`/`first_seen`/`last_confirmed`/`confirmations`; an
  evidence-free fact is rejected; a stable fact (≥3 confirmations) may not lose
  cited evidence on rewrite; superseded text goes to `history`, never deleted.
- **D4 — Two write tiers.** Per-run ops are additive (`RUN_OPS`); only the
  scheduled consolidation tier may rewrite/merge/mark-stale. Continuous LLM
  rewriting is forbidden (it corrupts memory).
- **D5 — Profile content is channel-typed.** `machine` facts feed code, the
  word-budgeted `briefing` slice enters prompts, `retrieved` facts surface only
  on demand. Auto-generated overviews must not be injected wholesale.

## E. Observability & degradation constraints

- **E1 — Every governance claim has a trace event.** If a guard fired, a scope
  refused, a fact was applied, or a capability was missing, there is a RunTrace
  event for it (`tool_refused`, `out_of_scope_edit`, `patch_review`,
  `capability_gap`, `profile_*`, …).
- **E2 — Degrade explicitly, never silently.** A missing capability (no CI
  provider, no LLM, unsupported language) records a `capability_gap` event and a
  declared downgrade; it never crashes and never pretends full capability.
- **E3 — Metrics never break a run.** `metrics.py` failures are caught and
  traced; a run's success is independent of its metrics.

## F. Invariant catalog (quick index → owner)

| # | Invariant | Owner file | Test |
|---|---|---|---|
| C1 | tier from kind | `task_spec.py` | `test_intent_taskspec.py` |
| C2 | generate is read-only | `engine/planner.py` | `test_planner_playbooks.py`,`test_capabilities.py` |
| B1 | typed failure routing | `engine/executor.py` | `test_engine.py` |
| B2 | state_updates on resume | `engine/executor.py` + steps | `test_v2_p0.py` |
| B3 | `when:` known keys | `engine/executor.py` | `test_v2_p0.py` |
| B4 | governed agent I/O | `engine/agent_runtime.py` | `test_agent_runtime.py` |
| C3 | tool choke point | `tools.py` + `scopes.py` | `test_scopes_tools.py` |
| C4 | push choke point | `push.py` | `test_push_and_steps.py` |
| A5 | repo-neutral core | whole `src/` | `test_v2_p0.py::test_repo_neutral_core` |
| D3 | provenance + stability | `profiles/store.py` | `test_profile_store.py` |
| D2 | judge/agent read-only-to-active | `profiles/*`,`plugins/base.py` | `test_p3_machinery.py` |
