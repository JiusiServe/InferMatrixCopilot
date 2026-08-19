# PROBE v23 — breadth sweep lens

Pre-registered 2026-08-18, before generation. Champion to beat: **v20**.

## Why

Two interventions that made findings *better written* both measurably cost recall
and were reverted — the only two recall intervals in the 21-arm campaign whose
95% CI excludes zero, and both negative:

| arm | change | Δrecall (train, n=10) |
|---|---|---|
| v21 | claim headlines + evidence quote blocks | −0.093 [−0.178, −0.007] |
| v22 | require trigger → path → consequence per finding | −0.082 [−0.153, −0.011] |

v22 complied with its instruction (claims 407 → 500 chars, findings 3.0 → 4.4
per item, genuine causal chains on inspection) and still lost recall. Effort was
not the constraint: v22 spent **more** tool calls than v20 (327 vs 306) while
reasoning about **fewer** distinct files (10.8 vs v20's 12.2). Allocation is.

Distinct source files per review tracks recall in order:
baseline **13.8**, v20 **12.2**, v22 **10.8**.

Structural cause hypothesised: the 4 round-1 lenses partition by checklist
*topic* (logic / behavior / contracts / verification), not by diff region. Every
lens sees the whole diff and self-selects hunks, so diff coverage is emergent and
all four can converge on the same salient hunks.

## Change

Add a 5th lens, `sweep`, to `_REVIEW_LENSES`. The existing four are untouched.
Its job is breadth only: enumerate every changed file, reach a finding or an
explicit no-issue conclusion for each, one pass per file, name what it could not
resolve. Lenses run concurrently, so this costs tokens but no wall-clock.

Sweep candidates compete for the cap-8 comment budget on normal merit — no
deprioritisation. Special-casing them would blunt the effect under test.

Runs at `full` depth (all lenses) and is available to the planner at `standard`.
It is NOT added to `DEFAULT_STANDARD_LENSES` and does not affect `light`, which
runs one pass with no lenses.

## Reach

Train depth distribution: full 7, standard 1, light 2. All four recall losers
(pr5009 −0.297, pr4923 −0.190, pr4859 −0.183, pr4804 −0.127) run `full`, so the
change reaches them. The two `light` items (pr4950 0.000, pr4970 +0.567) are
untouched by construction.

## Predictions (falsifiable, registered before generation)

- **P1** distinct files reasoned about per review rises from 12.2 toward the
  baseline's 13.8. If it does not move, the lens did not do its job and the
  recall reading is uninterpretable — diagnose before judging.
- **P2** Δrecall improves on v20's −0.005 on train. This is the probe's point.
- **P3** Δprecision stays positive. Shallow sweep candidates crowding the
  comment budget is the named risk; +0.046 is the number to protect.
- **P4** per-finding claim length does NOT grow materially past v20's 407 chars.
  If it does, v23 has drifted into the v21/v22 failure mode and the result is
  confounded.

## Kill criterion

If Δrecall CI excludes zero on the negative side, revert immediately as with
v21/v22 — do not iterate on a resolved regression.

## Gate

Success standard agreed with the user 2026-08-18: **point estimates positive on
both axes**, on a pre-registered fresh split, CIs reported honestly alongside.
The 5-item `test` split stays UNSPENT until an arm wins train **and** val — at
n=5 and sd≈0.18 its CI half-width is ±0.22 and it cannot resolve a near-zero
effect, so it is spent once, on a real candidate.
