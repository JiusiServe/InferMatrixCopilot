# plugins/base.py — spec

`LOC ~221 · edge (repo knowledge) · refactor-status: ok`

## Responsibility
`RepoPlugin` (repo knowledge at the edge), the plugin registry, and
deterministic Phase-0 bootstrap. `RepoPlugin` is the **container** for a repo's
two trust tiers (DESIGN §V2.3.0): its `.manifest` is **Tier 1** (`plugin.yaml`,
human-gated config) and `.profile_dir`/`.skills_dir`/`.debug_memory_db` are
**Tier 2** (agent-established, evidence-gated knowledge). Proposed rename:
`RepoPlugin` → `RepoAdapter`, `plugin.yaml` → `manifest.yaml` (see DESIGN naming
note) — "plugin" wrongly implies executable extension code.

## Public contract
`RepoPlugin` (props `status`, `repo_path`, `protected_branches`, `modules`,
`high_risk_modules`, `capabilities`, `skills_dir`, `debug_memory_db`,
`profile_dir`, `briefing()`; `module_for_path`); `load_plugin`,
`update_manifest`, `PluginRegistry(resolve/all)`; `fingerprint_repo`,
`draft_plugin`.

## Invariants
- **D2**: `update_manifest` rejects agent writes to `push`/`repo`/`upstream`.
- `capabilities` derives from the manifest (repo.path/language.*/ci.provider/
  upstream.*/modules) + explicit `capabilities:` — matched by playbook
  `requires:`.
- `high_risk_modules` = modules with `risk: high` (feeds patch-review, **A5**).
- `fingerprint_repo` deterministic, never mutates the target repo;
  `draft_plugin` stops at `status: draft` (human gate).
- `briefing()` renders the profile's briefing slice (empty when no profile).

## Scope — not here
No task logic, no LLM, no profile-store internals (delegates to
`profiles/store`).

## Dependencies (allowed)
`profiles/store` (inside `briefing()`), `pyyaml`; stdlib.

## Tests
`test_plugins.py`, `test_capabilities.py`.

## Refactor notes
Two concerns coexist cleanly: `RepoPlugin` (accessor) + registry + bootstrap.
If bootstrap grows (richer fingerprint), consider `plugins/bootstrap.py`. Keep
`capabilities` derivation as the single source the planner trusts — do not
duplicate capability logic in `cli.resolve` (it currently only ADDS repo.path
for REPO_PATHS, which is acceptable).
