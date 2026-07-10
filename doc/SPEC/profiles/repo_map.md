# profiles/repo_map.py — spec

`LOC ~138 · profiles (on-demand structure) · refactor-status: ok`

## Responsibility
An on-demand, goal-ranked, budgeted symbol map (design §V2.0.2: structure is
pulled, never pushed).

## Public contract
`RepoMap(repo, language, cache_dir?)` with `supported`, `index()`,
`render(query, budget_chars)`; `build_index`.

## Invariants
- Regex symbol index per language; disk-cached keyed by HEAD (one HEAD, one
  cache; rebuilds on drift).
- `render` is query-ranked + budget-capped; zero-score tail dropped.
- Unsupported language → honest "use grep" string (agent-runtime records a
  `capability_gap`).

## Scope — not here
Never injected into prompts — surfaced only as the `repo_map` tool
(wired in `agent_runtime._repo_map_tool`).

## Dependencies (allowed)
stdlib `re`/`json`/`subprocess`.

## Tests
`test_ci_and_repo_map.py`.

## Refactor notes
Regex-based (no tree-sitter dependency) — a deliberate simplicity/portability
trade. If precision becomes a problem, a tree-sitter backend can slot behind the
same `RepoMap.render` contract. Keep the "pulled on demand" stance — do not add
a code path that injects the map into a prompt.

## Concision — **K2** (shared language rules)
`_SYMBOL_RES` + `_SUFFIXES` are the third copy of the per-language rule set
(also `review._sweep_targets`, `profiles/establish`). Consume the shared
`profiles/languages.py` (K2). Preserve: `supported` false + honest "use grep"
for an unknown language.
