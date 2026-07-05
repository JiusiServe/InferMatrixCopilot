# Analysis — pure skill vs pure copilot vs copilot+skill (DeepSeek v4 pro)

## Optimization campaign toward RQS3>0.6 / RQS3e>0.5 (2026-07-05/06)

Six full eval cycles on the copilot_v2 arm, one mechanism change at a time —
every change is task-general (audited: no PR numbers, file names, or
benchmark tokens in any prompt). Numbers are single-run measurements of the
whole chain (fresh reviews + fresh v3 judging):

| iter | change (cumulative unless noted) | RQS3 | RQS3e | $ | min |
|---|---|---|---|---|---|
| base | 3 sequential lenses, free-form verify-merge | 0.50 | 0.34 | 0.24 | 12.8 |
| 1 | **parallel** lenses; **4th (verification) lens**; severity semantics + **coherent verdict rule** (minor+ ⇒ request changes); evidence-grounding widened to cited repo reads; simplify-over-document | **0.686** | **0.505** | 0.28 | 6.9 |
| 2 | + anti-self-censorship, exhaustive docstring sweep, demote-don't-drop | 0.498 | 0.374 | 0.28 | 6.0 |
| 3 | + samples×2/lens, per-item verdict reducer with per-item fail-open | 0.530 | 0.370 | 0.57 | 5.8 |
| 4 | samples×1; reducer drop duty re-armed; code-side severity cap | 0.527 | 0.403 | 0.26 | 5.5 |
| 5 | + reducer info-asymmetry fix (never drop for citing repo files outside its evidence pack); verification asks first-class; anti-censorship removed | 0.591 | 0.450 | 0.27 | 5.6 |
| 6 | + diff-anchored first sentence enforced at lens level | 0.577 | 0.431 | 0.26 | 6.6 |

What is STABLE across all runs of the iter-1+ stack (vs. 0.50/0.34 baseline):

- **decision 0.33 → 1.00** in 14 of 15 PR-runs — the coherent-verdict rule
  (approving while asking for in-PR changes is incoherent) plus the ensemble
  fail-open, which all but guarantees a minor+ comment survives. This is the
  single largest and most reproducible gain (worth +0.13 RQS3 alone).
- **wall-clock 12.8 → 5.5-7 min** (parallel lenses; lens count is now free in
  time, paid only in tokens). This is most of the RQS3e recovery.
- **actionability ~1.0** in every run (verify-and-merge rewrite).
- cost stable at ~$0.26/review (samples×2 doubled it for no recall gain and
  was reverted — Cost-of-Pass's "majority voting rarely justifies its cost"
  reproduced exactly).

What is NOT stable — and the honest headline: **recall_w and precision swing
±0.2 per PR between runs of identical code** (4849 recall across runs: 0.60,
0.10, 0.00, 0.60, 0.30; 4678 precision: 1.00, 0.83, 0.42, 0.72, 0.07, 0.63).
Two sources, both measured: (a) lens finding-generation variance — the same
lens rolls 0-6 candidates on the same diff; (b) judge noise — validity κ≈0
cross-model, and the coverage judge pattern-matches GT file names (it scored
gt1 "miss" on a review that found the *same stale-consumer defect* in a file
the human reviewers missed). With 3 PRs × ≤6 findings, single-run RQS3 has
±0.1 noise: **iteration 1 measured 0.686/0.505 — the only run to cross both
bars — but replicates of near-identical configs (0.50-0.59) show that roll
cannot be claimed as stable.** The shipped default is the iter-6 stack (best
structural properties; its two runs: 0.591/0.450, 0.577/0.431).

Reducer lessons that generalize (now pinned in test_agent_ensemble.py):

