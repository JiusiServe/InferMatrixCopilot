# T3 — final config, 3 val replicates (89 verdicts)

Config: knowledge (9f7e1e6) + delivery fixes (2646d12) + cache optimization
(2deb571) + PR-time checkout (627da79) + review salvage (91f6012).
Judge: Sonnet 5, blind, tool-less. T3 = mean over replicate means.

| dim | r1 | r2 | r3 | T3 mean | baseline |
|---|---|---|---|---|---|
| actionability | 0.62 | 0.72 | 0.69 | **0.68** | 0.75 |
| completeness | 0.45 | 0.64 | 0.48 | **0.52** | 0.82 |
| correctness | 0.54 | 0.69 | 0.53 | **0.59** | 0.79 |
| gap_hit | 0.20 | 0.20 | 0.20 | **0.20** | 0.20 |
| grounding | 0.51 | 0.70 | 0.54 | **0.58** | 0.79 |
| precision | 0.52 | 0.69 | 0.61 | **0.61** | 0.89 |
| recall | 0.46 | 0.36 | 0.35 | **0.39** | 0.59 |

Wins (copilot/baseline): r1 3/27, r2 3/26, r3 0/30

## Headlines
- **gap_hit 0.20 vs 0.20 — TIED with the frontier baseline** (was 0.00 at
  T0-T2); the PR-time checkout mechanism converted in every replicate.
- Costs: ~$0.12/item vs baseline $1.26 (10.5x); sweep wall ~19 min/replicate.
- Replicate spread (correctness 0.51-0.70) confirms single-roll stage
  comparisons sit inside noise; these are the campaign's first defensible
  arm numbers.
- Remaining gap forensics (see T3_FORENSICS.md): dominated by mechanical
  delivery/policy defects, NOT model depth — T4 punch list follows.
