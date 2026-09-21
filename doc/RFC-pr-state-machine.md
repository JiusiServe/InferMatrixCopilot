# RFC — PR state machine: maintainers join when the PR is almost ready

- Status: proposed — design only, nothing implemented
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
  lifecycle, and it deliberately overrides two of #116's boundaries
  (no auto-close, mention-only routing). Those overrides are listed under
  [Decisions that need repo-owner sign-off](#decisions-that-need-repo-owner-sign-off).
- Evidence: `vllm-project/vllm-omni` as of 2026-09-21 (GitHub search API and
  the bot's live `/api/status`). Every number is reproducible from those two
  sources; the design has no tests yet because it has no code yet.

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

## Goals and non-goals

Goal: **one maintainer touch per merged PR — the merge decision.** Everything
before that (routing, review, CI nudges, re-review after pushes, inactivity
handling) is automatic, and a maintainer is paged exactly once, when the PR
passes a defined ready gate.

Non-goals:

- The bot never merges. Ever. Not behind a flag.
- The bot never approves. A bot `APPROVE` reads as a merge recommendation and
  GitHub counts it toward required approvals; the bot's positive signal is the
  `bot:ready-for-maintainer` label and the page, nothing else.
- No new model calls beyond the reviews the sweep schedules. The state
  projection is pure bookkeeping over ledgers the bot already keeps.
- Other adapters stay opted out until they ask (`LIFECYCLE_REPOS` semantics).

## The state machine

### States

A PR has exactly one state at a time. The state is a **projection of the
current head**: the reconciler recomputes it every cycle from evidence and
writes it down (see [Storage](#storage)). A push re-enters `under_review`.

| # | State | Meaning | Who acts | Label |
| --- | --- | --- | --- | --- |
| 1 | `new` | Seen; owner routing not yet run (≤ 1 cycle, 120 s) | bot | — |
| 2 | `needs_owner` | Routing found no owner and no review has run yet | bot (review still proceeds) | `bot:needs-owner` |
| 3 | `owner_routed` | Owner @-mentioned; awaiting the first review sweep | bot | `bot:under-review` |
| 4 | `under_review` | Current head has no completed review, or CI is still pending on a reviewed head | bot | `bot:under-review` |
| 5 | `changes_requested` | Completed review on this head has an open blocker/major finding, or the PR has merge conflicts | author | `bot:changes-requested` |
| 6 | `ci_failing` | A watched/required check is red on this head | author | `bot:ci-failing` |
| 7 | `ready_for_maintainer` | Ready gate passed; the owner has been paged | maintainer | `bot:ready-for-maintainer` |
| 8 | `stale` | ≥ 7 days without human activity | author | `bot:stale` |
| 9 | `parked` | ≥ 14 days without human activity; the bot converts the PR to draft on entry | author | `bot:parked` |
| 10 | `draft` | Author's own draft; unmanaged, no clocks (today's behaviour) | author | — |
| — | `closed` | Merged or closed on GitHub (terminal for a human close; a bot close is re-openable and stays watched) | — | — |

Ten live states plus the terminal one. `draft` exists so that an author's
draft and a bot-parked PR are never confused: the former has no clock, the
latter is on its way to closure.

### Projection order

First match wins. The order encodes "what is the most urgent thing a person
must do", so it is also the kanban column order. The projection reads
**evidence only** (GitHub facts, ledger rows, the clock); it never reads its
own previous output or whether an action was posted. Whether the reminder,
the draft conversion or the close has actually happened is a *sub-status*
(`action_pending` / `action_done`), so a failed write cannot hide a state.

```text
closed            GitHub state is MERGED or CLOSED,
                  OR clock ≥ CLOSE_DAYS (30) on a managed PR   -- entry action: close
draft             GitHub isDraft and the bot did not convert it (no parked_at)
parked            managed AND parked_at set, GitHub isDraft, clock ≥ PARK_DAYS (14)
                  OR managed AND no parked_at AND clock ≥ PARK_DAYS
                                                               -- entry action: convert to draft
under_review      parked_at set, GitHub isDraft, AND (clock < PARK_DAYS OR NOT managed)
  (resume_pending)                                             -- entry action: mark ready for review, clear parked_at
                                                               -- (an exempt label un-parks regardless of clock age)
stale             managed AND clock ≥ STALE_PR_DAYS (7)       -- entry action: reminder
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
PR with 14 idle days is not `parked`, is never drafted, and keeps flowing
through the head-bound states (it is reviewed by the sweep and can reach
`ready_for_maintainer`); an exempt PR that *was* parked before the label was
added projects `resume_pending` and is un-drafted. The three discovery
states are mutually exclusive with `under_review` by construction: they hold
only while no review attempt exists on any head *and* the sweep has not
claimed the current head; the sweep's claim is the event that moves a PR out
of them. A PR that is red or conflicting before its first review still shows
`owner_routed`, and the CI/conflict nudge is sent from there (the transition
table keys nudges on head, not on state).

Two rules make the projection total and keep the clock states consistent
with GitHub:

- **`closed` is projected from the clock, not only from GitHub.** At day 30
  a parked PR *changes state* to `closed` with sub-status `action_pending`,
  and the entry action closes it on GitHub. A state that could only be
  entered after its own action had run would never be entered.
- **`parked_at` means "the current draft state is the bot's", nothing
  more, and it is verified every visit.** Like the closure watch, the
  parking obligation is bound to the bot's own event: the reconciler stores
  the timestamp of its `convertPullRequestToDraft` call, and on each visit
  checks the PR's timeline for the latest `convert_to_draft` /
  `ready_for_review` pair. If GitHub reports not-draft, or the latest
  `convert_to_draft` event is not the bot's, or a `ready_for_review` event
  follows the bot's conversion — a human marked it ready, even if the
  author re-drafted it before the next poll — `parked_at` is cleared in
  that cycle and a transition row records "parking retired by <actor>".
  From then on a draft is an author draft: exempt from clocks, never
  un-drafted, never auto-closed.
- **A resumed PR is `under_review` with sub-status `resume_pending`.** When
  an author comments on a bot-parked PR without pushing, the clock resets
  but GitHub still says draft and `parked_at` is still set. That
  combination is a state of its own, whose entry action is the un-draft
  mutation and clearing `parked_at`; from then on the normal rules apply.
  The same shape handles a bot-closed PR that gets activity: it stays
  `closed` (GitHub says so) and the reopen is a *scheduled* action of that
  state (next section).
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
| `REQUEST_CHANGES` review | completed review on current head has ≥ 1 open blocker/major | PR + head + `block_generation` | head moved → dismiss with "superseded by <sha>"; all findings closed or disputed on the same head → dismiss with "resolved" |

**One review per blocking interval.** The key deliberately excludes the
finding set. While the open-finding set on a head stays non-empty, the
same review stays active and its *body* is edited in place (the reviews
API allows a body update) to list the currently open findings, so a
partial dispute `{A,B} → {A}` and its withdrawal `{A} → {A,B}` change the
text and never the key. The review is dismissed only when the set becomes
empty or the head moves. `block_generation` is a counter on the `pr_state`
row that increments only when the wanted condition turns from false to
true on the same head (a dispute withdrawn after *every* blocker had been
disputed). GitHub cannot un-dismiss a review, so that case needs a new
review, and the generation makes its key distinct while a same-SHA re-run
still derives the same key and is a no-op. Ordering: a new generation is
posted only after the previous review's dismissal is confirmed, so the
live set never holds two active `REQUEST_CHANGES` reviews for one PR.
| conflict comment | `mergeable_state == dirty` on current head | PR + head + `conflict` | head moved → superseded; clean again on same head → retracted |
| CI-failed comment | required/watched check red on current head | PR + head + `ci_failed` (existing) | head moved → superseded; green on same head → retracted (existing) |
| ready page | ready gate true on current head | PR + head + `ready_to_merge` (existing) | any gate condition false on same head → retracted; head moved → superseded (existing) |
| stale reminder | clock ≥ 7 d | PR + window start (existing) | never retracted; a new window gets a new key |
| draft conversion + parked comment | clock ≥ 14 d, bot-managed | PR + window start + `park` | human activity → un-draft (`resume`, same window key) |
| close + closing comment | clock ≥ 30 d, bot-managed | PR + window start + `close` | author comment or new head within `REOPEN_WATCH_DAYS` → reopen, key PR + `closed_by_bot_at` + `reopen`; a bystander's comment never reopens |
| review job on current head | head unreviewed, sweep time reached, budget left | PR + head + `review` (existing attempt uniqueness) | head moved → attempt `superseded` (existing) |
| exactly one `bot:*` label | always, equal to the projected state | PR + state | state changed → swap; human removed it → 24 h hold, then re-apply if the state still holds |

Consequences the reviewer's two sequences must satisfy, and which are
acceptance cases below:

- A PR sitting in `changes_requested` for a conflict whose nightly review
  then finds a blocker: the state does not change, but the desired set now
  contains a `REQUEST_CHANGES` review keyed on that head and the current
  `block_generation`, so it is posted.
- A `ready_for_maintainer` PR whose CI turns red on the same head: the
  projection goes straight to `ci_failing`, and independently the ready
  page is retracted because its wanting condition is false, while the
  CI-failed comment is posted because its condition is true.
- A PR that is `stale` and then pushed: the reminder is kept (never
  retracted), the label swaps, and the review job for the new head is
  desired at the next sweep.

Every write, and every retraction, goes through the claim protocol with the
key in the table; a key includes the *event* it answers (window start,
`closed_by_bot_at`, head SHA, `block_generation`), never just the PR, so a
PR that is closed and reopened twice gets two distinct reopen claims, and
a head gets a second `REQUEST_CHANGES` claim only when a full dispute is
withdrawn and the generation advances — never because the open-finding set
changed while non-empty.

Note the asymmetry: `stale` and `parked` win over everything below them
because time-based states describe the *author*, not the head. A stale PR that
happens to be CI-green is still stale; a push clears both in one cycle because
a push is human activity.

### Transitions

| From → To | Trigger | GitHub side effect | Dedupe key |
| --- | --- | --- | --- |
| `new` → `owner_routed` / `needs_owner` | first cycle after discovery | owner @-mention comment (existing #117 loop) | PR + head + routing digest (existing) |
| `owner_routed` / `needs_owner` / any → `under_review` | nightly sweep claims the head, or a push lands | none | — |
| `under_review` → `changes_requested` | review completes with open blocker/major | bot review `REQUEST_CHANGES` on this head; findings inline (existing publisher) | PR + head + `request_changes` |
| `under_review` → `changes_requested` | `mergeable_state == dirty` | one comment asking for a rebase, with base SHA | PR + head + `conflict` |
| any → `ci_failing` | required check red | one comment @author (+ distinct last pusher) with job, SHA, link (existing #121) | PR + head + `ci_failed` (existing) |
| `changes_requested` / `ci_failing` → `under_review` | push | bot dismisses its own stale `REQUEST_CHANGES` with "superseded by <sha>"; lifecycle note superseded (existing) | — |
| `under_review` → `ready_for_maintainer` | ready gate passes | one comment @owner: "ready for a maintainer look", verdict badge, disputed-finding count | PR + head + `ready_to_merge` (existing) |
| `ready_for_maintainer` → `under_review` | push, or CI turns red, or a new blocker | ready note retracted (existing lifecycle retract) | — |
| any managed → `stale` | day 7, no human activity | one reminder @author (+ coordinator) (existing #120) | PR + inactivity window start (existing) |
| `stale` → `parked` | day 14, still no human activity | GraphQL `convertPullRequestToDraft` (the REST update endpoint has no `draft` field); one comment: "parked; push or comment to resume" | PR + window start + `park` |
| `parked` → `closed` | day 30, still no human activity (projected from the clock; the close is the entry action) | REST `PATCH state: closed`; one comment: "closed for inactivity; push or comment reopens" | PR + window start + `close` |
| `stale` / `parked` → `under_review` | any human commit, comment or review | GraphQL `markPullRequestReadyForReview` if the bot parked it (never on an author's own draft); sub-status `resume_pending` until it succeeds | PR + window start + `resume` |
| `closed` (by bot) → `under_review` | scheduled action of `closed`: author comment, or the branch head differs from `close_head_sha` | REST `PATCH state: open`, then `markPullRequestReadyForReview`; if the fork branch is gone the reopen fails and one comment says so | PR + `closed_by_bot_at` + `reopen` |

The two draft mutations are the first GraphQL calls the bot makes; the client
gains one `graphql(query, variables)` method with the same retry, budget and
identity handling as the REST path, and the PR's `node_id` is stored on the
`pr_state` row when it is first seen so no extra read is needed at action
time.

Everything the table posts goes through the existing claim protocol
(`comment_claims.py`: shadow → claimed → posted / failed / withdrawn, lease
recovery, orphan adoption after a crash). Nothing new is invented for writes.

### Ready gate

`ready_for_maintainer` requires all of, on the current head:

1. not draft, not parked, not stale;
2. every watched or required check green, `lifecycle.py` classification
   `complete == True` (unknown required-set counts as not ready, as today);
3. `mergeable_state == "clean"`;
4. a completed review attempt on this head;
5. **no open blocker/major finding.** Blocker/major findings are carried
   forward across heads: each one the bot posted stays on the PR's ledger of
   open findings until it is explicitly closed. A finding closes only by one
   of:
   - a later head's re-review lists it in `finding_dispositions` as
     `resolved_or_outdated` **with `head_recheck == "fixed"`**. The Direct
     contract also allows `head_recheck == "still_affected"`
     (`direct_routing.py:221`, `:893-900`); that value keeps the finding open.
     A re-review that simply omits a carried finding does not close it — the
     sweep's re-review prompt receives the carried list and must return a
     disposition for every entry, and a missing entry counts as
     `still_affected`;
   - the author marked it disputed: a 👎 reaction on the bot's inline comment
     or a reply in its thread. Disputed findings do not block; they are
     counted and shown in the ready page ("2 findings disputed by the
     author") so the maintainer arrives at exactly the disagreement.

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
   `disputed_findings` on the `pr_state` row locally, with no model call;
   the desired-set diff then dismisses the `REQUEST_CHANGES` review when
   nothing blocking remains and the projection can move to
   `ready_for_maintainer` in the same cycle. Because disputed findings stay
   in the scan set, a 👎 removed later re-opens the finding on the next
   scan and the ready page is retracted. Reactions and replies from anyone
   other than the PR author are ignored for this purpose.

The quality-readiness verdict (`ready` / `concerns` / `needs_rework`) is
attached to the page as a badge and never gates: it has no calibration data
yet, and a silent hold on a verdict nobody can inspect is the failure mode
this RFC exists to remove.

### Who is paged

The same owner the routing loop mentioned at open (the module or model owner
from the #117 scorer; module signal wins over model signal). The page records
the routing reason exactly as the assignment ledger does. If routing produced
no owner, the page falls back to `MERGE_NOTIFY_LOGINS`, and if that is empty
the PR is `ready_for_maintainer` with sub-status `unrouted` and only the
dashboard shows it (today's `ready_unrouted` behaviour).

The owner is a reviewer, not necessarily a committer, so the page may bounce.
That is accepted for now; a derived committer catalog (who merged PRs
touching this module in the last 90 days, an API fact) is the obvious
follow-up and is named under open questions.

### Clocks

One clock per PR: `last_human_activity_at = max(last non-bot commit,
comment, review)` — the #120 definition, including its rule that an
`updated_at` bump the fetched events cannot explain counts as activity.
The bot's own comments, reviews, labels, draft conversions and closes never
move it.

| Day | Transition | Reversible by |
| --- | --- | --- |
| 7 | reminder, `stale` | any human activity |
| 14 | draft, `parked` | any human activity (bot un-drafts) |
| 30 | close, `closed_by_bot` | author comment or push (bot reopens) |

The window is keyed by the last *confirmed* human activity, so a reminder, a
park or a close can never open a new window by itself. PRs carrying any of
`STALE_EXEMPT_LABELS` are never reminded, parked or closed.

## Triggers

### Nightly sweep (04:00 Asia/Shanghai)

Replaces "review on mention only". Once a day the sweep selects open,
non-draft, non-parked, non-stale PRs whose current head has no completed
review attempt, and enqueues reviews in this priority order:

1. PRs that are CI-green and mergeable (closest to the gate);
2. PRs never reviewed, newest first;
3. PRs pushed since their last review (re-reviews reuse thread dispositions,
   so they are the cheapest);
4. legacy backlog (open before the flag turned on), oldest last.

Capacity, from the live step medians (`llm` 290 s in Direct mode, `strict`
919 s in Strict mode, one Strict worker):

| Setting | Default | Rationale |
| --- | --- | --- |
| `AUTO_REVIEW_ENABLED` | `false` | shadow first, like every #116 flag |
| `AUTO_REVIEW_AT` | `04:00` (host TZ, UTC+8) | owner's choice; off-peak for CI and for people |
| `AUTO_REVIEW_WINDOW_HOURS` | `6` | sweep must finish before the working day; leftovers carry to the next night at the same priority |
| `AUTO_REVIEW_BUDGET` | `60` | ≈48 new PRs/day plus re-reviews; at 5 min each with 2 Direct workers this is ~2.5 h |
| `AUTO_REVIEW_MODE` | `direct` | automatic reviews run Direct only; the 50/50 Strict split stays on mention-triggered reviews so the experiment's sample is not swamped |
| `AUTO_REVIEW_BACKFILL_PER_NIGHT` | `10` | legacy backlog (1,037 non-draft open PRs today) drains slowly instead of flooding authors |

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

### Watching bot-closed PRs

A PR the bot closed leaves the open set on GitHub but not the reconciler's.
Its `pr_state` row keeps `closed_by_bot_at` and the head SHA at close time,
and for `REOPEN_WATCH_DAYS` (default 90) the row stays in the deadline set
with a daily deadline. On each visit the reconciler re-reads the PR (one
request) and checks two things: a comment **by the PR author** since the
close (the repo-wide comment feed already covers closed PRs, so this is
usually free), and a head SHA different from the one recorded at close (a
push to a closed PR's branch updates the PR's head, and only people with
write access to that branch can do it). Either one plans the reopen action.
A comment by anyone else, maintainer included, does not reopen: the author
is the person whose absence closed the PR, so only the author's return
reopens it, and a maintainer who wants it back reopens it by hand, which the
bot never undoes.

The watch is bound to **the closure event the bot caused, not to the PR.**
On every visit the reconciler first confirms that the PR's current closure
is still the bot's: GitHub's `closed_at` must equal the timestamp the bot
recorded at close (the closing comment id is stored beside it as a second
witness). If the PR has been reopened by anyone since, `closed_by_bot_at`,
`close_head_sha` and the watch deadline are cleared in the same cycle — the
watch is retired, and the PR is projected from live evidence again. If it is
later closed by a human, `closed_at` no longer matches any bot close, so no
watch exists and nothing reopens it, whatever the author does. The sequence
"bot closes → maintainer reopens → maintainer closes → author comments"
therefore ends with the PR closed.
After the watch window the row is frozen; a later comment gets no automatic
reopen, and the closing comment says so ("reopens automatically within 90
days").

## Bot powers

New GitHub writes, each behind its own flag, each shadow-first:

| Power | Flag | Default | Notes |
| --- | --- | --- | --- |
| state labels `bot:*` (7) | `PR_STATE_LABELS_ENABLED` | `false` | labels must pre-exist in the repo (the labeler already refuses to create); the reconciler swaps exactly one `bot:*` label at a time; a human removing a label is treated as a request to hold — no re-apply for 24 h, and the removal is logged |
| `REQUEST_CHANGES` on its own review | `REQUEST_CHANGES_ENABLED` | `false` | only for blocker/major, only on the head it reviewed; dismissed by the bot itself when the head moves; never `APPROVE` |
| convert to draft | `PARK_ENABLED` | `false` | day 14; un-drafts on human activity |
| close | `AUTO_CLOSE_ENABLED` | `false` | day 30; reopens on author activity; overrides #116 "no auto-close" and needs repo-owner sign-off before the flag is ever set |
| reopen | part of `AUTO_CLOSE_ENABLED` | — | only PRs with `closed_by_bot_at` set; a human close is never reopened |

Existing safety gates stay in front of all of them: `POST_MODE=review`,
`ALLOW_POST`, the write budget, and the claim protocol. In shadow mode the
reconciler writes the would-be action to `state/artifacts/pr-state/` and
promotes it exactly once when the flag turns on, as #120 and #121 do.

## Storage

Two new tables in the bot ledger. They hold obligations the bot has taken
on toward contributors (which drafts it made, which PRs it closed and
promised to reopen), so rollback is a sequence, not a drop; see
[Rollback](#rollback).

```sql
CREATE TABLE pr_state (
  repo TEXT NOT NULL, pr_number INTEGER NOT NULL,
  state TEXT NOT NULL,              -- one of the eleven names above
  sub_status TEXT,                  -- awaiting_sweep | queued | running | ci_pending | unrouted | legacy | conflict
                                    -- | action_pending | action_done
  head_sha TEXT NOT NULL,
  node_id TEXT NOT NULL,            -- GraphQL id, needed for the draft mutations
  since_at TEXT NOT NULL,           -- when this state was entered
  reason TEXT NOT NULL,             -- one line, human readable, shown on the kanban
  pager_login TEXT,                 -- who was paged for ready_for_maintainer
  last_human_activity_at TEXT,      -- the single clock
  next_deadline_at TEXT,            -- earliest of clock day 7/14/30, next sweep, label hold, reopen watch
  parked_at TEXT, closed_by_bot_at TEXT,
  close_head_sha TEXT,              -- head at bot close; a different head means a push → reopen
  label_applied TEXT,               -- the bot:* label the bot believes is on the PR
  open_findings INTEGER NOT NULL DEFAULT 0,
  disputed_findings INTEGER NOT NULL DEFAULT 0,
  block_generation INTEGER NOT NULL DEFAULT 0,   -- bumps each time REQUEST_CHANGES becomes wanted again on the same head
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
  actions_json TEXT NOT NULL,       -- comment/review/label ids written, or the shadow artifact path
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
  the event it answers (head SHA and `block_generation` for a
  `REQUEST_CHANGES`, head SHA for a conflict / CI / ready note, window
  start for reminder / park / close, `closed_by_bot_at` for reopen). The
  transition row stores
  the keys of the writes it caused in `actions_json`, and a write that
  happens without a transition gets its own row with `from_state ==
  to_state`. Two artifacts on the same head and in the same state (a
  conflict comment, then a `REQUEST_CHANGES` after the nightly review)
  therefore have distinct keys and both are posted; a restart or a CI
  re-run on the same SHA re-derives the same keys and is a no-op.

The existing tables are not changed. `workflow_jobs`, `review_attempts`,
`lifecycle_notes`, `stale_windows` and `applied_labels` remain the evidence;
`pr_state` is what the kanban, the pager and the clocks read.

## Kanban

The dashboard gains one board: one column per state in projection order, one
card per PR showing head, `reason`, `since_at`, open/disputed findings, pager,
and the next scheduled automatic action ("parks in 3 days", "in tonight's
sweep #12"). The existing "resolved / attention" buckets are replaced by
state counts, which also fixes the invisible-status gap (queued, running,
blocked, timed out, rerouted all land in a column).

## Ownership split

| Concern | Owner |
| --- | --- |
| projection, reconciler, sweep, clocks, labels, draft/close/reopen, dashboard | `omni-reviewbot` |
| review verdict, severities, `finding_dispositions`, quality verdict, head binding — the per-head facts | this repo, via the SDK (`build_review_result`, `build_quality_result`) |
| `open_findings` / `disputed_findings` counts | the bot, because they combine SDK per-finding results with reaction and reply data only the bot reads |

**SDK change required (this repo, a contract version bump).** Today
`build_review_result` projects each disposition record onto three fields —
`anchor`, `disposition`, `declared` (`contract.py:81`, `sanitize_dispositions`)
— and the Direct completion decision reports aggregate counts only. Neither
carries what the ready gate needs to retire a carried blocker. The review
result gains a head-bound, versioned per-finding list:

```text
findings: [
  { finding_id,            # stable across heads: hash(rule_id or normalized title, anchor path, symbol)
    severity,              # blocker | major | minor | nit, after demotion
    anchor,                # path + line range on head_sha, or null (general finding)
    comment_id,            # GitHub inline comment the bot posted for it, when published
    disposition,           # new | duplicate | extends_existing | resolved_or_outdated
    head_recheck,          # fixed | still_affected | null (only for resolved_or_outdated)
    carried_from,          # finding_id on the previous reviewed head, or null
    head_sha }
]
```

The sweep's re-review passes the carried open findings (id, severity,
anchor, comment id) into the run's context, and the SDK result must return
one entry per carried id; a missing entry is treated as `still_affected`
by the bot. A contract test in this repo fixes a carried blocker on a new
head and asserts the result closes it (`resolved_or_outdated` + `fixed`),
and a second test asserts that `still_affected` and omission both leave it
open. The existing aggregate `finding_dispositions` field stays for
compatibility.

The copilot stays stateless per run. Re-review after a push is an ordinary
`pr_review` run with the existing thread context; no new task kind.

## Rollout

Every step is a flag flip on the host; nothing changes on GitHub until the
named flag is on. Each step runs at least three nights before the next.

1. **Shadow.** `PR_STATE_ENABLED=true`, everything else off. Tables fill, the
   kanban shows states, would-be actions land in artifacts. Exit criterion:
   the projection agrees with a hand check on 30 PRs sampled across columns,
   and no PR flips state more than twice a day without a push.
2. **Labels.** Repo owner creates the seven `bot:*` labels;
   `PR_STATE_LABELS_ENABLED=true`. Exit: no label churn complaints for a
   week; label removals by humans are logged and honoured.
3. **Sweep.** `AUTO_REVIEW_ENABLED=true` at budget 20, then 60. Exit: sweep
   finishes inside the window on three consecutive nights; review failure rate
   no worse than mention-triggered reviews (today 14 failed of 105).
4. **Request changes + ready page** `REQUEST_CHANGES_ENABLED=true`. Exit: a
   maintainer sampling 20 ready pages finds ≤ 2 that should not have been
   paged (false-ready ≤ 10 %).
5. **Park.** `PARK_ENABLED=true`, after repo-owner sign-off.
6. **Close.** `AUTO_CLOSE_ENABLED=true`, after repo-owner sign-off, with a
   two-week announcement comment on the repo's discussion/issue.

### Rollback

Turning a flag back to `false` stops *new* actions of that kind at once.
It does not by itself undo what the bot already did to contributors' PRs,
and the ledger rows that record those obligations must outlive the
feature. The full unwind, run by the existing `lifecycle-retract` command
extended to the new artifact kinds, is:

1. **Freeze.** All `PR_STATE_*`, `AUTO_REVIEW_*`, `REQUEST_CHANGES_*`,
   `PARK_*` and `AUTO_CLOSE_*` flags off. The reconciler keeps running in
   *unwind mode*: it computes no new desired artifacts, but it still
   visits rows with a pending obligation.
2. **Unwind live artifacts**, in this order, each through the claim
   protocol and logged as a transition row: dismiss every active
   `REQUEST_CHANGES` review ("withdrawn: automation disabled"); retract
   every live ready / CI / conflict note (existing retract path); remove
   every `bot:*` label; un-draft every **open** PR with `parked_at` set
   (never an author's own draft — that is exactly why `parked_at` is
   stored). A PR that was parked and then closed cannot be marked ready
   while closed (GitHub rejects it), so its `parked_at` is left in place
   and handled by step 3.
3. **Honour reopen obligations.** Rows with `closed_by_bot_at` keep their
   watch for the remainder of `REOPEN_WATCH_DAYS`, still bound to the
   bot's own closure event and still answering only to the author. No
   PR is bulk-reopened: the closing comment promised "reopens on your
   push or comment", and that promise is kept, not replaced. When the
   author does return, the reopen action reopens, marks ready and clears
   `parked_at` in one step, as it always does. When the watch expires
   with no return, the row's obligations are retired together: the PR
   stays closed and draft (GitHub already shows it as closed; the draft
   flag is unreachable and immaterial), and the row is marked
   `obligations_expired` so step 4 no longer waits on it.
4. **Retire the tables** only when step 2 has confirmed every live
   artifact withdrawn and step 3 has no row left inside its watch window.
   Until then `pr_state` and `pr_state_transitions` stay, read-only for
   everything but the unwind. Nothing is ever dropped while an open PR
   has `parked_at` set or a `closed_by_bot_at` row is inside its watch
   window; an expired row blocks nothing.

Rollback of a single step (say, labels only) is steps 1 and 2 restricted
to that artifact kind; the tables stay.

## Decisions that need repo-owner sign-off

1. **Auto-close at day 30** (overrides #116). Proposed mitigation: reopen on
   any author activity, closing comment names the exact command, exempt
   labels honoured.
2. **Bot `REQUEST_CHANGES`.** With the main-branch ruleset disabled it does
   not block a merge mechanically, but it is visible on every PR list.
3. **Seven `bot:*` labels** created in the repo.
4. **`MERGE_NOTIFY_LOGINS` fallback** stays a single login until a committer
   catalog exists.
5. **Automatic reviews run in Direct mode only**, keeping the Strict split on
   mention-triggered reviews.

## Risks

| Risk | Mitigation |
| --- | --- |
| Review volume ≈48/day exceeds what one host can finish by morning | budget + window, leftovers carry over, Direct-only for automatic reviews; if the carry-over queue grows three nights running, the dashboard raises it as `attention` |
| Bot `REQUEST_CHANGES` on a false-positive blocker stalls a good PR | dispute path (👎 or reply) removes it from the gate immediately, and the ready page shows the dispute; false-ready and false-block rates are tracked per week |
| Labels edited by humans fight the reconciler | 24 h hold after a human removal; hold is logged and visible on the card |
| Parking/closing a PR whose author is on leave | 30 days total, three notices, exempt labels, reopen on one comment |
| Fork branch deleted after auto-close | reopen impossible; comment says so; `closed_by_bot` stays for the record |
| A stuck lifecycle claim blocks a state (today 266 stale notes sit in `claimed`) | the transition row's `actions_json` is the audit; a claim older than its lease is withdrawn by the existing recovery path, and the kanban card shows "action pending since" |
| Budget exhaustion silently freezes a column | fail closed *and* count it: `PR_STATE_BUDGET_EXHAUSTED` events are on the dashboard's reliability story |

## Acceptance criteria

- [ ] Every open PR in the watched repo has exactly one `pr_state` row and one
      column on the kanban; no PR is in "neither bucket".
- [ ] Same evidence in, same state out, zero new transition rows (property
      test over recorded evidence).
- [ ] A push moves `changes_requested`, `ci_failing`, `ready_for_maintainer`,
      `stale` and `parked` back to `under_review` within one cycle and the
      bot's own `REQUEST_CHANGES` is dismissed.
- [ ] The ready page fires only when all five gate conditions hold, once per
      head, and names the owner with the routing reason.
- [ ] Disputed findings never block and are counted on the page.
- [ ] Dispute → undispute on one head yields exactly one active
      `REQUEST_CHANGES` review at any time: the first is dismissed on the
      dispute, a second with `block_generation + 1` is posted when the 👎
      is removed, and a same-SHA re-run posts nothing more.
- [ ] Partial dispute on one head, `{A,B} → {A} → {A,B}`, edits the body of
      the single active review twice, never dismisses it, never bumps
      `block_generation`, and never posts a second review.
- [ ] Writes follow evidence, not transitions: a PR already in
      `changes_requested` for a conflict gets a `REQUEST_CHANGES` review
      when its review finds a blocker; a `ready_for_maintainer` PR whose CI
      turns red on the same head has its ready page retracted and a
      CI-failed comment posted in the same cycle.
- [ ] Day-7 / 14 / 30 transitions each fire at most once per inactivity
      window across restarts; bot activity never restarts the clock.
- [ ] The sweep never exceeds its budget or window; leftovers are visible.
- [ ] Shadow mode writes nothing to GitHub; each flag promotes its own shadow
      artifacts exactly once.
- [ ] Every new GitHub write is retractable by the reconciler and the
      retraction is logged in `pr_state_transitions`.
- [ ] The bot never merges, never approves, never reopens a human-closed PR.
- [ ] Rollback fixture: with three PRs (one bot-parked, one bot-closed
      inside its watch window, one with an active `REQUEST_CHANGES` and a
      `bot:*` label), the unwind un-drafts the first, leaves the second
      closed but reopens it on the author's later comment, dismisses and
      unlabels the third, and refuses to drop the tables until the second
      PR's watch window has passed.
- [ ] Park → close → rollback → expiry: a PR parked at day 14 and closed at
      day 30 is not touched by the unwind's un-draft step (it is closed);
      an author comment inside the watch window reopens it, marks it ready
      and clears `parked_at`; with no author return the watch expires, the
      row is marked `obligations_expired`, the PR stays closed, and table
      retirement proceeds.
- [ ] A bot-closed PR reopens on the author's comment or on a new head, and
      does not reopen on a comment from anyone else (bystander fixture).
- [ ] A reopen watch is retired the cycle a PR is reopened by anyone; after
      "bot closes → maintainer reopens → maintainer closes → author comments"
      the PR stays closed.
- [ ] A human marks a bot-parked PR ready: `parked_at` is cleared on the
      next visit. If the author then converts it to draft again, even
      between two polls, the PR is an author draft (`draft` state, no clock,
      never un-drafted, never auto-closed), because the timeline's latest
      `convert_to_draft` event is not the bot's.
- [ ] An exempt-labelled PR idle for 14 days is neither `stale` nor `parked`,
      is still swept and can reach `ready_for_maintainer`; a parked PR that
      gains the exempt label is un-drafted.

## Tests

- Projection unit tests: one fixture per state and per precedence pair
  (stale-but-green, conflict-and-red, reviewed-but-CI-pending, disputed-only),
  plus the exhaustiveness fixtures: reviewed green PR, bot-parked, author
  comment without push (→ `under_review` / `resume_pending`); parked PR at
  day 30 with no evidence change (→ `closed` / `action_pending`); a
  randomly generated evidence table must never hit `unclassified` for the
  combinations the RFC names.
- Reconciler tests with a fake GitHub client: crash between transition row
  and action, restart, same-SHA CI re-run, human label removal, fork deleted,
  a deadline visit with zero evidence change that still closes the PR.
- Clock tests: reminder does not restart window; park then push un-drafts;
  park then comment un-drafts; bot-closed then author comment reopens;
  human-closed never reopens; bot-closed → human reopen → human close →
  author comment stays closed; exempt label added to a parked PR un-drafts
  it and exempt-but-idle never parks; **two consecutive close/reopen cycles
  on one PR each get their own claim and both succeed**.
- Sweep tests: budget, window, priority order, backfill quota, carry-over.
- Dispute tests: a reaction-only dispute (author 👎, no reply, no push) is
  picked up on the dispute-scan deadline, dismisses the `REQUEST_CHANGES`
  review and lets the PR reach `ready_for_maintainer` without a model call;
  a bystander's 👎 changes nothing; removing the sole 👎 on a PR whose
  every blocker was disputed re-opens the finding and retracts the ready
  page; a 👎 placed on a carried finding's original comment from an older
  head is found after a push because the scan follows the stored comment
  id.
- Contract tests in this repo: the per-finding result carries `finding_id`,
  `severity`, `head_recheck` and `carried_from` across the SDK boundary; a
  carried blocker closes only with `resolved_or_outdated` + `fixed`, and
  stays open on `still_affected` or omission.

## Metrics for success

Reported weekly on the dashboard, computed from `pr_state_transitions` and
the GitHub API:

- maintainer touches per merged PR (human comments + reviews before merge),
  target ≤ 1 for PRs that entered through the sweep;
- share of merged PRs that were paged as `ready_for_maintainer` before the
  first maintainer comment;
- false-ready rate (maintainer requests changes after a ready page);
- median time from open to `ready_for_maintainer`;
- reopen rate after bot close, and reopened-then-merged count.

## Known defects to fix on the way

- `retry_failed_review` filters on status `timed_out` (`ledger.py:1936,1947`)
  but the writer records `timeout` (`watcher.py:895`), so timed-out reviews are
  never retried; the sweep's carry-over depends on this working.
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
- Whether `draft` PRs get a provisional review in the sweep. Declined for
  now: today's rule ("draft PR 不处理") stands, and drafts opt in by marking
  ready.
