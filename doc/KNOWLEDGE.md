# Knowledge base — provenance, authorization & layout

The copilot's repo knowledge is a **vendored copy** of the human-curated community
knowledge base **zuiho-kai/claude-workflow-starter**, imported at upstream commit
`f2dc8248f62fa590c9bae13f92492a175a7c3c32` and maintained **in this repo** as
ordinary tracked files at the repo-root **`knowledge/`** (= `settings.knowledge_dir`).
It is being reorganized in-repo (folder rename, code-mirror, detail-preserving
curation — see `doc/PLAN-knowledge-reorg.md`); upstream is not modified.

- Source: https://github.com/zuiho-kai/claude-workflow-starter
- Imported from commit: `f2dc8248f62fa590c9bae13f92492a175a7c3c32` (2026-07-13)
- **Authorization:** the author (zuiho) authorized copying the content into this
  repo for local use and reorganization; confirmed by the repo owner (Taichang
  Zhou) on 2026-07-16 — "we can also copy there contents as our local content,
  which I have already get their authorization." Upstream ships no LICENSE file,
  so this recorded authorization is the licensing basis. Attribution retained
  (this page + the upstream README kept in-tree).
- **Fidelity:** the import is byte-identical to `f2dc824` except two machine-local
  Claude Code permission files (`.claude/settings.local.json`,
  `skills/claudeception/.claude/settings.local.json`) — excluded because they
  carry the author's machine-local grants (including a private host address),
  which the knowledge tree's own validator policy forbids. Their exact bytes are
  preserved in the audit baseline.
- **Audit baseline:** `doc/reorg-audit/baseline/` holds the upstream `ls-tree`
  manifest, a full `git archive` tarball (+sha256) of `f2dc824`, and `dates.tsv`
  (per-file upstream created/updated dates, captured before the submodule's git
  history was removed — used for page frontmatter).
- **Code-mirror pin:** the `knowledge/repos/vllm-omni/components/` source maps
  are verified against vllm-omni `main @
  238fc0a609311235a671940cf209a7eb72c1dc29` (every stated path exists there).

## Layout: general vs repo-specific
The knowledge base separates the two, and so do we — the whole tree is **shared**,
never nested under one adapter:

- `knowledge/general/` — **general, cross-repo** agent experience (review, ci,
  debug, git, planning, remote, …). Shared across every repo. (Renamed from
  upstream's `framework/` — see the reorg plan.)
- `knowledge/repos/<repo>/` — **repo-specific** knowledge. Each adapter references
  only its own slice via `manifest.yaml → knowledge.repo_subdir`
  (e.g. `repos/vllm-omni`).

The former AI-generated `adapters/vllm_omni/profile/` (`source: agent` facts) has
been **retired** in favor of this richer human-authored source. The remaining
`adapters/vllm_omni/manifest.yaml` (structural: repo path, modules, risk,
capabilities, push policy) is human-authored and stays — the code depends on it.

## How the copilot uses it
- **Briefing (always-on):** the general slice `settings.knowledge_general_docs`
  + the adapter's repo-specific `briefing_docs`
  (`repos/<repo>/rules.md` + `_index.md`), each capped.
- **On demand:** the cross-platform `doc_search` / `doc_read` tools reach every
  deeper guide, incident, component, and model page in the shared `general/`
  slice plus the active adapter's `knowledge.repo_subdir`. Other repos' slices
  are refused. Search is implemented in Python (no host `grep` dependency), and
  title/frontmatter/heading hits rank first.
- **MCP direct access:** the same repo-scoped `doc_search` / `doc_read` tools are
  exposed read-only over MCP, so a capable host model can use the knowledge base
  directly without starting a workflow. Workflow agents and MCP share the same
  access implementation and containment rules.
- **Observability:** missing, escaped, or unreadable briefing documents emit
  `knowledge_warning` / `capability_gap` RunTrace events instead of silently
  removing the knowledge briefing.

## Maintaining the vendored tree
Edit `knowledge/` in place like any other tracked content; every change goes
through normal PR review plus the tree's own gates:

1. Read `doc/PLAN-knowledge-reorg.md`, `knowledge/CONTRIBUTING.md`, and exactly
   one linked contribution topic. Preserve the plan's owner-scoped inventory,
   union-first curation, and raw/synthesized split.
2. Route content by role and owner: rules for auditable invariants, guides for
   procedures, architecture for stable boundaries, and the existing raw layer
   for complex evidence. Do not create a catch-all review page.
3. Treat `knowledge/SCHEMA.md` only as an additive metadata overlay. Evaluation
   cases, hidden labels, predictions, judgments, and generated reports stay in
   `eval/` and outside always-on briefing documents.

    python knowledge/tools/check_knowledge_tree.py
    python knowledge/tools/check_wiki_lint.py

To cherry-pick a future upstream improvement, diff against
https://github.com/zuiho-kai/claude-workflow-starter and import the specific
pages (deliberate, reviewable — there is no submodule link anymore).
