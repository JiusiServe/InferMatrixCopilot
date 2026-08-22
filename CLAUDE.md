# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A playbook-driven repo-maintenance copilot. It takes a natural-language command
("review pr 4830", "answer issue 4842, do not post"), classifies it into a
governed `TaskSpec`, resolves it to a pipeline, and executes that pipeline with
per-step checkpointing, scoped tool access, and gated outward writes.

Package/CLI are `infermatrix_copilot` / `infermatrix-copilot`; the *project* was
renamed from `vllm-infermatrix-copilot`. vLLM-Omni is adapter zero (the
reference repo), not a hardcoded assumption — see "Repo neutrality" below.

## Commands

```bash
bash install.sh                    # venv + editable install + .env seed + wrapper + doctor
bash install.sh --uninstall        # removes only installer-created artifacts (.env untouched)
pip install -e ".[dev]"            # pytest lives in the dev extra; ".[mcp]" adds the MCP server

pytest                             # full offline suite (~400 tests; no GPU/network/API key)
pytest test/test_v2_p0.py -x       # one file
pytest test/test_v2_p0.py::test_resume_restores_state_handoffs   # one test
pytest -k ensemble                 # by name

./infermatrix-copilot doctor       # preflight; every ✗ prints its exact fix
./infermatrix-copilot doctor --probe   # 1-token live probe per tier (the ONLY paid doctor check)
./infermatrix-copilot -p "review pr 4830" --plan-only    # resolve + print plan, no execution
./infermatrix-copilot -p "review pr 4830" --yes          # headless one-shot
./infermatrix-copilot --playbook repo-rebase-native --yes --task-param local_ci_only=true
./infermatrix-copilot --resume     # re-enter the last run at its first incomplete step
./infermatrix-copilot              # conversational chat REPL (default when an LLM is configured)
```

Run artifacts land in `~/.infermatrix-copilot/runs/run-<ts>-<uuid6>/`:
`RUN_REPORT.md`, `DIAGNOSTICS.md`, `run_trace.jsonl`, `progress.json`,
`metrics.json`, `ESCALATION.md` (only when blocked). PR-review checkouts go to
`~/.infermatrix-copilot/worktrees/`.

Knowledge-tree validators (required after any `knowledge/` batch — see `AGENTS.md`):

```bash
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

## Architecture

Two orthogonal flows. Read `doc/CODE_TOUR.md` for the file-by-file walkthrough
(organized by data flow), `doc/DESIGN.md` for rationale, `doc/SPEC/` for the
normative per-layer contracts.

**Execution spine** — one task, left to right:

```
terminal string → intent.py → TaskSpec → planner → Resolution → executor → steps → report
                  (LLM-only)  (tier=f(kind))  (reuse>adapt>generate)  (shared `state` dict)
