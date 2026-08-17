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

## Generation note (appended before any verdict existed)

* The smoke item `pr4816` was generated first, under the identical commit and
  configuration, and its review text was read in full to confirm the four
  conversion fixes actually fire end-to-end. They do: the `[resolved]`
  residual about CI lane coverage was promoted into a scored comment, two
  ```suggestion blocks rendered, and severities spread across
  major/minor/nit instead of collapsing to all-minor. **That artifact is
  reused as the val arm's pr4816 rather than regenerated**, so that no
  version of this item is ever chosen from two candidates. Disclosed because
  it means one of the five val artifacts was read by the operator before
  judging; the judge is blind and automated, so this cannot move its score,
  but the fact belongs on the record rather than in a shell history.
* One defect observed in that smoke and deliberately NOT fixed before
  measuring: the ledger dedupe (normalized 90-char prefix) still let four
  near-identical `[claim-verified]` lines about the same `base` import
  survive. Editing the pipeline after seeing an artifact and before judging
  it is how a probe turns into config selection. It is recorded here as an
  input to the NEXT iteration, not patched into this one.

## Amendment — the first v17 run was contaminated by an unintended mixture

Written after the first run's verdicts existed, BEFORE the corrected run was
generated. It concerns a configuration fault, not a result, and the corrected
arm's analysis plan is unchanged from the body above.

**What happened.** Every earlier arm in this campaign (v13-v16) was launched
with `MOA_WHEN=off` in its environment; their manifests record `'off'`. The
v17 launch did not set it, so it fell through to the code default
`moa_when="full"` (config.py:345), which enables mixture-of-agents on every
full-depth PR review. Depth distributions are identical between the v16 and
v17 runs on the same items (full 7 / standard 1 / light 2 on train), so
nothing about the items changed — only the environment passed to the sweep.

**What it did.** MoA dispatched round-1 lenses to three vendors:
investigator + behavior to `mimo-v2.5`, adversary + verification to
`qwen3.6-plus`, reducer staying on the tier model.

* `qwen3.6-plus` returned `403 AccessDenied.Unpurchased` on 24 of its 27
  attempts — that subscription is not active.
* `mimo-v2.5` failed 10 times, each failure landing ~8 minutes in with the
  same `content[].thinking` 400.
* 104 minutes of the run were spent on member attempts that were then thrown
  away and redone.

**Corrected magnitude** (this paragraph replaces an earlier claim of "24% of
productive round-1 lenses were written by mimo-v2.5", which was inferred from
seat names rather than measured, and was wrong by ~2.6x). Attributing by the
model recorded on each `agent_dispatch` that produced usable output:

| model | attempts | productive outputs | output tokens |
|---|---|---|---|
| `deepseek-v4-pro` | rest + all fallbacks | 155 (89.1%) | 2,298,061 (89.3%) |
| `mimo-v2.5` | 30 | 16 (9.2%) | 183,047 (7.1%) |
| `qwen3.6-plus` | 27 | 3 (1.7%) | 94,497 (3.7%) |

DeepSeek still wrote ~90% of the work. Both member figures are UPPER BOUNDS:
`BudgetedLLM.create` (moa.py:215-227) reserves an estimated cost per LLM call
and, on a refused reservation, reruns that individual call on the tier model
while the lens keeps its original dispatch label. With `moa_max_usd = $1.50`
against per-item spend of $0.85-1.66, that budget trips partway through most
items. The trace cannot resolve how much lower the true share is, because
only the dispatch carries a model and the per-call fallback emits none — a
second provenance defect of the same family as the one below.

The contamination is therefore real but much smaller than first reported.
The corrected run remains warranted: a ~10% vendor substitution concentrated
in the two round-1 lenses is still not the arm the probe pre-registered, and
the wasted 104 minutes distorts every latency number.

So `goal_v17_val_sonnet` and `goal_v17_train_sonnet` do NOT measure the arm
they are named for. They are retained, not deleted, and relabelled **v17-moa
(unintended vendor mixture)**; the arm and judgment directories keep their
original names because each verdict's `_roles` block records that name, and
renaming would leave the provenance pointing at a directory holding different
data. A README in each directory states what actually ran.

**The corrected run.** Identical code (`ae1b6f1`), identical items, identical
judge and analysis, with `MOA_WHEN=off` verified through the RESOLVED
settings rather than the env string (`moa_eligible(...) == False`). New
names so nothing is overwritten: arms `copilot_v17ds_val` /
`copilot_v17ds_train`, judgments `goal_v17ds_val_sonnet` /
`goal_v17ds_train_sonnet`.

**Fixed in advance:** the corrected run's numbers are the v17 result. The
contaminated run is reported alongside as what it is, and no version of any
item is chosen between the two. If pr4825 crashes again — its fault was the
`content[].thinking` 400 on the DeepSeek path, which MoA-off does not
address — it is reported MISSING under the same rule as before, not retried
until it passes.

**Provenance defect this exposes**, recorded for a general fix: the arm
manifest records `moa_when` from the environment variable, so it wrote
`"(default)"` while the resolved value was `"full"`. Manifests must record
resolved settings, not env strings. This is the third instance of provenance
capturing the input rather than what ran (after the routed-seat mislabeling
and the Fable quota exhaustion).
