# engine/steps/issue.py — spec

`LOC ~131 · step library (issues) · refactor-status: ok`

## Responsibility
Issue fetch, drafted-answer & triage agent steps, and gated posting.

## Steps (4)
`issue.fetch` (deterministic/read); `agent.draft_issue_answer`,
`agent.triage_issues` (agent/read, read-only scope); `issue.post_answer`
(script/push).

## Invariants
- Agent steps ground claims in fetched text/code via the governed runtime.
- `issue.post_answer` double-gated (**C5**).
- `_issue_agent_step` is the shared factory; the two `agent.*` handlers are
  registered imperatively (`register_step`).

## Scope — not here
No agent governance internals; no posting authorization beyond `post_step`.

## Dependencies (allowed)
`scopes`, `engine/step`, `._common`, `..agent_runtime`.

## Tests
Covered via issue playbooks + `test_agent_runtime` paths.

## Refactor notes
Well-sized. The `_issue_agent_step` factory + `_render_answer`/`_render_triage`
pattern is clean; if a third issue agent step appears, keep using the factory.

## Concision — **K4/K7**
`issue.fetch` uses the "from state" early-return (K7 `from_state`) and verbose
`state_updates` literals (K4 `published(...)`). Small wins; preserve B2.
