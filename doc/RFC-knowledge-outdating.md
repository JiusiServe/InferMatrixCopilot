# RFC — Knowledge outdating: a rule that stopped being true must stop being served

- Status: proposed — design only, nothing implemented
- Owner: this repo owns knowledge policy — provenance format, lifecycle states,
  proposal/apply semantics and validators — exactly as in
  [`RFC-knowledge-intake.md`](RFC-knowledge-intake.md); ReviewBot owns evidence,
  model, Git and publication orchestration and consumes the versioned public SDK
- Evidence: measured against the live catalog at `e40258d3` and upstream
  `vllm-project/vllm-omni` between `44d3ae10` (2026-09-06) and `3d952d13`
  (2026-09-11) — 116 commits, 828 files changed. Every number below is
  reproducible from those two revisions; the design has no tests yet because it
  has no code yet.

## Motivation

Knowledge **enters** the catalog on a merge event. Nothing ever makes it
**leave**. After six weeks of daily intake the tree holds 104 rule pages and 488
distinct rule IDs, and not one rule has ever been retracted, superseded or
retired.

Three properties of the current pipeline make this structural, not accidental:

1. **The distiller never reads a rule as a claim.** It sees the day's merged PRs
   and their bounded diff excerpts, and writes new sections. At no point does it
   ask whether an existing rule is still true.
2. **The only modelled relationship between new and old knowledge is
   namespace.** Since PR #142 the SDK loads every existing rule ID tree-wide —
   but solely to reject ID collisions. Two rules may assert opposite things
   about the same function and the pipeline is satisfied, provided their IDs
   differ.
3. **Apply is append-only by construction.** `_updated_page` rewrites the
   `updated:` frontmatter field and appends sections. There is no expressible
   operation that marks an existing rule false, so even a model that knew could
   not say so.

The result is not merely incomplete knowledge — it is *misleading* knowledge.
When an upstream PR removes a behaviour, the batch distills a new rule
describing the new behaviour, while the old rule asserting the removed behaviour
stays on the same page, at equal authority, its page `updated:` date refreshed
by the very append that contradicted it. The reviewer receives both in one quick
map with nothing marking which is current. A reviewer that has no rule reads the
source; a reviewer handed two contradictory rules cites one of them.

This is already observable in the tree, not hypothetical:

- **Five rule IDs head a section on two different pages** — `DIFF-1g` and
  `DIFF-1h` (`components/diffusion/rules-output-lifecycle.md` and
  `rules-attention.md`), `MCPMO-4d`, `MMH3-1k`, `MMH3-1n`. PR #142 rejects new
  duplicates; it cannot see the ones that predate it.
- **`MMH3-4e` contradicted `MMH3-4a`** and was folded into it by hand during the
  2026-09-10 curation pass. Nothing in the pipeline would have caught it.
- **Seven rules cite symbols that no longer exist upstream** — `DIFF-2c`
  (`WanTransformer3DModel`), `DIFF-1ag` (`PromptUpdateMixin`), `MMH3-2g`
  (`_normalize_cache_config`), `MOSSTTS-1b` and `Q3TTS-2a` (`npu_rotary_mul`),
  `EXEC-9a` and `OMNIVOICE-1a` (`model_dtype`) — in a five-day window alone.
- **Page-level `updated:` cannot carry freshness.** Every append resets it, so
  44 pages all declare `2026-09-05` while carrying rules distilled in July.

## Non-goal: a freshness scanner

The obvious mechanism — and the one this repo already runs for its own SPEC
pages via `tools/check_spec_freshness.py` — is to flag a rule when the code it
cites changes. Measured over the window above, that does not work here:

| Signal | Rules flagged | Verdict |
|---|---|---|
| a cited file was touched | 456 of 497 (92%) | noise |
| a cited symbol was touched | 405 of 492 (82%) | noise |
| **a cited symbol or file was removed** | **7 of 492 (1.4%)** | **signal** |

vLLM-Omni merges roughly 24 PRs a day; 828 files moved in five days. Any
detector keyed on *change* flags four rules in five every week, and the two or
three genuine staleness events drown. The SPEC gate works for this repo's own
docs because this repo is not that hot — the same design applied to the rules
catalog would produce an alarm nobody can act on.

The distinction that carries signal is **existence**, not change: did the thing
the rule names stop existing. In the same window 221 definitions were removed
without being re-added and 7 files were deleted, and the seven rules that
intersect them are all genuinely stale. That is a reviewable volume — one to two
rules a day.

## Design

### 1. Per-rule provenance

Every rule carries, inline, a compact marker appended to its existing source
footnote: the upstream SHA it was verified against and the date. Bulky anchors —
the upstream paths and symbols the rule constrains — live in a per-owner sidecar
committed beside the page.

The split is forced by the page cap. A full inline trailer costs 92.4 KiB across
the catalog and pushes four pages past the 32 KiB validator limit immediately
(`components/scheduler/rules.md` by 3,718 bytes, `models/minimax-h3/rules.md` by
1,743, `models/minicpm-o-4-5/rules.md` by 903, `components/serving/rules.md` by
899). The compact marker costs 12.6 KiB and pushes only `scheduler` over, by 274
bytes — a page that must be split regardless, since it sits at 272 bytes free.

Anchors are not invented: the distiller already receives `changed_paths` per
evidence event and discards them. This RFC keeps them.

Per-rule granularity is mandatory, not a preference. Page-level markers alias:
one append refreshes the whole page and 20 older rules on it silently claim
today's date.

### 2. Channel one — reconcile at write time

The PR that invalidates a rule is almost always the PR that touches that rule's
code, so the routing that selects owner pages for today's batch already brings
the right old rules into view.

