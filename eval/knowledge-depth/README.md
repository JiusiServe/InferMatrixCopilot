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

## Completion campaign at the same source pin

The new policy fixes the denominator at 79 features × seven facets and requires **each facet above 90%** (at least 72/79), every feature to have recognized depth, and production-file breadth at least 85%. An incomplete checkpoint remains partial and cannot publish or merge. `--unlimited-subscription` requires authenticated Zcode GLM-5.3 extraction and an independent Codex subscription judge; no configured fallback or invoiced zero is inferred.

The workflow is structural coverage review → shared evidence indexing → targeted deepening → source-reference and actual native-record audits → retrieval acceptance → independent review → CI → merge. Positive knowledge and unknowns remain separate; historical strict absence records, if present, are not passing tests or demonstrated capabilities.

[The frozen retrieval baseline](jiuwenswarm-completion-retrieval-before-20261002.json) contains 237 probes and their actual context. Its `storage.format` is `depth-retrieval-deduplicated-v1`: cases reference hash-bound document metadata and execution budgets; `content_blobs` stores repeated text once. `audit_depth_retrieval.expand_report()` verifies every reference and reconstructs the original report against `expanded_report_sha256`. Large collections use one record per line. Baseline page hits do not mean all facets were injected: description plus paths delivers 162 of the 173 available facets within the unchanged two-page/6,000-character budget.

[The archived artifacts flow block](jiuwenswarm-artifacts-flow-legacy-20261002.json) retains its exact original bytes, proof and native approval. The stricter caller-scope check cannot prove the flattened callback edges; with the user's confirmed repair choice it is excluded from current recognition pending a newly extracted and independently approved replacement. The other 172 original blocks stay unchanged; this retirement does not remove a feature or facet from the denominator.

## Lightweight recognition and 13 concurrent workers

JiuwenSwarm explicitly selects `semantic_depth.acceptance_mode: lightweight`; other repositories default to strict. `kb deepen jiuwenswarm --acceptance-mode lightweight --unlimited-subscription` uses pinned source/project-document citations and one independent Codex call for all new facets of each feature. Representative flow paths and labeled design inference are allowed. Lightweight recognition does not claim deterministic runtime-call certification or generate verified-absence certificates. Old strict blocks retain their original bytes, hashes and labels; the publication audit counts the strict-plus-lightweight union once per feature/facet.

The campaign runner defaults to 13 isolated workers and accepts `--workers 13`. Each worker owns its checkpoint, model gateway and trace archive. The parent builds one immutable source/test/document index bound to the source pin, policy and index version. Initial extraction packets offer up to 24 KB of source/test lines, 8 KB of relevant document lines and 4 KB of existing knowledge; subsequent corrections retrieve evidence for the specific gap. Format, references, hashes, receipts and counts are checked incrementally; comprehensive audits, retrieval acceptance and full CI run at delivery.

Each missing facet receives an initial attempt and at most three corrections. The round is saved before dispatch, including review-only retries. Restarting or `--retry-unfinished` does not reset this lifetime limit. Passed facets are frozen; failure in another facet does not discard them. After exhausted repairs, the facet remains unknown with its reason. Creating the campaign's STOP file stops new dispatch and drains active calls; the supervisor records progress in `drain.json`.

Validation knowledge labels runtime assertions, source-text assertions, helper-unit assertions or existing documented manual checks. Manual entries include their documented action and expected observation and explicitly say this batch did not execute them. Missing tests never become verified absence, and knowledge about assertions does not mean tests passed.

Zcode calls retain pre-dispatch system/prompt inputs, streamed native events, replies, requested/reported model identities, duration, reported usage and failure/interruption status under the ignored campaign archive. Content-addressed blobs and worker-specific paths prevent concurrent overwrites. These archives support future extraction analysis; raw trajectories stay outside the product knowledge tree and Git reports. Unreported invoiced cost remains unknown. Retrieval preserves two documents and 6,000 characters, exposing acceptance modes and validation types separately for available and injected facets.