1. **Free-form reducers silently lose findings** — asking the merge LLM to
   re-emit the final list let it keep 1 of 10 candidates (iter-1's 4678).
   The reducer now returns one keep/drop/dup verdict per NUMBERED candidate;
   code assembles deterministically and unmentioned candidates are KEPT
   (fail-open per item, not per call).
2. **Per-item fail-open without an armed drop duty inverts the failure**:
   iter-3's reducer dropped 0 of 12 — precision collapsed to 0.31-0.44. The
   verify duty and the fail-open must coexist: verify each, drop refuted,
   keep unmentioned.
3. **The reducer has less evidence than the lenses** (diff pack vs. repo
   tools) — untreated, "verify" degenerates into "drop whatever I can't
   see", which deletes exactly the repo-impact findings the v3 rubric
   legitimizes (measured: it dropped a correct benchmark-verification ask as
   "not a concrete defect" and a repo-context finding as "not in the PR
   diff"). Verdicts on repo-cited claims are now judged on coherence of the
   cited evidence, not visibility in the reducer's pack.
4. **Caps must be code, not prompt** — reducers ignored a prompted 6-comment
   cap; the budget is now deterministic (severity-ordered, cap 5).

Next steps the data supports: (a) replicate-mean evaluation (report mean ±
spread over N runs per config — single runs cannot rank configs at this n);
(b) more PRs with unresolved GT (resolution contamination caps achievable
recall: the final merged diff already contains the fixes reviewers asked
for); (c) a cross-family judge for validity (κ≈0 within-family); (d) the
c-CRAB executable-verification direction for the recall judge.

## RQS v3 (second literature pass — see METRIC_V3.md, RESULTS_V3.md)

v3 fixes the two failure modes v2's own reliability stats exposed: validity
judging at κ≈0, and harmonic zeroing of silent reviews (the Opus arm's 0.14).
Grounded in: multi-trial majority + anchored rubrics (arXiv 2606.13685),
decision-level correctness / true negatives (Sphinx, arXiv 2601.04252),
weak-signal aggregation (arXiv 2604.24525), determinism-over-judging
(c-CRAB, arXiv 2603.23448).

| arm | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|
| **copilot_v2 ensemble** | **0.19** | 0.75 | **0.92** | **0.33** | **0.50** | 739k |
| claudecode_skill (DeepSeek) | 0.15 | 0.89 | 0.92 | 0.00 | **0.46** | 638k |
| pure_copilot | 0.15 | 0.83 | 0.50 | 0.00 | **0.36** | 10k |
| claudecode_opus_skill | 0.10 | 0.78 | 0.50 | 0.00 | **0.33** | 1.81M |
| copilot_skill | 0.08 | 0.42 | 0.33 | 0.17 | **0.23** | 25k |

What v3 shows:

1. **The ranking survives a third metric construction** — copilot_v2 ensemble
   stays on top (0.50), claudecode_skill second. Three differently-built
   metrics (v1 F1, v2 harmonic RQS, v3 weighted-arithmetic RQS3) now agree on
   the top two, which is no longer attributable to metric artifacts.
2. **The Opus arm recovers from 0.14 to 0.33** — the arithmetic aggregate
   prices its two silent APPROVEs at their component weight instead of
   zeroing whole PRs, and the anchored rubric lifts its precision to 0.78.
   Its residual gap is now legible: decision 0.00 (it approved all three PRs
   humans requested changes on) — a defensible-judgment-vs-GT disagreement,
   not a metric artifact.
3. **The decision column is the cleanest new signal**: on #4679 (two blocking
   human issues) copilot_v2 was the ONLY arm of five to output REQUEST
   CHANGES. Deterministically extracted, no judge involved.
4. **Honest reliability read**: even with anchored rubrics and 3 trials,
   validity self-consistency κ=0.23 and cross-model κ=0.00 — the coin-flip
   diagnosis (arXiv 2606.13685) holds for this judge family; 6-vote share
   averaging smooths the *score* but per-finding agreement stays poor.
   Precision remains the weakest column at this n; recall/actionability/
   decision are the load-bearing ones. The c-CRAB direction (executable tests
   derived from review comments — no LLM judge at all) is the right long-term
   fix.

### Efficiency in the metric: RQS3e (cost/time folded in — Cost-of-Pass, arXiv 2504.13359)

RQS3e = RQS3 · f($) · f(min), f(x) = 1/(1+log10(1+x/ref)), refs $1 / 10 min
per review (explicit budget assumptions, env-overridable — see METRIC_V3.md).

| arm | RQS3 | $/review | min/review | **RQS3e** | $-of-quality | Pareto ($, RQS3) |
|---|---|---|---|---|---|---|
| claudecode_skill | 0.46 | $0.19 | 3.0 | **0.38** | $0.41 | **frontier** |
| pure_copilot | 0.36 | $0.01 | 0.9 | **0.35** | $0.01 | **frontier** |
| copilot_v2 | 0.50 | $0.24 | 12.8 | **0.34** | $0.48 | **frontier** |
| copilot_skill | 0.23 | $0.01 | 1.1 | **0.22** | $0.04 | dominated |
| claudecode_opus_skill | 0.33 | $3.20 | 5.5 | **0.17** | $9.70 | dominated |

(Opus = actual CLI-billed USD; DeepSeek arms = cache-miss list-rate estimate,
an upper bound.)

**With time and cost in the score, the headline flips**: claudecode_skill
takes RQS3e 0.38 — the ensemble's quality lead (+0.04 RQS3) doesn't cover a
4.3x wall-clock disadvantage at the 10-min reference budget. The ensemble's
dollar discount is negligible (f($0.24)=0.92); its TIME discount is the
whole penalty (f(12.8 min)=0.74) and comes from the three lenses running
sequentially. Since the lenses are independent by construction, running
them concurrently (~5 min projected incl. reduction) puts RQS3e at ~0.39 —
narrowly back above claudecode_skill (0.38) without touching quality. That
concurrency change in `run_agent_step_ensemble` is the single
highest-leverage optimization the metric identifies. Under an async/nightly
budget (V3_TIME_REF_MIN=60) the two are statistically tied already
(0.422 vs 0.419) — at nightly latencies the quality column should decide.

- The dollar frontier has three points: pure_copilot (cheap floor),
  claudecode_skill (middle), copilot_v2 (quality ceiling). In DOLLARS the
  ensemble is nearly free to prefer over Claude Code (+$0.05/review for
  +0.04 RQS3) because DeepSeek tokens are cheap.
- The ensemble's real price is TIME: 12.8 min/review (3 sequential lens
  loops + reduction) vs 3.0 for Claude Code. Its lenses are independent —
  running them concurrently would cut wall-clock ~3x to ~4-5 min; that is
  the identified next optimization, not a metric issue.
- claudecode_opus_skill is Pareto-dominated on every axis ($9.70/quality
  point, 24x claudecode_skill) — consistent with Cost-of-Pass's finding
  that premium models pay off only where cheaper ones fail the task class;
  here the harness+skill, not model strength, was binding.
- copilot_skill is dominated (skill-as-prompt adds cost, subtracts quality);
  pure_copilot remains the right choice when review latency/budget is
  capped (72% of the ensemble's quality at 4% of its dollar cost).

## Sample E: the 3-lens ensemble (run_agent_step_ensemble) — RQS 0.34, best arm

The robustness mechanism the multi-sample analysis below kept pointing at is
now shipped: `agent.review_diff` runs as a perspective-diverse ensemble
(lenses: logic/simplifiability, behavior/in-repo consumers, contracts/docs/
assumptions — each sample goes DEEP on one slice instead of sampling one
corner of the whole checklist), followed by a verify-and-merge reduction
(dedupe with consensus weighting, per-item verification against the diff,
self-contained rewrite; base contract fields are merged deterministically in
code — reducers truncate when asked to re-emit whole contracts, and they
conflate step status with the artifact's verdict, both hit live and now
pinned by tests).

| arm (v2 metric) | recall_w | precision | actionability | **RQS** | tokens |
|---|---|---|---|---|---|
| **copilot_v2 ensemble (E)** | **0.19** | 0.81 | 0.92 | **0.34** | 738,675 |
| claudecode_skill | 0.15 | 0.69 | 0.92 | 0.27 | 637,883 |
| pure_copilot (old step) | 0.15 | 0.83 | 0.50 | 0.26 | 10,188 |
| copilot_skill | 0.08 | 0.50 | 0.33 | 0.10 | 24,903 |

Sample E is the best arm on both metrics (v1 F1 0.33 vs 0.19/0.13; v2 RQS
0.34 vs 0.27) — best recall, near-best precision, near-best actionability
simultaneously, where every earlier configuration traded one for another.
Notable: on #4678 (the "pure domain knowledge" PR where every arm ever
measured scored recall 0 on the v2 jury) the ensemble scored gt1=0.5 AND
gt2=0.25 — the simplifiability lens caught the re-derived
`get_ulysses_parallel_world_size` idiom class. RQS 0.62 on that PR.

Honest costs and caveats:
- ~740k tokens/review (3 tool-loop lenses + reducer) — Claude Code territory,
  ~70x the old single-shot. `REVIEW_ENSEMBLE=0` restores the cheap path.
- #4849 recall was 0 this run (v2 jury; the v1 judge scored the same review
  gt1=0.5 — judge noise cuts both ways). Variance is reduced, not eliminated.
