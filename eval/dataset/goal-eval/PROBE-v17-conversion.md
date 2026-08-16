# Probe pre-registration — v17 (conversion fixes) on the spent splits

Written and committed BEFORE any v17 review artifact or verdict exists.

This is a **probe, not a measurement**. `val` and `train` have both been
iterated on for the whole campaign, so a favourable number here is evidence
that the fixes do what they were built to do, and is NOT evidence about the
holdout. Stating that in advance is the point of writing this first.

## Question

Commit `ae1b6f1` ("Conversion fixes") repaired four paths where the arm
produced the right reasoning and then routed it away from what the judge
scores:

1. `[resolved]`-with-residual findings rendered into the unscored "Validated"
   block; now promoted to review comments (`_promote_resolved_residuals`).
2. A lens whose final came back empty was silently dropped by both retry
   paths (one holdout item discarded 5 whole passes / ~2.1M input tokens);
   now retried.
3. The comment contract had no patch field, so the renderer could not emit a
   code suggestion at all (baseline: 72 fenced suggestions per wave; arm: 0).
   Added `suggestion` + render path + a severity-is-a-decision rule.
4. The findings ledger ranked but never deduped; overflow bullets clipped
   mid-word.

**Do these conversion fixes move paired Δrecall against the same CC+Opus 5
baseline, on splits where an earlier configuration of the same pipeline has
already been judged?**

## Design (fixed here)

* **Arm**: `v17` = HEAD `ae1b6f1`. DS v4-pro core, `deepseek-v4-flash` on
  planner + promotion, **no `REVIEW_LENS_BACKENDS` routing**. Fable-5 quota
  is still exhausted (probed 2026-08-16: "You've reached your Fable 5
  limit."), so routing Fable into the adversary/round-2 seats would produce
  dead seats again. The arm is therefore labelled and reported as
  *core-only*, and the routing gate in `run_copilot_arm.py` is a no-op by
  construction because nothing is routed.
* **Baseline**: `baselines/claudecode_opus5`, already on disk for both
  splits — the arm generates alone, so the wave-5 arm/baseline worktree race
  cannot recur.
* **Items**: `val` (5 PRs: 4893, 4810, 4825, 4837, 4816) as requested, **plus
  `train`** (10 PRs: 5009, 4923, 4804, 4870, 4817, 4977, 4926, 4859, 4970,
  4950). Train is added — disclosed here, before any data — because val alone
  cannot answer the question: at v13 three of its five items scored an exact
  0.000 paired Δrecall and its item-level sd was 0.171, versus 0.041 on
  train. Val is the split the user asked for; train is the split that can
  resolve a small effect.
* **Reference points** (both already on disk, same baseline, same judge):
  * `goal_v13_val` — Δrecall −0.032 [−0.244, +0.180], n=5.
  * `goal_v16f_train_sonnet` — Δrecall +0.002 [−0.027, +0.031], n=10, and
    the only split where the v16 Fable seats actually ran (15/15 live).
* **Judge**: `claude-sonnet-5` via `judge_val.py`, 3 replicates, blind
  pairwise, `PR_CONTEXT_MODE=no_discussion` on generation. Unchanged.
* **Analysis**: `paired_analysis.py goal_v17_val_sonnet` and
  `... goal_v17_train_sonnet`, reported separately (different n, different
  reference points — pooling them would hide which split moved).

## Decision rule (fixed here)

* The train comparison is against **v16-with-live-Fable**, so it asks
  "does the cheaper core-only arm plus conversion fixes match or beat the
  arm that had two Fable seats?" A CI overlapping v16's +0.002 is a pass.
* **No config selection on this data.** Whatever the probe shows, the next
  holdout measurement is a fresh pre-registration; this document cannot be
  cited as its result.
* A per-item Δ table is reported either way, and any item whose generation
  errors is regenerated once, then reported as missing — never dropped from
  the denominator.
* Judge/arm cost is expected ~$25 total. No third split is run if the answer
  is ambiguous; ambiguity is reported as the result.
