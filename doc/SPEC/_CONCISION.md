# Concision plan — making the codebase smaller without losing a guarantee

This is the cross-cutting plan the refactor follows to make the codebase
**concise**: remove duplication, delete dead code, and collapse repeated
boilerplate into shared helpers. Every item names the exact sites (grep-backed),
the estimated line saving, the abstraction to introduce, and the invariant that
must survive. Per-file specs carry a matching **Concision** subsection.

## Status — K1–K7 applied on `main` (2026-07-10)

All seven items are **done** (211 tests green throughout; each shipped as its
own commit). Outcome: −2 net files (3 shims + 4 dead dataclasses removed, 1
shared `profiles/languages.py` added), and every duplication below collapsed to
a single source of truth. Raw line count is roughly flat because K2 trades
three divergent copies for one shared module (DRY, not fewer lines); the real
win is maintainability — a new step now reuses `_common` guards, and language
rules live in one place. Keep this doc as the record of *why* those helpers
exist so they are not re-inlined.

## Two axes — do not confuse them

- **Concision** (this doc): fewer lines, less duplication, less dead code.
  Preferred for this refactor.
- **Cohesion split** (per-file "Refactor notes"): break an oversized file into
  focused files — improves readability but adds files and does NOT reduce total
  lines.

Where they conflict, **prefer concision**. Example: `agent_runtime.py` (685 LOC)
had a cohesion-split note, but the concision win there was smaller (dedupe the
repair-round and evidence-cap code), not the split — so the dedup came first.
The cohesion split followed once the file was still hard to navigate.

## Cohesion splits applied (2026-07-10, after K1–K7)

Two oversized files were split into packages once the concision passes above
left them still dense (219 tests green throughout; public import surfaces
preserved via re-exporting `__init__`s, so no importer changed):
- `engine/agent_runtime.py` (685 LOC) → `engine/agent_runtime/` —
  `dispatch`/`knowledge`/`utils` (substrate) + `runner`/`ensemble` (entries).
- `engine/steps/review.py` (341 LOC) → `engine/steps/review/` —
  `prompts` (eval-tuned text) + `utils` (deterministic helpers) + `steps`
  (handlers).
- `engine/steps/pr.py` (484 LOC) → `engine/steps/pr/` — split by concern:
  `fetch` (read-only) + `rebase` + `debug` + `publish` (both risk=push steps)
  + `utils` (`extract_signature`).
- `cli.py` (406 LOC) → `cli/` — `copilot` (the orchestrator class, kept whole)
  + `entry` (argparse/REPL) + `utils` (pure formatters); `__init__`/`__main__`
  preserve the `omni_copilot.cli:main` entry point and `python -m` parity.
In every case the stateless/pure helpers moved to a `utils.py` so the class/
handler files carry control flow, not plumbing. Eval-citation comments moved
with their code, and public import surfaces were preserved via re-exporting
`__init__`s (one test's white-box monkeypatch target was updated to the new
submodule — `pr.debug._gh` — the only test change across all four splits).

## Rules the concision refactor must not break

- Every invariant tagged in a per-file spec survives verbatim; every guard test
  still passes (a helper may change *how* a guarantee is met, never *whether*).
- New helpers live where the dependency rules allow (`engine/steps/_common.py`
  for step helpers; a leaf data module for shared data). A helper must not
  create a forbidden cross-import (`_ARCHITECTURE.md` §4).
- A helper that would be used **once** is not worth it — only extract at ≥2
  real call sites (the numbers below all qualify).

## Prioritized catalog (highest value first)

### K1 — Delete dead target dataclasses  ·  ~35 LOC  ·  risk: none
`ModuleTask`, `ModuleSchedule`, `ValidationPlan`, `RebaseRunSpec` in
`targets/base.py` (now `push.py`) were used nowhere but their re-exports
(verified: 0 other importers). Delete the four dataclasses + their re-exports.
**Keep** `PushPolicy`/`PushDecision`/`guard_push` (the live push guard).
*Invariant to preserve:* C4 (push guard) untouched.

