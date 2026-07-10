# config.py — spec

`LOC ~116 · configuration · refactor-status: ok`

## Responsibility
`Settings` (pydantic-settings) loaded from env / `.env`.

## Functionality
Typed fields + safe defaults for LLM, repos, engine, push safety, PR debug,
external rebase, agent runtime, ensemble, profiles, patch triggers, metrics,
escalation. Derivation helpers.

## Public contract
`Settings` with all tunables; `reviewer`, `intent` (fallback to `agent_model`);
`repo_path(name)`.

## Invariants
- Secrets only via env/`.env` (git-ignored, never committed).
- Repo-specific defaults (`default_repo`, `rebase_agent_root`,
  `high_risk_modules`, `cost_ref_*` keys) are **fallbacks only**; plugin/profile
  overrides them (**A5**). These are the sole allowed repo literals here
  (leak-capped at 3).

## Scope — not here
No logic beyond derivation helpers; no I/O beyond env loading.

## Dependencies (allowed)
`pydantic-settings` only.

## Extension points
New tunable → a typed field with a safe default and a one-line comment stating
meaning/units.

## Tests
Exercised indirectly across the suite (fixture builds `Settings(_env_file=None,
...)`).

## Refactor notes
Growing broad but single-concern — acceptable. If it keeps growing, group into
nested settings models (LLMSettings/PushSettings/ProfileSettings) rather than
splitting the file. Do NOT move repo-specific defaults out to plugins yet
(they're fallbacks); the refactor goal is that a profiled repo never reads them.
