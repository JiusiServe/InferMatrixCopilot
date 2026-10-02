# Independent retrieval delivery review

## Review scope

- Base SHA: 2b669678bd5bf43a77edf5b296c5d59dc4497591.
- Diff: baseline -> working tree, including tracked production, tests, workflow/spec changes and 156 JiuwenSwarm metadata edits.
- Owners: knowledge/general/review/rules.md; full enumeration, no rule groups.
- In-scope untracked files: tools/audit_review_retrieval.py; test/test_knowledge_retrieval.py; eval/knowledge-depth/retrieval-contract-20261002.md; jiuwenswarm-retrieval-acceptance-20261002.json; jiuwenswarm-retrieval-baseline-20261002.json; jiuwenswarm-retrieval-depth-audit-20261002.json.
- Author-supplied contract: eval/knowledge-depth/retrieval-contract-20261002.md is the implementation handoff contract. It explicitly states that it is not evidence of earlier design approval. The user request and baseline live contracts provide the authorized scope.
- Evidence boundaries: no network, paid model, broad pytest or duplicate extraction/audit. This review is read-only except this report. The main agent owns final test/CI and publication. This second wave re-reviewed the entire current source, workflow and test diff after F1, including the checker compatibility change. Later production edits invalidate this source verdict.

## Owner rule audit

| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| REV-1a | PASS | knowledge_docs.py:KnowledgeDocs.related is shared by direct_routing.py:direct_review_plan, sdk/v1/direct.py:DirectClient.plan and engine/agent_runtime/runner.py:run_agent_step; existing explicit read/search remain independent operations with unchanged contracts. | - |
| REV-1b | PASS | runner.py:run_agent_step gates automatic injection on profile_briefing_enabled; test_agent_runtime.py:test_review_prompt_gets_scoped_knowledge_and_respects_ablation covers enabled hit, enabled miss and disabled hit. Direct/SDK use the same result without a ranking fork. | - |
| REV-2a | PASS | One read-only evidence packet and this single report cover correctness plus subtraction; git diff and bounded source reads were reused; no second reviewer or broad test duplication. | - |
| REV-2b | PASS | Subtraction signal triggered by related API, parser helper, metadata writer and tool; the scope/census/item ledger below proves one retrieval result with three consumer adapters and one canonical metadata writer. | - |
| REV-2c | PASS | Bounded 10-minute independent review; parent received the initial status and confirmed finding promptly. CI/mergeability do not exist for this uncommitted worktree; no fabricated PR metadata. | - |
| REV-3a | PASS | .github/workflows/test.yml runs python -m pytest -q and both knowledge validators. Parent reports the equivalent full suite passed before the final proof guard, and final targeted proof/depth/SDK/Agent plus checker tests passed afterward. Final remote CI is pending; this report does not call the earlier full-suite result final-head evidence or use a focused probe as lane evidence. | - |
| REV-3b | PASS | Handoff retrieval-contract-20261002.md provides estimated 300–400 production additions; parent now reports 256 added/21 removed under src plus two checker lines, below both that budget and 1,000. The separate offline acceptance script is also within 400 total additions. Largest source addition is knowledge_docs.py. Generated 156 metadata edits, docs and eval JSON are not production-code budget. | - |

## Public ingress matrix

