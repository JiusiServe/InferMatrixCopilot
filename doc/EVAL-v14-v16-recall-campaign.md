# Campaign report — v14→v16 recall attack (2026-08-15)

Successor to `doc/EVAL-goal-strict-vs-opus5.md` (the v7→v13 campaign, which
ended at 15—15 combined fresh verdicts under a GPT judge and a −.16 recall
ratio under the Sonnet judge). This campaign's goal, set by the owner: make
the Strict pipeline beat the recorded `baselines/claudecode_opus5` arm on
**both** recall and precision, using cursor-agent-based configurations and
distillation from Fable traces.

**Result in one line: parity within measurement precision at ~1/3 the cost —
and the campaign's most useful output is arguably the measurement correction
that established that, not the pipeline work that preceded it.**

## What was built

Method: forensics on spent splits (per-GT-finding coverage matrices with
stage-of-loss classification from the arms' own traces), plus a Claude Fable 5
*teacher arm* run through the identical pinned harness as the baseline on the
train split — which caught the pr4870 GOLD latent gap exactly (the #4910
dual-axis mechanism human review missed), giving a concrete distillation
target rather than a stylistic one.

Landed (all default-on, kill-switched, `doc/RFC-review-recall-v14.md`):

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

## Honest verdict against the goal

The goal — both means strictly above the baseline — is **not demonstrated**,
and with the corrected statistics it was never demonstrated at any point in
the campaign. What is supported by the data:

* the arm reaches **parity within measurement precision** on fresh human-GT
  holdouts, at roughly a third of the baseline's cost;
* the recall deficit is concentrated, not diffuse — 3 of 10 wave-4 items carry
  the aggregate, the other 7 sit inside ±.06;
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

## Open

Wave 5 (`goal-eval/PREREG-wave5.md`) is a pre-registered, one-shot pooled
measurement taking the fresh-item pool to 20 for the v16 recall question,
with its decision rule fixed in advance — including the instruction not to
run a third wave if the interval still contains zero.
