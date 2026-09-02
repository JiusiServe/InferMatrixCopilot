# Knowledge base — provenance, authorization & layout

The copilot's repo knowledge is a **vendored adaptation** of the human-curated
common knowledge base **zuiho-kai/claude-workflow-starter-private**. The original
tree was imported at `f2dc8248f62fa590c9bae13f92492a175a7c3c32`; common rules are
currently synchronized through private `master @
296ea45c73ecb30f9138e16619fa00fd4d482cd4`. They are maintained **in this repo**
as ordinary tracked files at the repo-root **`knowledge/`**
(= `settings.knowledge_dir`).

The relationship is subset-based, not snapshot replacement:

```text
private master common knowledge ⊆ InferMatrixCopilot knowledge
```

`InferMatrixCopilot` may retain adapter-, component-, model-, schema- and
frontmatter-specific extensions. A common-baseline sync imports missing semantic
deltas with `framework/` mapped to `general/`; it must not delete target-only
extensions merely because they are absent from the common source.

- Current common source: https://github.com/zuiho-kai/claude-workflow-starter-private
- Original public source: https://github.com/zuiho-kai/claude-workflow-starter
- Imported from commit: `f2dc8248f62fa590c9bae13f92492a175a7c3c32` (2026-07-13)
- Common baseline synchronized through:
  `296ea45c73ecb30f9138e16619fa00fd4d482cd4` (2026-07-29)
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
- **Audit baseline:** `doc/archive/reorg-audit/baseline/` holds the upstream `ls-tree`
  manifest, a full `git archive` tarball (+sha256) of `f2dc824`, and `dates.tsv`
  (per-file upstream created/updated dates, captured before the submodule's git
  history was removed — used for page frontmatter).
- **Code-mirror pin:** the `knowledge/repos/vllm-omni/components/` source maps
  are verified against vllm-omni `main @
c588208cc6132b08f5066420468e047ca581fbdc`. The canonical machine baseline
  is `adapters/vllm_omni/release_baseline.yaml`.
- **AFD code-mirror pin:** the `knowledge/repos/afd-plugin/components/` owner
  maps and architecture summaries are verified against
  `vllm-project/afd-plugin` default branch at
  `a432692ed7d5dd6437a4755b530ee7aaf2685dad` (vLLM 0.26.0 baseline).
  Deliberately NOT written as `main @ <sha>`: this file is a
  `pin_documents` entry, and the release audit requires every marker in
  that form to equal `audited_sha`. This SHA belongs to another
  repository, so the pin syntax is reserved for vllm-omni pins only.

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
- **On demand:** the cross-platform `doc_search` / `doc_read` tools recursively
  reach every deeper Markdown page in the shared `general/`
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

1. Read `knowledge/CONTRIBUTING.md`, `knowledge/SCHEMA.md`, and exactly one
   linked contribution topic. The reorganization plan is historical, not an
   active directory contract.
2. Route content by role and owner: rules for auditable invariants, direct
   feature pages for component/model procedures, architecture for stable
   boundaries, and the existing raw layer for complex evidence. Do not create
   a catch-all review page or a `guides/` layer under a source owner.
3. Treat `knowledge/SCHEMA.md` only as an additive metadata overlay. Evaluation
   cases, hidden labels, predictions, judgments, and generated reports stay in
   `eval/` and outside always-on briefing documents.

    python knowledge/tools/check_knowledge_tree.py
    python knowledge/tools/check_wiki_lint.py

For a future common-baseline sync, diff the last recorded private-source commit
against `zuiho-kai/claude-workflow-starter-private` `master`, then import only
the semantic delta. Preserve target-only pages and additions, map
`framework/` to `general/`, retain target frontmatter, and resolve rule-ID
collisions explicitly. There is no submodule link and a whole-tree replacement
is not a valid synchronization method.
