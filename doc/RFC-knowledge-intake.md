# RFC — Knowledge intake: merged-PR and bugfix learnings return as reviewed knowledge PRs

- Status: implemented, shadow-first and default-off — copilot side in
  PR #110 (`pr.harvest_debug_knowledge`), reviewbot side in
  zuiho-kai/omni-reviewbot#21 (intake ledger) and #22 (daily distiller)
- Owner: knowledge plane (`knowledge/`, `AGENTS.md` contract) on this side;
  `omni_reviewbot.knowledge_intake` / `knowledge_distiller` on the bot side
- Evidence: `test/test_knowledge_harvest.py` (step + executor/resume e2e),
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

- The model **only proposes**: it reads a dedicated work clone of this repo
  (never the live checkout the Direct bridge imports) and returns
  catalog-constrained structured output — target `rules.md` page from the
  scanned catalog, a new auditable rule id, one complete section in the
  page's own language and format, cited sources. Source events are fenced
  as `<untrusted_data>`; instructions never come from them.
- Code **applies mechanically and append-only**: new sections plus an
  `updated:` frontmatter bump. Existing sections are never rewritten —
  merging and pruning stay human/curator work. Proposals that miss the
  catalog, collide with an existing rule id, or fail shape checks are
  dropped and counted.
- The **validators are the gate**: `check_knowledge_tree.py` and
  `check_wiki_lint.py` run in the clone; a failure — or a missing
  validator — fails the batch closed. Rows stay `pending` and retry on the
  next daily batch, bounded by an attempt cap that parks poison rows
  visibly as `error`. The vllm-omni release audit runs in CI on the PR, as
  it does for any knowledge edit.

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

## The cross-repo contract

The drop record is the only coupling between the two repos:

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

## Fit with this repo's invariants

- **Repo neutrality**: the harvest step contains no repo literal; the drop
  directory is plain settings, empty by default.
- **State via `state_updates` / executor restore**: the step consumes the
  executor-maintained `outputs` map, which the resume path restores from
  `progress.json` — pinned by the crash-then-resume e2e test.
- **Read-wide/write-narrow**: the tree is still written only by humans
  merging PRs; the automation's write surface is a drop directory and a
  fork.

## Alternatives considered

- **Per-event PRs** — cleanest provenance, but several PRs a day on an
  active repo turns the promotion gate into review spam. Daily batch with
  skip-if-empty bounds the load; provenance lives in the PR body instead.
- **Direct writes to the tree (or pushing to this repo)** — rejected
  outright: it deletes the human promotion step the knowledge plane is
  built on, and would require granting the bot write access here.
- **Copilot-hosted distiller** — this repo has no daemon; the reviewbot
  already runs a poll loop with maintenance gating, budgets, and crash
  recovery, so the scheduled half lives there and this repo stays a
  library plus one playbook step.
- **Stopping at skill candidates / debug memory** — that is where learnings
  already go today; both are run-scoped proposals with no path into the
  human-curated tree. This design is that missing path, not a replacement
  for them.

## Rollout

1. Reviewbot: `KNOWLEDGE_INTAKE_ENABLED=true` — merged-PR recording plus
   daily shadow batches; inspect artifacts and `knowledge-batch` output.
2. Wire the bugfix channel: point this repo's `KNOWLEDGE_INTAKE_DIR` and
   the reviewbot's `COPILOT_INTAKE_DIR` at the **same directory** (v1
   assumes a shared host). Without this pair, everything else works but
   `pr_debug` learnings are silently absent from batches — both values
   default to empty/off.
3. Create the bot's fork of this repo; set `KNOWLEDGE_FORK_SLUG`.
4. `KNOWLEDGE_PR_ENABLED=true` under `POST_MODE=review` — PRs start; every
   one is reviewed like any other knowledge edit.

Rollback at any stage is turning the flag off; nothing in the tree changes
without a merged PR.
