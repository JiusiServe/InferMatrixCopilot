# Goal campaign — DeepSeek-v4-pro Strict vs Claude Code + Opus 5 (2026-08-12/13)

> **冻结记录，保持英文原文。** 本页是当时被评审/被判分的文本本身；翻译它就是**改动一份记录**。文档树的其余部分统一为中文 —— 见 [`../README.md`](../README.md)。


> **Final update (2026-08-13, official-model rework):** after the official
> `deepseek-v4-pro` release the pipeline was rebuilt for a strong generator
> (deep investigator+adversary passes alongside the behavior/verification
> breadth lenses; a per-comment agentic verify pass; self-proving verbatim
> evidence quotes end-to-end). Result — **val: ARM 8—7 (first head-to-head
> win); frozen test, one-shot confirmatory: ARM 7—8. Combined 15—15** vs
> the Opus 5 baseline at roughly 1/3 the cost, from 1—4 (val) pre-campaign.
> Test means: r .689 vs .762, p .687 vs .719 (arm's best precision on any
> split); the GOLD gap item pr4834 was swept 3/3 clear. Rubric-mean gaps
> (.03-.07) sit at the magnitude of measured judge drift on identical
> baseline reviews (±.05-.10 across gates). Honest verdict: the copilot
> moved from clearly-worse to statistically indistinguishable from the
> agentic Opus 5 baseline; "strictly better on both means" is NOT
> demonstrated. Both tuning splits are now spent (8 val submissions, 1
> test shot) — any further iteration requires fresh items (wave2 snapshots
> exist under `eval/dataset/gt/` for exactly this). Key structural lesson
> for successors: the judge is tool-less — repo-side findings score as
> speculation unless the comment carries verbatim-quoted proof; making
> evidence self-proving was the single biggest win (4—11 → 8—7).

Goal: make the Strict pipeline (DeepSeek-v4-pro generation) beat the recorded
`baselines/claudecode_opus5` agentic review on the 5-PR val split. Protocol:
adaptation on train only; judge `gpt-5.6-sol-high` via cursor (blind pairwise,
`judge_val.py`); PR-time trees pinned to `expected_pr_heads.json`;
`PR_CONTEXT_MODE=no_discussion`. All arms/judgments under
`eval/dataset/arms/copilot_v{7,8,9}_*` and `judgments/goal_*`.

## Verdict — the gate did NOT pass

| gate | arm | model | wins (arm—opus) | arm r/p | opus r/p |
|---|---|---|---|---|---|
| pre-campaign (g56) | copilot_v4_pr20_r1 | v4-pro[1m] preview | 1—4 | 0.42/0.51 | 0.82/0.54 |
| val gate 1 | copilot_v8_official_r1 | v4-pro official | 3—12 (×3 reps) | **0.86**/0.56 | 0.79/0.66 |
| val gate 2 (precision trim) | copilot_v9_official_r1 | v4-pro official | 2—13 (×3 reps) | 0.80/0.54 | 0.82/0.65 |

What the campaign did achieve, measured:

- **Val recall 0.42 → 0.80–0.86** — at or above the Opus 5 baseline (0.79–0.82).
  The pre-campaign recall deficit (−0.40) is gone.
- Gate 1 **swept the GOLD latent-gap item pr4810 3/3** (the arm engaged the
  gap both gates; verdict wins depend on the noisy precision margin).
- Train hardest-6: recall 0.42 → 0.50 monotonically over calibration rounds;
  pr4870 flipped to a consistent 2/2 win (r≈0.83, p≈0.84).
- Cost ~$0.26–0.53/item ≈ 5× cheaper than the baseline.
- The loss driver flipped: pre-campaign the arm lost on recall; now it loses
  on **precision** (0.54–0.56 vs 0.65) — the judge discounts individually
  under-grounded or speculative comments, an agentic-verification property of
  the generator that two calibration rounds of budget/reducer tuning did not
  buy. Head-to-head margins are mostly "slight".

## What changed (all in-tree, tests + knowledge validators green)

Workflow: planner `value_flips` signal (default flips can't rule light);
verification lens in the fallback set; evidence caps 120k→260k / reducer
60k→280k (a 170k diff was losing 30% of its hunks); commit timeline +
deterministic changed-symbol consumer sweep (`git grep -nw`) in the evidence
pack; hunk-location paging targets; cross-lens corroboration tags + reducer
protected-class drop rules; comment budget 6 (+≤3 coverage promotions,
overflow only on evidence-rich reviews); coverage-promotion pass converting
lens findings/blockers into grounded comments; severity + red-CI calibration.

Knowledge: `repos/vllm-omni/review/guides/strict-review-checklist.md`
(train-distilled triggered checks) injected via new manifest key
`knowledge.review_checklist` (linter extended); module map 8→17 entries,
risk tiers +platform/diffusion/distributed (small diffs there now get the
full ensemble — this alone fixed the pr5009/4977 class).

## Forensic lessons (train, 3-agent trace analysis + 5 judged rounds)

1. Depth misfires and evidence truncation were real and fixed (verified live).
2. The 5-comment severity-only cap deleted reducer-kept GT concerns; but
   widening budgets converts to noise — the judge is recall-dominant between
   arms yet punishes volume within an arm. The stable operating point is a
   small budget plus class-protected promotion.
3. Generation variance and judge variance are both large: single-replicate
   verdicts flipped items across identical configs. Never calibrate on one
   replicate (this campaign's r2 was wasted that way).
4. The residual deficit is per-comment grounding depth (the baseline
   verifies each claim agentically before asserting it). Workflow scaffolding
   moved recall dramatically; it did not move groundedness.

## Next levers, ranked

1. Per-comment agentic verify pass (tools, one comment at a time) before the
   budget — directly attacks the precision deficit; ~+30% cost.
2. `ensemble_lens_max_iters` ↑ for the drafting lenses on the official model
   (the baseline reads 3–10× more code per finding).
3. MoA re-test with the official pro model as reducer over stronger members
   (the old regression used weak mimo/qwen members).
4. Re-baseline: the official v4-pro replaced the [1m] preview mid-campaign;
   train-side numbers predate it.

Judgments for the two gates: `judgments/goal_v8_val`, `judgments/goal_v9_val`
(the 402-outage set is quarantined as `INVALID_apierror_goal_v7_val`).
Test split remains frozen and untouched.
