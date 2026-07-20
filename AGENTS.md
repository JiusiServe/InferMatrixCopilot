# Repository instructions

## Knowledge edits

`knowledge/` is a vendored adaptation of
`zuiho-kai/claude-workflow-starter`. Before adding, moving, or deleting any
knowledge page:

1. Read `doc/PLAN-knowledge-reorg.md`, `knowledge/CONTRIBUTING.md`, then exactly
   the one linked contribution topic that matches the change. The plan's
   owner-scoped inventory and detail-retention rules remain authoritative for
   this vendored tree.
2. Route each conclusion by both purpose and code owner. PR-learning and review-
   experience intake may produce only executable rules in the nearest owner's
   `rules.md`; model-specific rules stay with that model owner. Raw PR material
   is temporary input outside the repository and must be deleted after the
   owner-scoped rule batch passes validation. Never add PR case/history/result/
   incident pages or collapse heterogeneous owners into one catch-all page.
3. Treat `knowledge/SCHEMA.md` as an additive metadata overlay only. Existing
   `incidents/`, `history/`, and `results/` files are legacy material, not an
   allowed destination for new PR learning. Generated evaluation cases, hidden
   labels, predictions, judgments, and run reports belong under `eval/`, not in
   the product knowledge tree.
4. Never persist raw evidence pages or replay outputs. Update the nearest
   `_index.md` for every current rules page.
5. Run both validators after the complete owner-scoped batch:

   ```powershell
   python knowledge/tools/check_knowledge_tree.py
   python knowledge/tools/check_wiki_lint.py
   ```
