# 06 — Repo-Profile Knowledge Subsystem (`profiles/`)

The curated knowledge layer over the immutable RunTrace/evidence layer. Design
§V2.3; architecture borrowed from the personal-agent profile store. Governs how
repo-specific knowledge is established, stored, consumed, and maintained.

## Subsystem invariants (apply to all files here)

- **Provenance + stability (D3)** — every fact carries `source`/`evidence`/
  `first_seen`/`last_confirmed`/`confirmations`. Evidence-free facts are
  rejected. Stable (≥3) facts never lose cited evidence on rewrite; superseded
  text → `history`; nothing is deleted (dormancy, not deletion).
- **Two write tiers (D4)** — per-run ops additive (`RUN_OPS`); consolidation-tier
  only may rewrite/merge/mark-stale (`CONSOLIDATE_OPS`).
- **Channel-typed content (D5)** — `machine` (code-consumed), `briefing`
  (word-budgeted prompt slice), `retrieved` (on-demand). Overviews are never
  injected wholesale.
- **Agents propose, humans dispose (D2)** — establishment/consolidation agents
  emit typed-op candidates through the store's gates; the judge is read-only.

---

## `profiles/store.py`

- **Responsibility** — the curated fact store: typed patch ops as the only write
  surface, provenance/stability gates, channel-typed rendering.
- **Public contract** — `ProfileStore(root)`; `apply_ops(ops, tier, actor)
  -> per-op reject reasons`; `active(channel?, module?)`; `render_briefing(budget)`;
  `render_report()`. `Fact`; `RUN_OPS`/`CONSOLIDATE_OPS`; constants `CHANNELS`,
  `KINDS` (command/constraint/convention/trap/note), `SOURCES`
  (deterministic/agent/human), `STABLE_CONFIRMATIONS`, `BRIEFING_WORD_BUDGET`.
- **Invariants**
  - Ops are the ONLY mutation path; malformed/forbidden ops are rejected
    individually (never raise); wrong-tier ops rejected.
  - `add_fact` requires non-empty text + evidence; a duplicate id is a
    confirmation, not a new fact. `rewrite_fact` never leaves a fact
    evidence-free and, if stable, may not drop cited evidence. `merge_facts`
    leaves a pointer stub (`status=merged`), never deletes. `mark_stale` excludes
    from all channels but keeps for audit.
  - `render_briefing` emits only active `briefing`-channel facts, most-confirmed
    first, under the hard word budget.
  - Every accepted op is appended to `ops_log.jsonl`; `save()` re-renders
    `PROFILE_REPORT.md`.
- **Scope** — storage + gates + rendering. No LLM, no repo scanning, no step
  logic.
- **Tests** — `test_profile_store.py`.

## `profiles/establish.py`

- **Responsibility** — Stage 0–1.5 helpers for establishment.
- **Public contract** — `fact_id`, `build_doc_corpus`, `is_redundant`,
  `extract_directives`, `scan_modules`, `HUMAN_DOC_NAMES`, `LANGUAGE_SUFFIXES`.
- **Invariants** — the **redundancy filter** (`is_redundant`, 6-word shingle vs
  README+docs) drops any briefing line the repo's own docs already state (the
  ETH-study rule). `scan_modules` is deterministic, language-keyed, skips
  non-code dirs. `extract_directives` bounds line length (short imperative only).
- **Scope** — pure deterministic helpers. No LLM, no store writes.
- **Tests** — `test_profile_steps.py` (`test_redundancy_filter_shingles`,
  `test_scan_modules_skips_non_code_dirs`, …).

## `profiles/repo_map.py`

- **Responsibility** — an on-demand, goal-ranked, budgeted symbol map (design
  §V2.0.2: structure is pulled, never pushed).
- **Public contract** — `RepoMap(repo, language, cache_dir?)` with `supported`,
  `index()`, `render(query, budget_chars)`; `build_index`.
- **Invariants** — regex symbol index per language; disk-cached keyed by HEAD
  commit (rebuilds on drift; one HEAD, one cache); render is query-ranked and
  budget-capped; zero-score tail dropped; unsupported language → an honest "use
  grep" string (the agent-runtime records a `capability_gap`).
- **Scope** — structure indexing/rendering. Never injected into prompts; only
  surfaced as the `repo_map` tool.
- **Tests** — `test_ci_and_repo_map.py`.

## `profiles/consolidate.py`

- **Responsibility** — deterministic Stage-4 helpers: staleness decay + drift
  detection.
- **Public contract** — `decay_stale(store, days) -> stale ids`;
  `detect_drift(plugin, store) -> findings`.
- **Invariants** — `decay_stale` flips over-window active facts to `stale`
  (excluded, not deleted). `detect_drift` is **report-only** — declared module
  paths that vanished, facts joined to unknown modules; it never mutates.
- **Scope** — deterministic detection only; no LLM, no auto-fix.
- **Tests** — `test_p3_machinery.py`.

## The establishment/maintenance pipeline (`engine/steps/profile.py`)

- **Stages** — 0: `profile.fingerprint` (+ `structure_scan`), 1.5:
  `profile.ingest_docs` (redundancy-filtered human directives), 1:
  `agent.profile_repo` (non-obvious, evidence-cited facts; overviews forbidden;
  redundancy-filtered; typed-op applied), 4: `detect_drift` → `decay_stale` →
  `agent.profile_consolidate` (the ONLY rewrite/merge tier; LLM proposes, store
  gates decide) → `profile.judge` (read-only → `JUDGE_REPORT.md`).
- **Invariants** — fingerprint drafts a plugin at `status: draft` for unknown
  repos (human gate); `structure_scan` never overwrites declared modules;
  `agent.profile_repo` facts without evidence are rejected by the store;
  consolidation's LLM output passes the same stability gates (a stable-fact
  evidence-drop is rejected even when the model proposes it); the judge never
  calls `apply_ops`. No-LLM paths record a `capability_gap` and run only the
  deterministic stages.
- **Change control** — profile edits are knowledge edits (patch-review trigger);
  promotion draft→candidate→active is human; consolidation is one reviewed,
  revertable commit under `plugins/<repo>/`.
- **Tests** — `test_profile_steps.py`, `test_p3_machinery.py`.