Each proposal gains a required relation field: `new`, `supersedes: [ids]`, or
`contradicts: [ids]`, with the routed pages' existing rules shown in the prompt.
This costs no extra model call and no extra evidence — the diff excerpts and the
tree-wide rule-ID map are already loaded. It converts the daily batch from
*append* into *reconcile*, and it is the mechanism that would have caught
`MMH3-4e` against `MMH3-4a`.

### 3. Channel two — removal as the trigger

Per batch, compute the definitions and files that ceased to exist between each
rule's `verified-against` SHA and the batch head, and intersect with rule
anchors. Flagged rules enter the same daily PR as mandatory supersede-or-retire
decisions.

Critically, this signal is **machine-checkable**: the SDK confirms the anchor is
absent at the head SHA without trusting the model's judgment.

### 4. Channel three — the reviewer as sensor

Semantic staleness — the code still exists but the rule's claim about it is now
false — is invisible to both channels above. The only component that ever
compares a rule against current source is the reviewer, which already reads
every cited file at the frozen head under the Direct contract.

The reviewer reports that a served rule contradicts source at the reviewed head
through the mailbox issue already built for `pr_debug` records
(`KNOWLEDGE_INTAKE_ISSUE`, JiusiServe/InferMatrixCopilot#135), which has to date
carried zero comments.

This channel has a prerequisite the others do not: **nothing in the review path
records which rules a review was served or used.** `rule_id` appears only in the
knowledge write path; a stored review artifact contains no rule IDs and no route
references at all. That instrumentation ships first.

### 5. Lifecycle and archive

States are `active`, `contested`, `superseded(by)`, `retired(reason)`, following
ADR practice: a record is never deleted, only superseded or deprecated.

Superseded and retired rules **move** to a per-owner `rules-archive.md`, leaving
a one-line tombstone in the live page pointing at them. Archive pages stay out
of Direct routing: findable in git, invisible to the reviewer.

This is also the first mechanism that ever returns bytes to a rule page. The
catalog is append-only today, which is why every capacity incident so far —
`ci/rules.md`, `configuration/rules.md`, and now `scheduler` at 272 bytes free —
has been resolved by a hand-run page split.

### 6. Trust display

A rule that is `contested`, or whose `verified-against` predates its owner shelf
life, is served marked so the reviewer must confirm it against source before
citing it as authority. The marker must be a flag character, not prose: the
Direct quick map is capped at 3,500 characters by test.

## Safety: full lifecycle authority, bounded

The agent may supersede, retire and archive within the daily batch; the PR
review remains the only promotion gate, preserving the knowledge-plane invariant
that agents propose and humans promote. The risk this accepts is that a
misjudging model can now remove correct knowledge, and that a large lifecycle
diff degrades the human gate into a rubber stamp. Five constraints bound it
without reducing the authority:

1. **Retirement is never destructive.** A retire moves the section to the
   archive page in the same commit and leaves a tombstone. Nothing is deleted;
   a wrong retirement is a one-line revert.
2. **Retirement is gated on a machine-checked fact.** The SDK verifies the cited
   anchor is genuinely absent at the head SHA. A model that merely believes a
   rule is obsolete can mark it `contested` but cannot retire it.
3. **Supersede requires a named live replacement** present in the catalog or the
   same batch, reusing the `allowed_sources` discipline that already governs new
   rules.
4. **Lifecycle actions carry their own budget**, separate from the eight-rule
   proposal budget, starting at five per day against a measured one to two. This
   is what keeps the diff small enough for the gate to stay real.
5. **Lifecycle changes land in their own commit** inside the daily PR, so what
   left the catalog is reviewed separately from what joined it.

Rejections stay fail-closed with persisted reasons, reusing the machinery from
omni-reviewbot#40.

## Rollout

**Increment one** — instrumentation plus the two free channels. In this repo:
per-rule marker and sidecar written at distill time; the relation field in the
proposal schema; the anchor-absence verifier; the archive apply path; sidecar
to page 1:1 enforcement in `knowledge/tools/check_knowledge_tree.py`. In
ReviewBot: the existing-rules prompt section, per-batch removal computation, the
lifecycle budget and commit separation. Across both: log the rule IDs Direct
serves and the review cites.

The same write path carries two already-open defects, which this increment
closes: apply updates neither the `sources:` frontmatter nor `_index.md`.

**Backfill** — all 488 rules start undeclared. Anchors and `verified-against`
are backfilled mechanically from each rule footnote of the form `PR #n` via the
GitHub API. The cheaper alternative, declaring an amnesty at the current
`release_baseline.yaml` `audited_sha`, is rejected: it would make the
re-verification ordering meaningless for the length of a full sweep.

**Increment two** — channel three, and a bounded re-verification sweep ordered
by oldest `verified-against`, designed against the usage data increment one
produces rather than against assumption.

## Honest limits

- The 1.4% figure extracts symbols from backticked prose, not from stored
  anchors, because stored anchors do not exist yet. It is a proxy; real coverage
  will shift once anchors are explicit, most likely upward.
- Channels one and two catch structural staleness. A rule whose claim quietly
  became wrong while every symbol it names still exists is caught only by
  channel three, and only if the reviewer notices.
- Removal flags are advisory, never blocking in CI. A rule goes stale because
  upstream moved, not because the PR under test did; failing this repo build on
  a third party merge would be wrong.
- The re-verification sweep competes for the same daily model budget as intake,
  which is already draining 20 rows a day against roughly 24 arriving. Increment
  two must resolve that contention explicitly rather than silently deepening the
  backlog.
