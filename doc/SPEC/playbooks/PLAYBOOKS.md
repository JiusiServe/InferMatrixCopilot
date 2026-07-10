# playbooks/*.yaml — spec

`9 files · declarative orchestration data · refactor-status: ok`

## Responsibility
Declarative, ordered step lists (with `foreach`, `when:`, per-step `params`)
realizing a task kind.

## Contract per file
`name, version, status, task_kinds, repos, requires?, params, provenance,
success, steps[]`.

## The registered playbooks
- `repo-rebase` — **locked**, L0, `requires: [orchestrator.external]`.
  Byte-identical zero-regression — do NOT edit its step list.
- `pr-rebase`/`pr-debug`/`pr-review`/`issue-answer`/`issue-triage` — active,
  repo-neutral (`repos: []`, `requires: [repo.path]`).
- `repo-profile` — active, repo-neutral (onboards a second repo).
- `repo-rebase-native`, `profile-consolidate` — **candidates** (planner-
  invisible; run only via `--playbook`).

## Invariants
- Every step id unique; every `step` name registered (enforced by
  `store.validate`).
- Write/push steps appear only in vetted (non-generated) playbooks.
- Locking is for code-modifying/pushing playbooks; promotion
  candidate→active→locked is a human act with provenance.

## Scope — not here
No code, no repo knowledge beyond `repos`/`requires` matching.

## Extension points
A new task realized as a YAML file; a new repo reuses the repo-neutral playbooks
(zero core change) once its profile satisfies `requires`.

## Refactor notes
These are the "config" half of the reuse>adapt>generate model — keep them
declarative. Resist adding conditional logic beyond `when:`/`foreach`; anything
richer belongs in a step. When repo #2 onboards, it should need NO new playbook
(that is the invariance test).