| Ingress | Actual dispatcher | Contract check | First expensive operation | Owner adapter/consumer | Production-path test/evidence |
|---|---|---|---|---|---|
| Direct MCP review(mode=direct) | `thin_mcp_server.py:review` -> `direct_routing.py:direct_review_plan` | Existing Direct metadata normalization; repository support guard and KnowledgeDocs related-path validation | `KnowledgeDocs.related` scoped file verification/read | `KnowledgeDocs.related` -> Direct related_knowledge | test_thin_mcp_server.py existing routing/budget assertions updated; no strict engine/repo resolution added |
| Python SDK plan | `sdk/v1/direct.py:DirectClient.plan` -> `direct_review_plan` | Existing typed request validation and pinned KnowledgeView | `KnowledgeDocs.related` scoped file verification/read | `DirectClient._document_ref` binds returned docs to the same view | test_sdk_v1.py:test_related_depth_reaches_sdk_with_content_addressed_refs_and_read_budget; existing read_document context binding retained |
| Agent review and ensemble lens | `runner.py:run_agent_step`; `ensemble.py:run_agent_step_ensemble` reuses runner | Existing diff_signals parser; briefing ablation; no retrieval policy duplicated in caller | `doc_related` -> `KnowledgeDocs.related` file read | `AgentDispatchContext.briefing` -> first model prompt | test_agent_runtime.py positive/negative/ablation prompt test; ensemble passes identical evidence into runner |
| Explicit agent doc_related | `knowledge.py:_repo_docs_tool` closure | KnowledgeDocsError produces visible refused response; selected repo scope only | `KnowledgeDocs.related` file read | `knowledge.py:doc_related` JSON response | test_knowledge_retrieval.py scope/input tests; explicit doc_read/search remain available |
| Knowledge init | `init_knowledge.py:_Knowledge._build` | Existing reviewed policy loader and explanatory page check | `knowledge_coverage.py:feature_metadata` Page parsing | `init_stages.py:_Stage._conclude` publication delta | Code inspection: canonical writer runs after generated knowledge, preserving bodies |
| Knowledge deepen init/resume | `init_knowledge_depth.py:_KnowledgeDepth._build` | Existing accepted checkpoint digest and upstream source proofs checked before rendering hints | `knowledge_depth.py:verified_blocks` proof validation | `knowledge_coverage.py:feature_metadata` -> `init_stages.py:_Stage._conclude` publication delta | test_kb_knowledge_depth.py accepted page hints and resume assertions; no accepted body/digest mutation |
| Offline acceptance CLI | `tools/audit_review_retrieval.py:main` | Reviewed policy, report destination outside product KB, verified KnowledgeView | `direct_routing.py:direct_review_plan` for two probes per feature | `audit_review_retrieval.py:main` JSON report plus nonzero exit on delivery failure | Code inspection; report clearly separates catalog delivery from real PR recall/RQS |

## Producer-consumer trace

| Value or contract | Producer | Transformations | Final consumer | Stop/failure owner | Evidence |
|---|---|---|---|---|---|
| Retrieval identity/paths/globs | Feature policy | feature_metadata edits only YAML fields | KnowledgeDocs.related matching | Policy loader/explanatory type guard | Read-only baseline comparison: all 156 changed JiuwenSwarm pages have identical bodies after frontmatter |
| Depth prose/proof | render_block / accepted checkpoint | depth_sections checks body digest, duplicate facet, safe relative evidence path, span shape and 64-hex evidence digest; visible_text hides proof | Direct plan / SDK / agent prompt | depth_sections rejects malformed shape; init/audit owns upstream source verification | Re-review in-memory valid control and four malformed proofs with correct enclosing body hashes all behaved correctly |
| Context excerpt/bounds | KnowledgeDocs.related | Feature ranking/dedup; at most two 3,000-character documents | related_knowledge and fenced briefing | KnowledgeDocs.related | test_knowledge_retrieval.py large depth, whole-block selection and bounds cases |
| Navigation allowance | Related documents more_available | Direct adds one read per returned incomplete document | execution_budget and navigation_policy.related_document_read_paths | Direct plan provider | SDK/MCP budget assertions updated; no unconstrained index walk introduced |
| Snapshot/reference | KnowledgeView | verify callback before files; _document_ref uses the same view | SDK read_document(review_context_id=...) | KnowledgeView/SDK existing context owner | Existing immutable context read implementation retained; reader tamper probe test supplied |
| Knowledge trust boundary | Curated explanatory prose at source pins | JSON encoding and tag escaping; missing_facets explicit | Review background, never hard-rule routing | Reviewer must verify PR head | runner.py untrusted_data wrapper; workflow/spec updates say missing facets are unknown |

## Source-consumer decision matrix

