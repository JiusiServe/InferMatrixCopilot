# Goal evaluation report — one-click NL copilot vs the CC+Opus baseline

2026-07-18 · hook-reviewed eval plan v3 (6 review rounds; plan + trail + all
tooling in `eval/dataset/goal-eval/`) · metric definitions reused unchanged
from `eval/dataset/judge_val.py` (7 dims, blind pairwise, 3 judge replicates,
Sonnet-5 judge) · recorded baseline never rerun.

**Framing (stated per plan):** this is *retrospective synthesis under thread
visibility* — issue arms read the resolution thread (every arm always has),
and it is **not** blind pre-resolution maintenance. The frozen test split was
NOT run (see Gate outcome); all numbers below are val-split, paired, 3
generation × 3 judge replicates, machine-validated (30/30 verdicts, schema,
blinding, arm-content hashes, PR-time-checkout head assertions).

## Evidence matrix (asymmetries reported, not hidden)
| Arm | PR checkout | PR discussion | pr_context | Issue thread |
|---|---|---|---|---|
| CC+Opus (recorded 2026-07-11) | post-merge live repo | reachable via gh | n/a | full |
| A0 = copilot_v2_t4 (pre-change) | PR-time tree | not fetched | none | full |
| A1/A2 (this work) | PR-time tree | EXCLUDED (`PR_CONTEXT_MODE=no_discussion`) | title/body/labels/linked issues | full |

## Quality (val split; mean over 3 generation replicates ± sd across replicates)
| dim | A0 (pre-change) | A1 (new, MoA off) | A2 (MoA always) | Δ(A1−A0) | gate |
|---|---|---|---|---|---|
| PR recall | 0.516 ± 0.002 | 0.520 ± 0.021 | 0.550 ± 0.042 | **+0.004** | needs ≥ +0.03 ✗ |
| PR precision | 0.727 ± 0.043 | **0.800 ± 0.034** | 0.778 ± 0.036 | **+0.073** | ✓ (5/5 items ≥) |
| PR actionability | 0.761 ± 0.033 | 0.731 ± 0.062 | 0.700 ± 0.036 | −0.029 | tolerance −0.02 ✗ |
| gap_hit (GOLD item) | 1.00 | 1.00 | 1.00 | 0 | ✓ |
| issue correctness | 0.711 ± 0.024 | 0.689 ± 0.038 | 0.695 ± 0.034 | −0.022 | ✗ (marginal) |
| issue grounding | 0.644 ± 0.009 | 0.651 ± 0.027 | 0.622 ± 0.047 | +0.007 | ✓ |
| issue completeness | 0.688 ± 0.013 | 0.696 ± 0.023 | 0.664 ± 0.038 | **+0.008** | needs ≥ +0.03 ✗ |

Per-item paired deltas (A1−A0 sign counts): precision +5/−0 (the one broad,
consistent win); recall +2/−2; actionability +3/−2 with a single −0.46 item
(pr4825) driving the mean miss; correctness +2/−3, all items within ±0.12.
Replicate sds of 0.02-0.06 put the sub-±0.03 deltas inside judge noise
(consistent with eval/ANALYSIS.md's ±0.2 single-run swings).

**Note on A0-val vs the frozen-test numbers:** re-judged A0 val recall is
0.516 (test was 0.47) and correctness 0.711 (test 0.62) — split and judge-pass
differences of this size are exactly why the plan required paired val judging
rather than gating against test numbers.

## MoA ablation (A2 vs A1, same rule)
Recall +0.030 numerically crosses the threshold but is a **single-item
effect** (pr4893 +0.32; the other 4 PR items are slightly negative, sign count
+1/−4) — under the precommitted sign-count guard this is not a win claim.
Completeness −0.031, actionability −0.032, grounding −0.029 regress past
tolerance, and MoA generation costs ≈3× ($2.78 vs $0.91 per replicate).
**Decision: MoA does not promote to default.** It ships config-gated
(`MOA_WHEN=full` — engages only on full-depth/performance runs where the
operator explicitly wants maximum depth; `off` disables). The mechanism is
live-verified (members served, budget capped, fallbacks tested).

## Cost & latency (val, per item; canonical span-based calculator)
| | A1 (new) | CC+Opus baseline (real-billed) |
|---|---|---|
| USD mean / median / p95 | **$0.091 / ~$0.06 / ~$0.24** | $1.26 / $1.05 / $3.21 |
| wall_s mean / median / p95 | 305 / 173 / 946 | 213 / 149 / 682 |
| tokens (in, mean) | ~0.7M (deepseek, cached) | ~1.3M (Opus) |
service-time split (A1 r1): agent $0.890, reducer $0.018, planner $0.001.
Campaign totals: $92.4 settled of the $150 ceiling ($30 final-confirmation
earmark released unused); every paid attempt ledgered (`campaign_ledger.jsonl`).

## Gate outcome — honest verdict
**The promotion gate FAILED**: neither target dimension (PR recall, issue
completeness) reached the +0.03 minimum effect, and actionability/correctness
dipped marginally past the −0.02 tolerance. Per the plan's failure-honesty
clause the frozen test split was **not** run and no baseline-exceeding quality
claim is made. What the campaign DID establish:
- **PR precision +0.073** — broad (5/5 items), the one above-noise quality gain
  (reducer dup-guard, verdict calibration, don't-repeat-maintainers prior).
- **~14× cheaper than the baseline** at comparable median latency (Pareto
  statement: better precision + far lower cost, but NOT dominant — recall/
  completeness unchanged, mean wall slower).
- The shipped UX/robustness/instrumentation work (one-command install, doctor,
  URL routing with identity validation, upfront clarify, adaptive depth,
  MoA machinery, span-accurate accounting) is delivered and fully tested
  (~400 tests green) independent of the quality gate.

## Protocol notes
- Mid-campaign provenance drift detected and contained: a concurrent edit to
  `pr/fetch.py` (HTTP-406 diff fallback) landed after A1; verified inert for
  the evaluated path (0 fallback events; asserted absent in every A2 run);
  logged in `goal-eval/provenance_drift_log.jsonl`.
- One malformed verdict (lowercase `winner`) was deleted and re-judged under
  the retry rule; all 9 replicate/judgment sets machine-validated.
- Baseline caveats carried from its manifest: merged-PR contamination; its
  post-merge checkout vs our PR-time trees (evidence matrix above).

## Next levers (recall/completeness, in order of expected value)
1. **B8 issue-seeded repo-map** (research doc: aider's personalized-PageRank
   locator) — the highest-ceiling recall lever; the grep-sweep prompt alone
   (B4/E8) did not move recall.
2. Recall-targeted lens redesign: the maintainer-concern classes A0/A1 both
   miss are test-adequacy and scope questions (baseline autopsy §A) — a
   dedicated test-efficacy lens rather than prompt lines inside existing ones.
3. Completeness: the slot contract renders correctly but judges score against
   thread specifics — related-artifact retrieval (timeline tool) needs to feed
   the draft evidence pack, not just be available as a tool.
4. Re-run A2 with stronger members (the current mimo/qwen mixture REGRESSED
   grounding — member quality, not the mechanism, is the suspect).
