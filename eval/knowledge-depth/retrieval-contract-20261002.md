# Bounded review retrieval contract

Baseline: `2b669678bd5bf43a77edf5b296c5d59dc4497591`.
User scope: improve retrieval and update the workflow, following the Chinese knowledge comparison report.
This document records the review input and acceptance matrix at implementation handoff; it does not claim an earlier design approval.

Unique owner: `KnowledgeDocs.related`; all consumers use its result. Estimated production additions: 300–400 lines; current additions about 250. No new model calls, provider, KB stage, or hard-rule route.

| Input / producer | Consumer | Required behavior |
|---|---|---|
| Frozen diff paths + PR description | Direct MCP / SDK plan | Deterministic bounded explanatory context; preserve description-first hard-rule routes |
| `pr_diff` + `pr_context` | Agent dispatch | Same retrieval; untrusted-data fencing; briefing ablation disables automatic injection |
| Feature policy | `knowledge` / accepted `knowledge-deepen` pages | Canonical hints; preserve bodies, source pins and accepted checkpoint proofs |
| Old pages without hints | Retrieval | Pinned-source-path fallback; no migration prerequisite |
| Intact partial depth | All consumers | Prefer deep prose within a selected feature; expose available/missing facets and source pin |
| Edited, duplicate or malformed depth | All consumers | Do not present invalid facet as checked depth |
| Other repo / structural cards / rules | Automatic context | Exclude; explicit general read/search behavior remains available |
| Activated KB snapshot | Direct + SDK | Verify reads; bind references and later reads to the original view |
| Long prose | All consumers | Two documents, 3,000 characters each, 6,000 total; budget incomplete-document followups |
| Rejected extraction | Depth workflow | Preserve empty-stage semantics; do not publish metadata-only failure |

Validation: representative positive/negative tests at actual Direct, SDK and Agent entry points; 79 catalog cases with descriptions and paths plus 79 diagnostic paths-only cases; independent pinned upstream breadth/depth audit. Catalog delivery is not real PR recall/RQS improvement. Reports remain outside product knowledge.

Review owner rules: `knowledge/general/review/rules.md` (full, no grouped owner contract).
Baseline contracts: `doc/architecture/SPEC/knowledge_docs.md`, `direct_routing.md`, `sdk.md`, `engine/agent_runtime.md`, `kb_service.md` and root repository invariants.