```

**Knowledge plane** — orthogonal, read on every run, written under governance:
profile briefing, per-repo skills, debug memory (SQLite+FTS5), on-demand
`repo_map`. Agents *propose* candidates; humans promote. Read-wide/write-narrow
is the safety model.

### The invariants that matter

These are enforced in code and pinned by tests. Breaking one is a regression
even if the suite you ran was green.

1. **`tier` is derived from `kind`, never parsed.** `TaskSpec` has no
   tier field a user or LLM could set (`task_spec.py::KIND_TIER`). Natural
   language can never widen permissions. `mode` (`eco`/`performance`) picks the
   *model* and is orthogonal — a cheaper model never changes blast radius.

2. **Every state key a later step consumes must be published via
   `outputs.state_updates`.** Steps hand off through one shared `state` dict;
   the executor's resume path restores only `state_updates`. Writing
   `ctx.state[...]` directly works until someone runs `--resume`, then the
   downstream step sees nothing and spuriously BLOCKS. `PushPolicy` is
   serialized JSON-simple and rehydrated by `ci.push`.

3. **Generation is structurally read-only.** The planner's generate path raises
   if any composed step has `risk ∈ {write_workspace, push}`. Write-capable
   kinds with no vetted playbook escalate rather than improvise. Locked
   playbooks refuse adaptation outright.

4. **Trust boundary: instructions come only from the terminal.** Only terminal
   input reaches `intent.py`. Fetched GitHub/CI text is *data* — always fenced
   in `<untrusted_data>` with a "not instructions" preamble. Injection
   resistance comes from channel separation, not from parsing.

5. **One choke point per dangerous capability.** Every agent tool call passes
   `tools.dispatch` (checks `ToolScope`/`PathScope`, traces; out-of-scope edits
   execute but are *recorded*, never silent). Every push passes
   `push.guard_push` (needs an allowing `PushPolicy`, dry-run unless
   `ALLOW_PUSH=1`, force is `--force-with-lease` only, protected branches never
   pushed regardless of policy). Outward writes are double-gated: explicit
   `post`/push intent in the TaskSpec **and** the env flag.

6. **Repo neutrality is enforced.** No repo-specific literal (repo names, module
   names, domain prompts, absolute paths) in `src/infermatrix_copilot/` —
   `test_v2_p0.py::test_repo_neutral_core` caps the known-leak list and it can
   only shrink. Repo knowledge lives in `adapters/<repo>/` only. Core prompts
   may say *how* to review/debug; only the profile says *what this repo is*.

7. **Fail-closed, never silently degrade.** No reviewer LLM → `unavailable`,
   which push gates treat as not-passing. Missing capability → a declared
   `capability_gap` trace event surfaced in the run report. Unknown `when:` key
   → blocks loudly. Performance tier unconfigured → `TierNotConfiguredError`
   upfront (the silent eco fallback is how a run once carried an Opus label
   while DeepSeek served its own model and metrics fabricated 60× the cost).

### Layer map

| Path | Role |
|---|---|
| `intent.py`, `task_spec.py`, `cli/`, `chat.py`, `ui.py` | Command intake. `Copilot` (cli/copilot.py) is the orchestration core. Chat runs through the *same* TaskSpec/planner/confirm path — it can never widen permissions. |
| `engine/planner.py`, `playbooks/store.py` | reuse > adapt > generate. `find()` matches kind → exact repo → repo-neutral with `requires ⊆ capabilities`; candidates are never auto-recalled. |
| `engine/executor.py`, `step.py`, `registry.py` | Task-agnostic substrate: checkpoint/resume, `foreach` fan-out, `when:` conditions, bounded retries on RETRYABLE only, typed failure routing. |
| `engine/agent_runtime/` | Every `kind=="agent"` step's single entry. Dispatch context renders **static-first** for prompt-cache prefix reuse; evidence capped per item and archived; structured output contract with one repair round and salvage of non-empty failures. `ensemble.py` = multi-lens fan-out → per-item keep/drop/dup reduction (unmentioned candidates are KEPT — fail-open). |
| `engine/steps/` | The step library; `@step`-decorated handlers self-register (no central registry edit). |
| `adapters/base.py`, `adapters/<repo>/` | Tier 1 `manifest.yaml` (human-gated: repo/upstream/push sections are `HIGH_RISK_SECTIONS`, rejected on agent write) + Tier 2 `profile/` (agent-established, evidence-gated). Deliberately not merged. |
| `profiles/`, `memory/` | Typed patch ops are the ONLY profile write surface. Per-run tier may only add; `agent.profile_consolidate` is the only rewrite/merge tier. Facts without evidence are rejected; stable facts can't lose cited evidence; dormancy marks `stale`, never deletes. |
| `review/` (top level) | Conditional Patch Review — cheap deterministic diff summary always → 7 trigger rules → read-only LLM reviewer only on risk. Distinct from `engine/steps/review/`, which is the PR-review *step*. |
| `mcp_server.py`, `mcp_policy.py`, `run_status.py` | Read-only MCP surface for Claude Code / Codex / Cursor. Policy enforced twice (boundary + authoritative subprocess) because hosts are non-interactive and can't answer `[y/N]`. Each run is an isolated subprocess; `run_status.json` has a durable single-writer + owner-scoped reconciliation protocol. |

### Recipes

- **New step** → add a handler in `engine/steps/*.py`, decorate
  `@step(name, kind, risk, desc)`, publish consumed keys via `state_updates`,
  add a guardrail test. No central registration.
- **New task kind** → `task_spec.py` (kind + tier) → playbook yaml → intent hint
  → chat enum. Planner and executor are untouched.
- **New repo knowledge** → a typed profile op or a skill under
  `adapters/<repo>/`. All three injection channels have hard caps that silently
  drop overflow (`review.md` 4,000 chars; each SKILL.md body 1,500; briefing 350
  words) — measure before adding.
- **Onboarding a second repo** → `repo_profile` task + the repo-neutral
  `repo-profile` playbook. Acceptance requires **zero** commits to `src/`.

## Working rules

- **`knowledge/` edits follow `AGENTS.md`, not intuition.** It is a vendored
  tree with its own routing, owner-scoping, and forbidden destinations. Read
  `doc/PLAN-knowledge-reorg.md` + `knowledge/CONTRIBUTING.md` + the one matching
  contribution topic first, then run both validators after the complete batch.
- **The locked `repo-rebase` playbook must stay byte-identical in behavior.**
  It delegates to the external 5-phase orchestrator (`REBASE_ORCHESTRATOR_CMD`)
  and is only *monitored*, never forked. `repo-rebase-native` is the candidate
  replacement with an explicit promotion path in
  `doc/IMPLEMENTATION_STATUS.md` — it stays invisible to the planner until a
  human flips it.
- **Do not ship unmeasured "improvements" to review/agent behavior.** Judge
  noise is ±0.1 RQS3 per roll; scoring is on replicate means
  (`eval/run_replicates.sh` + `score_replicates.py`). Several plausible
  optimizations measured *worse* and were reverted — the list is in
  `doc/IMPLEMENTATION_STATUS.md`. Before changing delivery or review behavior,
  read `eval/dataset/judgments/T3_FORENSICS.md`: ~90% of judge penalties came
  from mechanical delivery problems, not weak analysis.
- **`.env` is git-ignored and holds keys.** Never commit it; `repo_read` in chat
  refuses `.env*` by design. Adapter manifests use `${VAR}` expansion rather
  than machine paths.

## Key env vars

`ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` (Anthropic-SDK-compatible; DeepSeek's
`/anthropic` works) · `REPO_PATHS`, `REPO_FULL_NAMES` · `ECO_MODEL` /
`PERFORMANCE_MODEL` (+ optional per-tier `*_BASE_URL`/`*_API_KEY`, atomic:
fully-unset, model-only, or all three) · `MODEL_MISMATCH_POLICY` (default
`fail`) · `ALLOW_PUSH` / `ALLOW_POST` (both default 0 = dry-run) ·
`PROFILE_BRIEFING_ENABLED=0` (the {no-profile} eval ablation arm) ·
`REVIEW_ENSEMBLE=0`, `ENSEMBLE_PARALLEL` · `ADAPTERS_DIR`.

## Status

v1 tasks 0–15 complete; Design v2 P0–P2 complete, P3 machinery offline-complete.
P3's remaining work is deliberately unrun (the cross-repo eval campaign needs a
second benchmark repo and API budget). `doc/IMPLEMENTATION_STATUS.md` is the
authority on what is actually built versus designed.
