# memory/skills.py — spec

`LOC ~120 · memory (procedural knowledge) · refactor-status: ok`

## Responsibility
Procedural knowledge, gated harder than debug memory.

## Public contract
`SkillStore(dir)` with `find`, `propose`, `promote`, `candidates`,
`load_all`, `render_for_prompt`; `Skill` (with a `trigger` for recall).

## Invariants (**D1**)
- Agents may only `propose` (writes the candidates file); `promote` to an active
  `SKILL.md` is a curator/human act.
- `find` ranks by module hit + text hit + run_count; only `status: active`
  skills load.

## Scope — not here
No per-repo namespacing (applied by `_ScopedKnowledge`); no LLM; not the curator
UI.

## Dependencies (allowed)
`pyyaml`; stdlib.

## Tests
`test_memory.py`.

## Refactor notes
Clean propose→promote gate — do not add an agent-callable `promote`. The
`trigger` field is the Devin-style recall cue; keep it first-class as more
trigger-gated retrieval lands. Per-repo dir is caller-chosen
(`adapter.skills_dir`) — keep path-agnostic.
