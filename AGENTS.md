# Repository instructions

## Knowledge edits

`knowledge/` is a vendored adaptation of
`zuiho-kai/claude-workflow-starter`. Before adding, moving, or deleting any
knowledge page:

1. Read `knowledge/CONTRIBUTING.md`, then read exactly the one linked
   contribution topic that matches the change.
2. Treat that contribution workflow as the source of truth for ownership,
   directory placement, page shape, indexes, and incident handling.
   `knowledge/SCHEMA.md` is an additive metadata overlay only; it does not
   authorize a second knowledge layout or new page category.
3. Put reusable conclusions in the nearest owner's existing `rules.md` first.
   Add an `incidents/` page only when the upstream incident criteria and format
   are satisfied. Do not create review-answer dumps under `history/` or
   `results/`, and do not put evaluation cases, labels, predictions, judgments,
   or generated reports in the knowledge tree.
4. Never add raw evidence pages to an adapter's always-on briefing.
5. Update the nearest `_index.md`, then run both:

   ```powershell
   python knowledge/tools/check_knowledge_tree.py
   python knowledge/tools/check_wiki_lint.py
   ```