- Validity κ collapsed to 0.03 pooled — precision columns remain
  jury-noise-limited at this n; the RANKING and the recall/actionability
  columns are the trustworthy signals.

## Fifth arm: REAL Claude Code + skill on REAL Opus 4.8 (native CLI auth)

Same Claude Code harness, skill, and read-only allowlist as claudecode_skill —
only the generator differs (the one cross-model arm; judges remain the
DeepSeek jury).

| arm (v2) | recall_w | precision | actionability | **RQS** | tokens | $ |
|---|---|---|---|---|---|---|
| claudecode_opus_skill | 0.10 | 0.83 | 0.50 | **0.14** | 1.81M | $9.59 total |
| claudecode_skill (DeepSeek) | 0.15 | 0.69 | 0.92 | 0.27 | 638k | — |
| copilot_v2 ensemble | 0.19 | 0.81 | 0.92 | 0.34 | 739k | — |

Per PR: #4679 RQS **0.41** with gt1=0.75 — the deepest verification of the
blocking SSE issue any arm produced (53 turns, 4.3M tokens). #4678 and #4849:
confident APPROVE with 1-2 non-GT findings → recall 0 → RQS 0.

The result is the cleanest demonstration yet of the skill's brevity ethos:
Opus obeys "most PRs get few comments; some get an empty APPROVE" *better*
than DeepSeek does — it verifies the checklist thoroughly (blocker-scan table,
all PASS), concludes the PR is fine, and approves. Precision 0.83 (highest of
the CC arms), recall starved. **Precision through silence is a property of
the skill's comment budget, not of model weakness** — upgrading the model
made it stronger, not weaker. The ensemble beats it on this GT-recall metric
because its lenses are *obligated* to sweep and report labeled findings.