| Source | Consumer scope / dispatcher | Decision | Conflicts with | Production-path evidence |
|---|---|---|---|---|
| Policy entry points and source globs | Direct/SDK/Agent explanatory context | ROUTE | Multiple hints are relevance signals, not conflicting user values; exact pinned source > entry > glob | One KnowledgeDocs.related scoring implementation |
| Frontmatter sources in old pages | Same explanatory context | ROUTE | Coexists with policy hints; stronger exact source match; no migration prerequisite | test_old_explanatory_pages_use_pinned_sources_without_new_metadata |
| PR title/body/diff | Same explanatory context | ROUTE | Complements paths; no effect on hard-rule owner route selection | direct_review_plan passes joined query; runner uses same related owner |
| Valid depth plus basic feature page | Feature-scoped result | ROUTE | Feature dedup selects depth; overview boosts feature rank without hiding depth | test_stronger_overview_match_cannot_hide_intact_feature_depth |
| General, other repo, rules and structural cards | Automatic explanatory injection | NOT_APPLICABLE | Explicit doc_read/search retain their separate scope/contract | Scoped repo enumeration and early kb:file exclusion |
| Edited/duplicate/malformed proof | Checked depth facets | NOT_APPLICABLE | Invalid blocks do not become checked depth; missing/bad sha and absolute/traversing source paths are rejected | Resolved F1: lifecycle.py:depth_sections plus related-consumer regressions |
| profile_briefing_enabled=false | Automatic agent injection | DEFAULT | Existing ablation disables automatic background; explicit tools remain callable | Agent positive/negative/disabled test |
| Accepted checkpoint text vs rendered hints | Deepen publication | ROUTE | Accepted digest binds original checkpoint; metadata rendering happens after proof check | _KnowledgeDepth._build accepted_sha256 check precedes feature_metadata |
| All-rejected depth extraction | Deepen publication | NOT_APPLICABLE | accepted=false avoids metadata-only output; existing empty-stage contract retained | _KnowledgeDepth._build guard around hints |

## Subtraction audit

subtraction_signal=triggered.

### Scope ledger

| Behavior / production file / test group | Authorized goal or current RFC slice | KEEP / DELETE / DEFER | Evidence |
|---|---|---|---|
| Deterministic related retrieval and shared depth reader | User: improve retrieval; expose existing knowledge to review | KEEP | knowledge_docs.py, lifecycle.py; no model call/provider/index service |
| Direct field plus SDK references plus agent injection/tool | Existing review consumers need the same explanatory context | KEEP | Three actual entry chains above; no second retrieval owner |
| Canonical feature metadata and 156 header migration | User: update init workflow and use existing feature KB | KEEP | feature_metadata reused by knowledge and knowledge-deepen; exact body preservation verified |
| Specs, skills, Cursor instructions, playbook acceptance | User: update workflow | KEEP | Explain bounded retrieval, source pins, missing facets and offline delivery acceptance |
| Regression tests and offline eval tool/reports | Measured retrieval acceptance | KEEP | Tests map to scope, snapshots, bounds and consumer delivery; reports stay under eval |
| Checker heading-ID compatibility and two integration regressions | Required independent review can enumerate the existing stable owner IDs | KEEP | check_review_report.py retains bold/table syntax, adds heading syntax and still rejects duplicate definitions |
| New embedding/provider/extraction, persistent cache or hard-rule route | Not part of current slice | DEFER | None added in the diff; existing rules/route registry unchanged |

### Abstraction census and minimal design

Current census: one retrieval method KnowledgeDocs.related; one canonical safe_source_path predicate shared with the existing init/audit safe_path alias; one depth format parser and shared constants; one policy-to-frontmatter writer; one tool closure; one additive SDK dictionary field/reference projection; one Direct followup budget projection; one agent untrusted renderer; one offline acceptance CLI. Existing init/audit proof verification remains the owner of upstream reads.

Minimal owner design: feature policy writes canonical hints; KnowledgeDocs owns scoped reading, validity projection, ranking and bounded text once; Direct consumes that result, SDK attaches its existing DocumentRef, and Agent encodes it for its existing briefing. Init/audit retains upstream verification. This explanation needs no repair timeline.

### Item ledger

