# RFC — Knowledge intake: merged-PR and bugfix learnings return as reviewed knowledge PRs

- Status: implemented, shadow-first and default-off — producer intake in
  PR #110 (`pr.harvest_debug_knowledge`), provider domain contract in public
  SDK 0.2.0 (`infermatrix_copilot.sdk.v1.KnowledgeCurator`), and ReviewBot
  orchestration in zuiho-kai/omni-reviewbot#21/#22
- Owner: this repo uniquely owns knowledge policy, catalog/prompt/proposal/apply
  semantics and validators; ReviewBot owns evidence/model/Git/ledger/publication
  orchestration and consumes the versioned public SDK only
- Evidence: `test/test_knowledge_harvest.py` (step + executor/resume e2e),
  `test/test_sdk_knowledge_v1.py` (provider boundary, rollback and locking),
  reviewbot `tests/test_knowledge_intake.py`, `tests/test_knowledge_distiller.py`,
  `tests/test_e2e_knowledge_flow.py` (cross-repo contract pinned)

## Motivation

The knowledge tree has a written intake contract — PR-learning produces only
executable rules in the nearest owner's `rules.md`, raw material is deleted,
two validators plus the release audit gate every batch — but no automated
feeder. Learnings evaporate at exactly the two moments they are freshest:

1. **A vllm-omni PR merges.** The review discussion and final diff often
   carry a generalizable lesson (a contract the reviewer had to rediscover,
   a failure class the diff fixed), and today nobody distills it.
2. **A copilot `pr_debug` run lands a fix.** The agent produced a verified
   root cause and fix; `record_debug_memory` keeps it in the run-scoped
   debug store, but nothing carries it into the human-curated tree.

The constraint that shapes everything below is the knowledge plane's safety
model: **agents propose, humans promote**. Any automation that writes the
tree directly would break it. A pull request against this repo *is* the
promotion gate — review and merge are the human act — so the design's job is
to deliver well-formed, validator-clean proposals as PRs, and nothing else.

## Design

Three stages, deliberately decoupled so each can fail without losing events.

### 1. Recording (cheap, every watch cycle)

- **Every merged PR counts — literally.** The reviewbot scans GitHub's
  closed pulls directly (drafts and never-tracked PRs included) with a
  durable cursor in GitHub's own timestamp format; rows are unique per
  source, so overlapping windows and crashes re-read but never drop or
  duplicate. It does not trust its own `tracked_pulls`.
- **Bugfix runs arrive as drop files.** This repo's
  `pr.harvest_debug_knowledge` step (end of the `pr-debug` playbook, risk
  `knowledge`) writes one JSON record per run into
  `knowledge_intake_dir` (`KNOWLEDGE_INTAKE_DIR`) — but only when the fix
  actually landed: a real, non-dry-run `ci.push` and at least one fix with
  both root cause and verification (the same bar as debug memory). The
  step is fail-open by design: unset directory, dry-run, zero verified
  fixes, or a write error each no-op with an honest summary — closing the
  learning loop must never fail the landed fix.
- Records land in a `knowledge_intake` SQLite table, `pending` until a
  batch consumes them.

### 2. Distillation (expensive, at most once a day)

- ReviewBot converts pending rows into typed `KnowledgeEvidenceEvent` values
  and one bounded `KnowledgeEvidenceBatch`. It creates `KnowledgeCurator`
  over a dedicated work clone of this repo — never the immutable knowledge
  resources shipped inside the runtime wheel — then asks the SDK to build the catalog-constrained
  prompt and strict JSON schema. ReviewBot invokes the configured model; the
  model **only proposes**.
- The SDK treats all source events and model output as untrusted. Evidence is
  fenced as `<untrusted_data>`; catalog membership, proposal shape, rule ID,
  one complete heading, source citations, duplicate IDs and target-page SHA
  are checked mechanically. Accepted proposals receive content-addressed IDs;
  rejected model indexes and stable reasons are returned to the host.
- `KnowledgeCurator.apply()` **applies mechanically and append-only**: complete
  new sections plus the one `updated:` frontmatter bump. Existing sections are
  never rewritten. The SDK serializes writers across threads/processes and
  rechecks target SHAs after acquiring the lock, so a stale daily worker cannot
  overwrite a concurrent edit.
- The **validators are the gate**: the SDK runs exactly
  `check_knowledge_tree.py`, then `check_wiki_lint.py`, inside the clone. A
  missing validator fails before any write; a failed, timed-out or unlaunchable
  validator restores every target page byte-for-byte and raises a typed error.
  ReviewBot leaves rows `pending` for retry, bounded by its attempt cap. The
  vllm-omni release audit additionally runs in CI on the PR, as for any
  knowledge edit.

### 3. Publication (fork-based, double-gated)

- The date-scoped branch (`knowledge/intake-YYYY-MM-DD`) pushes to the
  **bot's fork**; the PR targets this repo. The bot holds no write access
  here — merging the PR is the human promotion gate, and the PR body lists
  every source event plus the validator transcript.
- Shadow is the default: the batch stays a local commit plus an artifact
  under the bot's `state/artifacts/knowledge-intake/`. Posting requires
  `POST_MODE=review` **and** `KNOWLEDGE_PR_ENABLED` with a configured
  fork — the same double-gate shape as every outward write on both sides.
