# JiuwenSwarm implementation-knowledge depth

The pinned run at `f0a69728c96b5961d993449f1a901cbd2f4dac5b` added **173 checked facets across 77 feature-depth pages**. Every accepted block is bound to an actual Codex review, its exact prose, and pinned source spans. The independent audit reports no proof errors.

| Measure | Before | After |
| --- | ---: | ---: |
| Feature breadth | 79/79 | 79/79 |
| Production-file breadth | 2043/2199 (92.91%) | 2043/2199 (92.91%) |
| Features with checked depth blocks | 0/79 | 77/79 |
| Checked depth facets | 0/553 | 173/553 (31.28%) |
| Features with all seven depth facets | 0/79 | 0/79 |
| Production files participating in depth evidence | 0 | 115 |

Breadth includes checked interface records and feature summaries. The 115 participating files are witnesses for particular claims, not files with exhaustive behavior coverage. Existing owner explanations also remain useful; this conservative depth metric counts only the new bound blocks.

All 79 features received extraction attempts. **Cron and skill evolution have no approved depth facets** after retries; their existing summaries remain. Other missing facets are listed per feature in the [full report](jiuwenswarm-f0a69728c96b.json). A full seven-facet feature is still an open target.

Generation used Zcode GLM-5.3 at low effort; review requested Codex gpt-6-sol at low effort. The completed traces contain 121 generation calls and 112 review calls, including failures. The generator reports served identity when it returns a result; Codex does not report served-model identity. Two interrupted generation attempts have unreported usage and are recorded separately.

Inputs included existing knowledge, 299 distinct source files, and 86 project documents. Of those documents, 24 came from the partial `.doc_project_maintainer` collection, used for 66 features. Historical test ledgers were context rather than evidence of current test passes. Validation facets describe assertions at the source pin; upstream JiuwenSwarm tests were not executed here.

The final batch used $56 of fixed review accounting, plus $4 of earlier diagnostic accounting, within the original $60 ledger ceiling. Native subscription clients report no invoiced USD cost. These amounts are budget reservations, not measured billing or a cap on an actual invoice.

The report contains the frozen knowledge baseline and input digest, code revisions used by the native calls, input paths, before/after audits, knowledge and policy hashes, and per-block native approval bindings. Raw prompts and verdict replies remain in ignored local state.

Recompute the audit against a clean checkout at the exact pin:

```bash
PYTHONPATH=src python tools/audit_knowledge_depth.py \
  --repo jiuwenswarm \
  --upstream /path/to/pinned/jiuwenswarm \
  --pin f0a69728c96b5961d993449f1a901cbd2f4dac5b \
  --report /path/to/local/depth-audit.json
```

`kb widen jiuwenswarm` expands explanatory knowledge. `kb deepen jiuwenswarm` adds implementation facets; `--retry-unfinished` retries gaps with cumulative accounting and priority for features without accepted depth. Use a fresh state directory after publishing and merging a batch. Existing rule-focused `kb init --stage deepen` keeps its original behavior.
