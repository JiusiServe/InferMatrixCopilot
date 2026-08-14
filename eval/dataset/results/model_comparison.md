# Model comparison — Strict pipeline vs Claude Code + Opus 5

Campaign: make the Strict copilot (DeepSeek v4-pro official) beat the
CC+Opus 5 baseline on PR review. Baseline = Claude Code + Opus 5 on the same
pinned PR-time worktree with the same frozen sanitized snapshot
(`baselines/claudecode_opus5`). All comparisons are blind pairwise judgments
(`judge_val.py`): randomized X/Y order, 3 replicates per item, tool-less judge
scoring against human ground-truth reviews. Machine-readable copies:
`model_comparison.json` / `model_comparison.csv` in this directory (regenerate
with the aggregator; numbers below are computed from the raw verdict JSONs,
not hand-kept).

Last updated: 2026-08-14. All arms complete.

## Headline: wave-2 holdout (10 fresh PRs, human-only GT), judge = claude-sonnet-5

Wins are verdict counts out of `3 × n_items` (arm—baseline, no ties occurred).

| arm | route | wins | recall | precision | actionability | judgment set |
|---|---|---|---|---|---|---|
| DS v4-pro r1 (re-scored) | v13 pipeline | **10—20** | 0.32 / 0.44 | **0.83** / 0.79 | 0.80 / 0.89 | `goal_v13_wave2_sonnet` |
| DS v4-pro r2 (fresh gen) | v13 pipeline | 3—27 | 0.28 / 0.51 | 0.80 / 0.82 | 0.78 / 0.88 | `goal_ds_wave2_r2_sonnet` |
| MiMo-v2.5 (re-scored) | v13 pipeline | 2—25 | 0.27 / 0.47 | 0.73 / 0.81 | 0.59 / 0.88 | `goal_mimo_wave2_sonnet` |
| Composer-2.5 † | cursor-agent harness | 4—26 | 0.38 / 0.51 | 0.75 / 0.80 | 0.77 / 0.88 | `goal_composer_wave2_sonnet` |
| Grok-4.5 † ‡ | cursor-agent harness | 2—28 | 0.30 / 0.46 | 0.81 / 0.78 | 0.71 / 0.89 | `goal_grok45_wave2_sonnet` |

Rubric cells are mean arm / mean baseline over that set's verdicts.

† **Harness-different, never pooled with pipeline rows**: Composer and Grok
have no raw completions API, so they run headless `cursor-agent` end-to-end
(loop + model), not the v13 pipeline with only the model swapped. They answer
a different question and are listed for context only.

‡ **Grok row is contamination-tainted** — see the audit section below. 9 of
10 items are disqualified; clean-only tally is 0—3 (pr5550 only), and both of
its verdict wins landed on a contaminated item (pr5957).

## Earlier gates, judge = GPT-5.6 Sol 272K High (not comparable to Sonnet rows)

| gate | arm | wins | judgment set |
|---|---|---|---|
| val (dev gate, 5 PRs) | DS v4-pro, v13 pipeline | **8—7** (first win) | `goal_v13_val` |
| test (5 PRs) | DS v4-pro, v13 pipeline | 7—8 | `goal_v13_test` |
| wave-2 holdout | DS v4-pro r1, v13 pipeline | 14—16 | `goal_v13_wave2` |
| wave-2 holdout | MiMo-v2.5, v13 pipeline | 2—27 | `goal_mimo_wave2` |

Under GPT-5.6 the DS arm reached parity (val+test 15—15, wave-2 near-parity
14—16 with precision 0.748 > 0.672 for the first time). The Sonnet re-score
revised that story: GPT-5.6 credits recall leniently; Sonnet's strict
crediting exposes the recall gap. **Cross-judge numbers must never be pooled.**

## Cost (generation, per item, wave-2 holdout)

| arm | mean $/item | mean wall |
|---|---|---|
| CC + Opus 5 baseline | $3.58 | 547 s |
| DS v4-pro r1 (v13) | $0.79 | 1139 s |
| DS v4-pro r2 (v13) | $0.78 | 1322 s |
| MiMo-v2.5 (v13) | $0.43 | 1728 s |
| Composer-2.5 (harness) | n/a (flat plan) | 177 s |
| Grok-4.5 (harness) | n/a (flat plan) | 284 s |

DS-on-v13 delivers its verdict count at ~22% of the baseline's dollar cost.

## Leakage audit (harness arms only)

Pipeline arms and the Claude baseline *prevent* discussion/out-of-tree access
(tool allowlist). `cursor-agent` has no allowlist, so harness arms *detect*
violations post-run over the full stream-json tool log and disqualify items.

- **Composer-2.5**: 1/10 items failed — `pr5884` read its own cursor terminal
  log (`~/.cursor/projects/.../terminals/…`). Benign class (harness scratch
  file, no methodology or discussion content). Clean-only tally 4—23.
- **Grok-4.5**: 9/10 items failed (`pr5509 5610 5703 5715 5840 5863 5884
  5957 5976`). Every failure includes reading
  `~/.claude/skills/imreview/SKILL.md` — our own review-methodology skill —
  despite an explicit "do not read ANY file outside this working directory …
  reviews that do are disqualified" prompt line that Composer obeyed. `pr5703`
  additionally read a rule file from the installed copilot package's
  vllm-omni knowledge base, and `pr5976` read installed upstream vllm source.
  This is real contamination (our methodology and curated repo knowledge in
  its context), and even so Grok won only 2/30 verdicts — both on
  contaminated `pr5957`. Clean item: `pr5550` only (0—3). Prompt-level
  boundary instruction is demonstrably insufficient for this model; any rerun
  needs environment-level prevention (e.g. hiding `~/.claude/skills` from the
  agent) before its numbers can be taken at face value.

## Standing caveats

1. **Generation-replicate variance is huge**: the same config + judge gave
   10—20 (r1) vs 3—27 (r2). Never quote a single-replicate result as *the*
   number; the campaign's open protocol item is ≥3 generation replicates.
2. **Judge dependence**: GPT-5.6 vs Sonnet flip the parity conclusion; the
   standing protocol is judge = claude-sonnet-5, and any historic GPT numbers
   are labeled as such.
3. **Precision is judge-robust and solved** (DS 0.80–0.83 ≥ baseline under
   both judges); **strict-credit recall (~0.3 vs ~0.5) is the open gap**.
   Remaining lever: coverage-driven second investigation round (RFC q3).
4. gap_hit scored 0.00 for every arm and the baseline on wave-2 under Sonnet.

## Raw data

- Verdicts: `eval/dataset/judgments/<set>/pr*.r*.json` (+ per-set
  `JUDGE_REPORT.md` with per-verdict rationales)
- Review artifacts: `eval/dataset/arms/<arm>/pr*.md` (+ `.cost.json`,
  harness arms also `.events.jsonl` tool logs)
- Baseline: `eval/dataset/baselines/claudecode_opus5/`
- Campaign narrative: `doc/EVAL-goal-strict-vs-opus5.md`, RFC
  `doc/RFC-strict-review-deep-engine.md`, GitHub issue #72, PR #71.
