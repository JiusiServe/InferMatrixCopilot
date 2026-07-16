# RQS v3 — reliability-first review-quality metric

v2's own agreement stats showed its weakest link: validity judging pooled at
κ≈0 (one live case had the validity jury and the coverage judge contradict
each other on the same finding), and the harmonic aggregate zeroes any review
that (correctly or not) stays silent — the Opus 4.8 arm produced the eval's
deepest verification and scored 0.14 because two justified-looking APPROVEs
zeroed two PRs. v3 fixes both, based on a second literature pass.

## Literature → design decisions

1. **Multi-trial majority voting + rubric anchoring** ("The Coin Flip Judge?",
   arXiv 2606.13685): pointwise LLM judgments flip across identical trials;
   majority over repeated trials improves reliability fast (with quickly
   diminishing returns), and anchored rubrics with examples reduce arbitrary
   variation. → v3 validity = **3 trials × 2 judge models = 6 votes per
   finding**, vote-share scored, with an **anchored rubric** that explicitly
   legitimizes repo-context findings (the v2 jury's main contradiction class)
   and includes worked VALID/INVALID examples. Self-consistency κ (trial vs
   trial, same model) and cross-model κ are both reported.
2. **Decision-level correctness / true negatives** (Sphinx, arXiv 2601.04252):
   score the verdict itself, and treat "correctly predicting no comment is
   needed" as a scoreable outcome rather than an automatic zero. → v3 adds a
   **decision component**: the review's APPROVE / REQUEST-CHANGES verdict
   against what human maintainers actually did before merge. (Caveat: all 3
   benchmark PRs drew substantive human change requests, so the current GT
   can't yet *reward* a clean approve — adding known-clean PRs is the listed
   extension.)
3. **Components are weak signals; don't over-aggregate** (arXiv 2604.24525:
   automated evaluators agree with developer labels at only 0.44–0.62, over-
   predict usefulness, near-zero MCC): a product/harmonic aggregate launders
   judge noise in any one component into a hard zero. → v3 aggregates by
   **weighted arithmetic mean** (recall .35, precision .25, actionability .20,
   decision .20) — a zero component now costs its weight instead of the whole
   score — and per-component reliability stats stay in the report.
4. **Deterministic beats judged where possible** (c-CRAB, arXiv 2603.23448,
   scores reviews by whether executable tests derived from human comments pass
   after revision — no LLM judge at all): → v3 extracts verdicts by
   deterministic regex first (LLM fallback only when no explicit verdict), and
   keeps v2's deterministic severity/resolution GT weights. Executable-test
   scoring is the long-term direction; out of scope at n=3.

### v3.1 rubric fix: requested-change findings (2026-07-06)

A live probe (judge re-run with a `why` field) showed the validity jury
systematically voting INVALID on findings phrased as requests — "Add a test
for the widened rejection path" was rejected with "diff does not contain any
such test; claim of added test unverifiable". The jury was verifying asks as
if they were descriptions of the diff, contradicting this metric's own
design (requested actions are findings; doc-asks are never invalid per se —
Sphinx's decision-level framing assumes reviews request things). v3.1 adds
one rubric clause + one anchored example: a requested-change finding is
judged on whether the underlying issue is real in the diff; the requested
change being absent from the diff is the finding's point, never a reason to
vote invalid. Applied identically to every arm; all validity caches
re-judged under the same 6-vote protocol.

## Definition

Per PR and arm:

- `recall_w` — unchanged from v2: severity×resolution-weighted human-issue
  coverage (full/partial/miss), mean over the 2-model coverage jury.
- `precision` — mean over findings of the 6-vote validity share
  (anchored rubric, 3 trials × 2 models).
- `actionability` — unchanged from v2 (the most reliably judged dimension).
- `decision` — 1.0 if the review's verdict matches the human outcome
  (request_changes for all three benchmark PRs), 0.5 if no verdict is
  extractable, 0.0 on mismatch.

`RQS3 = 0.35·recall_w + 0.25·precision + 0.20·actionability + 0.20·decision`

Reported alongside: validity self-consistency κ per judge model, cross-model
κ on majority votes, and the v2 coverage/actionability κ.

## Efficiency in the metric: RQS3e (Cost-of-Pass, arXiv 2504.13359)

Cost and time are part of the metric (their central claim: inference-time
techniques like majority voting often don't justify their marginal cost —
exactly the question our ensemble raises). The efficiency-adjusted headline:

`RQS3e = RQS3 · f(usd) · f(minutes)`, with `f(x) = 1 / (1 + log10(1 + x/ref))`

- Log-scale discount, because arm costs span orders of magnitude
  ($0.01–$3.20): a linear penalty would be dictated entirely by the most
  expensive arm, and a ratio (quality/$) degenerates toward whichever arm is
  cheapest regardless of quality.
- The references are EXPLICIT budget assumptions, env-overridable
  (`V3_COST_REF_USD=1.0`, `V3_TIME_REF_MIN=10`): at the ref cost the
  discount is ~23%; well under it, ~0. $1 and 10 min approximate the scale
  at which an automated review starts to rival a maintainer's skim of the
  PR. For a nightly/async deployment where latency is nearly free, raise
  `V3_TIME_REF_MIN` and RQS3e converges back to RQS3.
- Cost inputs: Opus arm = actual CLI-billed USD; DeepSeek arms = token
  estimate at cache-miss list rates (an upper bound).

Alongside RQS3e, the report keeps the undiscounted RQS3, **cost-of-quality**
($/RQS3 point), **min-of-quality**, and Pareto-frontier membership on
($, RQS3) — the frontier still shows the full deployment tradeoff that any
single scalar necessarily collapses.

## Limitations

Same-family jury for DeepSeek-generated arms and cross-family for the Opus
arm (self-preference bias, arXiv 2604.22891, deflates the foreign model);
n=3 merged PRs (contamination bound for gh-enabled arms); no clean-approve
PR in GT yet, so `decision` currently only penalizes wrong approvals rather
than rewarding right ones.
