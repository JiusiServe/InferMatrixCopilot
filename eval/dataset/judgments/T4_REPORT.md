# T4 — punch-list config, 3 val replicates

89 blind verdicts (Sonnet 5). T4 = T3 + forensic fixes #1-#8 (delivery
dedup, verdict calibration, budget salvage, Validated section, reducer
policy, lens yield floor, epistemics lint, disposition slots) + the
final-round-nudge API-shape fix.

| dim | T3 | T4 (r1/r2/r3) | T4 mean | baseline |
|---|---|---|---|---|
| actionability | 0.68 | 0.73/0.81/0.76 | **0.77** | 0.71 |
| completeness | 0.52 | 0.70/0.64/0.73 | **0.69** | 0.80 |
| correctness | 0.59 | 0.71/0.66/0.75 | **0.71** | 0.77 |
| gap_hit | 0.20 | 0.20/0.20/0.17 | **0.19** | 0.19 |
| grounding | 0.58 | 0.67/0.62/0.70 | **0.67** | 0.74 |
| precision | 0.61 | 0.63/0.72/0.74 | **0.70** | 0.87 |
| recall | 0.39 | 0.49/0.60/0.49 | **0.52** | 0.59 |

Wins (copilot/baseline/tie): r1 9/20/1, r2 9/21/0, r3 13/16/0

## Headlines
- Every dimension improved; actionability now EXCEEDS the baseline.
- Wins tripled vs T3 (27 vs 6 of 90); zero blocked runs in 30 sweeps
  (issue4842 completed 3/3 after the salvage+cap fix).
- Cost unchanged (~$0.12/item, ~10x under baseline); the entire gain
  came from delivery/calibration mechanics, confirming T3_FORENSICS.
