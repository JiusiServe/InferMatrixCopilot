# Frozen test — CLEAN-ROOM run (numeric aggregates only)

Protocol: sweeps+judging entirely in a temp dir; outputs/traces of both
arms never viewed by the operating agent; judge rationales discarded
unread; all raw artifacts deleted after this aggregation. 3 arm
replicates, 90 blind verdicts (Sonnet 5).

| dim | copilot (r1/r2/r3 -> mean) | baseline |
|---|---|---|
| actionability | 0.87/0.81/0.82 -> **0.83** | 0.76 |
| completeness | 0.71/0.68/0.62 -> **0.67** | 0.69 |
| correctness | 0.65/0.62/0.59 -> **0.62** | 0.54 |
| gap_hit | 0.21/0.21/0.25 -> **0.23** | 0.20 |
| grounding | 0.58/0.50/0.56 -> **0.55** | 0.54 |
| precision | 0.84/0.76/0.78 -> **0.79** | 0.80 |
| recall | 0.51/0.46/0.43 -> **0.47** | 0.53 |

Wins (copilot/baseline/tie): r1 21/9/0, r2 14/16/0, r3 12/18/0
