# Knowledge attribution & provenance

The vLLM-Omni repo knowledge this adapter injects and retrieves is the
human-curated community knowledge base **zuiho-kai/claude-workflow-starter**,
**referenced (not copied)** as a git submodule at `knowledge/` and pinned to a
specific commit. Their content is used **UNMODIFIED** — it is the single source
of truth; this repo never edits it.

- Source: https://github.com/zuiho-kai/claude-workflow-starter
- Referenced at: `adapters/vllm_omni/knowledge/` (git submodule)
- Pinned commit: `f2dc8248f62fa590c9bae13f92492a175a7c3c32`
- Reuse/reference authorized by the author.

The former AI-generated `profile/` (typed facts tagged `source: agent`) has been
**retired** in favor of this richer, human-authored source. The remaining
`manifest.yaml` (structural: repo path, modules, risk, capabilities, push
policy) is human-authored and stays — the copilot code depends on it.

## How the copilot uses it
- `manifest.yaml` → `knowledge:` names the submodule dir, the vllm-omni subtree,
  and the `briefing_docs`.
- `RepoAdapter.briefing()` injects the always-on slice — the hard-gate
  `rules.md` + the `_index.md` navigation table — capped.
- The `doc_search` / `doc_read` agent tools reach **every** deeper guide,
  incident, and component/model page on demand (nothing is lost — the full tree
  is on disk and versioned; only the always-on slice is bounded).

## Working with the submodule
After cloning this repo, materialize the knowledge base:

    git submodule update --init adapters/vllm_omni/knowledge

To move to a newer upstream snapshot (deliberate, reviewable):

    git -C adapters/vllm_omni/knowledge pull origin master
    git add adapters/vllm_omni/knowledge   # commit the new pinned commit
