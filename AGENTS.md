# Repository instructions

## Knowledge edits

Before adding, moving, or deleting any knowledge page:

1. Read `doc/knowledge/CONTRIBUTING.md`, then exactly the one linked contribution
   topic that matches the change. The current contract is that entry page plus
   `doc/knowledge/contributing/`, `doc/knowledge/SCHEMA.md` and the two validators;
   `doc/archive/PLAN-knowledge-reorg.md` is archived history, not the directory
   contract. Keep working owner-scoped and merge synonymous conclusions union-first.
2. Route each conclusion by both purpose and code owner. PR-learning and review-
   experience intake may produce only executable rules in the nearest owner's
   `rules.md`; model-specific rules stay with that model owner. Raw PR material
   is temporary input outside the repository and must be deleted after the
   owner-scoped rule batch passes validation. Never add PR case/history/result/
   incident pages or collapse heterogeneous owners into one catch-all page.
3. Treat `doc/knowledge/SCHEMA.md` as an additive metadata overlay only. Existing
   `incidents/`, `history/`, and `results/` files are legacy material, not an
   allowed destination for new PR learning. Generated evaluation cases, hidden
   labels, predictions, judgments, and run reports belong under `eval/`, not in
   the product knowledge tree.
4. Never persist raw evidence pages or replay outputs. Update the nearest
   `_index.md` for every current rules page.
5. Editing `knowledge/repos/vllm-omni/` also touches a machine contract the two
   validators cannot see: `owner_documents` entry pages, in-body SHA pins and
   upstream `sources:` are reconciled by `tools/audit_vllm_omni_release.py`, and
   any PR touching that slice runs it in `enforce` mode
   (`doc/knowledge/contributing/validation.md`).
6. Run both validators after the complete owner-scoped batch:

   ```powershell
   python knowledge/tools/check_knowledge_tree.py
   python knowledge/tools/check_wiki_lint.py
   ```
