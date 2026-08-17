# config.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~418 · configuration · refactor-status: oversized`

## Responsibility
`Settings` (pydantic-settings) loaded from env / `.env`, plus the derivation
helpers that turn a run's tier and backend selection into a concrete target.

## Functionality
Typed fields + safe defaults for LLM endpoints and per-tier models, repos,
engine budgets, push safety, PR debug, external rebase, agent runtime,
ensemble, MoA, review depth and per-pass routing, Strict backend selection,
profiles, patch triggers, metrics and escalation.

## Public contract
`Settings` with all tunables; `reviewer` / `intent` (falling back to
`agent_model`); `repo_path(name)`; `model_for(mode)`; `tier_target(role)` →
`ResolvedTarget`; the `strict_backend` validator.

## Invariants (**A5**, **C2**, **B1**)
- Secrets only via env / `.env` (git-ignored, never committed).
- Repo-specific defaults (`default_repo`, `rebase_agent_root`,
  `high_risk_modules`, `cost_ref_*`) are **fallbacks only**; adapter/profile
  overrides them. These are the sole allowed repo literals here, leak-capped
  at 3 and pinned by `test_v2_p0.py::test_repo_neutral_core`.
- **`STRICT_BACKEND` is validated upfront**, listing the legal set on failure.
  An unknown backend must never reach `providers.resolve_provider` — two
  layers, because a `.env` typo must not start a doomed run.
- **`tier_target` returns an EMPTY key for harness providers.** Harness auth
  lives in the vendor CLI's own state and this codebase never sees it. The one
  exception is `deepseek`, which is API-keyed and resolves its credential
  inside its own transport — see `providers/deepseek.md`.
- **Fail-closed served-model guard**: a served model that does not match the
  requested one is an error, not a silent substitution.
- **A reasoning model needs token headroom.** The gray-zone review planner
  silently failed on every gray item for two campaigns because thinking
  consumed a 400-token ceiling before any JSON appeared — caps on
  reasoning-model calls are correctness settings, not cost knobs.

## Scope — not here
No logic beyond derivation helpers; no I/O beyond env loading; no provider
transports (`providers/`); no model calls.

## Dependencies (allowed)
`pydantic-settings` only.

## Extension points
New tunable → a typed field with a safe default and a one-line comment stating
meaning and units. New backend → a registry entry plus this file's validator
set, never a new branch here.

## Tests
`test_llm_providers.py`, `test_tier_split.py`, `test_providers.py`; exercised
indirectly across the suite (the fixture builds `Settings(_env_file=None, ...)`).

## Refactor notes
Grew from ~116 to ~418 LOC across the v3 backend work and is now genuinely
oversized, but still single-concern. If it grows again, group into nested
settings models (`LLMSettings` / `PushSettings` / `ReviewSettings` /
`BackendSettings`) rather than splitting the file — call sites depend on one
`Settings` object reaching every `StepContext`.
