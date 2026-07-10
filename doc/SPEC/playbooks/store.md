# playbooks/store.py — spec

`LOC ~166 · planning (registry) · refactor-status: ok`

## Responsibility
The versioned playbook registry: load/parse/validate YAML, recall by
kind+repo+capabilities, persist candidates.

## Public contract
`Playbook`, `PlaybookStep`, `parse_playbook`, `playbook_to_doc`;
`PlaybookStore(dir, registry)` with `find(kind, repo, capabilities?)`,
`missing_capabilities(kind, capabilities)`, `get`, `all`, `save_candidate`,
`validate`.

## Invariants
- Statuses `candidate | active | locked | retired`; only active/locked recalled
  by `find`; candidates run only via explicit `--playbook`.
- `find`: exact-repo wins; repo-neutral match only when `requires ⊆
  capabilities` (when known); locked > active; higher version > lower.
- `validate` refuses a playbook referencing an unregistered step (fail at load).
- `save_candidate` forces `status=candidate` (**D1** — no self-promotion).

## Scope — not here
No execution, no planning policy (planner's), no step logic.

## Dependencies (allowed)
`engine/registry`, `pyyaml`.

## Extension points
New playbook field → extend `Playbook` + `parse_playbook` + `playbook_to_doc`
together.

## Tests
`test_planner_playbooks.py`, `test_capabilities.py`, `test_review_step.py`.

## Refactor notes
Clean. `Playbook`/`PlaybookStep` are data; `PlaybookStore` is mechanics — keep
them separable. If DAG playbooks arrive, `PlaybookStep` gains edges but the
`find`/`validate` contract stays.
