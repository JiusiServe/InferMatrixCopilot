# Optimized scope-routing replay

This result set uses corrected review-time merge bases, the generated
`REPLAY_SCOPE.json` coverage ledger, and route-specific questions. It contains
three independent `gpt-5.6-sol` high-reasoning runs for four cross-module PRs.

| Case | Run seconds | Tokens | Historical findings hit |
|---|---:|---:|---|
| PR 5001 r1 | 584.7 | 216,127 | 4/4 |
| PR 5001 r2 | 501.2 | 211,450 | 3/4 |
| PR 5001 r3 | 420.6 | 191,497 | 3/4 |
| PR 4718 r1 | 395.2 | 105,005 | 1/1 |
| PR 4718 r2 | 363.1 | 120,831 | 1/1 |
| PR 4718 r3 | 239.9 | 139,067 | 1/1 |
| PR 4106 r1 | 483.6 | 84,099 | 1/1 |
| PR 4106 r2 | 294.4 | 80,585 | 1/1 |
| PR 4106 r3 | 464.5 | 193,976 | 1/1 |
| PR 5088 r1 | 278.6 | 106,344 | 1/1 |
| PR 5088 r2 | 277.8 | 116,301 | 1/1 |
| PR 5088 r3 | 232.4 | 73,547 | 1/1 |

The raw run directories remain under
`C:\Users\user\.omni-copilot\replay_review`. No pytest process was used.

Final gate: **pass**. Weighted hit recall and same-opinion recall are both
0.9048, precision is 0.7037, all-run weighted recall is 0.7143, and mean
pairwise hit-set Jaccard is 0.9167.
