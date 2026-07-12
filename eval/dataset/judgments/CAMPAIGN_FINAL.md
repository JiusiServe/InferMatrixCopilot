# vllm_omni_bench campaign — final report (2026-07-12)

One self-improvement cycle of the vllm-omni-copilot, measured against a
Claude Code + Opus 4.8 baseline on a 40-item dataset (20 PR reviews + 20
issue answers; 10/5/5 train/val/test per kind; test frozen until the end).
Judge: Sonnet 5, blind pairwise + rubric, 3 replicates throughout.

## The arc (val, copilot rubric means)

| dim | T0 | T3 (knowledge+delivery+cache+mechanism) | T4 (+forensic punch list) | baseline |
|---|---|---|---|---|
| actionability | 0.52 | 0.68 | **0.77** | 0.71-0.75 |
| completeness | 0.56 | 0.52 | **0.69** | 0.80-0.84 |
| correctness | 0.74* | 0.59 | **0.71** | 0.77-0.84 |
| recall | 0.48 | 0.39 | **0.52** | 0.58-0.67 |
| precision | 0.66 | 0.61 | **0.70** | 0.84-0.89 |
| grounding | 0.67 | 0.58 | **0.67** | 0.74-0.80 |
| latent-gap | 0.00 | 0.20 | 0.19 | 0.17-0.21 |
(* single-roll numbers; T3/T4 are 3-replicate means — ±0.1 roll noise applies
to all single-roll stage comparisons.)

## FROZEN TEST (held-out, one-shot, 90 verdicts)

| dim | copilot ($0.12/item) | Opus 4.8 ($1.26/item) |
|---|---|---|
| latent-gap hit | **0.28** | 0.11 |
| actionability | **0.83** | 0.78 |
| correctness | **0.68** | 0.59 |
| precision | 0.79 | 0.81 |
| grounding | 0.61 | 0.65 |
| completeness | 0.66 | 0.72 |
| recall | 0.45 | 0.53 |

Head-to-head wins 37/90 (41%; was 7% pre-campaign). Zero blocked runs.
**GOLD generalization: pr4834 gap_hit 1.00 across all 9 verdicts** — the
over-strictness lesson distilled from TRAIN ground truth transferred to a
held-out item and caught what human review missed; the baseline scored 0.11.

## Knowledge attribution (no-briefing ablation, val, 88 verdicts)

Briefing+checklist removal costs only: completeness -0.07, correctness -0.05,
precision -0.04, grounding -0.04; actionability/recall unchanged; gap_hit
UNCHANGED-or-higher (0.26) — gap detection is the checkout MECHANISM, not
checklist prose (consistent with T1: checklist alone scored 0.00).

## What moved the needle, ranked by measured effect
1. Delivery & calibration code (T4 punch list; T2 renderer/salvage): the
   largest gains — judges were scoring mangled deliverables, not weak
   analysis. Verdict calibration alone flipped 14/15 wrong REQUEST CHANGES.
2. Mechanisms: PR-time checkout took latent-gap 0.00 -> parity-or-better;
   budget salvage eliminated blocked runs; windowed reads + evidence caps
   cut cost 3x and halved sweep time (cache hit 50%->74%).
3. Prompt knowledge (briefing/checklist/skills): real but small (+0.04-0.07),
   concentrated on issue completeness/correctness.
4. Remaining gap to Opus (recall/completeness/grounding on complex items):
   genuine investigative depth — the T5 candidate is a scoped stronger-model
   uncertainty-resolution pass (~$0.10-0.25/item).

## Costs
Whole campaign: baseline $58.54 + copilot arms ~$15 (13 sweeps of 10-30 items)
+ judging (~500 Sonnet verdicts). Final arm: ~$0.12/item, ~19-min val sweeps.

## Reproducibility
Dataset/protocols: vllm_omni_dataset.yaml + README (SIP-Bench partitions,
anti-Goodhart rules). Arms: arms/*/; judgments: judgments/*/; per-stage
reports: T3_REPORT/T3_FORENSICS/T4_REPORT. Judge: judge_val.py (SPLIT/ARM_A_DIR
env). Sweeps: run_copilot_arm.py + run_t{3,4}.sh + run_final.sh.
