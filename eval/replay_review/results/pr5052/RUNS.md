# PR #5052 performance replay runs

Target: `ea0e11f8195feff3d543ad384bdd4f59d262c4bf` against base `9014bb9917291e78a22f05214f3a37d9d6090d6e`.

All runs used Codex `0.144.6`, `gpt-5.6-sol`, reasoning `high`, ChatGPT subscription authentication, read-only sandbox, ignored user config, a history-free `git archive` snapshot, and the pinned performance knowledge hash `e43ed842...ecfe4d6`.

| run | elapsed | tokens | findings | historical opinions hit |
|---|---:|---:|---:|---:|
| r1 | 210.6 s | 102,952 | 4 | 4/4 |
| r2 | 214.7 s | 108,043 | 4 | 4/4 |
| r3 | 212.3 s | 81,732 | 4 | 4/4 |

The four stable opinions were: missing warmup, identical-input isolation proof,
failure paths exiting zero, and the small-sample p90 index. Every run assigned
the first three `major` and p90 `minor`; the curated label currently calls p90
`major`, so semantic reproduction is perfect while exact-severity reproduction
is 3/4 by weight 0.75.

Scorer result:

- weighted hit recall: `1.00`
- weighted same-opinion recall: `0.75`
- precision: `1.00`
- all-run weighted recall: `1.00`
- mean pairwise hit-set Jaccard: `1.00`
- MVP gate: `PASS`

The source outputs are kept outside the repository under
`C:\Users\user\.omni-copilot\replay_review\pr-5052-ea0e11f8-r*`.
