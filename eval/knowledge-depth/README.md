# JiuwenSwarm implementation-knowledge depth

## Current completion result: partial delivery

The completion campaign at `f0a69728c96b5961d993449f1a901cbd2f4dac5b` retains **490 recognized facets: 207 strict and 283 lightweight**, counted once per feature/facet. This is **490/553 (88.61%)**. The fixed denominator remains 79 features × seven dimensions. **63 facets remain unknown**: 53 were unsupported after their bounded extraction/correction rounds, and 10 initially accepted lightweight facets were withdrawn after the final independent content review found wrong feature attribution or claims beyond the evidence. Withdrawal preserves the review record; it does not prove that the project lacks the capability or tests.

The target requires each dimension to exceed 90% (at least 72/79), recognized depth for every feature, and production-file breadth of at least 85%. This delivery **does not meet the target**. Its partial result is reviewable in a draft PR; it is not eligible for merge. The campaign's initial attempt plus at most three corrections is a persisted lifetime limit, including across resumes; late withdrawals do not reset it.

Current delivery reports:

- [Chinese comparison and PR-review impact](jiuwenswarm-lightweight-comparison-cn-20261002.md), with [machine-readable comparison](jiuwenswarm-lightweight-comparison-cn-20261002.json).
- [Final source/native audit summary](jiuwenswarm-lightweight-final-20261002.json), with [source bindings](jiuwenswarm-lightweight-source-depth-20261002.json) and [native approval bindings](jiuwenswarm-lightweight-native-approvals-20261002.json).
- [Final retrieval acceptance](jiuwenswarm-lightweight-retrieval-after-20261002.json).
- [Independent content review](jiuwenswarm-independent-content-review-20261002.json) and [withdrawn-content quarantine](jiuwenswarm-content-quarantine-20261002.json).
- [Local validation record](jiuwenswarm-local-validation-20261002.json); final CI results are recorded on the draft PR.

The campaign used 13 isolated feature workers, a shared immutable evidence index and a persistent Zcode start/cooldown schedule. Native Zcode/Codex attempt journals, prompts, streamed events and replies remain in ignored local campaign state outside Git and the knowledge tree. Git reports contain bounded findings, hashes and provenance rather than raw native trajectories. Unreported usage and invoiced cost remain unknown. The historical 173-facet report and the separate original artifacts-flow retirement archive below remain preserved as historical evidence, without adding retired blocks back to current recognition.

## Historical 173-facet baseline

The initial pinned run at `f0a69728c96b5961d993449f1a901cbd2f4dac5b` reported **173 checked facets across 77 feature-depth pages**, before the later artifacts-flow retirement. Each accepted block was bound to an actual Codex review, its exact prose, and pinned source spans. Its original independent audit reported no proof errors under the checks then in use.

| Measure | Before | After |
| --- | ---: | ---: |
| Feature breadth | 79/79 | 79/79 |
| Production-file breadth | 2043/2199 (92.91%) | 2043/2199 (92.91%) |
| Features with checked depth blocks | 0/79 | 77/79 |
| Checked depth facets | 0/553 | 173/553 (31.28%) |
| Features with all seven depth facets | 0/79 | 0/79 |
| Production files participating in depth evidence | 0 | 115 |

Breadth includes checked interface records and feature summaries. The 115 participating files are witnesses for particular claims, not files with exhaustive behavior coverage. Existing owner explanations also remain useful; this conservative depth metric counts only the new bound blocks.

All 79 features received extraction attempts in that historical run. **Cron and skill evolution had no approved depth facets** after its retries; their existing summaries remained. Its missing facets are listed per feature in the [historical full report](jiuwenswarm-f0a69728c96b.json).

Generation used Zcode GLM-5.3 at low effort; review requested Codex gpt-6-sol at low effort. The completed traces contain 121 generation calls and 112 review calls, including failures. The generator reports served identity when it returns a result; Codex does not report served-model identity. Two interrupted generation attempts have unreported usage and are recorded separately.

Inputs included existing knowledge, 299 distinct source files, and 86 project documents. Of those documents, 24 came from the partial `.doc_project_maintainer` collection, used for 66 features. Historical test ledgers were context rather than evidence of current test passes. Validation facets describe assertions at the source pin; upstream JiuwenSwarm tests were not executed here.

The historical batch used $56 of fixed review accounting, plus $4 of earlier diagnostic accounting, within the original $60 ledger ceiling. Native subscription clients report no invoiced USD cost. These amounts are budget reservations, not measured billing or a cap on an actual invoice. The later completion campaign uses the explicit unlimited-subscription mode described below.

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

The new policy fixes the denominator at 79 features × seven facets and requires **each facet above 90%** (at least 72/79), every feature to have recognized depth, and production-file breadth at least 85%. An incomplete checkpoint remains partial; a draft PR can document it, but it cannot be merged as a completed batch. `--unlimited-subscription` requires authenticated Zcode GLM-5.3 extraction and an independent Codex subscription judge; no configured fallback or invoiced zero is inferred.