Caveats: same merged-PR contamination bound as the other CC arm; the DeepSeek
jury judging Opus output is the one cross-family judging cell (self-preference
bias, arXiv 2604.22891, would deflate it); n=3; actionability 0.50 is computed
over very few findings.

## copilot_v2 — the shipped step improved from these findings (pr-review@4)

What was built (`agent.review_diff` v2 + `pr.gate_check`, playbook v4):
deterministic gate checks (draft/merge-state/failing CI — the issue class no
diff-only model caught), an evidence-grounded tool loop over the repo
checkout, the domain checklist (incl. "undocumented assumptions/invariants" —
added because #4849's ground truth was exactly that), severity labels with an
explicit `[unverified]` escape hatch, and a verify-and-rewrite editor pass.

**Lesson learned the hard way:** the first version told the model "do not
invent findings" with maintainer brevity — and it reproduced the pure_skill
failure mode exactly: three justified APPROVEs, RQS 0.00, despite doing the
evidence work (6+ lookups). On this model, *precision through silence* beats
recall to death; the fix is *precision through labeling* (nits welcome,
[unverified] allowed and marked). That change alone took RQS from 0.00 to
0.38 on the next sample.

**Multi-sample results** (3 samples of the identical final config; the eval's
single-run tables understate variance — samples preserved in
`raw/copilot_v2_samples/`):

| sample | recall_w | precision | actionability | RQS |
|---|---|---|---|---|
| A (prompt-based step) | 0.27 | 0.72 | 0.91 | 0.38 |
| B (prompt-based step) | 0.08 | 0.19 | 0.81 | 0.14 |
| C (prompt-based step) | 0.21 | 0.53 | 0.76 | 0.23 |
| D (unified agent runtime) | 0.12 | 0.29 | **1.00** | 0.11 |
| E (runtime + 3-lens ensemble, RESULTS_V2 table) | 0.19 | 0.81 | 0.92 | **0.34** |
| **mean A–D (range)** | 0.17 | 0.43 | 0.87 | **0.22 (0.11–0.38)** |

Sample D is the 修正方案 runtime step (dispatch context, evidence pack, skill
injection, output contract). Its per-PR results show the seeded skills doing
their job — both skill-targeted GT classes hit (#4679 gt1 breaking-change
consumers 0.5, #4849 gt1 undocumented assumption 0.25) and actionability a
perfect 1.00 (the structured review_comments contract). Its jury precision is
demonstrably noise: on #4679 the validity jury scored all 4 findings invalid
while the coverage judge matched one of those same findings to ground truth —
mutually contradictory judgments (validity κ=0.32). Read actionability,
coverage, and cost; not the precision column.

Mean RQS ≈ pure_copilot (0.26) and claudecode_skill (0.27) — which are single
samples with presumably similar variance — at ~1/4 of Claude Code's tokens.

Robust conclusions (hold across every sample):
- **Actionability ~0.81–0.91** vs the old step's 0.50 — every finding is now a
  file:line directive. This is the dimension the jury judges reliably (κ=0.6+).
- **Breadth across samples**: the three samples collectively touched **5 of 8**
  ground-truth issues (4678 gt1; 4679 gt1, gt3; 4849 gt1, gt2 — including two
  issues no other arm ever hit), vs 2/8 for the old step and 3/8 for Claude
  Code + skill. Each run samples a different corner of the checklist.
- **Evidence-grounding works mechanically**: 6–23 repo lookups per review, gate
  step deterministic, editor output clean.

Honest negatives:
- **Per-run variance is large** (RQS 0.14–0.38); a single review samples one
  subset of what the step can find, and false positives still occur (a live
  #4837 sample disputed changes that are actually correct). The validity
  judge's κ≈0 means the precision column mixes arm noise with judge noise.
- Practical mitigation if review quality matters more than cost: run the
  review step 2–3 times and merge/dedupe findings (union recall is the strong
  suit) — a natural future `foreach` fan-out + merge step.

---

## RQS v2 update (literature-grounded rerun — see METRIC_V2.md, RESULTS_V2.md)

Re-scoring the same nine cached reviews with the v2 metric (severity/resolution-
weighted recall, jury-judged precision + actionability, CRScore-style
pseudo-reference comprehensiveness/conciseness, 2-judge jury with Cohen's κ):

| arm | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** |
|---|---|---|---|---|---|---|
| pure_copilot | 0.15 | 0.83 | 0.50 | 0.04 | 0.17 | **0.26** |
| copilot_skill | 0.08 | 0.50 | 0.33 | 0.18 | 0.67 | **0.10** |
| pure_skill | 0.00 | 0.33 | 0.67 | 0.01 | 0.17 | **0.00** |

What v2 adds beyond confirming the v1 ranking:

1. **The ranking is metric-robust.** A completely different construction
   (weighted GT, juries, pseudo-references, harmonic aggregate) preserves
   pure_copilot > copilot_skill > pure_skill. That ordering is now hard to
   attribute to metric artifacts.
2. **Judge noise is real and now measured.** Inter-judge agreement:
   validity κ=0.23 (poor!), alignment κ=0.44 (moderate), actionability κ=0.65
   (substantial). v1's precision numbers carried invisible ±noise — e.g. the
   pure-skill nit on #4678 flipped from valid (v1 judge) to invalid (v2 jury).
   Any future precision claims need the jury; actionability is the most
   reliably judgeable dimension.
3. **Comprehensiveness exposes the brevity ceiling.** Against ~12
   pseudo-references per PR, even the best arm covers ≤0.46 — 1-2-finding
   reviews structurally cannot cover a diff's reviewable surface. The skill's
   comment budget optimizes precision at a hard cap on comprehensiveness.
4. **copilot_skill has a distinct profile v1 hid**: best comprehensiveness
   (0.18) and conciseness (0.67) — its findings align with legitimate review
   topics — but weakest actionability (0.33): the skill guidance produced
   on-topic but non-directive comments on this model.
5. The harmonic RQS zeroes any arm with a zero component (per spec) — read the
   sub-scores, not just the headline, at this n.

v2 limitations: same-family 2-model jury (cross-family slot is env-pluggable
via `V2_JUDGE_MODELS`); alignment is judge-based, not embedding-based; n=3.

## Fourth arm: REAL Claude Code + skill (same DeepSeek model)

`claudecode_skill` = genuine headless Claude Code (v2.1.199, `claude -p`,
`ANTHROPIC_BASE_URL` → DeepSeek, model deepseek-v4-pro) with the skill
installed as a project skill, subagents enabled, and `gh` restricted to
read-only PR subcommands (posting structurally impossible).

| arm | recall_w | precision | actionability | conciseness | **RQS v2** | turns | sec |
|---|---|---|---|---|---|---|---|
| claudecode_skill | 0.15 | 0.69 | **0.92** | **0.78** | **0.27** | 20–27 | ~180 |
| pure_copilot | 0.15 | 0.83 | 0.50 | 0.17 | 0.26 | 1 | 52 |
| copilot_skill | 0.08 | 0.50 | 0.33 | 0.67 | 0.10 | 1 | 65 |
| pure_skill (simulated) | 0.00 | 0.33 | 0.67 | 0.17 | 0.00 | ≤18 | 94 |

Takeaways:

1. **The harness was most of the skill's missing value.** Real Claude Code +
   skill scores RQS 0.27 where our simulated skill arm scored 0.00 — same
   model, same skill. Subagents, `gh` evidence, and Claude Code's execution
   discipline are what make the skill work; the skill text alone (arms 1/3)
   does not transfer.
2. **Best actionability (0.92) and best single ground-truth hit** (0.75 on
   #4679's blocking SSE-compat issue). Its #4679 finding was genuinely novel:
   a recipe file added to the repo *after* the PR merged that still carries
   the exact bug class the human reviewer flagged elsewhere — real follow-up
   work the humans missed (scored only in precision, not recall, per design).
3. **Cost is in a different league**: ~640k input tokens/review (inflated by
   per-turn cache reads across 20–27 turns — turns and wall-clock ~180s are
   the fairer comparators, vs 1 call / ~52s for pure_copilot). Roughly even
   RQS with pure_copilot at ~60× the tokens: the copilot's cheap pass buys
   almost the same headline score, while Claude Code buys actionability,
   verification depth, and novel findings.
4. **Contamination caveat**: on merged PRs, `gh pr view` exposes the human
   review threads our ground truth comes from — the review header shows it saw
   review metadata (round count, approval). Its recall numbers should be read
   as an upper bound; rerunning on open PRs (or blocking review fields) is the
   clean protocol.
5. Validity κ dropped to 0.02 with the new data — precision columns are noise
   at this sample size; actionability (κ=0.61) and the ranking are the
   trustworthy signals.

---

## v1 analysis (original)

Numbers in [RESULTS.md](./RESULTS.md); metric in [README.md](./README.md);
raw reviews/judgments in `raw/`.

## Headline

| arm | recall_GT | precision | **F1** | tokens/review | seconds |
|---|---|---|---|---|---|
| pure_copilot | 0.12 | 0.83 | **0.19** | ~10k | 52 |
| copilot_skill | 0.08 | 0.67 | **0.13** | ~25k | 65 |
| pure_skill | 0.00 | 0.67 | **0.00** | ~101k | 94 |

**On DeepSeek v4 pro, the copilot's plain structured pass wins** — it is also
10× cheaper than the skill agent. But the far more important result is the
absolute level: **every configuration scored low against what human
maintainers actually raised** (best recall 0.25 on any single PR).

## Why each arm scored what it did

1. **The human review value on these PRs came from knowledge no arm had.**
   The ground-truth issues required: product constraints ("action and sound
   cannot co-occur, simplify the branches" — #4678), project idioms ("call
   `get_ulysses_parallel_world_size()` directly" — #4678), cross-repo
   awareness (in-repo demo clients / docs broken by the SSE default — #4679),
   and live merge state (the file renamed on main → modify/delete conflict —
   #4679). A diff, however carefully read, doesn't contain these.

2. **pure_skill: the skill's discipline works against a weaker model.**
   The skill encodes maintainer ethos — "most PRs should get 1-5 short
   comments; some just get an empty APPROVE", "prioritize high-confidence
   findings over coverage theater". Claude-class models fill that confidence
   bar with real insight; DeepSeek, lacking it, obeys the brevity rule and
   converges to a confident APPROVE plus a style nit (#4678: full blocker-scan
   table, all PASS, verdict APPROVE — both human issues missed). Perfect
   precision when it spoke; zero recall. It spent its 100k tokens *verifying*
   its few claims against the repo (hence precision 1.0 where it commented),
   not discovering issues.

3. **pure_copilot: cheap concreteness pays.** The generic "meticulous
   reviewer, findings with file:line" prompt produces 2 concrete claims per PR
   with no brevity suppression — and twice one of them overlapped the top
   human issue (the stream=True SSE breaking change on #4679; the
   first-output-is-parent assumption area on #4849). Highest specificity
   (0.83) and lowest cost.

4. **copilot_skill: guidance redirected rather than sharpened.** With the
   skill checklist injected but no tools, DeepSeek leaned on the skill's
   process items ("run the affected e2e tests", "verify the benchmark") —
   actionable but not what the humans flagged. Its one partial hit (#4849) had
   perfect precision.

## Fairness caveats (beyond README's)

- The harness gave **no arm** `gh` access (only local diff/metadata/repo).
  The skill's own workflow starts with a `gh`-based gate check that would very
  likely have caught #4679's merge-conflict issue (gt4) natively — so the
  pure-skill arm is handicapped on exactly one GT issue by harness design.
- One PR (#4678) yielded zero recall for all arms — its ground truth is pure
  domain knowledge; it deflates all arms equally.
- n=3 PRs, self-model judge (blind, normalized findings). Directional only.

## What this suggests building

The three arms fail in complementary ways, which points at one configuration
none of them is yet: **copilot's structured evidence steps (fetch diff +
`gh pr checks`/mergeable state + changed-file blame/rename detection) →
skill checklist as the review rubric → repo read tools for verification.**
- The merge-conflict GT and CI-gate class of issues become deterministic
  *steps*, not model insight (the copilot already fails-closed this way
  elsewhere).
- The skill's checklists stay valuable as *what to look for*, with the
  brevity rule relaxed for weaker models (or the review model upgraded —
  rerunning this harness with a Claude-class model is one command).
- The copilot's cheap concrete pass remains the floor: never return an empty
  APPROVE without the evidence steps having run.
