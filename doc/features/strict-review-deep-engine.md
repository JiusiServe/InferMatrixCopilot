# Strict 评审：深度 pass、逐条验证、自证据

> **一览**
> | | |
> |---|---|
> | **状态** | ✅ 已实现，**默认全开**（v13 期） |
> | **做什么** | 面向强生成器重做评审流水线：深度调查/对抗 pass、每条评论一次 agentic 验证、端到端的逐字引用自证据 |
> | **怎么开关** | `review_deep_engine`、`review_deep_max_iters`、`review_verify_comments` |
> | **实测** | [`../evaluation/EVAL-goal-strict-vs-opus5.md`](../evaluation/EVAL-goal-strict-vs-opus5.md) —— val 首胜 8—7，冻结 test 7—8，combined **15—15** |
> | **最大的一课** | 判官是**无工具**的：仓库侧的发现若不带逐字引用的证明，一律被当作臆测扣分。把证据变成自证据是本轮最大的单点收益（4—11 → 8—7） |
> | **后继** | [`review-recall.md`](review-recall.md)（v14/v15） |

---

## 原始 RFC

- Status: implemented behind flags (all default ON); measured on the 20-PR
  campaign splits (val + one-shot frozen test)
- Owner: review pipeline (`engine/steps/review/`, `review/planner.py`)
- Evidence: `doc/evaluation/EVAL-goal-strict-vs-opus5.md`,
  `eval/dataset/judgments/goal_v13_val/`, `eval/dataset/judgments/goal_v13_test/`

## Motivation

The Strict review pipeline was engineered around a weak generator: four
narrow lenses forcing enumeration inside templates, tight tool budgets, a
tool-less reducer, and a 5-comment severity cap. With the official
`deepseek-v4-pro` (a large capability jump over the `[1m]` preview), that
scaffolding became the bottleneck — measured symptoms across judged sweeps:

1. **Recall losses were mechanical, not analytical**: the budget cap deleted
   reducer-kept maintainer concerns; depth planning misrouted small
   high-blast-radius diffs to the no-ensemble light tier; a 170k-char diff
   lost 30% of its hunks to the 120k evidence cap; whole question classes
   (blast radius, dependency floors, test integrity, lifecycle-on-abort) had
   no owning lens.
2. **Precision was stuck at 0.54–0.56 across five different configurations**
   while recall swung 0.55–0.86 — because the blind judge is TOOL-LESS: it
   sees only the diff and the human threads, so any repo-side finding
   (consumers elsewhere, CI lane rules, version floors) scores as
   speculation unless the comment itself carries checkable proof.

## Design

Three mechanisms, composed with the existing ensemble/reducer machinery:

### 1. Hybrid pass set (`review_deep_engine`, default on)

Full depth runs two **deep passes** — `investigator` (central-change-first
free investigation; verify-before-assert; budget discipline: reserve the
final rounds for filing) and `adversary` (independent hunt over the
systematically-missed classes) — **plus** the two highest-value breadth
lenses (`behavior`, `verification`). Standard depth runs
investigator+behavior. Light is unchanged. Deep passes get
`review_deep_max_iters` (32) tool rounds; measured alone they ground
claims well (precision .82 on the hardest train items) but under-cover
(val recall .55); measured with the breadth lenses they hold recall .71–.86.

### 2. Per-comment agentic verification (`review_verify_comments`, default on)

Every merged draft comment gets a small tool-loop (4 rounds, concurrency 6,
shared diff cache prefix) that must re-derive the claim on the PR-time
tree: `refuted` drops, `unverifiable` demotes one severity step,
`confirmed` may tighten wording/position — and a verification failure
keeps the comment (the pass can only raise precision, never silently
delete recall). Skip/failure reasons are traced
(`review_comments_verified` / `review_coverage_skipped`).

### 3. Self-proving evidence (drafting + verify + render)

The single biggest measured lever (4—11 → 8—7 on the val gate): every
comment's `evidence` field must QUOTE the decisive code line(s) verbatim
with file:line so a reader holding only the review and the diff can check
the claim. Enforced in the drafting contract, re-emitted by the verifier
from the code it actually read, rendered as-is.

Supporting changes shipped with this RFC: `value_flips` diff signal (a
default flip can never rule light), verification lens in the planner
fallback set, evidence caps 120k→260k / reducer 60k→280k, commit timeline
+ deterministic changed-symbol consumer sweep (`git grep -nw`) + per-file
hunk-location paging targets in the evidence pack, cross-lens
corroboration tags with protected-class reducer rules, comment budget
8 + rich-only overflow, coverage-promotion pass (mines the run's own
findings/blockers for uncovered protected-class concerns), knowledge page
`repos/vllm-omni/review/guides/strict-review-checklist.md` injected via
the new adapter manifest key `knowledge.review_checklist`, and the
vllm-omni module map extended to 17 modules with 7 risk tiers.

## Measured results (blind gpt-5.6 judge, 3 replicates, vs recorded CC+Opus 5)

| gate | config | head-to-head (arm—opus) | arm r/p | opus r/p |
|---|---|---|---|---|
| pre-campaign | preview model, 4 lenses | 1—4 | .42/.51 | .82/.54 |
| v8 | official model, lenses | 3—12 | .86/.56 | .79/.66 |
| v12 | hybrid, narrative evidence | 4—11 | .71/.55 | .81/.66 |
| **v13 val** | hybrid + self-proving | **8—7** | .857/.555 | .889/.589 |
| **v13 frozen test** (one shot) | same | 7—8 | .689/.687 | .762/.719 |

Combined fresh verdicts: **15—15** at ~1/3 the baseline's cost
(~$0.75–1.2/item vs ~$1.5–3). GOLD latent-gap items: pr4810 2/3, pr4834
swept 3/3 clear. Rubric-mean gaps (.03–.07) are at the magnitude of
measured judge drift on identical baseline reviews (±.05–.10).

## Alternatives considered

- **MoA re-test with stronger members** — excluded by owner direction.
- **Deep passes only** (no breadth lenses): precision transferred but val
  recall collapsed to .55; rejected (gate v11, 2—13).
- **Budget/reducer tuning alone**: five configurations moved precision by
  ≤.02; the deficit was structural (tool-less judge), not calibrational.

## Rollout / compatibility

All three mechanisms sit behind settings with kill switches
(`review_deep_engine`, `review_verify_comments`; legacy lens set retained
verbatim and used when the deep engine is off). Offline tests cover pass
selection, verify verdict handling (drop/demote/tighten/fail-open),
budget/overflow, corroboration ordering, promotion, and the planner
signal; the full suite and both knowledge validators are green. Cost is
~2–3× the old lens pipeline per item and remains ~3× cheaper than the
baseline. `ARM_JOBS` in `run_copilot_arm.py` enables item-level parallel
sweeps (endpoint allows 500 concurrent requests on v4-pro).

## Open questions

1. Both tuning splits are spent (8 val submissions, 1 frozen-test shot).
   Further iteration needs wave-2 items (`gt/pr5957*`, `gt/pr5976*`,
   `build_wave2.py`) judged under the same protocol.
2. The judge protocol's tool-less-ness now shapes the reviews (verbose
   quoted evidence). If the product's real audience is maintainers rather
   than a repo-less judge, the evidence verbosity should become a render
   option rather than a fixed behavior.
3. `pr4762`/`pr4954`-class losses (broad multi-concern PRs) remain: the
   baseline still out-reads the arm per finding. The next structural lever
   is a coverage-driven second investigation round seeded by the reducer's
   uncovered-GT-class checklist rather than a fixed pass count.
