---
name: knowledge-base-contribution
description: How to add/extend the curated `knowledge/` wiki correctly — route by
  verified root cause to the right owner dir, pick the page type (rules vs architecture
  vs guides vs incidents), register in the nearest _index.md, keep always-on briefing
  pages tight, and pass check_knowledge_tree.py
trigger: recording a lesson / 复盘 / sinking a rule / adding or editing a knowledge/ wiki page
modules:
- knowledge_base
- docs
status: active
created_at: 2026-07-20
run_count: 0
---

## When this applies
You're told to "record a lesson / 复盘 / sink a rule", or you're adding or editing
a page under `knowledge/`. Full guide + copy-paste templates: `doc/EXTENDING-KNOWLEDGE.md`.

## Steps
1. **Owner first.** Reusable across repos → `general/<topic>/`; whole repo →
   `repos/<repo>/`; shared code module → `repos/<repo>/components/<module>/`; one
   model → `repos/<repo>/models/<model>/`. Route by the *verified* root cause, not
   where the symptom showed. Machine facts (host/path/token/venv) → git-ignored `local/`.
2. **Page type.** Next-run-changing rule (trigger → do → don't → verify) → nearest
   `rules.md`, one stable ID per constraint. Stable data-flow/boundaries →
   `architecture.md`. Longer method → `guides/`. Complex reproducible history only
   → `incidents/YYYY-MM-DD-short-name.md`. The default product of a retrospective
   is a rule, not an incident.
3. **One canonical copy.** State each fact on exactly one page; every other place
   links to it. Never duplicate a near-identical rule across owners.
4. **Register in the SAME change.** Add a `遇到什么 → 查看哪里` row for the page (or
   a child-dir link) in the nearest `_index.md`. An unregistered page fails the gate.
   Synthesis-layer pages (rule/guide/architecture/index in general/repos) also need
   frontmatter (`title/created/updated/type` + a `tags` value from `knowledge/SCHEMA.md`);
   evidence-layer pages (incidents/history/results) take none.
5. **Keep always-on pages tight.** `rules.md` + `_index.md` load as briefing on
   every task — keep them to triggers/gates/navigation. Push narrative and long
   repros into `guides/` / `incidents/` (pulled on demand via doc_search/doc_read).

## Verification
```
python knowledge/tools/check_knowledge_tree.py     # structure/index/links/incidents
python knowledge/tools/check_wiki_lint.py          # synthesis frontmatter + tag taxonomy
```
Split limits: warn ≥300 non-empty lines or 16 KiB; must split ≥500 lines or 32 KiB.
Group dirs (guides/incidents/history/references/results/rfcs) allow ≤20 pages; other
dirs warn above 7. Incidents need the five `编号/归属/状态/搜索词/影响范围` fields, a
valid state, and a unique 编号. Deliver via PR — the tree is vendored; never edit upstream.

## Anti-patterns
- Adding a page but not linking it from the nearest `_index.md` (gate failure).
- Sinking a story into `incidents/` when a `rules.md` entry was the real deliverable;
  or copying a rule into two owners instead of linking one canonical copy.
- Fattening `rules.md` with narrative — it's always-on briefing budget.
- Real machine addresses/paths/credentials in a tracked page (they go in `local/`).
- Routing by where the symptom appeared instead of the verified root cause.
- A synthesis page with no frontmatter, or a `tags` value not in `SCHEMA.md` — fails `check_wiki_lint.py`.
