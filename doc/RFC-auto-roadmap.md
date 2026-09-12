# RFC — Auto roadmap: the taxonomy is human, the status is not

- Status: proposed — design only, nothing implemented
- Owner: this repo owns the roadmap document contract — marker grammar,
  feature/edge/attachment schema, the extraction quote gate, status derivation
  and the body/mermaid renderers — and ships it in the versioned public SDK, as
  in [`RFC-knowledge-intake.md`](RFC-knowledge-intake.md); the management bot
  (today `omni-reviewbot`, being refactored from review to management) owns
  enrollment discovery, GitHub I/O, model calls, the state of record, the hosted
  service and its authentication. One deliberate deviation from that precedent
  is named in [Ownership](#ownership).
- Evidence: measured against `vllm-project/vllm-omni` over **2026-08-17 to
  2026-09-11** — 300 merged PRs, 19 roadmap/tracking issues, and the 25 PRs
  curated onto the world-model roadmap #7074. Every number below is reproducible
  from the GitHub API over that window; the design has no tests yet because it
  has no code yet.

## Motivation

vLLM-Omni runs **19 roadmap/tracking issues**, written by 15 different authors.
Exactly one of them is current, and it is current because a person is holding it
upright by hand: #7074 took **88 body edits in six days** — 24, 24, 26 and 12 on
the last four — every one of them from the same account.

The other eighteen decay. #6494, *"[RFC][Tracking] Full-Duplex Serving Roadmap
and PR Status"*, tracks 129 PR and issue numbers, was last body-edited on
2026-09-05, and **five of the PRs it tracks have merged since** without the body
changing. Eight of the nineteen have not been touched in two weeks or more,
the oldest since 2026-07-15.

This is structural, not a discipline problem. Three properties guarantee it:

1. **The status in the body is a copy, not a view.** Every `Merged`, every
   merge date, every owner handle in the table is a literal typed at edit time.
   When a PR merges, nothing in the system knows that a roadmap claimed
   otherwise. The roadmap cannot go stale slowly — it goes stale the moment
   upstream moves, and stays wrong until a human notices.
2. **Nothing links a PR back to the roadmap it belongs to.** Of the 25 PRs
   curated onto #7074, **2 cite the roadmap RFC at all** (8%). The membership
   relation exists only in the roadmap document, in the direction that cannot be
   queried.
3. **The rendered graph is a second copy of the same facts.** Statuses are
   restated as mermaid `class` assignments in a different namespace, so each
   merge needs two edits that can disagree — and already do. #7074's graphs
   carry **36 edges but only 6 between named features**, wiring PR numbers and
   pseudo-nodes (`READY`, `BASE`, `PROF`) instead, while **14 of 19 feature
   sections state a dependency in prose** (`— P0 after E1`, `E5 … requires`,
   `E2 … depends on`). The drawn graph and the written graph are already
   different graphs.

The cost is not only the editing. A roadmap is read as the authority on what is
done; a roadmap that is confidently wrong about five merged PRs misdirects the
people who trust it, and that is worse than a roadmap nobody reads.

## Non-goal: deriving the roadmap from PR traffic

The reading of "auto dive the relationship of feature/rfcs/prs" that the issue
invites is a classifier: watch merged PRs, infer which feature each belongs to,
draw the graph. Measured over the window above — 300 merged PRs, about **12 a
day** — that does not work:

| Signal | Flags | Of the 8 curated in-window | Verdict |
|---|---|---|---|
| PR cites the roadmap it belongs to | 2 of 25 curated PRs | — | **8% recall** — the edge is not written down |
| PR body cites any issue | 108 of 300 (36%) | — | mostly unrelated issues |
| PR body cites an **RFC** issue | 22 of 300 (7%) | — | too sparse to build on |
| title keyword (`lingbot`/`minimax`/`ar-diffusion`/`world`…) | 40 of 300 (1.5/day) | 6 | **15% precision** |
| label `world model` | 2 of 300 | 1 | applied to 0.7% of traffic |
| label `diffusion` | 87 of 300 (3.3/day) | 6 | **6% precision** |

A classifier over these proposes roughly one and a half PRs a day of which
about one in seven belongs. And the denominator tells the real story: a human
selected **8 of 300** merged PRs as roadmap-relevant. The roadmap is a
*selection*, and the selection is judgment — which model to prioritise, which
refactor counts as a milestone, which bugfix is noise. That judgment is not
recoverable from the artifacts, because it was never written into them.

What the same signals are good for is **prefiltering**: the title keyword carries
88% recall (22 of the 25 curated PRs) while cutting the candidate set to 40 of
300. Useless as a classifier, exactly right as a gate in front of one.

And one thing *is* derivable, completely and without a model: **status**. A PR's
state, merge commit, merge date, author and assignees are API facts. Every hour
of the 88 edits went into copying those facts by hand.

So: the agent maintains and extracts. It never invents.

## Design

### 1. Enrollment is the consent

A roadmap is managed only if its body carries an enrollment marker, placed by
the issue author:

```
<!-- roadmap: v1 managed
     tracks: E, L, M
     propose-attachments: on
     prefilter: lingbot, minimax, ar-diffusion, world, realtime
-->
```

Eighteen of the nineteen roadmaps belong to other people. Editing someone's
issue body because an operator added a number to a config file records the
wrong party's consent; a marker in the body is the author's own, revocable by
deleting one line, and it travels with the artifact. **No marker, no write — not
even a comment.** An unknown schema version blocks loudly rather than writing a
body it half-understands (invariant 7).

### 2. The recurring write target is a comment the bot solely owns

The obvious target is the body itself — #7074 already carries
`<!-- roadmap-status:start … end -->`, a `<!-- feature-status -->` marker per
feature, `<!-- roadmap-people: {…} -->` and `%% roadmap-colors:start … end %%`,
put there by hand for a renderer to read. Writing back into those regions and
guarding it with a hash of the human-owned text does not work, and the reason is
not subtle:

**GitHub has no conditional write for an issue body.** `PATCH /issues/:n`
replaces the body unconditionally; there is no `If-Match`, no
compare-and-swap. So read-check-write is a genuine time-of-check/time-of-use
race, and at 24 human edits a day on a single roadmap with an hourly bot write,
the window is not theoretical. Two failures follow directly: an edit landing
between the check and the `PATCH` is silently destroyed, and — worse — a bot
splicing into a body it cached can **restore an enrollment marker someone just
deleted**, so revocation (§1) would not actually revoke.

So the recurring lane does not write the body at all. The agent maintains **one
comment per enrolled roadmap, of which it is the sole author**, holding the PR
table, the last-verified line, the consolidated feature-status table, the
people map and the rendered mermaid. There is no human content in the region
it replaces, so there is nothing to clobber and no concurrency guarantee to
fake. The body keeps the taxonomy, the prose and the enrollment marker, and the
bot only ever *reads* it.

The cost is honest and small: the canvas parses the bot comment instead of the
body, and per-feature status stops being inline beside each feature's prose,
becoming one table in the comment. The canvas is ours to change. The alternative
— a write path that loses a maintainer's edit a few times a month and cannot
honour a revocation — is not.

The body is written exactly twice in this design: once by the bootstrap (§3),
one-shot and confirm-gated, and once per accepted attachment (§6). Both are
rare, human-triggered and supervised, and both re-read the body and splice into
*that* read immediately before writing, aborting if the enrollment marker is
gone. A supervised one-shot can carry a residual race that an unattended hourly
loop cannot.

### 3. Bootstrap: extraction under a quote gate

A repo with no machine-readable roadmap needs an on-ramp, and the material is
already there: **19 of 19 roadmaps carry headings or checklists, 12 of 19 carry
a PR table, 12 of 19 name five or more PR numbers.** The taxonomy has been
written; it is only trapped in prose.

So the bootstrap is an extraction, and extraction can be gated the way
clustering cannot. Every feature, edge and PR attachment the bootstrap emits
carries the verbatim span of the source body it came from. A validator re-reads
the body and rejects any element whose quote is not present character for
character. **Nothing is emitted that a human did not already write** — the same
discipline `allowed_sources` imposes on distilled rules.

Edges come from both the prose (14 of 19 sections) and the mermaid graphs (6
feature-to-feature edges), both cited. Where they disagree, the extraction
records both and the human resolves it once, during accept. After that the
mermaid graph becomes **rendered output**, regenerated from the feature graph
into the bot comment (§2) rather than maintained as a second source that can
drift from the prose. That retires the copy described in Motivation (3): the
body states dependencies once, in prose, and the drawing is derived from it.

The bootstrap is one-shot and human-accepted as a whole draft. It is explicitly
not a recurring job: re-extracting a body the agent itself now maintains would
launder its own output back into evidence.

### 4. The maintain loop: two lanes, two cadences

The two kinds of work have opposite economics, and the entire measured cost sits
in the cheap one.

**Lane one — status. Every poll cycle, no model call.** For each tracked PR,
read state, `mergedAt`, author and assignees from the API; recompute the four
agent-owned regions; write. This is all 88 of the hand edits and all five of
#6494's stale rows. It costs API calls on ~25 PRs and nothing else. Because it
has no LLM dependency, a model outage degrades proposals only — the roadmap
everyone reads stays correct.

**Lane two — attachment proposals. Once a day, one batched model call per
roadmap.** The enrolled prefilter cuts the day's merges to roughly 1.5
candidates; the model judges those against the feature list and emits proposals
with evidence. Never a write to the body.

### 5. The agent reports PR state; it does not declare features done

#7074 says it plainly: *"Merged means the linked implementation landed, not that
all performance or service acceptance criteria passed"*, and *"E3, L1, L4–L6
include integration or validation beyond their linked PRs"*. E2 is held at
`partial` by human judgment while camera interaction is unfinished, even though
its linked PR merged.

So the rollup the agent computes is **PR-linked state only**. Where a feature
carries a human-set verdict, the agent renders that verdict and reports the PR
facts beside it — it never overwrites an acceptance judgment with an arithmetic
one. A roadmap that auto-marks a feature complete because its PR merged is a
roadmap that lies faster than a stale one.

### 6. Promotion and the service

Proposals land in the state of record and surface in the management bot's
roadmap service, where a maintainer accepts or rejects. An accept adds the PR to
that feature's tracked set — which is taxonomy, so it is one of the two writes
that touch the body (§2), performed immediately while the maintainer is present
rather than deferred to a cycle. Rejections persist with their reason,
fail-closed, reusing the rejection machinery from omni-reviewbot#40.

The service authenticates with GitHub OAuth and authorises on **`push`
permission to the target repo**, so an accept is attributable to a person with
real authority over the roadmap — the authority the gate's legitimacy depends
on. This is the first authenticated surface on a host that has only ever served
anonymous `do_GET`, which is why §Safety bounds what a session can do.

## Safety: an ungated upstream write, bounded

A comment edit and an issue-body edit both land in a third-party upstream repo
with no PR gate. This RFC accepts that, and bounds it:

1. **The recurring lane writes only what the bot authored** (§2). Human text is
   not in its reachable set, so the hourly loop cannot lose an edit no matter
   how the race falls.
2. **The two body writes are supervised and splice into a fresh read.** Both
   bootstrap and attachment promotion re-read the body immediately before
   writing, splice into that read rather than a cached copy, and abort if the
   enrollment marker has gone. This does not close the race — GitHub offers no
   conditional write — it bounds it to a request round-trip on an operation a
   human just triggered and is watching.
3. **Every write is revertable to an exact prior text.** The state of record
   commits the pre-write body or comment before the write, so recovery is a
   restore, not a reconstruction. This is the main reason the state of record
   exists at all, and it also lets the canvas render while the issue is
   mid-edit.
4. **The HTTP surface takes a proposal id and a verdict, never roadmap
   content.** It can only apply proposals the agent already computed and
   quote-validated, and every apply re-runs the quote gate before writing. A
   session compromise buys an attacker "accept a proposal that was already on
   offer" — not arbitrary writes into upstream issues with the bot's token.
5. **Acceptance verdicts are out of reach** (§5), as is any roadmap carrying no
   enrollment marker (§1).

Outward writes stay double-gated as everywhere else: explicit post intent plus
the environment flag.

## Ownership

The contract lives here and ships in the versioned public SDK: marker grammar,
feature/edge/attachment schema, the quote-gate validator, status derivation and
the body/mermaid renderers. All of it is repo-neutral — `adapters/vllm_omni/`
carries nothing but the enrollment of #7074 (invariant 6).

The management bot owns every side effect: enrollment discovery, GitHub I/O,
model calls, the state of record, the service and its OAuth.

**The deviation from `RFC-knowledge-intake.md`:** the bootstrap runs as a task
kind in this repo (`roadmap_bootstrap`, tier L2 — reads the target repo, writes
knowledge, confirm-gated, like `repo_profile`), not as SDK functions the bot
orchestrates. Bootstrap is one-shot, judgment-heavy, and writes into someone
else's RFC; it wants exactly what the execution spine provides and the bot does
not — `--plan-only` preview, a confirm gate, evidence archived, a run report.
The maintain loop stays in the bot, where a per-cycle refresh belongs and where
the spine deliberately will not run a write-capable kind unattended.

## Rollout

**Increment one — the contract and the status lane.** SDK: marker grammar,
schema, validators, renderers, status derivation. Bot: enrollment discovery, the
bot-owned status comment and its poll-cycle refresh, the state of record and its
revert path. Canvas: parse the comment instead of the body. Enrol #7074 only.
This writes no issue body, needs no model, no authentication and no bootstrap,
and it removes the entire measured cost: the 24 edits a day, and the five-row
drift on #6494 once that roadmap enrols.

**Increment two — bootstrap.** The `roadmap_bootstrap` task kind and the
quote-gate validator. Run against the other eighteen roadmaps only as their
authors enrol them.

**Increment three — the judgment lane and the authenticated service.** OAuth,
the push-permission check, the proposal apply path, and the daily batched model
call.

The order is deliberate: increment one carries 100% of the measured cost and
requires neither a model nor a new security surface, and increment three — the
one that puts authentication on a public host — must not gate it.

## Honest limits

- **The precision numbers rest on one roadmap.** 25 curated PRs, 8 of them
  inside the measured window. That is thin, and it is the only labelled
  attachment data that exists. Increment three should re-measure against
  whatever enrols before its budget is set.
- **`world model` precision of 50% is on n=2.** Listed for completeness; it is
  not a usable measurement.
- **Extraction inherits the source's errors.** A roadmap that is already stale
  extracts cleanly into a stale machine-readable roadmap. Only the maintain loop
  fixes that, which is the argument for bootstrap being an on-ramp and never a
  recurring job.
- **The feature→PR link stays human-maintained**, and the status lane is only as
  right as that link. A feature whose PR list is wrong becomes confidently wrong
  faster than before. Nothing here detects a PR that should have been on the
  roadmap and never was — that is exactly the 15%-precision problem, and it
  stays a proposal for a human.
- **12 merged PRs a day is this repo over this window.** A hotter repo changes
  the prefilter arithmetic and the daily budget; it does not change the design.
- **The two body writes carry an unclosable race.** GitHub exposes no
  conditional update for an issue body, so bootstrap and attachment promotion
  can still overwrite an edit made in the round-trip between their final read
  and their write. Moving the hourly lane to a bot-owned comment removes this
  for everything that runs unattended; for the two supervised writes it is
  reduced to a window a human is watching, and the state of record makes it
  recoverable. It is not eliminated, and no design against this API can
  eliminate it.
- **OAuth on the management bot host is a new security surface.** The blast
  radius bound in §Safety(4) limits what a compromised session reaches; it does
  not remove the surface, and it is the single riskiest thing this RFC proposes.
