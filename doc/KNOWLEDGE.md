# Shared knowledge base — attribution & layout

The copilot's repo knowledge is the human-curated community knowledge base
**zuiho-kai/claude-workflow-starter**, **referenced (not copied)** as a git
submodule at the repo-root **`knowledge/`** and pinned to a specific commit.
Their content is used **UNMODIFIED** — it is the single source of truth; this
repo never edits it.

- Source: https://github.com/zuiho-kai/claude-workflow-starter
- Referenced at: `knowledge/` (git submodule = `settings.knowledge_dir`)
- Pinned commit: `f2dc8248f62fa590c9bae13f92492a175a7c3c32`
- Reuse/reference authorized by the author.

## Layout: general vs repo-specific
The knowledge base separates the two, and so do we — the whole tree is **shared**,
never nested under one adapter:

- `knowledge/framework/` — **general, cross-repo** agent experience (review, ci,
  debug, git, planning, remote, …). Shared across every repo.
- `knowledge/repos/<repo>/` — **repo-specific** knowledge. Each adapter references
  only its own slice via `manifest.yaml → knowledge.repo_subdir`
  (e.g. `repos/vllm-omni`).

The former AI-generated `adapters/vllm_omni/profile/` (`source: agent` facts) has
been **retired** in favor of this richer human-authored source. The remaining
`adapters/vllm_omni/manifest.yaml` (structural: repo path, modules, risk,
capabilities, push policy) is human-authored and stays — the code depends on it.

## How the copilot uses it
- **Briefing (always-on):** the general slice `settings.knowledge_general_docs`
  (`framework/_index.md`) + the adapter's repo-specific `briefing_docs`
  (`repos/<repo>/rules.md` + `_index.md`), each capped.
- **On demand:** the `doc_search` / `doc_read` agent tools reach **every** deeper
  guide, incident, component, and model page across the shared base (general or
  repo-specific), contained under `knowledge/`. Nothing is lost — the full tree is
  on disk and versioned; only the always-on slice is bounded.

## Working with the submodule
After cloning this repo:

    git submodule update --init knowledge

To move to a newer upstream snapshot (deliberate, reviewable):

    git -C knowledge pull origin master
    git add knowledge      # commit the new pinned commit