| Current abstraction | KEEP / INLINE / MERGE / MOVE / DELETE | Code anchor | Survival proof or removal |
|---|---|---|---|
| Related selection/ranking/excerpt | KEEP | knowledge_docs.py:KnowledgeDocs.related | All three consumers need the exact same semantics; no duplicate ranker |
| Relative source path predicate | MERGE | lifecycle.py:safe_source_path; knowledge_depth.py:safe_path; knowledge_docs.py:_source_path | Canonical shape policy owns retrieval and evidence paths; compatibility aliases preserve the existing callable |
| Depth format constants/parser | KEEP | lifecycle.py:DEPTH_BLOCK/DEPTH_FACETS/depth_sections | KB proof implementation aliases canonical format; no copied regex/facet set |
| Policy metadata writer | KEEP | knowledge_coverage.py:feature_metadata | Two init stages plus current migration share one producer; preserves body |
| SDK related reference projection | KEEP | sdk/v1/direct.py:DirectClient.plan | Uses existing DocumentRef and frozen read contract; representation differs from MCP dictionary |
| Direct followup projection | KEEP | direct_routing.py:direct_review_plan | Caller owns review budget, retrieval owner owns truncation; no second truncation/default |
| Agent JSON tool/rendering | KEEP | knowledge.py:_repo_docs_tool; runner.py:run_agent_step | Tool and prompt are two existing consumer representations; same related result |
| Offline acceptance CLI | KEEP | tools/audit_review_retrieval.py:main | Measures current public Direct behavior; no runtime cache/background scheduler |
| Stable-rule definition format extension | KEEP | check_review_report.py:RULE_DEFINITION_RE | Existing general/review/rules.md uses heading IDs; two-line extension preserves old definitions and duplicate checks |

### Net result

Scope subtraction: zero removals required; every retained behavior/file/test maps to requested retrieval/workflow scope. Architecture subtraction: zero further safe deletions identified; the format constants and path predicate were merged into their shared owner and consumers reuse one selection implementation. The final fix deletes the former standalone knowledge_depth.safe_path implementation; its import alias preserves the API. Correctness F1 is not counted as subtraction.

## Resolved finding

F1 is closed after the entire current diff was re-reviewed. The shared depth reader now requires a 64-hex bound evidence digest and a safe relative path. The canonical safe_source_path helper is also the object exported through the former init/audit safe_path name and retrieval alias; identity was checked in the live interpreter. A valid models block remains accepted; removing its digest, replacing the digest with a non-hex value, or changing its path to absolute/traversing forms while recomputing the enclosing block hash all cause rejection. Four new regressions exercise the actual related consumer with intact enclosing hashes, so malformed proof shape is independently covered. No upstream I/O or second parser/normalizer was added.

The checker validation boundary is closed: the two-line definition regex extension recognizes ##/### IDs alongside existing bold/table syntax. Integration regressions verify the same report succeeds with heading definitions and mixed duplicate definitions still fail.

## Open findings

- None. No actionable findings remain in the reviewed current diff.

## Completion

Correctness and design/subtraction are clean for the reviewed source diff; no new actionable finding after the F1 fix. The read-only body comparison again verified all 156 metadata pages preserve their baseline bodies exactly. This review ran no broad pytest or duplicate catalog audit.

Parent-provided validation evidence: Python 3.12 / PyYAML 6.0.3 / pytest 9.1.1 / mcp 1.30, PYTHONPATH=src, both knowledge validators, doc links/citations and SPEC freshness passed. The frozen-tree `python -m pytest -q` passed before the final proof guard; final representative proof/depth/SDK/Agent tests and checker integration tests passed after it. Final whole-tree CI remains pending and belongs to the publisher; the earlier full-suite result is not claimed to cover subsequent changes.

The inspected refreshed acceptance report records description+paths 79/79 feature hits and 77/77 available depth hits, paths-only 77/79 feature hits and 75/77 depth hits (ttse and worktree ambiguous), maximum 5,571 content characters and median 1,962 ms. Its knowledge tree hash is ceed356ae274258689ddff368713fa6d60314e41e1e523dcc8f125b5119f48f0 and policy hash c23eefb5057bfdff6a7be55cd663b5e9dc636cc2d76741b39d875088a8216661. The publisher is refreshing the identical corpus after the proof guard to record final provenance; this review does not wait for that run or remote CI. Catalog delivery is distinct from real PR recall/RQS, which remains unmeasured.

OWNER RULE COVERAGE: knowledge/general/review/rules.md: 7/7 stable IDs inventoried — 7 pass / 0 fail / 0 missing evidence / 0 not applicable
SUBTRACTION VERDICT: PASS — all retained scope has a concrete consumer; one retrieval, metadata, format and source-path owner; compatibility aliases retain existing public calls
CORRECTNESS VERDICT: PASS — F1 resolved; current complete source diff has no actionable findings; final full-tree CI remains an explicit publisher verification boundary
AUDITS RUN: coverage,ingress,producer-consumer,source-consumer,duplication,layering,edge-cases,surface-area — 0 findings (0 P0, 0 P1, 0 P2)
