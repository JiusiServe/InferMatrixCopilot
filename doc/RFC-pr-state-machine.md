# RFC — PR state machine: maintainers join when the PR is almost ready

- Status: implementation in progress; comment-only plan approved 2026-09-22
- Owner: the management bot (`omni-reviewbot`) owns the state of record, the
  reconciler, the nightly sweep, every GitHub write and the dashboard; this
  repo owns the per-head verdict contract it consumes (review verdict,
  finding severities and dispositions, quality readiness) and ships it in the
  versioned public SDK, as in [`RFC-knowledge-intake.md`](RFC-knowledge-intake.md)
  and the roadmap RFC.
- Parent: InferMatrixCopilot #116 (PR lifecycle umbrella) and its children
  #117 owner routing, #120 stale reminder, #121 CI closed loop, #122 perf
  questions — all four are live on `vllm-project/vllm-omni` behind flags.
  This RFC is the layer that turns those four independent loops into one
  lifecycle. It adds automatic reviews while preserving the prohibition
  on automatic PR state changes. The comment-only constraint below governs
  every runtime path.
- Evidence: `vllm-project/vllm-omni` as of 2026-09-21 (GitHub search API and
  the bot's live `/api/status`). Every number is reproducible from those two
  sources. These are historical counts, not rollout acceptance measurements.

## Motivation

The bot already runs six loops against vllm-omni, and none of them knows what
the others did. A PR's situation today is the join of twelve independent
vocabularies (GitHub state, review job status, review attempt state, owner
assignment outcome, CI lifecycle kind, comment claim state, note state, stale
window, applied-label state, review verdict, quality verdict, run state) with
roughly sixty values between them. The dashboard reconstructs two buckets in
SQL ("resolved" and "attention"); queued, running, blocked, timed-out and every
reroute status fall into neither and are invisible on the trend chart.

Maintainer engagement is the visible cost:

| Fact (2026-09-21) | Value |
| --- | --- |
| Open PRs / of which draft | 1,236 / 199 |
| Open non-draft PRs with no update for 7 / 14 / 30 days | 439 / 130 / 28 |
| PRs opened in the last 7 days | 334 (≈48 per day) |
| PRs merged in the last 7 days | 174 |
| PRs closed unmerged in the last 7 days | 12 |
| Reviews the bot has ever posted | 135 (86 of the last 105 attempts) |
| Owner-routing comments posted | 1,598 |
| Stale reminders posted / stale PRs in the queue | 505 / 715 |
| `ready_to_merge` pages live right now, all to one login | 17 |

Three structural gaps produce that table:

1. **Review is opt-in by mention.** A review runs only when an authorized
   person (trusted reviewer, module owner, or collaborator) comments the bot's
   handle (`README.md` "监控规则": later commits never re-trigger, drafts are
   skipped). So the person the bot is meant to relieve has to act first, and
   135 reviews over ~1,000 PRs is the result.
2. **Nothing composes the signals.** `ready_to_merge` is exactly GitHub's
   `mergeable_state == "clean"` (`lifecycle.py:105`), so a maintainer is paged
   on a PR the bot itself flagged as broken, or on one it never looked at. The
   stale reminder fires after 7 days and then nothing happens: 715 PRs sit in
   the stale queue with 505 reminders posted and no next step.
3. **The bot cannot move a PR.** It may comment, and it may add up to three
   topic labels to an unlabeled PR. It cannot mark a PR as needing changes,
   park it, or close it, so every PR that stops moving waits for a human to
   notice.

## Constraint: the bot has no GitHub write authority

Decided 2026-09-22, and it governs everything below. **The bot never writes
GitHub's label field, never converts a PR to draft, never closes or reopens
one, and never posts a blocking review.** It may post comments and
`COMMENT` reviews; that is its whole outward surface.

This is not a permission GitHub can express. Posting a review requires
`pull_requests: write`, and that same permission grants labelling, draft
conversion and closing — there is no setting that allows one and forbids the
others. So the constraint is ours to keep, which means it has to be
structural: the write methods are removed from the client rather than
hidden behind a flag, because a flag is a thing somebody can turn on.

**Every label in this document still exists — in our ledger, not on GitHub.**
The projection keeps computing each state, the labeler keeps inferring the
repository's content labels (`new model`, `diffusion`, `tts`, `omni`, `VLA`)
from changed files, and both are stored and shown on our own board. What
changes is only where they are written down. A maintainer reading GitHub
sees no state from us; they see comments, and the board has the rest.

What this costs, plainly: **the bot can no longer act on a PR, only talk
about it.** Parking and closing become recommendations a person carries out.
The goal below — one maintainer touch per merged PR — is not reachable under
this constraint, because every state change is now a human action. What
survives is the part that was always the most valuable: a maintainer is told
exactly when a PR is worth their attention, instead of finding out by
reading the list.

## Goals and non-goals

Goal, as originally written and now bounded by the constraint above:
**one maintainer touch per merged PR — the merge decision.** Under no write
authority this is the ceiling rather than the target, since parking and
closing are human actions; the reachable goal is that a maintainer is paged
once, at the right moment, and never has to scan the list. Everything
before that (routing, review, CI nudges, re-review after pushes, inactivity
handling) is automatic, and a maintainer is paged exactly once, when the PR
passes a defined ready gate.

Non-goals:

- The bot never merges. Ever. Not behind a flag.
- The bot never approves. A bot `APPROVE` reads as a merge recommendation and
  GitHub counts it toward required approvals; the bot's positive signal is the
  ready page and the board, nothing else.
- The bot never posts `REQUEST_CHANGES` either. A blocking verdict changes
  what a person is allowed to do with their PR, which is the same kind of
  authority as closing it, and clearing a wrong one would need a dismissal
  write the bot no longer has.
- No new model calls beyond the reviews the sweep schedules. The state
  projection is pure bookkeeping over ledgers the bot already keeps.
- Other adapters stay opted out until they ask (`LIFECYCLE_REPOS` semantics).

## The state machine

### States

A PR has exactly one state at a time. The state is a **projection of the
current head**: the reconciler recomputes it every cycle from evidence and
writes it down (see [Storage](#storage)). A push re-enters `under_review`.

| # | State | Meaning | Who acts | Our label (ledger, not GitHub) |
| --- | --- | --- | --- | --- |
| 1 | `new` | Seen; owner routing not yet run (≤ 1 cycle, 120 s) | bot | — |
| 2 | `needs_owner` | Routing found no owner and no review has run yet | bot (review still proceeds) | `bot:needs-owner` |
| 3 | `owner_routed` | Owner @-mentioned; awaiting the first review sweep | bot | `bot:under-review` |
| 4 | `under_review` | Current head has no completed review, or CI is still pending on a reviewed head | bot | `bot:under-review` |
| 5 | `changes_requested` | Completed review on this head has an open blocker/major finding, or the PR has merge conflicts | author | `bot:changes-requested` |
| 6 | `ci_failing` | A watched/required check is red on this head | author | `bot:ci-failing` |
| 7 | `ready_for_maintainer` | Ready gate passed; delivery is tracked separately | maintainer | `bot:ready-for-maintainer` |
| 8 | `stale` | ≥ 7 days without human activity | author | `bot:stale` |
| 9 | `parked` | ≥ 14 days without human activity; draft/closure suggestions may be due | author | `bot:parked` |
| 10 | `draft` | Any GitHub draft; unmanaged, no clocks (today's behaviour) | author | — |
| — | `closed` | Merged or closed on GitHub. Always a human act now, so terminal while GitHub reports it closed | — | — |

Ten live states plus the terminal one.

`parked` and `draft` no longer differ by who drafted the PR, because the bot
drafts nothing. `parked` means "idle for at least 14 days" whether or not a notice has
been delivered; if a person does convert it, GitHub reports a draft and
the PR leaves the clocked states the same way an author's draft does. The
`parked_at` column records when we said so, not when anything happened.

### Projection order

First match wins. The order encodes "what is the most urgent thing a person
must do", so it is also the kanban column order. The projection reads
**evidence only** (GitHub facts, ledger rows, the clock); it never reads its
own previous output or whether an action was posted. Whether the notice for a
boundary has actually been posted is a *sub-status* (`action_pending` /
`action_done`), so a failed post cannot hide a state. The actions themselves
— drafting, closing — are no longer ours, so `action_done` means the notice
went out, never that the PR moved.

```text
closed            GitHub state is MERGED or CLOSED                (always a human act)
draft             GitHub isDraft                                (whoever drafted it)
parked            managed AND clock ≥ PARK_DAYS (14)           -- entry action: 14-day notice
                                                               -- and at clock ≥ CLOSE_DAYS (30): 30-day notice
stale             managed AND clock ≥ STALE_PR_DAYS (7)        -- entry action: 7-day reminder
new               no assignment outcome recorded for this PR   (≤ 1 cycle)
needs_owner       no review attempt on any head, sweep has not claimed this head, assignment = no_owner
owner_routed      no review attempt on any head, sweep has not claimed this head, owner assigned
ci_failing        required/watched check red on current head          (lifecycle kind ci_failed)
changes_requested completed review on head has an open blocker/major,
                  OR mergeable_state == dirty
under_review      no completed review attempt on current head (sweep-claimed, queued, running, or pushed since),
                  OR CI incomplete/unknown on a reviewed head           (lifecycle kind pending)
ready_for_maintainer
                  ready gate passed                                    (lifecycle kind ready_to_merge)
```

```text
under_review      (fallback) any evidence combination not matched above
  (unclassified)                                               -- counted on the dashboard, no action
```

where `clock = now − last_human_activity_at`, and "managed" means open,
not an author draft, not carrying any `STALE_EXEMPT_LABELS` label. The
guard applies to the clock states and to their artifacts alike: an exempt
PR with 14 idle days is not `parked`, is never notified, and keeps flowing
through the head-bound states (it is reviewed by the sweep and can reach
`ready_for_maintainer`); an exempt PR that was `parked` before the label was
added simply stops being `parked` on the next projection, with nothing to
undo, because nothing was done to it. The three discovery
states are mutually exclusive with `under_review` by construction: they hold
only while no review attempt exists on any head *and* the sweep has not
claimed the current head; the sweep's claim is the event that moves a PR out
of them. A PR that is red or conflicting before its first review still shows
`owner_routed`, and the CI/conflict nudge is sent from there (the transition
table keys nudges on head, not on state).

Two rules make the projection total and keep the clock states consistent
with GitHub:

- **`closed` comes from GitHub alone.** A PR is closed when a person closes
  it. The day-30 boundary is a notice, not a state: the PR stays `parked`
  and the board shows that its close notice went out. An earlier draft
  projected `closed` from the clock and closed the PR as the entry action;
  with no close authority that state would describe something that never
  happens.
- **`parked_at` means "we said this should be parked", not "it is drafted".**
  Nothing verifies a draft state against the timeline any more, because the
  bot no longer owns any draft. If a person does convert the PR, GitHub
  reports `isDraft` and it leaves the clocked states exactly as an author's
  own draft does.
- **There is no resume path.** A parked PR that gets human activity simply
  has its clock reset and re-enters `under_review` on the next projection.
  The `resume_pending` sub-status existed to carry an un-draft mutation, and
  there is no mutation to carry.
- **A final fallback** maps anything unmatched to `under_review` with
  sub-status `unclassified` and increments a dashboard counter, so an
  unforeseen evidence combination is visible instead of stateless.

### Actions: desired set versus live set

The state is a projection for people. **Writes are not driven by state
transitions at all.** Each cycle, for every visited PR, the reconciler
computes the *desired set* of bot artifacts for the current evidence and
diffs it against the *live set* it recorded, exactly as `lifecycle.py`
already does for its two note kinds ("the reconciler moves rows in BOTH
directions — retract when the state leaves, restore in place when it
returns, supersede when the head moves"). A transition may happen with no
write, and a write may happen with no transition.

Desired artifacts, each with the evidence that wants it and its dedupe key:

| Artifact | Wanted while | Key | When no longer wanted |
| --- | --- | --- | --- |
| owner @-mention | PR seen, routing done | PR + head + routing digest (existing) | never retracted |
| conflict comment | `mergeable_state == dirty` on current head | PR + head + `conflict` | head moved → superseded; clean again on same head → retracted |
| CI-failed comment | required/watched check red on current head | PR + head + `ci_failed` (existing) | head moved → superseded; green on same head → retracted (existing) |
| ready page | a `ready_entry_seq` has been entered and its page has not been delivered | PR + `pr_state_epoch` + `ready_entry_seq` | delivered → no longer wanted; never retracted once sent |
| 7-day reminder | clock ≥ 7 d | PR + window start (existing) | never retracted; a new window gets a new key |
| 14-day park notice | clock ≥ 14 d, managed | PR + window start + `park` | never retracted; a new window gets a new key |
| 30-day close notice | clock ≥ 30 d, managed | PR + window start + `close` | never retracted; a new window gets a new key |
| review job on current head | head unreviewed, sweep time reached, budget left | PR + head + `review` (existing attempt uniqueness) | head moved → attempt `superseded` (existing) |
| exactly one state label **in our ledger** | always, equal to the projected state | PR + state | state changed → the row is updated; nothing is written to GitHub, so nothing can be fought over |

Two things are gone from this table and are worth naming, because earlier
drafts turned on them. There is no `REQUEST_CHANGES` review, so none of the
machinery it needed survives either — no `block_generation` counter, no
body-edit-in-place, no dismissal ordering, no "one review per blocking
interval". And there is no draft conversion, close or reopen, so the
`park`/`close` rows are notices rather than actions: nothing is retracted
because a sentence already said to somebody cannot be unsaid, and the un-park
and reopen paths do not exist.

**The ready page is keyed on the entry, not the head.** `ready_entry_seq` is
a counter on the `pr_state` row that increments when the projection moves
into `ready_for_maintainer` from anything else. Keying on the head would
page again for every push to a finished PR; keying on the PR alone would
never page again after CI broke and was fixed. The entry is the event a
maintainer actually cares about.

**The page is wanted while the entry is undelivered *and* the PR is still
ready.** The entry is a moment and the transition row is written
immediately, so a wanting condition phrased as "entered ready this cycle"
would evaporate before a post that failed on budget could be retried, and
that page would be lost silently — the one message this design exists to
send. `ready_paged_seq` records the last sequence actually delivered, and a
page is wanted while `ready_entry_seq > ready_paged_seq` **and the
projection still says `ready_for_maintainer`**.

Both halves are needed. Without the first, a budget failure loses the page.
Without the second, a page that failed on Monday could be sent on Tuesday
for a PR that has since been pushed to or blocked — announcing "ready for a
maintainer look" about an unreviewed or failing PR, which is exactly the
false-ready the gate exists to prevent. When readiness is lost with a page
still pending, the entry is **cancelled**: `ready_paged_seq` is advanced to
`ready_entry_seq` and a transition row records "page cancelled: no longer
ready". Should the PR become ready again later, that is a new entry and a
new sequence. A restart mid-post is covered by the claim protocol as
elsewhere.

**A rung already passed is skipped.** The three idle notices share one
ladder, and on any given pass only the highest rung whose clock has passed
is wanted. A PR idle 40 days when the ladder turns on wants the 30-day
notice and not the other two; without this, enabling the feature walks 715
PRs up three rungs each.

Consequences the reviewer's two sequences must satisfy, and which are
acceptance cases below:

- A PR sitting in `changes_requested` for a conflict whose nightly review
  then finds a blocker: the state does not change and no new artifact is
  wanted, because the findings are published by the review itself. The
  blocker shows on the board and holds the ready gate; nothing is posted
  twice.
- A `ready_for_maintainer` PR whose CI turns red on the same head: the
  projection goes straight to `ci_failing` and the CI-failed comment is
  posted. The ready page is not retracted — it was a notification, and it
  was true when sent. If CI is fixed and the PR returns to ready,
  `ready_entry_seq` advances and a second page is sent, which is the
  behaviour a maintainer wants.
- A PR that is `stale` and then pushed: the reminder is kept (never
  retracted), our state label changes in the ledger, and the review job for the new head is
  desired at the next sweep.

Every post, and every retraction, goes through the claim protocol with the
key in the table; a key includes the *event* it answers (window start, head
SHA, `ready_entry_seq`), never just the PR, so a PR that goes ready, breaks
and goes ready again gets two distinct page claims, while a re-run against
the same evidence derives the same key and is a no-op.

Note the asymmetry: `stale` and `parked` win over everything below them
because time-based states describe the *author*, not the head. A stale PR that
happens to be CI-green is still stale; a push clears both in one cycle because
a push is human activity.

### Transitions

| From → To | Trigger | GitHub side effect | Dedupe key |
| --- | --- | --- | --- |
| `new` → `owner_routed` / `needs_owner` | first cycle after discovery | owner @-mention comment (existing #117 loop) | PR + head + routing digest (existing) |
| `owner_routed` / `needs_owner` / any → `under_review` | nightly sweep claims the head, or a push lands | none | — |
| `under_review` → `changes_requested` | review completes with open blocker/major | none beyond the review the publisher already posts, as a `COMMENT` with findings inline | — |
| `under_review` → `changes_requested` | `mergeable_state == dirty` | one comment asking for a rebase, with base SHA | PR + head + `conflict` |
| any → `ci_failing` | required check red | one comment @author (+ distinct last pusher) with job, SHA, link (existing #121) | PR + head + `ci_failed` (existing) |
| `changes_requested` / `ci_failing` → `under_review` | push | lifecycle note superseded (existing) | — |
| `under_review` → `ready_for_maintainer` | ready gate passes | one comment to the routed owner, or down the fallback chain when there is none: "ready for a maintainer look", verdict badge, disputed-finding count | PR + `pr_state_epoch` + `ready_entry_seq` |
| `ready_for_maintainer` → `under_review` | push, or CI turns red, or a new blocker | none; the page stands as sent | — |
| any managed → `stale` | day 7, no human activity | one reminder @author (+ coordinator) (existing #120) | PR + inactivity window start (existing) |
| `stale` → `parked` | day 14, still no human activity | one comment: "no activity for 14 days; consider converting this to a draft" | PR + window start + `park` |
| `parked`, day 30 | day 30, still no human activity | one comment: "no activity for 30 days; consider closing this" — the state does not change, because only a person can close | PR + window start + `close` |
| `stale` / `parked` → `under_review` | any human commit, comment or review | none; the clock resets and the ladder starts over on the next window | — |

Every row's side effect is a comment or nothing. The bot converts no drafts,
closes nothing, reopens nothing and dismisses nothing, so the rows that used
to describe those actions are gone rather than flag-gated.

No GraphQL client is needed. It was in this design only for
`convertPullRequestToDraft` and `markPullRequestReadyForReview`, neither of
which the bot may call, so the REST path remains the whole of it and
`node_id` need not be stored.

Everything the table posts goes through the existing claim protocol
(`comment_claims.py`: shadow → claimed → posted / failed / withdrawn, lease
recovery, orphan adoption after a crash). Nothing new is invented for writes.

### Ready gate

`ready_for_maintainer` requires all of, on the current head:

1. not draft, not parked, not stale;
2. `lifecycle.py` supplies `ready_verified == True` for this head: the
   required-check set is known, required and watched checks are present,
   complete and passing, pagination is complete, and required app identities
   match.
   Missing or pending evidence never counts as green;
3. `mergeable_state == "clean"`;
4. a completed review attempt on this head;
5. **no undisputed open blocker/major finding.** Published blockers remain
   in the findings ledger across heads. Only a complete, head-bound recheck
   of the carried set with `outcome == "fixed"` closes a finding. A
   `still_affected` or `unverified` answer leaves it unresolved; omission,
   malformed answers and incomplete coverage cannot resolve it. The request
   and result shapes are defined in [the SDK contract below](#sdk-boundary).

   An author can dispute a finding with a 👎 reaction on its bot comment
   or a reply in its thread. A dispute removes that finding from the ready
   gate without proving it fixed. Disputed findings stay in the ledger and
   are counted on the ready page so the maintainer sees the disagreement.
   Review evidence and dispute state are stored separately; withdrawing a
   dispute restores blocking status unless a valid explicit fix remains.

   **Disputes are an evidence source with their own deadline, not a
   by-product of the next review.** Thread replies arrive through the
   repo-wide comment feed the reconciler already reads every cycle.
   Reactions have no feed, so every PR with ≥ 1 **unresolved** blocker/major
   — open *or disputed*; only `fixed` ends a finding's life — carries a
   `DISPUTE_SCAN_INTERVAL` deadline (default 15 min), folded into the row's
   `next_deadline_at`. On that deadline the reconciler reads the reactions
   on each unresolved finding's stored `comment_id` from the findings
   ledger, whatever head that comment was posted on (a carried finding
   keeps the comment id of its first publication until the re-review
   posts a new one), one request per comment, counted against
   `PR_STATE_REQUEST_BUDGET`; the existing daily feedback scan is too slow
   for this and is left as is. Either source updates `open_findings` /
   `disputed_findings` on the `pr_state` row locally, with no model call, so
   the projection can move to `ready_for_maintainer` in the same cycle once
   nothing blocking remains. Because disputed findings stay in the scan set,
   a 👎 removed later re-opens the finding on the next scan and the PR
   leaves ready — the page already sent is not retracted, and a later return
   to ready advances `ready_entry_seq` and pages again. Reactions and
   replies from anyone other than the PR author are ignored for this
   purpose.

The quality-readiness verdict (`ready` / `concerns` / `needs_rework`) is
attached to the page as a badge and never gates: it has no calibration data
yet, and a silent hold on a verdict nobody can inspect is the failure mode
this RFC exists to remove.

### Who is paged

The same owner the routing loop mentioned at open (the module or model owner
from the #117 scorer; module signal wins over model signal). The page records
the routing reason exactly as the assignment ledger does. If routing produced
no owner, the page falls back to `MERGE_NOTIFY_LOGINS`, and if that is empty
to `STALE_COORDINATOR_LOGIN` — the login the stale reminders already copy,
so it is a person who has agreed to hear from the bot about neglected PRs.
The PR carries sub-status `unrouted` either way, and the board marks it, but
**the page is still sent**: 128 open PRs have no routed owner today, and
leaving those to the dashboard alone would mean the state machine never
pages anyone about the PRs least likely to have someone watching them.

Only if both fallbacks are unset is the page skipped, and that is a
misconfiguration rather than a designed path: the projection still reaches
`ready_for_maintainer`, the board shows `unrouted`, and the dashboard raises
it as `attention` so the empty configuration is visible instead of silent.

The owner is a reviewer, not necessarily a committer, so the page may bounce.
That is accepted for now; a derived committer catalog (who merged PRs
touching this module in the last 90 days, an API fact) is the obvious
follow-up and is named under open questions.

### Clocks

One clock per PR: `last_human_activity_at = max(last non-bot commit,
comment, review)` — the #120 definition, including its rule that an
`updated_at` bump the fetched events cannot explain counts as activity.
The bot's own comments and reviews never move it.

| Day | State | Notice | Cleared by |
| --- | --- | --- | --- |
| 7 | `stale` | reminder | any human activity |
| 14 | `parked` | "consider converting this to a draft" | any human activity |
| 30 | `parked` | "consider closing this" | any human activity |

All three are notices; none of them changes the PR. The window is keyed by
the last *confirmed* human activity, so a notice can never open a new window
by itself, and only the highest rung whose clock has passed is sent on any
given pass. PRs carrying any of `STALE_EXEMPT_LABELS` are never notified.

## Triggers

### Nightly sweep (04:00 Asia/Shanghai)

Replaces "review on mention only". Once a day the sweep selects open,
non-draft, non-parked, non-stale PRs whose current head has no completed
review attempt, and enqueues reviews in this priority order:

1. PRs that are CI-green and mergeable (closest to the gate);
2. PRs never reviewed, newest first;
3. PRs pushed since their last review (re-reviews reuse thread dispositions,
   so they are the cheapest);
4. legacy backlog (open before the flag turned on), oldest first.

To prevent lower bands from waiting indefinitely, the sweep reserves
`max(1, budget // 5)` slots for eligible heads that have waited at least
one day since first eligibility or their last allocation of review capacity.
At the initial budget this is four slots. The remaining slots follow the
priority bands, and legacy-band work still respects the backfill quota.
The ledger preserves `first_eligible_at` and `last_selected_at` across
restarts and retries; a new head starts a new queue age. Queue eligibility
is refreshed outside the nightly window as well.

Capacity, from the live step medians (`llm` 290 s in Direct mode, `strict`
919 s in Strict mode, one Strict worker):

| Setting | Default | Rationale |
| --- | --- | --- |
| `AUTO_REVIEW_ENABLED` | `false` | shadow first, like every #116 flag |
| `AUTO_REVIEW_AT` | `04:00` (`Asia/Shanghai`) | fixed named timezone, independent of host timezone; off-peak for CI and for people |
| `AUTO_REVIEW_WINDOW_HOURS` | `6` | bounded nightly scheduling; unfinished eligible work carries forward with its queue age |
| `AUTO_REVIEW_BUDGET` | `20` | initial measured exposure; increase toward 60 only after at least three successful nights and review of queue, failure and latency measurements |
| `AUTO_REVIEW_MODE` | `direct` | automatic reviews run Direct only; the 50/50 Strict split stays on mention-triggered reviews so the experiment's sample is not swamped |
| `AUTO_REVIEW_BACKFILL_PER_NIGHT` | `10` | legacy-band reviews are bounded independently; accepted configuration range is 0–10 |

The mention trigger stays exactly as it is, as the immediate manual path, and
a mention-triggered review counts against no nightly budget.

Bootstrap rule: when the flag turns on, PRs already open are marked
`legacy` in `pr_state` and are *not* reviewed unless they hit priority 1 or
the backfill quota. Their stale clocks already run today and keep running.

### Per-cycle reconciler (every poll, 120 s)

Each cycle the reconciler visits two sets of PRs and recomputes the
projection for each:

1. **Evidence changed** — new head, check conclusion, review completion,
   human comment or review, label edit, draft toggle, as seen by the existing
   feeds (PR snapshot, repo-wide comment feed, check reads).
2. **Deadline reached** — every `pr_state` row carries `next_deadline_at`,
   the earliest of: clock day 7 / 14 / 30, the next sweep time if the head is
   unreviewed, and the label-hold expiry. Rows whose deadline has passed are
   visited even if nothing on GitHub changed. Inactivity is the whole point
   of the clock states, so they cannot depend on an event arriving.

For each visited PR: project → if the state differs, append the transition
row → compute the desired artifact set for the current evidence
([Actions](#actions-desired-set-versus-live-set)) → diff against the live
set → execute each add, retract or supersede under the claim protocol →
record the result on the transition row (or on a no-transition action row
when the state did not change). If an action fails or is over budget, the
state still changes and the row's sub-status is `action_pending`; the
deadline is set to "retry next cycle", so the action is retried without
re-deciding the state.

At most one transition per PR per cycle. Bounded by
`PR_STATE_REQUEST_BUDGET` reads and `PR_STATE_WRITE_BUDGET` writes per cycle,
both fail closed (skip the rest of the list, log, retry next cycle) — the
same shape as the #120/#121 budgets.

### Closed PRs

A closed PR is closed by a person, so there is nothing to watch and no
obligation to honour. It leaves the open set on GitHub and the reconciler
drops it: the `pr_state` row records `closed`, the transition log keeps the
history, and nothing reopens it.

The previous draft had a 90-day reopen watch here, with `closed_by_bot_at`,
`close_head_sha`, a rule about whose comment counts as the author's, and a
sequence for "bot closes → maintainer reopens → maintainer closes". All of
it existed to make the bot's own closures recoverable. The bot closes
nothing, so none of it is needed, and the columns behind it are dropped
rather than left unwritten.

## Bot powers

The bot writes to GitHub in exactly one way: it posts comments, and reviews
with `event="COMMENT"`. There is no second kind of write, now or behind a
flag. `add_labels`, `remove_label`, `close_pull`, `reopen_pull`,
`dismiss_review` and the draft mutations are removed from the client, so the
constraint cannot be undone by configuration — only by a commit, which is
reviewable.

| Message | Where it comes from | Flag | Default |
| --- | --- | --- | --- |
| ready page: one comment @-mentioning the routed owner | new emitter driven by the projection | `READY_PAGE_ENABLED` | `false` |
| 7-day reminder | `stale.py`, shipped and running (505 posted) | `STALE_PR_ENABLED` | today's value, unchanged |
| 14-day "should be parked" notice | `stale.py`, new rung | `IDLE_LADDER_ENABLED` | `false` |
| 30-day "should be closed" notice | `stale.py`, new rung | `IDLE_LADDER_ENABLED` | `false` |

The 14- and 30-day notices extend the existing stale reminder rather than
forming a second emitter, because that module already has everything a
second one would have to rebuild: a write budget (10 per cycle, so the 715
PRs already past 7 days drip instead of arriving at once), idempotency keyed
by the inactivity window so its own comment cannot retrigger it, a
timeline-verified human-activity watermark, suspension when evidence is
partial, and ledger-backed note rows. Two modules commenting about idleness
on the same PRs would be the worst outcome, so there is one ladder.

**The new rungs need their own switch.** `STALE_PR_ENABLED` is already on;
hanging the 14- and 30-day notices off it would turn them on the moment the
code shipped, with no shadow period and no way back to today's behaviour.
`IDLE_LADDER_ENABLED` defaults to `false`, and with it off `stale.py` does
exactly what it does now.

**A rung already passed is skipped, not replayed.** A PR idle 40 days on the
day the ladder turns on gets the 30-day notice only. Without this, enabling
the feature would walk every one of those PRs up three rungs.

**The ready page fires once per entry into `ready_for_maintainer`**, not once
per head and not once per lifetime. It stays silent while a PR remains
ready, and pages again only if the PR leaves ready — CI breaks, a new
blocker, a conflict — and later returns, which is exactly when a maintainer
needs telling a second time. On enable it records the PRs that are already
ready without paging anyone, the same first-run baseline the assignment and
stale scanners use, so turning it on is not an event.

**This emitter replaces the one already running.** `lifecycle.py` publishes
a `ready_to_merge` note today — 20 are live on the watched repo — and it
pages on `mergeable_state == "clean"` alone, with no requirement that the
head was reviewed or that findings are closed. That is the false-ready the
gate in this RFC exists to remove, so the two must not coexist: left
running, the old path would page unreviewed PRs and double-page eligible
ones.

Cutover, in the same release that enables the new emitter:

1. `ready_to_merge` leaves the lifecycle reconciler's desired set. The
   module keeps its other kinds (`ci_failed` and the rest) unchanged, and
   any `ready_to_merge` claim still pending is withdrawn through the
   existing recovery path rather than left to expire.
2. Every live `ready_to_merge` note is judged against the new gate. A PR
   that passes it **keeps its note**, and the baseline sets
   `ready_paged_seq = ready_entry_seq` so the new emitter does not say the
   same thing twice. A PR that fails it has the note **retracted** through
   the existing retract path, because it was posted under a weaker rule and
   is precisely the false-ready this design promises to stop.
3. After cutover the gated emitter is the only code path that can post a
   ready page. An acceptance case asserts it.

**PRs with no routed owner are still paged.** 128 of them exist today. The
fallback chain is owner → `MERGE_NOTIFY_LOGINS` → `STALE_COORDINATOR_LOGIN`,
as [Who is paged](#who-is-paged) sets out; the board marks them `unrouted`,
and only an entirely unset configuration skips the page, which the dashboard
raises as `attention`.

Existing safety gates stay in front of all of this: `POST_MODE=review`,
`ALLOW_POST`, the write budget, and the claim protocol.

## Storage

The bot ledger stores projected evidence, notification obligations and
transition history. Pending comments must be settled before tables retire; see
[Rollback](#rollback).

```sql
CREATE TABLE pr_state (
  repo TEXT NOT NULL, pr_number INTEGER NOT NULL,
  state TEXT NOT NULL,              -- one of the eleven names above
  sub_status TEXT,                  -- awaiting_sweep | queued | running | ci_pending | unrouted | legacy | conflict
                                    -- | action_pending | action_done
  head_sha TEXT NOT NULL,
  since_at TEXT NOT NULL,           -- when this state was entered
  reason TEXT NOT NULL,             -- one line, human readable, shown on the kanban
  pager_login TEXT,                 -- who was paged for ready_for_maintainer
  last_human_activity_at TEXT,      -- the single clock
  next_deadline_at TEXT,            -- earliest of clock day 7/14/30 and the next sweep
  parked_at TEXT,                   -- when we SAID it should be parked, not when anything happened
  state_label TEXT,                 -- our state label for this PR; ledger only, never written to GitHub
  content_labels_json TEXT,         -- inferred taxonomy (new model / diffusion / tts / omni / VLA), ledger only
  open_findings INTEGER NOT NULL DEFAULT 0,
  disputed_findings INTEGER NOT NULL DEFAULT 0,
  ready_entry_seq INTEGER NOT NULL DEFAULT 0,    -- bumps on each entry into ready_for_maintainer; keys the page
  ready_paged_seq INTEGER NOT NULL DEFAULT 0,    -- last sequence delivered OR cancelled; a page is due while entry > paged AND the PR is still ready
  -- ready_entry_seq counts from 0 in a fresh table, but comment claims
  -- OUTLIVE the table: after a rollback that retires pr_state and a later
  -- re-enable, entry 1 would present the same page key as the entry 1 that
  -- was already posted, and the claim would suppress a real page. So the
  -- key carries pr_state_epoch, a single integer in ledger metadata that
  -- the migration increments every time these tables are created. Metadata
  -- is not part of the retirement, so the epoch never goes backwards.
  updated_at TEXT NOT NULL,
  PRIMARY KEY (repo, pr_number)
);
CREATE TABLE pr_state_transitions (
  id INTEGER PRIMARY KEY,
  repo TEXT NOT NULL, pr_number INTEGER NOT NULL,
  from_state TEXT, to_state TEXT NOT NULL,
  head_sha TEXT NOT NULL,
  reason TEXT NOT NULL,
  evidence_json TEXT NOT NULL,      -- the inputs the projection saw (check states, attempt id, findings, clock)
  actions_json TEXT NOT NULL,       -- comment/review ids written, or the shadow artifact path
  created_at TEXT NOT NULL
);
CREATE INDEX pr_state_transitions_pr ON pr_state_transitions (repo, pr_number, id);
```

Reconciler contract:

- **Pure projection.** `project(evidence) -> (state, sub_status, reason)` is a
  function with no I/O, unit-tested against fixture evidence. The same
  evidence must yield the same state and produce no new transition row.
- **One writer.** The reconciler runs inside the existing single-writer
  process (`single_writer.py`); the sweep only enqueues review jobs.
- **Transition, then act.** The transition row is written *before* any GitHub
  write, with `actions_json` filled in afterwards, so a crash between the two
  leaves a row that the orphan-adoption path can finish, never a duplicate
  comment.
- **Dedupe keys are per artifact, never per state.** The authoritative key
  for every write is the one in the
  [artifact table](#actions-desired-set-versus-live-set): artifact kind plus
  the event it answers (head SHA for a conflict or CI note,
  `pr_state_epoch` + `ready_entry_seq` for the ready page, window start for
  the 7/14/30 notices). The
  transition row stores
  the keys of the writes it caused in `actions_json`, and a write that
  happens without a transition gets its own row with `from_state ==
  to_state`. Two artifacts on the same head and in the same state (a
  conflict comment, then a CI-failed note after a push)
  therefore have distinct keys and both are posted; a restart or a CI
  re-run on the same SHA re-derives the same keys and is a no-op.

Existing evidence tables remain authoritative; additive migrations preserve claims and history. `workflow_jobs`, `review_attempts`,
`lifecycle_notes`, `stale_windows`, `idle_ladder_windows` and historical
`applied_labels` remain evidence. Current internal labels use
`inferred_labels`, and `auto_review_queue` retains eligibility/service age;
`pr_state` is the derived projection for the kanban, pager and clocks.

## Kanban

The dashboard gains one board: one column per state in projection order, one
card per PR showing head, `reason`, `since_at`, open/disputed findings, pager,
and the next scheduled automatic action ("draft suggestion due in 3 days", "in tonight's
sweep #12"). The existing "resolved / attention" buckets are replaced by
state counts, which also fixes the invisible-status gap (queued, running,
blocked, timed out, rerouted all land in a column).

## Ownership split

| Concern | Owner |
| --- | --- |
| projection, reconciler, sweep, clocks, our labels, notices, dashboard | `omni-reviewbot` |
| review verdict, published `findings`, explicit `finding_rechecks`, quality verdict and head binding | this repo, via the SDK (`build_review_result`, `build_quality_result`) |
| `open_findings` / `disputed_findings` counts | the bot, because they combine SDK per-finding results with reaction and reply data only the bot reads |

### SDK boundary

**Implemented SDK contract.** [Copilot #180](https://github.com/JiusiServe/InferMatrixCopilot/pull/180)
ships Direct `1.1.0` and Strict `1.3.0` through the public
`infermatrix_copilot.sdk.v1` surface. Published findings and carried-finding
rechecks are separate data sets, defined by
[`sdk/v1/models.py`](../src/infermatrix_copilot/sdk/v1/models.py),
[`sdk/v1/rechecks.py`](../src/infermatrix_copilot/sdk/v1/rechecks.py) and
[`contract.py`](../src/infermatrix_copilot/contract.py):

```text
carried_findings: [          # DirectReviewRequest / StrictReviewRequest
  { finding_id, source_head_sha, severity, path, title,
    body, line, disputed }
]
finding_rechecks: [          # DirectCompletionRequest / Strict result
  { finding_id, head_sha, outcome, evidence }
]                           # outcome: fixed | still_affected | unverified
findings: [                 # published findings in the Strict result
  { finding_id, severity, anchor, head_sha }
]
```

Finding identity derives from path and normalized finding text, excluding
line number and head. Publication comment IDs and consumer revision counters
belong to ReviewBot's ledger, not the provider's finding records. The
existing `finding_dispositions` audit remains separate and does not prove a
carried finding fixed.

Direct binds the issued review context to the carried set and expected
head, then validates explicit rechecks at completion. Strict persists the
carried request and rechecks the findings against its frozen checkout;
`build_review_result` returns `finding_rechecks`, `rechecks_complete` and
`recheck_missing`, including gaps when a run fails before review. Validation
rejects unknown/duplicate IDs, wrong-head answers and empty evidence. Every
carried ID needs a valid answer; `unverified` is an answer that leaves the
finding unresolved, while omission is a coverage gap.

[ReviewBot #85](https://github.com/JiusiServe/omni-reviewbot/pull/85) pins the
provider to `745f0a83e20ae3f5c5868b3504f4ef10c6284887` and consumes this
contract in Direct and Strict reviews. It retains a carried snapshot across
Strict retries, independently validates coverage before accepting fixes,
and guards fixes against stale review revisions. Unresolved answers remain
conservative when reviews race. Its migration reopens findings previously
closed by omission and invalidates that old readiness evidence. A dispute
remains independent of the underlying recheck outcome.

The copilot stays stateless per run. Re-review after a push is an ordinary
`pr_review` run with the existing thread context; no new task kind.

## Rollout

Every stage is enabled explicitly on the host; new feature comments require
their named flag. Check each stage against its exit criteria before advancing,
and keep the initial exposure until at least three successful nightly runs
have been observed. Merged code and passing CI do not constitute rollout
acceptance. Record the exact provider/bot pair, effective flags, observed
results and pending criteria for every stage.

1. **Shadow.** `PR_STATE_ENABLED=true`, everything else off. Tables fill, the
   kanban shows states, our labels are recorded. Exit criterion: the
   projection agrees with a hand check on 30 PRs sampled across columns, and
   no PR flips state more than twice a day without a push.
2. **Our labels.** The state label and the inferred content labels are
   written to the ledger and shown on the board. There is no GitHub step
   here and no repository labels to create, because nothing is applied to
   GitHub. Exit: a maintainer reading the board agrees with the labels on
   20 sampled PRs.
3. **Sweep and disputes.** Enable `AUTO_REVIEW_ENABLED=true` at budget 20
   and bounded `DISPUTE_SCAN_ENABLED=true`. Increase toward 60 only after
   the three-night observation requirement and measured results justify it.
   Exit: sweep finishes inside the window on three consecutive nights;
   review failure rate is no worse than mention-triggered reviews, measured
   over the same observation period.
4. **Ready page.** `READY_PAGE_ENABLED=true`, baselined so the PRs already
   ready are recorded without paging, and with the lifecycle
   `ready_to_merge` cutover above in the same release — the old emitter
   retires as the new one starts, never both running. Exit: a maintainer sampling 20 ready
   pages finds ≤ 2 that should not have been paged (false-ready ≤ 10 %).
5. **The idle ladder.** `IDLE_LADDER_ENABLED=true`; the 14- and 30-day
   notices join the existing 7-day reminder. This adds follow-ups to the
   inactive backlog, so it goes last. All rungs share the existing
   10-comment cycle budget, and backlog PRs get only the highest passed rung.

### Rollback

Turning a flag back to `false` stops *new* posts of that kind at once, and
under this design that is very nearly the whole of it: the bot holds no
state on anyone's PR, so there is nothing to unwind on GitHub except live
notes that the existing retract path already handles.

1. **Freeze.** All `PR_STATE_*`, `AUTO_REVIEW_*` and `READY_PAGE_*` flags
   off, and `IDLE_LADDER_ENABLED=false`, which returns `stale.py` to the
   7-day reminder it sends today. The reconciler keeps running in
   unwind mode: it computes no new desired artifacts but still visits rows
   with a live note.
2. **Retract the retractable notes** — CI and conflict — through the
   existing `lifecycle-retract` path and the claim protocol, each logged as
   a transition row. The ready page is *not* among them: it is a
   notification, it was true when sent, and the artifact table says it is
   never retracted. Retracting it here would contradict that and would tell
   a maintainer their PR is no longer ready when nothing about the PR
   changed.
3. **Settle pending pages.** A page that is due but undelivered
   (`ready_entry_seq > ready_paged_seq`) is cancelled rather than sent, by
   setting `ready_paged_seq = ready_entry_seq` and logging it. Without this
   the unwind could never finish: step 4 waits for no artifact to be
   outstanding, and a page wanted-until-delivered is outstanding for ever
   once posting is frozen.
4. **Retire the tables** once step 2 confirms no live CI or conflict note
   remains and step 3 has left no page due. Until then `pr_state` and
   `pr_state_transitions` stay, read-only for everything but the unwind.
   `pr_state_epoch` is **not** retired with them: it lives in ledger
   metadata precisely so that a later re-enable starts on a fresh epoch and
   cannot present a page key that the surviving comment claims have already
   seen.

Comments already posted are not retracted and cannot be: a reminder or a
page is a thing said to a person, and the rollback does not pretend
otherwise. Nothing else survives the freeze, because there are no labels to
remove, no drafts to undo and no closures to honour — which is the one
clear benefit of giving the bot no authority.

## Accepted rollout choices

The owner approved the implementation and staged rollout on 2026-09-22:

1. Ready notification recipients use owner → `MERGE_NOTIFY_LOGINS` →
   `STALE_COORDINATOR_LOGIN`. With no configured recipient, retain an
   undelivered page and surface `attention`; never silently mark it delivered.
2. Automatic reviews run in Direct mode. Mention-triggered reviews keep the
   existing experiment routing.
3. Extend the idle ladder at days 14 and 30 behind its own flag, share the
   existing write budget, and send only the highest passed rung on backlog.
4. Observe each rollout stage and at least three successful nights before
   increasing exposure. Production monitor incident/rollback authority is a
   separate decision and is not enabled by this feature.

## Implementation checklist (2026-09-22)

This is a source/CI checkpoint as of 11:12 UTC. Checked items identify merged
implementation, not enabled production behavior. The runtime acceptance
checklist below stays open until deployment observations establish it.

The tested target pair is ReviewBot
`8b30efe9806d065a66c80ee4b1148315e751c3df` with Copilot
`745f0a83e20ae3f5c5868b3504f4ef10c6284887`.
[Release workflow 35718662268](https://github.com/JiusiServe/omni-reviewbot/actions/runs/35718662268)
has passed `build-and-test`, including the exact-pair tests and release
bundle build. At this checkpoint `canary-record` is waiting through the
cooldown; production deployment and feature activation remain pending.

- [x] Projection/transition ledger, initial nightly sweep, finding ledger,
      deadline-first visits, dispute scanning and independent PR snapshot
      refresh merged flag-off (ReviewBot #73–#76).
- [x] Retry path recognizes the watcher's `timeout` status; retained in the
      automatic-sweep regression coverage.
- [x] Comment-only runtime authority, including internal labels, removed
      reactions and local-only knowledge exports:
      [ReviewBot #82](https://github.com/JiusiServe/omni-reviewbot/pull/82) and
      [Copilot #179](https://github.com/JiusiServe/InferMatrixCopilot/pull/179).
- [x] Only GitHub facts produce draft/closed; day 30 remains a recommendation
      on an open idle PR. Independent evidence and next actor are retained:
      [ReviewBot #84](https://github.com/JiusiServe/omni-reviewbot/pull/84).
- [x] Explicit carried-finding rechecks, omission migration, independent
      disputes and compatible provider pin:
      [Copilot #180](https://github.com/JiusiServe/InferMatrixCopilot/pull/180)
      and [ReviewBot #85](https://github.com/JiusiServe/omni-reviewbot/pull/85).
- [x] Current-head verified CI proof is required for readiness:
      [ReviewBot #86](https://github.com/JiusiServe/omni-reviewbot/pull/86).
- [x] Initial budget 20, explicit Asia/Shanghai window, bounded backlog,
      durable queue ages and reserved service for older waiting work:
      [ReviewBot #88](https://github.com/JiusiServe/omni-reviewbot/pull/88).
- [x] Extend `stale.py` with the 14/30-day rungs, highest-passed backlog
      behavior, shared budget, uncertain-delivery recovery and re-enable
      coverage: [ReviewBot #87](https://github.com/JiusiServe/omni-reviewbot/pull/87).
- [x] Epoch/entry ready notifications, delivery recovery, cancellation and
      durable lifecycle cutover:
      [ReviewBot #90](https://github.com/JiusiServe/omni-reviewbot/pull/90).
- [x] Independent evidence, next actor, pending delivery and queue health
      on the board:
      [ReviewBot #89](https://github.com/JiusiServe/omni-reviewbot/pull/89).
- [ ] Deploy the tested provider/bot pair.
- [ ] Enable the staged runtime features and verify representative live
      states, delivery behavior and recovery against the deployed pair.
- [ ] Record stage observations, enable stages only after their exit criteria
      pass, and observe at least three successful nights before increasing
      exposure. No runtime-acceptance item is satisfied by this checklist.

## Risks

| Risk | Mitigation |
| --- | --- |
| Review volume ≈48/day exceeds what one host can finish by morning | budget + window, leftovers carry over, Direct-only for automatic reviews; if the carry-over queue grows three nights running, the dashboard raises it as `attention` |
| A false-positive blocker holds the ready gate | the finding never blocks a merge, only the page; the dispute path (👎) clears it from the gate immediately and the board shows the disagreement; false-ready rate tracked per week |
| Three idle notices land on a PR whose author is on leave | they are notices and change nothing; exempt labels skip them entirely; only the highest rung is sent |
| The day-14 and day-30 notices are noise on a repo the team does not own | one ladder, 10 posts per cycle, highest rung only, and the whole ladder is the last rollout step so it can be judged on the 7-day reminder's reception first |
| The board is the only place PR state exists, so nobody looks at it | the ready page is a push, not a pull — a maintainer never has to open the board to learn a PR needs them |
| A stuck lifecycle claim blocks a state (today 266 stale notes sit in `claimed`) | the transition row's `actions_json` is the audit; a claim older than its lease is withdrawn by the existing recovery path, and the kanban card shows "action pending since" |
| Budget exhaustion silently freezes a column | fail closed *and* count it: `PR_STATE_BUDGET_EXHAUSTED` events are on the dashboard's reliability story |

## Acceptance criteria

- [ ] Every open PR in the watched repo has exactly one `pr_state` row and one
      column on the kanban; no PR is in "neither bucket".
- [ ] Same evidence in, same state out, zero new transition rows (property
      test over recorded evidence).
- [ ] A push moves `changes_requested`, `ci_failing`, `ready_for_maintainer`,
      `stale` and `parked` back to `under_review` within one cycle.
- [ ] The ready page fires only when all five gate conditions hold, once per
      entry into ready, and names the owner with the routing reason.
- [ ] A PR that goes ready, breaks and goes ready again is paged twice;
      one that sits ready across many cycles is paged once; a re-run against
      the same evidence pages nobody.
- [ ] A PR with no routed owner is paged down the fallback chain (owner →
      `MERGE_NOTIFY_LOGINS` → `STALE_COORDINATOR_LOGIN`) and flagged
      `unrouted` on the board; the page is skipped only when every fallback
      is unset, and that raises `attention`.
- [ ] A ready page that fails on budget and whose PR is then pushed to is
      **cancelled, not sent**: `ready_paged_seq` advances, a transition row
      says "page cancelled: no longer ready", and no comment is posted. If
      the PR becomes ready again it is a new entry and is paged.
- [ ] Disputed findings never block and are counted on the page.
- [ ] Disputing the last open blocker lets the PR enter
      `ready_for_maintainer` and its page is sent; withdrawing that 👎
      re-opens the finding and the PR leaves ready with nothing retracted;
      neither direction dismisses or edits anything on GitHub.
- [ ] Writes follow evidence, not transitions: a `ready_for_maintainer` PR
      whose CI turns red on the same head gets a CI-failed comment in the
      same cycle, and its ready page is left standing.
- [ ] Day-7 / 14 / 30 notices each fire at most once per inactivity window
      across restarts; only the highest passed rung is sent; bot activity
      never restarts the clock.
- [ ] **The client exposes no method that writes a label, a draft state or a
      PR's open/closed state, and no review with an `event` other than
      `COMMENT`.** A test asserts this over the client's public surface, so
      the constraint fails the build rather than a review.
- [ ] Every label the design names exists in the ledger for every open PR —
      state and content both — and none of them is on GitHub.
- [ ] The sweep never exceeds its budget or window; leftovers are visible.
- [ ] Shadow mode writes nothing to GitHub; each flag promotes its own shadow
      artifacts exactly once.
- [ ] Every retractable note (CI, conflict) is retractable by the
      reconciler and the retraction is logged in `pr_state_transitions`.
- [ ] A **delivered** ready page is never retracted: not when the PR leaves
      `ready_for_maintainer`, not by the rollback unwind. Only an
      undelivered entry is ever cancelled.
- [ ] After cutover the lifecycle reconciler never posts a `ready_to_merge`
      note again, and the gated emitter is the only path that can page: a
      PR that is mergeable but whose head is unreviewed receives no ready
      page from either.
- [ ] Rollback → re-enable fixture: a PR paged at entry 1, then the unwind,
      then the tables recreated and the PR becomes ready again. The epoch
      has advanced, so the new entry presents a key the surviving claims
      have not seen and the page is sent; without the epoch this page is
      suppressed.
- [ ] Cutover fixture: of two PRs carrying a live `ready_to_merge` note,
      the one that passes the new gate keeps its note and is not paged
      again, and the one that does not has its note retracted; no pending
      `ready_to_merge` claim survives.
- [ ] The bot never merges, never approves, never blocks, never labels on
      GitHub, never drafts, never closes and never reopens.
- [ ] Rollback fixture: with three PRs — one carrying a live CI note, one a
      live conflict note, one with a ready page due but never delivered —
      the unwind retracts the first two and logs each retraction, cancels
      the third page instead of sending or retracting it, and only then
      allows the tables to be dropped. Pages already delivered are left
      alone. No PR is drafted, closed or relabelled by the unwind, because
      none was by the feature.

## Tests

- Projection unit tests: one fixture per state and per precedence pair
  (stale-but-green, conflict-and-red, reviewed-but-CI-pending, disputed-only),
  plus the exhaustiveness fixtures: reviewed green PR; a PR a person
  converted to draft (→ `draft`, unmanaged, no clocks); a `parked` PR at day
  30 with no evidence change (stays `parked`, close notice due); a
  randomly generated evidence table must never hit `unclassified` for the
  combinations the RFC names.
- Reconciler tests with a fake GitHub client: crash between transition row
  and post, restart, same-SHA CI re-run, a deadline visit with zero evidence
  change, and **a ready page that fails on budget is still due on the next
  cycle and is delivered exactly once**.
- Client-surface test: the GitHub client exposes no method that writes a
  label, a draft state or a PR's open/closed state, and no review with an
  `event` other than `COMMENT`.
- Clock tests: a notice does not restart the window; a PR idle 40 days when
  the ladder is enabled gets the day-30 notice only; a person drafting a
  `parked` PR moves it to `draft` and stops its clocks; an exempt label
  added to a `parked` PR stops the notices with nothing to undo; human
  activity at any rung resets the clock and the next window starts the
  ladder over.
- Sweep tests: budget, window, priority order, backfill quota, carry-over.
- Dispute tests: a reaction-only dispute (author 👎, no reply, no push) is
  picked up on the dispute-scan deadline and lets the PR reach
  `ready_for_maintainer` without a model call; a bystander's 👎 changes
  nothing; removing the sole 👎 on a PR whose every blocker was disputed
  re-opens the finding and the PR leaves ready, and a later return to ready
  pages again on a new `ready_entry_seq`; a 👎 placed on a carried
  finding's original comment from an older head is found after a push
  because the scan follows the stored comment
  id.
- Contract tests in this repo: Direct and Strict carry typed finding IDs
  and source heads; rechecks carry the current head, an explicit outcome
  and evidence. Cover complete `fixed`, `still_affected`, `unverified`,
  omission, duplicate/unknown IDs, wrong-head answers and early run failure.
  Consumer tests prove only complete explicit fixes close carried blockers
  and that concurrent reviews or dispute changes cannot erase unresolved
  evidence.

## Metrics for success

Reported weekly on the dashboard, computed from `pr_state_transitions` and
the GitHub API:

- maintainer touches per merged PR (human comments + reviews before merge),
  target ≤ 1 for PRs that entered through the sweep;
- share of merged PRs that were paged as `ready_for_maintainer` before the
  first maintainer comment;
- false-ready rate (maintainer requests changes after a ready page);
- median time from open to `ready_for_maintainer`;
- share of PRs that reached day 30 and what a human then did with them —
  the honest measure of whether the idle ladder is worth its noise, since
  the bot cannot act on the answer itself.

## Known defects to fix on the way

- Timeout retry spelling has been fixed; keep the regression case when
  validating the automatic sweep.
- `notified` and its variants were migrated away in the ledger but survive in
  the dashboard label map and the resolved set (`dashboard.py:40`,
  `ledger.py:4195`); they go when the buckets are replaced by state counts.
- `PROJECT_SPEC.md` still documents a review machine
  (`snapshotted`, `direct_ready`, `publishable`, `post_unknown`) that the ledger
  never implemented; it should be replaced by a pointer to this RFC.

## Open questions

- A derived committer catalog (merge history per module, no model) would make
  the ready page land on someone who can merge. Not in scope; tracked here so
  it is not forgotten.
- Whether re-reviews should skip PRs whose diff since the last reviewed head
  is below the diff budget's floor (docs-only, whitespace) — cheap to add, not
  needed for correctness.
- Whether the idle ladder should end in a person rather than a notice. With
  no write authority the bot can say "this should be closed" 715 times and
  nothing closes. A weekly digest to one coordinator — "these 12 crossed day
  30 this week" — might close more PRs than 715 individual comments, and
  would be quieter. Worth measuring once the ladder has run a month.
- Whether `draft` PRs get a provisional review in the sweep. Declined for
  now: today's rule ("draft PR 不处理") stands, and drafts opt in by marking
  ready.
