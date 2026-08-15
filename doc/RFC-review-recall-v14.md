# RFC — Strict review v14/v15: recall attack (duties, docs pass, second round, archaeology tools)

- Status: implemented behind settings (default ON); measured through the
  wave-4 gate — see "Measured results" below and
  `eval/dataset/results/model_comparison.md`
- Owner: review pipeline (`engine/steps/review/`, `review/planner.py`)
- Evidence: wave-2 forensics (3 trace-analysis agents over the spent holdout),
  Claude Fable 5 teacher arm on the train split
  (`eval/dataset/baselines/teacher_fable5/`), `doc/EVAL-goal-strict-vs-opus5.md`
- Predecessor: `doc/RFC-strict-review-deep-engine.md` (v13)

## Motivation

Under the standing claude-sonnet-5 judge, every v13 generator (DS api,
Composer/Grok via cursor backend, MoA) lost to CC+Opus 5 on strict-credit
recall (~0.29–0.35 vs ~0.42–0.56) with precision at parity. Per-item analysis
showed the loss concentrated on five wave-2 items (three docs PRs + 5884 +
5550); trace forensics with GT cross-reference located the losses precisely:

1. **Read-not-raised at the pass stage** (dominant): in every diagnosed miss
   the decisive evidence was in front of a pass — reducer/budget/verify were
   exonerated (`dropped: 0` everywhere). Passes accepted the author's framing
   (pr5550), re-derived numbers in confirm-mode (pr5863 memory model blessed;
   pr5840's own R²=0.095 unremarked), and never opened the in-tree sibling
   whose invariants the new code dropped (pr5550 L1, pr5884 F2).
2. **Report-assembly cuts**: the Validated render kept 8 arrival-order lines
   of 50+; on post-fix snapshots the judge's recall mass sits exactly in the
   resolved-thread confirmations being cut. Three verify-confirmed comments
   died at the cap-8 + rich-only overflow gate (pr5957). Anchor-unresolved
   repo-side comments rendered `file:?` and were docked as vague.
3. **Docs starvation**: docs-only diffs planned light (single pass, no
   protocol) while 30% of the holdout was docs PRs whose GT is claim
   corrections; every arm ran at roughly half the baseline's recall there.
4. **Pass death**: deep passes exhausting their budget sometimes answered the
   forced final with an EMPTY message (pr5976: two passes, 50 tool calls each,
   zero candidates delivered).
5. **Tool gaps**: the judge-decisive baseline moves — `git diff --stat
   base..HEAD`, reading a file at base, `git show`/`log -S` archaeology,
   evaluating the PR's own arithmetic — were inexpressible in the read-only
   toolset.

A Claude Fable 5 teacher arm over the train split (same pinned CC harness as
the baseline) confirmed the classes and added more; its shared-contract
producer census caught the pr4870 GOLD latent gap (the exact #4910 dual-axis
mechanism) that human review missed. Teacher and Opus both exhibit these
duties; our v13 prompts encoded none of them — supporting "pipeline gap", not
"model capability gap".

## Design

### 1. Investigation duties (prompts.py checklist 13–21 + pass focus)

Distilled from the union of Opus/Fable moves, each with a measured exemplar:
claim ledger (verify every checkable PR-body claim; `[claim-verified]`/
`[claim-refuted]` findings lines); sibling contrast (added class/file → read
the in-tree twin; invariants delta; concrete dedupe proposal); the PR's own
numbers (falsify with `calc`, never confirm-mode); merged-state revalidation
(semantic-merge audit); producer/consumer contract census incl. dummy-run/
platform twins; mode/variant matrix with loud-failure checks; dead-knob
recompute + comment audit; cache pathology; dispatch-linkage guard (the one
teacher false positive, encoded as a precision protection). Resolved-thread
confirmations became a first-class output (`[resolved]` prefix): on amended
heads they are most of what a reader checks a review against.

### 2. Docs pass (`_REVIEW_DOCS_PASS`) + planner depth

Docs-only/docs-heavy diffs: light only when genuinely small; mid → standard,
large → full (planner rules; asset/config riders no longer push docs PRs into
the gray zone). The deep engine swaps the code-shaped breadth lenses for a
docs pass: claims audit (falsify factual/quantitative statements against the
tree), user-journey walk (commands end-to-end, download-pattern vs restart
collisions), link/pin/nav mechanics under both rendering conventions, and
missing-caveat scope.

### 3. Archaeology + numeric tools (`review/repo_tools.py`)

`diff_stat`, `file_at_base`, `show_commit`, `search_history` (git, fixed
argv, validated inputs, bounded output) and `calc` (AST-whitelisted
arithmetic). Step-provided extra tools on every review pass and the verify
pass; reconstructed bridge-side from `scope.root` for harness backends
(closes that slice of the provider-registry M1 extra-tools gap).

### 4. Coverage-driven second round (RFC v13 open q3; `review_second_round`)

After reduce+promote, changed files with neither a comment nor a findings
line — plus an unchecked-claims signal — seed ONE bounded pass
(`review_second_round_max_iters` 16) that must either raise a verified
comment or record `[validated]`/`[resolved]` for each hole. Near-dup guard
against kept comments; additions face the same per-comment verify pass.

### 5. Report assembly fixes

Validated ledger ranked (`[resolved]`/`[claim-*]` first) and capped at 14,
not truncated in arrival order at 8; overflow renders verify-confirmed cut
comments even when the review is not "rich" (unverified tail still needs the
rich gate); anchor-unresolved comments render `file:~declared` instead of
`file:?` (publish still treats them as body-only); verify-pass evidence for
repo-side findings must carry the "unchanged by this diff, present in the
PR-time tree" attestation so a diff-only judge can classify it.

### 6. Loop robustness

An empty model reply after real tool calls gets exactly one loud nudge
(mid-loop and at the forced budget-exhausted final) — an empty final is the
only outcome strictly worse than any partial answer. Coverage-promotion
prompt de-hedged: promoted defects keep directive force ("could you
confirm…?" phrasing measurably converted a GT-matching concern into an
uncredited question).

## Cost

Docs PRs move light → standard/full (~2–3× on ~15% of items); second round
adds ≤1 pass on items with coverage holes; tools are subprocess-cheap. The
arm remains well under half the baseline's $/item.

## Rollout

Everything sits behind settings (`review_second_round`, existing deep-engine/
verify switches); the legacy path is untouched. Offline tests cover the new
planner rules, docs pass selection, second round (trigger/skip/near-dup),
overflow gate, ledger ranking, anchor fallback, loop nudges, and every new
tool including calc's sandbox. Knowledge checklist page rewritten with
teacher-distilled repo priors (injection cap 4k→7k chars).

## Measured results (added after the gates)

Train probe (v14, 2 sonnet replicates): 7—12—1, arm r .608 vs opus .609
(recall parity — sonnet-judged arms previously sat at ~.28–.35), arm p
.785 vs .765. Wave-3 gate attempt 1 measured broken machinery, not the
design: pass finals died at the 16k completion ceiling (a docs pass
emitted exactly 16,000 tokens), the repair round re-truncated at 8k with
a head-only window, and the gray-zone LLM planner had been silently
failing since the official reasoning model landed (its thinking consumed
the 400-token cap with zero text emitted — every gray item fell to
2-pass standard across two campaigns). Attempt 2 (machinery fixed):
5—25, with the losses relocated to a duties-vs-GT mismatch that wave-3
forensics then characterized (validation-bias inversion: the claim
ledger recorded the GT facts approvingly; test/gate epistemics, docs IA,
and CI-economy classes unowned). v15 encoded those classes (checklist
22–23, docs-IA extension, ledger-residue promotion, per-hunk second
round) plus the reducer failure-path collapse.

Wave-4 clean gate, three DS-core submissions (v15 r1, v15 r2 with
cheap seats on v4-flash, v16 with Fable in the adversary and
second-round seats) plus a Composer cursor-backend row. Raw win counts
10—20, 11—19, 6—23—1, 4—24—2.

**The statistically correct read (see `eval/dataset/paired_analysis.py`
and the results table) is parity within measurement precision, not
superiority.** Comparing raw rubric means across judgment sets is
invalid here: the baseline's own recall mean read .335 / .338 / .416
across three sets scoring the *same* baseline reviews (±.08 judge
drift). Pairing inside each verdict and clustering replicates by item
gives, pooled over 90 verdicts, Δrecall −.070 [−.161, +.021] and
Δprecision +.015 [−.025, +.055] — both intervals span zero. An earlier
revision of this RFC claimed precision above baseline from the raw
means; that claim is withdrawn.

What the campaign did establish: the arm reaches parity at ~1/3 the
cost ($0.97/item vs $3.09); the aggregate recall gap is carried by 3 of
10 items (the other 7 within ±.06); v15 leans precision (Δp +.029/+.022
across two independent replicates, same sign) while v16 leans recall
(best fresh-split recall .336) and reproduced the pr4870 GOLD-gap catch
*inside* the pipeline; and resolving a .07 difference at the observed
item-level sd (.127) needs ~32 items, which is why wave 5 extends the
fresh pool rather than another 10-item verdict being run. A v15
replicate was first invalidated by a DeepSeek 402 balance outage
(quarantined) and rerun after recharge.

## Open questions

1. Wave-3 (`build_wave3.py`, split `holdout3`) is the promotion gate; wave-2
   is spent (GT/rationales opened for this forensics round) and can only
   smoke-test.
2. The second round currently seeds on file coverage + claim coverage; the
   reducer's drop-reasons remain unplumbed (candidate seed for a future
   round).
3. GT on post-fix snapshots measures resolved-thread engagement, not
   bug-finding; the `[resolved]` channel targets exactly that — whether the
   judge credits it at scale is what the gate measures.
