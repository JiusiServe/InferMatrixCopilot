# Campaign report — v14→v16 recall attack (2026-08-15)

Successor to `doc/evaluation/EVAL-goal-strict-vs-opus5.md` (the v7→v13 campaign, which
ended at 15—15 combined fresh verdicts under a GPT judge and a −.16 recall
ratio under the Sonnet judge). This campaign's goal, set by the owner: make
the Strict pipeline beat the recorded `baselines/claudecode_opus5` arm on
**both** recall and precision, using cursor-agent-based configurations and
distillation from Fable traces.

**Result in one line: the arm matches CC+Opus 5 on precision and trails it on
recall by about five rubric points, at roughly a third of the cost — settled
by a pre-registered 20-item measurement, after an earlier claim of superiority
had to be withdrawn as a statistical artifact.**

## What was built

Method: forensics on spent splits (per-GT-finding coverage matrices with
stage-of-loss classification from the arms' own traces), plus a Claude Fable 5
*teacher arm* run through the identical pinned harness as the baseline on the
train split — which caught the pr4870 GOLD latent gap exactly (the #4910
dual-axis mechanism human review missed), giving a concrete distillation
target rather than a stylistic one.

Landed (all default-on, kill-switched, `doc/features/review-recall.md`):

* **Investigation duties** (checklist 13–23): claim ledger, sibling contrast,
  falsification of the PR's own numbers, semantic-merge audit, producer/
  consumer census, test/gate epistemics + CI economy, differential parity,
  dead-knob recompute, cache pathology.
* **Docs claims-audit/IA pass** replacing the code-shaped breadth lenses on
  docs-heavy diffs, plus planner depth scaling for docs.
* **Archaeology tools** — `diff_stat`, `file_at_base`, `show_commit`,
  `search_history`, `calc` — read-only, bridged to harness backends.
* **Coverage-driven second round** (the v13 RFC's open q3), seeded per-hunk
  from the run's own coverage holes with uncapped per-file diff slices.
* **Ranked verification ledger** with `[resolved]`/`[claim-*]` channels, and
  ledger-residue promotion (forensics found the misses were often already
  written down by the arm, recorded approvingly instead of raised).
* **Machinery fixes**, two of them long-latent: pass finals dying at the token
  ceiling with a crippled repair round, and the gray-zone planner silently
  failing on every gray item since the official reasoning model landed (its
  thinking consumed a 400-token cap before any JSON could appear).
* **Per-pass backend routing** (`review_lens_backends`), which turns the
  measured model complementarity into one arm.

## What was measured

Judge: claude-sonnet-5, blind pairwise, 3 replicates, against the pinned
Opus 5 baseline on identical frozen snapshots. Gates: wave 3 (spent, two
disclosed attempts), wave 4 (clean, three DS-core configs), wave 5 (power
extension, pre-registered).

| config | raw wins | Δrecall [95% CI] | Δprecision [95% CI] |
|---|---|---|---|
| v15 (all-DS) r1 | 10—20 | −.075 [−.184, +.035] | +.029 [−.022, +.080] |
| v15 r2 (flash cheap seats) | 11—19 | −.056 [−.175, +.064] | +.022 [−.027, +.071] |
| v16 (Fable adversary/round-2) | 6—23—1 | −.080 [−.169, +.010] | −.006 [−.069, +.058] |
| Composer cursor-backend | 4—24—2 | −.081 [−.206, +.044] | −.045 [−.095, +.005] |
| **pooled DS-core, 90 verdicts** | 27—62—1 | **−.070 [−.161, +.021]** | **+.015 [−.025, +.055]** |

Δ = arm − baseline, paired inside each verdict, clustered by item
(`eval/dataset/paired_analysis.py`). Cost: $0.97/item vs $3.09.

## The measurement lesson (the part worth keeping)

Mid-campaign this report would have claimed "precision above baseline on a
fresh holdout" — computed from each side's raw rubric mean. That claim was
**withdrawn**, because the raw means cannot support it: three wave-4 judgment
sets scoring the *same* baseline reviews returned baseline recall means of
.335 / .338 / .416 — ±.08 of pure judge drift, larger than every effect under
study. Pairing within the verdict (one judge call scores both candidates, so
its leniency cancels) and clustering replicates by item gives intervals that
all span zero.

Three consequences, all of which generalize past this campaign:

1. **Never compare an arm's mean from one judgment set against a baseline's
   mean from another.** Pair inside the verdict.
2. **Replicates of one item are not independent observations.** Ten items × 3
   replicates is n=10 for the CI, not n=30; treating it as 30 understates the
   standard error roughly two-fold.
3. **Check power before spending a holdout.** At the observed item-level sd
   (.127), resolving a .07 difference needs ~32 items. Wave 4's 10-item gates
   never could have answered the question they were run to answer — three
   configs were submitted against a bar the design could not measure.

## The pre-registered answer (wave 5)

Wave 4's 10-item gates could not resolve the effect they were run against, so
wave 5 was drawn, frozen, and **pre-registered before any wave-5 number
existed** (`eval/dataset/goal-eval/PREREG-wave5.md`): arm, items, judge,
analysis and decision rule fixed in advance, including the instruction not to
run a third wave if the interval still contained zero.

Primary analysis, v16 pooled over wave 4 + wave 5 (20 items, 60 verdicts):

| statistic | value | rule triggered |
|---|---|---|
| **Δrecall** | **−.049 [−.097, −.001]** | CI below 0 → the deficit is REAL; stop claiming parity on recall |
| **Δprecision** | **−.000 [−.041, +.040]** | CI contains 0 → parity |

The recall result is marginal (upper bound −.001) and should be read as *a
real but small deficit*, not a large one. It is also concentrated: of the 20
pooled items, 6 favour the arm, 4 are inside ±.02, and one item (pr5978,
−.37) supplies roughly a third of the gap. Per the pre-registration, **no
third wave was run.**

## Honest verdict against the goal

The goal — both means strictly above the baseline — is **not achieved**, and
with corrected statistics it was never achieved at any point in the campaign.
What the data supports:

* the arm **matches the baseline on precision and trails on recall by ~.05**,
  at roughly a third of the baseline's cost;
* the recall deficit is concentrated, not diffuse — a minority of items carry
  the aggregate on both wave 4 and the pooled set;
* **configuration effects replicate in sign** even where individual deltas are
  not significant: v15 leans precision (+.029/+.022 across independent
  generations), v16 leans recall (best fresh-split recall, .336) and is the
  only configuration that reproduced the GOLD-gap catch inside the pipeline;
* Composer-2.5 is a breadth proposer, not a closer (Δprecision −.045): best
  challenger recall, measurably worse precision, on three pipeline versions.

## Product recommendation

Both configurations are supported and documented in `.env.template`:

* **v15 (default, all-DS)** — precision-leaning, ~$1/item. The right default
  for volume review.
* **v16 (`REVIEW_LENS_BACKENDS` routing Fable into adversary + second round)**
  — recall-leaning, adds two harness sessions per item. The right choice for
  high-stakes PRs where a missed defect costs more than a spurious comment.

## Where a successor should start

The measurement is settled, so the next campaign should not re-litigate it.
Three things follow from the data:

1. **The gap is one item class, not a level.** A third of the pooled deficit
   comes from a single item; wave-3 forensics named the recurring classes
   (test/gate epistemics, docs information architecture, CI economy). Fixing
   the class beats another round of general duties.
2. **Budget the gate before the pipeline.** At the observed item-level sd
   (.103), a .05 effect needs ~38 items. Anything measured on 10 items is
   uninterpretable in this range — three configurations were submitted
   against a bar wave 4 could not measure.
3. **The remaining untried lever is a strong generator throughout.** Fable in
   two seats produced the campaign's best recall and the only in-pipeline
   GOLD-gap catch; Fable in every seat was scoped (~$10–20/item, inverting
   the cost story) and deliberately not run.