### K2 — Centralize per-language rules  ·  ~30–40 LOC + prevents drift  ·  risk: low
The "what is a source file / a symbol / a branch, per language" data is
triplicated: `review._sweep_targets` (`line_rules`), `establish`
(`LANGUAGE_SUFFIXES` + `scan_modules`), `repo_map` (`_SYMBOL_RES` + `_SUFFIXES`).
Introduce one leaf data module `profiles/languages.py` (pure data + tiny
accessors: suffixes, symbol regex, branch/index regex per language). The three
consumers import it. *Invariant to preserve:* unknown language degrades honestly
in each consumer (file-level sweep / empty module scan / "use grep").

### K3 — Step-handler guard helpers  ·  ~40–60 LOC  ·  risk: low
Add to `engine/steps/_common.py` and replace the repeated blocks:
- `require_repo(ctx) -> Path | StepResult` — the **8** `repo is None → BLOCKED`
  guards across step files become one line each.
- `adapter_or_result(ctx) -> RepoAdapter | StepResult` (or a `@needs_adapter`
  decorator) — the **7** `_adapter_from_state` + `isinstance(..., StepResult)`
  guards in `profile.py`.
- `no_llm_gap(ctx, step, effect) -> StepResult` — the **4** identical
  "no LLM → record `capability_gap` → return ok/skip" blocks.
- `store_for(adapter) -> ProfileStore` — the **6** `ProfileStore(adapter.profile_dir)`
  constructions in `profile.py`.
*Invariant to preserve:* typed BLOCKED returns (B1), the `capability_gap` trace
event (E2), and each step's public name/behavior.

### K4 — `state_updates` ergonomics  ·  readability + ~10 LOC  ·  risk: low
**21** call sites write `outputs={"state_updates": {...}, ...}` by hand. Add a
small constructor helper — `published(summary, *, state=None, **outputs)` or a
`StepResult.publishing(...)` classmethod — so a handoff is one clear call.
*Invariant to preserve:* **B2** — every state key a later step consumes is still
published; the helper makes it easier to comply, not optional.

### K5 — Retire the three engine shims  ·  ~26 LOC + 3 files  ·  risk: low
`engine/{builtin_steps,pr_steps,rebase_native_steps}.py` are re-export shims.
Migrate their importers (each shim's spec lists them), then delete the files and
their specs. *Invariant to preserve:* the `rebase_native_steps._RUNTIME`
"same object" guarantee until its fixtures are migrated.

### K6 — Deduplicate cli gate+confirm  ·  ~15 LOC  ·  risk: low
`Copilot.run_task` and `run_playbook` repeat the plan-review + `[y/N]` confirm
sequence. Extract `_gate_and_confirm(resolution, spec, assume_yes) -> bool`.
*Invariant to preserve:* plan-review before confirm; confirm fires for
`confirm_required or requires_review`.

### K7 — Fetch-step "from state" early return  ·  ~10 LOC  ·  risk: none
**5** fetch steps open with `if "X" in ctx.state: return ...(state_updates)`.
A `from_state(ctx, key) -> StepResult | None` helper collapses them.
*Invariant to preserve:* the injected/offline test path stays intact.

## Estimated total
~160–200 LOC removed and ~4 files deleted, with several repeated patterns
reduced to single call sites — before any cohesion split. The step files shrink
most (K3+K4+K7), which is where new steps are added, so the marginal cost of a
new step drops too.

## Suggested sequence (each independently shippable, tests green between)
1. K1, K5 (pure deletions — smallest diff, immediate shrink).
2. K3, K4, K7 (`_common.py` helpers — the step-file boilerplate collapse).
3. K2 (`profiles/languages.py` — the cross-file dedup).
4. K6 (cli helper).
5. Only then reconsider cohesion splits (per-file Refactor notes), now against a
   smaller, deduped baseline.
