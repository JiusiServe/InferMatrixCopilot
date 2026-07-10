# metrics.py — spec

`LOC ~342 · cross-cutting (measurement) · refactor-status: oversized`

## Responsibility
Compute and persist per-run `metrics.json` (CATQ = Q·S/C).

## Functionality
Reads the run's trace/artifacts; computes Q (weighted quality per kind over
known components), S (safety multiplier from incidents), C (RQS3e-style log cost
over USD + wall-clock vs reference budgets); writes `metrics.json`.

## Public contract
`collect_run_metrics(run_dir, settings, status) -> {quality, risk, cost, catq}`.

## Invariants
- **E3**: metrics are facts about a run and MUST NEVER break it — every failure
  caught and traced (`metrics_error`); a run's success is independent of metrics.
- Q uses KNOWN components only (renormalized, `partial` flagged); judged/GT
  merged later, never fabricated; safe-abstain scores on escalated runs.
- Incidents derive from explicit events + existing out_of_scope/tool_refused/
  patch_review-revise.

## Scope — not here
No influence on control flow. Measurement only.

## Dependencies (allowed)
`config`, `run_trace` (reads events); the price table lives here.

## Extension points
New quality component / cost term → extend the respective sub-computation with a
KNOWN-only rule; document the reference budget in `config`.

## Tests
`test_metrics.py`.

## Refactor notes
Largest cross-cutting file; three sub-metrics (Q, S, C) + price table + CATQ
assembly in one module. **Suggested split**: `metrics/quality.py`,
`metrics/safety.py`, `metrics/cost.py`, `metrics/__init__.py` (assembly +
`collect_run_metrics`). The `[planned]` gh-feedback/post-push-CI collectors
should land as new files under that package, not appended here.
