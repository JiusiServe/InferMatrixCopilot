# ci/providers.py — spec

`LOC ~118 · edge (CI) · refactor-status: ok`

## Responsibility
Profile-selected CI log adapters for pr-debug.

## Public contract
`provider_for(plugin, settings, gh_runner?) -> (provider|None, gap_reason)`;
`BuildkiteLogs.enrich`, `GithubActionsLogs.enrich`.

## Invariants
- Provider chosen by `profile.ci.provider`, never hardcoded.
- `enrich` is best-effort **per check** — an API error leaves that check
  name-grouped, never crashes.
- Missing provider/token → `(None, reason)`; the calling step records a
  `capability_gap` and degrades to name grouping (**E2**).

## Scope — not here
Log fetching only — no grouping/debugging logic; no signature normalization.

## Dependencies (allowed)
stdlib `urllib`/`json`/`re`; the `gh_runner` callable is injected (no direct
`._common.gh` import, keeping this package engine-independent).

## Extension points
New CI system → a `*Logs` class with `enrich` + a `provider_for` branch.

## Tests
`test_ci_and_repo_map.py`.

## Refactor notes
Clean adapter pattern. Keep the `enrich(failures) -> count` contract stable so
`pr.py` stays agnostic. The `gh_runner` injection is deliberate — do not import
`engine.steps._common` here (that would invert the dependency direction, **§ARCH.4.1**).