- The automatic cadence yields at most one PR per day. The distiller
  reuses the day-branch's **open** PR when one exists; if the day's PR was
  already merged or closed, a manual same-day rerun with new rules opens a
  follow-up PR on the same branch (showing only the new commits) — a
  deliberate consequence of trusting GitHub's open-PR state over local
  bookkeeping. Same-day reruns build on the day's branch (never
  reset it) and re-attempt publication of anything committed but
  unpublished — so a manual `knowledge-batch` retry after a failed push or
  PR creation recovers the same branch, and a no-rules retry can never
  mark rows done while their committed batch sits unpublished on the same
  branch. **The recovery boundary is the day**: the automatic cadence
  retries ~24h later under a fresh date branch, re-distilling the still-
  pending rows from upstream state. Rows are never lost, but a prior
  day's committed-yet-unpublished branch is not resumed — at worst it
  survives as a dead branch on the fork (no PR references it). Cross-day
  branch recovery was considered and skipped: it trades real complexity
  for saving one day of latency on an already-daily loop.

## The cross-repo contracts

There are two narrow, versioned seams; neither repo imports the other's private
modules.

The first is the producer drop record written by a Copilot run and consumed by
ReviewBot:

```json
{"run_id": "...", "repo": "owner/repo", "pr": 123, "kind": "bugfix_run",
 "title": "...", "groups": [{"signature": "...", "jobs": [],
 "root_cause": "...", "fix_summary": "...", "verification": "...",
 "files": []}], "created_at": "..."}
```

- `repo` carries the full GitHub identity from `repo_full_names` when
  configured; the reviewbot normalizes alias-form values to its watched
  slug so rows can never strand under an unqueryable key.
- Each side pins the shape in its own tests: the producer here in
  `test_knowledge_harvest.py` (field-level assertions on the written
  record), the consumer in the reviewbot's `tests/test_e2e_knowledge_flow.py`
  via a **deliberately duplicated** fixture — the repos share no code, so
  there is no single fixture both import. A change on one side breaks that
  side's test but not the other's; the contract therefore changes only in
  lockstep, with this section as the reference.

The second is the installed public Python SDK used by ReviewBot's adapter. The
call order is deliberately small:

```python
curator = KnowledgeCurator(dedicated_clone)
batch = KnowledgeEvidenceBatch(...)
prompt = curator.build_prompt(batch)
model_json = reviewbot_model_call(
    prompt, output_schema=curator.proposal_schema(max_rules=batch.max_rules)
)
validation = curator.validate_proposals(model_json, batch)
result = curator.apply(validation)
```

All values crossing that seam have lossless `to_dict()` projections and contain
document IDs, never provider absolute paths. ReviewBot uses `accepted_indexes`
and `rejected_indexes` to account for model rows. Malformed requests raise
`InvalidRequestError`; catalog/integrity/stale-writer failures raise
`KnowledgeCurationError`; validator failures raise `KnowledgeValidatorError`
whose `.result` records validator status/output and whether bytes were rolled
back. ReviewBot catches these public errors and owns retry/artifact decisions.

The SDK explicitly has no clone, model, ledger, commit, push, pull-request or
scheduling operation. Conversely, ReviewBot has no local catalog/prompt/parser/
apply/validator implementation: knowledge policy changes are released here and
adopted by pinning a new wheel version.

## Fit with this repo's invariants

- **Repo neutrality**: the harvest step contains no repo literal; the drop
  directory is plain settings, empty by default.
- **State via `state_updates` / executor restore**: the step consumes the
  executor-maintained `outputs` map, which the resume path restores from
  `progress.json` — pinned by the crash-then-resume e2e test.
- **Read-wide/write-narrow**: the tree is still written only by humans
  merging PRs; the automation's write surface is a drop directory and a
  fork.
- **Single policy owner**: knowledge domain rules live behind this repo's
  public SDK; the ReviewBot adapter is orchestration-only. Runtime state and
  publication credentials never flow into the provider library.

## Alternatives considered

- **Per-event PRs** — cleanest provenance, but several PRs a day on an
  active repo turns the promotion gate into review spam. Daily batch with
  skip-if-empty bounds the load; provenance lives in the PR body instead.
- **Direct writes to the tree (or pushing to this repo)** — rejected
  outright: it deletes the human promotion step the knowledge plane is
  built on, and would require granting the bot write access here.
- **Copilot-hosted daemon/orchestrator** — rejected: this repo has no daemon;
  ReviewBot already runs a poll loop with maintenance gating, budgets and crash
  recovery. **Copilot-owned domain library** is the chosen split: policy stays
  beside the governed knowledge tree without moving scheduling or publication.
- **Duplicated distillation helpers in ReviewBot** — rejected: catalog, prompt,
  validation and append logic would drift independently from `knowledge/`
  governance. The versioned SDK makes that dependency explicit and testable.
- **Stopping at skill candidates / debug memory** — that is where learnings
  already go today; both are run-scoped proposals with no path into the
  human-curated tree. This design is that missing path, not a replacement
  for them.

## Rollout

1. Build and pin InferMatrixCopilot SDK `0.2.0` in ReviewBot; its adapter must
   import only `infermatrix_copilot.sdk.v1` and exercise the full call order in
   a temp-clone integration test.
2. ReviewBot: `KNOWLEDGE_INTAKE_ENABLED=true` — merged-PR recording plus daily
   shadow batches; inspect typed curation results, artifacts and
   `knowledge-batch` output.
3. Wire the bugfix channel: point this repo's `KNOWLEDGE_INTAKE_DIR` and
   the reviewbot's `COPILOT_INTAKE_DIR` at the **same directory** (v1
   assumes a shared host). Without this pair, everything else works but
   `pr_debug` learnings are silently absent from batches — both values
   default to empty/off.
4. Create the bot's fork of this repo; set `KNOWLEDGE_FORK_SLUG`.
5. `KNOWLEDGE_PR_ENABLED=true` under `POST_MODE=review` — PRs start; every
   one is reviewed like any other knowledge edit.

Rollback at any stage is turning the flag off; nothing in the tree changes
without a merged PR.
