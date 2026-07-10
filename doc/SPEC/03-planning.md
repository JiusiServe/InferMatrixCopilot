# 03 — Planning & Playbook Registry

Modules: `engine/planner.py`, `playbooks/store.py`, `playbooks/*.yaml`.

---

## `engine/planner.py`

- **Responsibility** — resolve a `TaskSpec` (+ repo capabilities) to a runnable
  `Playbook` via **reuse > adapt > generate**, with capability-gap handling.
- **Public contract** — `Planner(store, registry)`; `resolve(spec,
  capabilities?) -> Resolution(mode, playbook, tier, requires_review, notes)`;
  raises `PlanningError`. `_GENERATE_TEMPLATES` — the fixed read-only step
  sequences for the three read-only kinds.
- **Invariants**
  - **Reuse** returns the recalled playbook verbatim (`requires_review=False`)
    when params fall within the declared surface.
  - **Adapt** (extra params on a non-locked playbook) sets `requires_review=True`,
    tier L1; a **locked** playbook refuses adaptation (raises).
  - **Generate** (**C2**) is reachable only for `READ_ONLY_KINDS`, uses a fixed
    template, and re-checks every composed step is `risk ∈ {read, report}` —
    raising otherwise. Write-capable kinds with no playbook raise.
  - **Capability gap** (§00.8): with `capabilities` known and no match, a
    write-capable kind raises "capability gap … run repo_profile"; a read-only
    kind falls through to generate. `capabilities=None` keeps v1 behavior.
  - `tier` on the Resolution comes from `spec.tier` (reuse/adapt) — the planner
    never invents a tier.
- **Scope** — selection + parameterization only. No step execution, no repo
  knowledge, no LLM calls. MUST NOT compose raw tools (**A3**).
- **Depends on** — `playbooks/store.py`, `task_spec.py`, `engine/registry.py`.
- **Extension points** — a new read-only kind that needs generation → a
  `_GENERATE_TEMPLATES` entry of read/report steps. Anything write-capable must
  ship a vetted playbook instead.
- **Tests** — `test_planner_playbooks.py`, `test_capabilities.py`.

## `playbooks/store.py`

- **Responsibility** — the versioned playbook registry: load/parse/validate YAML,
  recall by kind+repo+capabilities, persist candidates.
- **Public contract** — `Playbook`, `PlaybookStep`, `parse_playbook`,
  `playbook_to_doc`; `PlaybookStore(dir, registry)` with `find(kind, repo,
  capabilities?)`, `missing_capabilities(kind, capabilities)`, `get`, `all`,
  `save_candidate`.
- **Invariants**
  - Statuses: `candidate | active | locked | retired`; only `active`/`locked`
    are recalled by `find`. Candidates run only via explicit `--playbook`.
  - `find`: exact-repo playbooks win; repo-neutral (`repos: []`) match only when
    `requires ⊆ capabilities` (when capabilities are known); locked outranks
    active, higher version outranks lower.
  - `validate` refuses a playbook that references an unregistered step (fail at
    load, not at run).
  - `save_candidate` forces `status=candidate` — generated/adapted plans can
    never self-promote (**D1**).
- **Scope** — registry mechanics only. No execution, no planning policy (that is
  the planner's), no step logic.
- **Depends on** — `engine/registry.py`, `pyyaml`.
- **Extension points** — a new playbook is a YAML file (see below); a new
  playbook field → extend `Playbook`, `parse_playbook`, `playbook_to_doc`
  together.
- **Tests** — `test_planner_playbooks.py`, `test_review_step.py` (shape),
  `test_capabilities.py`.

## `playbooks/*.yaml` (the registered playbooks)

- **Responsibility** — declarative, ordered step lists (with `foreach`, `when:`,
  per-step `params`) that realize a task kind.
- **Contract per file** — `name, version, status, task_kinds, repos, requires?,
  params, provenance, success, steps[]`.
- **Invariants**
  - `repo-rebase` is **locked** (L0) and `requires: [orchestrator.external]`;
    behavior is byte-identical zero-regression — do not edit its step list.
  - `pr-rebase`/`pr-debug`/`pr-review`/`issue-answer`/`issue-triage` are
    repo-neutral (`repos: []`, `requires: [repo.path]`), active.
  - `repo-profile` is active + repo-neutral (onboards a second repo).
  - `repo-rebase-native` and `profile-consolidate` are **candidates** — invisible
    to the planner, run only via `--playbook`.
  - Every step id is unique; every `step` name is registered; write/push steps
    appear only in vetted (non-generated) playbooks.
- **Scope** — orchestration only (which steps, order, conditions, params). No
  code; no repo knowledge beyond `repos`/`requires` matching.
- **Extension/change control** — promoting candidate→active→locked is a human
  act with provenance; locking is for code-modifying/pushing playbooks.
