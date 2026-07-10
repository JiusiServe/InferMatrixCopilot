# vllm-omni-copilot — Specification (file-level)

A **normative, file-level** specification. The `doc/SPEC/` tree mirrors
`src/omni_copilot/`: **one spec file per source file**, at the same relative
path (`engine/steps/pr.py` → `doc/SPEC/engine/steps/pr.md`). Each spec covers a
fixed set of lenses. Two cross-cutting docs sit at the root and are referenced
(not repeated) by every per-file spec.

This SPEC is written to drive a **codebase refactor**: for any source file you
touch, its spec tells you what the file must keep guaranteeing, what does not
belong in it, which global constraints bind it, and where it is currently messy.

## Cross-cutting (read first)

- **[_ARCHITECTURE.md](_ARCHITECTURE.md)** — layers, dependency direction rules,
  functionality (the 7 task kinds), scope, data & artifacts, safety model,
  repo-invariance contract. The "big picture" every per-file spec assumes.
- **[_CONSTRAINTS.md](_CONSTRAINTS.md)** — global programming constraints
  (A structural, B contract, C safety, D knowledge, E observability) + the
  invariant catalog. Per-file specs cite these by id (e.g. `A2`, `C4`) instead
  of restating them.
- **[_CONCISION.md](_CONCISION.md)** — the plan for making the codebase smaller:
  a prioritized, grep-backed catalog of dead code, duplication, and boilerplate
  to remove (K1–K7), each with the shared helper to introduce and the invariant
  to preserve. This is what the "make it concise" refactor follows; per-file
  specs carry a matching **Concision** note where an opportunity applies.

## Per-file spec template (the lenses)

Every `*.md` under the mirrored tree uses these headings, in this order:

1. **Header line** — `LOC ~N · role · refactor-status`.
   `refactor-status ∈ {ok, oversized, split-candidate, shim-to-retire,
   trivial}`.
2. **Responsibility** — the single thing the file owns.
3. **Functionality** — what it actually does (behavior), briefly.
4. **Public contract** — exported symbols other code may use + their guarantees.
5. **Invariants** — properties that must hold on every path (the "don't break"
   list), each tagged with the constraint id it realizes.
6. **Scope — not here** — what explicitly does NOT belong in this file.
7. **Dependencies (allowed)** — the imports this file may have (enforces the
   §_ARCHITECTURE dependency rules). Anything else is a layering violation.
8. **Extension points** — the sanctioned way to add capability here.
9. **Tests** — the guard tests that pin the invariants.
10. **Refactor notes** — size/cohesion/coupling smells and concrete suggested
    moves/splits (a *cohesion* lens — improves readability, adds files).
11. **Concision** (only where an opportunity applies) — what in this file is
    dead, duplicated, or boilerplate, and which `_CONCISION.md` item (K1–K7)
    removes it. This is the lens the *make-it-concise* refactor consumes;
    where it conflicts with a cohesion split, concision wins.

## How to use this during refactor

- **Before editing a file**: read its spec. If your change adds a responsibility
  the spec doesn't list, the change belongs in a different file (or a new one) —
  add/adjust the spec first.
- **When splitting a file**: create the new spec files, move the relevant
  lenses, and keep the "Dependencies (allowed)" honest — a split that creates a
  cross-import the rules forbid is not done.
- **When deleting a shim** (`refactor-status: shim-to-retire`): migrate importers
  to the real module first (the spec lists who imports it), then delete both the
  code and its spec.
- **Invariants are the contract**: a refactor may move code freely but must
  preserve every invariant and every guard test named in the spec. If a test
  must change, the invariant changed — call it out.

## File index (mirrors `src/omni_copilot/`)

| Layer | Spec files |
|---|---|
| Interface / task | `task_spec` `intent` `cli` `chat` `ui` `config` |
| Engine substrate | `engine/step` `engine/registry` `engine/executor` `engine/planner` `engine/agent_runtime` `agent_loop` `tools` `scopes` `llm` |
| Step library | `engine/steps/__init__` `engine/steps/_common` `engine/steps/{workspace,rebase_ext,review,report,pr,issue,profile,rebase_native}` |
| Planning data | `playbooks/store` `playbooks/PLAYBOOKS` (the yaml) |
| Edge — languages | `profiles/languages` (per-language rules, shared) |
| Edge | `plugins/base` `targets/base` `ci/normalize` `ci/providers` `rebase/monitor` |
| Profiles | `profiles/store` `profiles/establish` `profiles/repo_map` `profiles/consolidate` |
| Cross-cutting | `review/{diff_summary,triggers,reviewer}` `memory/{debug_memory,skills}` `run_trace` `notify` `metrics` |

Trivial `__init__.py` re-export files are not specified individually
(`engine/steps/__init__` is, because it defines `register_builtin_steps`).
