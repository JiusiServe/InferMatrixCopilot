# T0 → T1 → T2: copilot arm vs Opus baseline on val

T0 = shipped arm. T1 = + knowledge (commit 9f7e1e6), unfixed build.
T2 = + delivery fixes (commit 2646d12). Judge: Sonnet 5, blind, 3 replicates,
30 verdicts per stage. Single arm-roll per item per stage — treat item deltas
as noisy; the flake-sensitivity row excludes issue4827 (T1 run derailed onto a
hallucinated topic and self-escalated; T0/T2 runs were normal).

## Copilot rubric means

| dim | T0 | T1 | T2 | T2-T0 |
|---|---|---|---|---|
| recall | 0.48 | 0.45 | 0.51 | +0.03 |
| precision | 0.66 | 0.61 | 0.60 | -0.06 |
| actionability | 0.52 | 0.63 | 0.69 | +0.17 |
| correctness | 0.74 | 0.60 | 0.73 | -0.01 |
| grounding | 0.67 | 0.58 | 0.70 | +0.03 |
| completeness | 0.56 | 0.48 | 0.63 | +0.07 |
| gap_hit | 0.00 | 0.00 | 0.00 | +0.00 |

## Flake sensitivity (issue4827 excluded from all stages)

| dim | T0 | T1 | T2 | T2-T0 |
|---|---|---|---|---|
| recall | 0.48 | 0.45 | 0.51 | +0.03 |
| precision | 0.66 | 0.61 | 0.60 | -0.06 |
| actionability | 0.52 | 0.63 | 0.69 | +0.17 |
| correctness | 0.72 | 0.75 | 0.70 | -0.01 |
| grounding | 0.65 | 0.72 | 0.69 | +0.04 |
| completeness | 0.57 | 0.60 | 0.62 | +0.06 |
| gap_hit | 0.00 | 0.00 | 0.00 | +0.00 |

## Wins vs baseline (of 30)

- T0: copilot 5 / baseline 25 / tie 0
- T1: copilot 3 / baseline 27 / tie 0
- T2: copilot 3 / baseline 27 / tie 0

## Per-item copilot means (T0 → T1 → T2)

| item | recall | precision | actionabi | correctne | grounding | completen |
|---|---|---|---|---|---|---|
| issue4793 | --→--→-- | --→--→-- | --→--→-- | 0.71→0.92→0.85 | 0.53→0.77→0.67 | 0.38→0.57→0.72 | 
| issue4827 | --→--→-- | --→--→-- | --→--→-- | 0.85→0.00→0.85 | 0.77→0.00→0.77 | 0.53→0.00→0.65 | 
| issue4842 | --→--→-- | --→--→-- | --→--→-- | 0.88→0.90→0.93 | 0.67→0.80→0.80 | 0.72→0.75→0.70 | 
| issue4891 | --→--→-- | --→--→-- | --→--→-- | 0.77→0.58→0.47 | 0.82→0.70→0.62 | 0.72→0.60→0.52 | 
| issue4905 | --→--→-- | --→--→-- | --→--→-- | 0.52→0.58→0.57 | 0.58→0.63→0.67 | 0.45→0.47→0.55 | 
| pr4810 | 0.47→0.33→0.28 | 0.57→0.45→0.60 | 0.58→0.60→0.68 | --→--→-- | --→--→-- | --→--→-- | 
| pr4816 | 1.00→1.00→1.00 | 0.81→0.58→0.47 | 0.63→0.62→0.65 | --→--→-- | --→--→-- | --→--→-- | 
| pr4825 | 0.07→0.40→0.40 | 0.65→0.82→0.60 | 0.17→0.67→0.67 | --→--→-- | --→--→-- | --→--→-- | 
| pr4837 | 0.82→0.42→0.83 | 0.67→0.65→0.63 | 0.57→0.62→0.68 | --→--→-- | --→--→-- | --→--→-- | 
| pr4893 | 0.07→0.12→0.03 | 0.60→0.53→0.70 | 0.67→0.67→0.78 | --→--→-- | --→--→-- | --→--→-- | 