The workflow is structural coverage review → shared evidence indexing → targeted deepening → source-reference and actual native-record audits → retrieval acceptance → independent review → CI → merge when the target and checks pass. Independent content review also checks feature attribution: a faithful description of a neighboring feature or shared-owner helper does not establish coverage for the requested feature. Withdrawn blocks are archived, excluded from recognition and retrieval, and reported as unknown without changing the denominator. Positive knowledge and unknowns remain separate; historical strict absence records, if present, are not passing tests or demonstrated capabilities.

[The frozen retrieval baseline](jiuwenswarm-completion-retrieval-before-20261002.json) contains 237 probes and their actual context. Its `storage.format` is `depth-retrieval-deduplicated-v1`: cases reference hash-bound document metadata and execution budgets; `content_blobs` stores repeated text once. `audit_depth_retrieval.expand_report()` verifies every reference and reconstructs the original report against `expanded_report_sha256`. Large collections use one record per line. Baseline page hits do not mean all facets were injected: description plus paths delivers 162 of the 173 available facets within the unchanged two-page/6,000-character budget.

[The archived artifacts flow block](jiuwenswarm-artifacts-flow-legacy-20261002.json) retains its exact original bytes, proof and native approval. The stricter caller-scope check cannot prove the flattened callback edges; with the user's confirmed repair choice that historical block is excluded from current recognition. Any replacement is counted only through its own source evidence and independent approval. The other 172 original blocks stay unchanged; this retirement does not remove a feature or facet from the denominator.

## Lightweight recognition and 13 concurrent workers

JiuwenSwarm explicitly selects `semantic_depth.acceptance_mode: lightweight`; other repositories default to strict. `kb deepen jiuwenswarm --acceptance-mode lightweight --unlimited-subscription` uses pinned source/project-document citations and one independent Codex call for all new facets of each feature. Representative flow paths and labeled design inference are allowed. Lightweight recognition does not claim deterministic runtime-call certification or generate verified-absence certificates. Old strict blocks retain their original bytes, hashes and labels; the publication audit counts the strict-plus-lightweight union once per feature/facet.

The campaign runner defaults to 13 isolated workers and accepts `--workers 13`. Each worker owns its checkpoint, model gateway and trace archive. The parent builds one immutable source/test/document index bound to the source pin, policy and index version. Initial extraction packets offer up to 24 KB of source/test lines, 8 KB of relevant document lines and 4 KB of existing knowledge; subsequent corrections retrieve evidence for the specific gap. Format, references, hashes, receipts and counts are checked incrementally; comprehensive audits, retrieval acceptance and full CI run at delivery.

Each missing facet receives an initial attempt and at most three corrections. The round is saved before dispatch, including review-only retries. Restarting or `--retry-unfinished` does not reset this lifetime limit. Passed facets are frozen; failure in another facet does not discard them. After exhausted repairs, the facet remains unknown with its reason. Creating the campaign's STOP file stops new dispatch and drains active calls; the supervisor records progress in `drain.json`.

Validation knowledge labels runtime assertions, source-text assertions, helper-unit assertions or existing documented manual checks. Manual entries include their documented action and expected observation and explicitly say this batch did not execute them. Missing tests never become verified absence, and knowledge about assertions does not mean tests passed.

Zcode calls retain pre-dispatch system/prompt inputs, streamed native events, replies, requested/reported model identities, duration, reported usage and failure/interruption status under the ignored campaign archive. Content-addressed blobs and worker-specific paths prevent concurrent overwrites. These archives support future extraction analysis; raw trajectories stay outside the product knowledge tree and Git reports. Unreported invoiced cost remains unknown. Retrieval preserves two documents and 6,000 characters, exposing acceptance modes and validation types separately for available and injected facets.

The 13 feature workers share a Zcode request schedule so simultaneous starts and observed provider rate limits do not trigger another burst. Defaults are `--zcode-start-interval 15` seconds and `--zcode-rate-cooldown 90` seconds. Observed native 429/account-1302 errors extend the cooldown and double start spacing up to 60 seconds; four later completions without a new rate limit allow a five-second recovery step. These are local scheduling settings, not claims about the provider's quota. Waiting, dispatch and cooldown events belong to the same durable native attempt trace; they do not create extra model-call records or reset a facet's four-round correction budget. Provider admission can delay a worker while other features or Codex reviews progress. A checkpoint-monitor read failure is diagnostic and must not terminate the campaign. Interrupted attempts retain their inputs and streamed events with unreported usage; an unfinished journal is not a completed or successful call.

Native approval auditing of new lightweight blocks binds the actual successful Zcode GLM-5.3 draft section and offered evidence to the approved prose, including deterministic inference/manual prefixes. A nearby generator call, unrelated reply, other model, or fallback is insufficient. Historical strict blocks retain their existing audit path and original hashes.
