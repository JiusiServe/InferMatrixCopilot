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
  are verified against vllm-omni `dev/vllm-align @
  4f2b32cd36e23325b53e20f6ddd5f5954edccb47` (every stated path exists there).

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
- **On demand:** the `doc_search` / `doc_read` agent tools reach **every** deeper
  guide, incident, component, and model page across the shared base (general or
  repo-specific), contained under `knowledge/`. Nothing is lost — the full tree is
  on disk and versioned; only the always-on slice is bounded.

## Maintaining the vendored tree
Edit `knowledge/` in place like any other tracked content; every change goes
through normal PR review plus the tree's own gates:

    python knowledge/tools/check_knowledge_tree.py

To cherry-pick a future upstream improvement, diff against
https://github.com/zuiho-kai/claude-workflow-starter and import the specific
pages (deliberate, reviewable — there is no submodule link anymore).
