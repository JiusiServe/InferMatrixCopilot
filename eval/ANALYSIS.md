# Analysis — pure skill vs pure copilot vs copilot+skill (DeepSeek v4 pro)

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
