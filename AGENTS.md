# Repository instructions

## Knowledge edits

`knowledge/` is a vendored adaptation of
`zuiho-kai/claude-workflow-starter`. Before adding, moving, or deleting any
knowledge page:

1. Read `doc/PLAN-knowledge-reorg.md`, `knowledge/CONTRIBUTING.md`, then exactly
   the one linked contribution topic that matches the change. The plan's
   owner-scoped inventory and detail-retention rules remain authoritative for
   this vendored tree.
2. Route each conclusion by both purpose and code owner. A must-do invariant
   belongs in the nearest owner's `rules.md`; a procedure belongs in a guide;
   stable boundaries belong in architecture; complex evidence belongs in the
   existing raw layer. Never collapse heterogeneous model, component,
   benchmark, and review knowledge into one catch-all page.
3. Treat `knowledge/SCHEMA.md` as an additive metadata overlay only. Preserve
   the planned `incidents/`, `history/`, and `results/` evidence roles. Generated
   evaluation cases, hidden labels, predictions, judgments, and run reports
   belong under `eval/`, not in the product knowledge tree.
4. Never add raw evidence pages to an adapter's always-on briefing. Update the
   nearest `_index.md` for every current synthesized page.
5. Run both validators after the complete owner-scoped batch:

   ```powershell
   python knowledge/tools/check_knowledge_tree.py
   python knowledge/tools/check_wiki_lint.py
   ```
