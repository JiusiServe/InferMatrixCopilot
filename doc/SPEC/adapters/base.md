# adapters/base.py — spec

`LOC ~221 · edge (repo knowledge) · refactor-status: ok`

## Responsibility
`RepoAdapter` (repo knowledge at the edge), the adapter registry, and
deterministic Phase-0 bootstrap. `RepoAdapter` is the **container** for a repo's
two trust tiers (DESIGN §V2.3.0): its `.manifest` is **Tier 1** (`manifest.yaml`,
human-gated config) and `.profile_dir`/`.skills_dir`/`.debug_memory_db` are
**Tier 2** (agent-established, evidence-gated knowledge). Renamed from "plugin"
2026-07-11 (`RepoPlugin`→`RepoAdapter`, `plugin.yaml`→`manifest.yaml`) —
"plugin" wrongly implied executable extension code (see DESIGN naming note).

## Public contract
`RepoAdapter` (props `status`, `repo_path`, `protected_branches`, `modules`,
`high_risk_modules`, `capabilities`, `skills_dir`, `debug_memory_db`,
`profile_dir`, `briefing()`; `module_for_path`); `load_adapter`,
`update_manifest`, `AdapterRegistry(resolve/all)`; `fingerprint_repo`,
`draft_adapter`.

## Invariants
- **D2**: `update_manifest` rejects agent writes to `push`/`repo`/`upstream`.
- `capabilities` derives from the manifest (repo.path/language.*/ci.provider/
  upstream.*/modules) + explicit `capabilities:` — matched by playbook
  `requires:`.
- `high_risk_modules` = modules with `risk: high` (feeds patch-review, **A5**).
- `fingerprint_repo` deterministic, never mutates the target repo;
  `draft_adapter` stops at `status: draft` (human gate).
- `briefing()` renders the profile's briefing slice (empty when no profile).

## Scope — not here
No task logic, no LLM, no profile-store internals (delegates to
`profiles/store`).

## Dependencies (allowed)
`profiles/store` (inside `briefing()`), `pyyaml`; stdlib.

## Tests
`test_adapters.py`, `test_capabilities.py`.

## Refactor notes
Two concerns coexist cleanly: `RepoAdapter` (accessor) + registry + bootstrap.
If bootstrap grows (richer fingerprint), consider `adapters/bootstrap.py`. Keep
`capabilities` derivation as the single source the planner trusts — do not
duplicate capability logic in `cli.resolve` (it currently only ADDS repo.path
for REPO_PATHS, which is acceptable).
