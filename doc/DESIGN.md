# Design

This repo implements the **vLLM-Omni Copilot** design
(`vllm-omni-rebase-agent/docs/copilot/copilot_design`, plus its
`implementation/` milestone plan). This document maps the design onto the code
here; the rationale lives in those source docs.

## Architecture

```
 user NL ──► intent.py ──► TaskSpec (task_spec.py)          §3.Y CLI layer
                              │  tier fixed by kind (L0/L1/L2), confirm gates
                              ▼
                     engine/planner.py                      §3.2 reuse>adapt>generate
              reuse ─────────┼───────── generate (read-only kinds only)
                              ▼
                  playbooks/store.py registry               §3.2 candidate/active/locked
                              ▼
                    engine/executor.py                      §3.X engine substrate
        per-step checkpoint/resume · retries · typed failures · escalation
                              ▼
             engine/builtin_steps.py (Step library)         §3.X.1 Steps
      tools.py + scopes.py (ToolScope/PathScope choke point) §3.3(2)
      review/ (diff summary → triggers → read-only reviewer) §3.3(3)
      memory/ (RunTrace, DebugMemory FTS5, gated skills)     §3.3(4)
      plugins/ (repo knowledge, draft bootstrap)             plugin layer
      targets/ (PushPolicy + guard_push)                     target layer
      notify.py (ESCALATION.md + email, exit 3)              goal #4
```

## Key decisions

1. **Wrap, don't rewrite the rebase.** The locked `repo-rebase` playbook
   delegates to the existing 5-phase orchestrator via `rebase.run_external`
   (`REBASE_ORCHESTRATOR_CMD`). Zero regression: this repo adds orchestration
   *around* the proven pipeline, it does not fork it. Native step-level
   decomposition of the rebase (waves, module agents) migrates later per the
   milestone plan.
2. **Own executor instead of LangGraph.** The design (§3.X.5) is explicit that
   LangGraph is a possible backend, not the domain abstraction. The executor
   here is ~150 lines, async, with per-step checkpoint/resume — dependency-free
   and fully testable. A LangGraph backend can be swapped in behind the same
   `Playbook`/`StepSpec` contracts if/when this merges with the parent agent.
3. **Tier is derived, never parsed.** `TaskSpec` has no tier field an LLM or
   user could set; `tier` is a property of the task kind. Natural language can
   therefore never widen permissions (§3.Y.4).
4. **Generation is structurally read-only.** The planner's generate path
   raises if any composed step has `risk` ∈ {write_workspace, push}; write-capable
   kinds without a vetted playbook escalate instead of improvising.
5. **Fail-closed reviews.** `run_patch_review` returns `unavailable` without a
   reviewer LLM; unparseable reviewer output degrades to `revise`. Push gates
   treat anything but `lgtm` as not-passing.
6. **Untrusted data is fenced.** GitHub-fetched text enters agent prompts inside
   `<untrusted_data>` markers with an explicit "not instructions" preamble, and
   only terminal input reaches the intent parser (channel separation, §3.Y.4).

## Module map

| Path | Design concept |
|---|---|
| `src/omni_copilot/task_spec.py`, `intent.py`, `cli.py` | §3.Y conversational CLI, TaskSpec, clarify-not-guess |
| `src/omni_copilot/engine/step.py`, `registry.py` | §3.X Step abstraction, vetted step library |
| `src/omni_copilot/engine/executor.py` | engine substrate: checkpoint/resume, typed failure routing |
| `src/omni_copilot/engine/planner.py` | §3.2 reuse > adapt > generate, L0/L1/L2 |
| `src/omni_copilot/engine/builtin_steps.py` | initial step palette (guard, rebase, review gate, push, gh reads, agent steps) |
| `src/omni_copilot/engine/agent_runtime.py` | unified Agent-Step runtime (修正方案): AgentDispatchContext, evidence pack (cap+archive), skill/memory retrieval + gated candidates, enforced scopes, structured output contract, full RunTrace; `run_agent_step_ensemble` — perspective-diverse fan-out + verify-and-merge for run-to-run robustness (eval-informed; any list-output agent step) |
| `src/omni_copilot/playbooks/store.py`, `playbooks/*.yaml` | Playbook registry: versioned, provenance, candidate/active/locked/retired |
| `src/omni_copilot/scopes.py`, `tools.py`, `agent_loop.py` | 框架层改进 (2): ToolScope/PathScope at one choke point |
| `src/omni_copilot/review/` | 框架层改进 (3): diff summary → trigger rules → read-only patch reviewer |
| `src/omni_copilot/run_trace.py`, `memory/` | 框架层改进 (4): RunTrace / DebugMemory / gated skills |
| `src/omni_copilot/plugins/` | RepoPlugin: plugin zero, registry, deterministic bootstrap → draft |
| `src/omni_copilot/targets/base.py` | Target-layer types + unified `guard_push` |
| `src/omni_copilot/notify.py` | goal #4: escalation channel, blocked exit code 3 |

## Data & artifacts per run

`~/.omni-copilot/runs/run-<ts>/`: `run_trace.jsonl` (facts), `progress.json`
(step checkpoints — resume re-enters the first incomplete step),
`RUN_REPORT.md`, `ESCALATION.md` (only when blocked).
