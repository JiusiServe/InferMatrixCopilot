# vllm-omni-copilot — Specification

A **normative** specification of the copilot, written level by level to mirror
the code tree. Where `CODE_TOUR.md` is a *reading guide* (how to walk the code)
and `DESIGN.md` is the *rationale* (why it is shaped this way), this SPEC is the
*contract*: what each layer and each module MUST do, MUST NOT do, and the
invariants a change may not break. Use it in review to decide whether a change
belongs where it was put and whether it keeps the code clean.

## How the SPEC is organized

Cross-cutting first, then one file per architectural level (each level maps to
directories/files under `src/omni_copilot/`):

| File | Covers | Code |
|---|---|---|
| [00-architecture.md](00-architecture.md) | Layers, dependency rules, functionality, scope, data & artifacts, safety model | whole tree |
| [01-constraints.md](01-constraints.md) | Global programming constraints + the invariant catalog | whole tree |
| [02-task-and-cli.md](02-task-and-cli.md) | Task layer & interfaces | `task_spec.py` `intent.py` `cli.py` `chat.py` `ui.py` `config.py` |
| [03-planning.md](03-planning.md) | Planning & playbook registry | `engine/planner.py` `playbooks/` |
| [04-engine.md](04-engine.md) | Engine substrate & governed agent runtime | `engine/{step,registry,executor,agent_runtime}.py` `agent_loop.py` `tools.py` `scopes.py` `llm.py` |
| [05-steps.md](05-steps.md) | The vetted step library | `engine/steps/*` |
| [06-profiles.md](06-profiles.md) | Repo-profile knowledge subsystem | `profiles/*` |
| [07-edge.md](07-edge.md) | Repo edge: plugins, targets, CI, rebase monitor | `plugins/` `targets/` `ci/` `rebase/monitor.py` |
| [08-crosscut.md](08-crosscut.md) | Review, memory, observability, escalation, metrics | `review/` `memory/` `run_trace.py` `notify.py` `metrics.py` |

## Per-module spec template

Every module entry in files 02–08 is specified against a fixed set of lenses.
A reviewer checks a change against exactly these:

- **Responsibility** — the one thing this module owns. (If a change adds a
  second unrelated responsibility, it belongs elsewhere.)
- **Public contract** — the symbols other code may use and the guarantees they
  make. Changing a guarantee is a breaking change.
- **Invariants** — properties that must hold on every path. These are the
  "must not break" list.
- **Scope** — what explicitly does NOT belong in this module.
- **Depends on** — the only imports allowed (enforces the dependency rules in
  §00). Anything outside this list is a layering violation.
- **Extension points** — the sanctioned way to add capability here.
- **Tests** — the guard tests that pin the invariants.

## Status & authority

- This SPEC describes the code at `main` after the v2 work and the
  `engine/steps/` refactor (211 offline tests). When code and SPEC disagree,
  that is a bug in one of them — reconcile, do not ignore.
- `IMPLEMENTATION_STATUS.md` tracks *what is built vs planned*; this SPEC
  specifies *what built code must guarantee*. Planned-but-unbuilt items are
  marked `[planned]` here.
