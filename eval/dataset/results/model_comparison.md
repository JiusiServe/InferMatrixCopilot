# Model comparison — Strict pipeline vs Claude Code + Opus 5

Campaign: make the Strict copilot beat the CC+Opus 5 baseline on PR review.
Baseline = Claude Code + Opus 5 on the same pinned PR-time worktree with the
same frozen sanitized snapshot (`baselines/claudecode_opus5`). All comparisons
are blind pairwise judgments (`judge_val.py`): randomized X/Y order, 3
replicates per item, tool-less judge scoring against human ground-truth
reviews. Machine-readable copies: `model_comparison.json` /
`model_comparison.csv` (regenerate with `aggregate_results.py`; numbers are
computed from the raw verdict JSONs, not hand-kept).

**Status: INTERIM (2026-08-15 early AM).** The Grok-4.6 r3 canonical row is
mid-backfill (4 items regenerating in a peer session after a
parallel-pass-window audit finding); one final regeneration follows the
peer's completion ping. Every other row is final.

## Wave-2 holdout, single-model arms, judge = claude-sonnet-5

Wins out of 3 × n_items (arm—baseline). Two routes, never pooled:
**v13-cb** = the copilot's own v13 Strict pipeline with the model served
through the cursor-agent backend (provider registry, MCP tool bridge — the
vendor CLI owns the inner tool loop); **harness** = raw cursor-agent
end-to-end (loop + model, no copilot pipeline).

| arm | route | wins | recall | precision | actionability | judgment set |
|---|---|---|---|---|---|---|
| DS v4-pro r1 (re-scored) | v13 api | **10—20** | 0.32 / 0.44 | **0.83** / 0.79 | 0.80 / 0.89 | `goal_v13_wave2_sonnet` |
| DS v4-pro r2 (fresh gen) | v13 api | 3—27 | 0.28 / 0.51 | 0.80 / 0.82 | 0.78 / 0.88 | `goal_ds_wave2_r2_sonnet` |
| MiMo-v2.5 (re-scored) | v13 api | 2—25 | 0.27 / 0.47 | 0.73 / 0.81 | 0.59 / 0.88 | `goal_mimo_wave2_sonnet` |
| Composer-2.5 | v13-cb | 4—25 (1 tie) | 0.32 / 0.43 | 0.73 / 0.78 | 0.71 / 0.88 | `goal_cb_composer25_wave2_sonnet` |
| Grok-4.5-high | v13-cb | 5—24 (1 tie) | 0.35 / 0.50 | 0.78 / 0.81 | 0.75 / 0.88 | `goal_cb_grok45_wave2_sonnet` |
| Grok-4.6-high r3 † | v13-cb | 2—16 (6/10 items, INTERIM) | 0.34 / 0.56 | 0.82 / 0.84 | 0.74 / 0.87 | `goal_cb_grok46_r3_sonnet` |
| Composer-2.5 | harness | 4—26 | 0.38 / 0.51 | 0.75 / 0.80 | 0.77 / 0.88 | `goal_composer_wave2_sonnet` |
| Grok-4.5 ‡ | harness | 2—28 | 0.35 / 0.55 | 0.84 / 0.82 | 0.70 / 0.90 | `goal_grok45_wave2_sonnet` |

† Canonical clean Grok-4.6 row (peer-session campaign run after the
skill-leak vector was closed; 4 items in backfill — pr5509/5703 for
hidden-path reads, pr5884/5957 after the parallel-pass-window audit finding
that a session straddling the vault cutoff cannot be exonerated by its end
timestamp). Two earlier Grok-4.6 v13-cb replicates are TAINTED by the skill
leak (see ledger): r1 (`INVALID_skillleak_copilot_cb_grok46`, 5—24 tainted)
and r2 (`goal_cb_grok46_wave2_sonnet`, 3—17—1 over its 7 kept items).
Their agreement with r3 indicates the leak was not driving the numbers.

‡ Harness Grok-4.5 is 9/10 contamination-disqualified (clean-only 0—3);
listed for the record.

## Normalized view (each arm ÷ its own in-matchup baseline)

The baseline's raw column wobbles across rows (independent judge calls,
pairwise context, item subsets), so cross-row comparison uses ratios computed
WITHIN each judgment set: `metric_arm / metric_baseline` over the same
verdicts (1.00 = parity), plus a tie-adjusted win share (ties = ½ win).

| arm | win share | recall index | precision index |
|---|---|---|---|
| DS v4-pro r1 (v13 api) | **0.33** | **0.74** | **1.05** |
| DS v4-pro r2 (v13 api) | 0.10 | 0.55 | 0.99 |
| MiMo-v2.5 (v13 api) | 0.07 | 0.57 | 0.91 |
| Composer-2.5 (v13-cb) | 0.15 | 0.74 | 0.93 |
| Grok-4.5 (v13-cb) | 0.18 | 0.71 | 0.96 |
| Grok-4.6 r3 (v13-cb, partial) | 0.11 | 0.56 | 1.00 |
| MoA r1 (mixture) | 0.18 | 0.70 | 1.01 |
| MoA r2 (mixture, peer) | 0.17 | 0.72 | 1.03 |
| Composer-2.5 (harness) | 0.13 | 0.75 | 0.94 |

Normalization makes the pattern unambiguous: **every arm recalls 26–45% less
than the baseline measured in its own matchup** (index 0.55–0.75), while
precision is within ±9% of parity everywhere (several arms above it). The
raw-score wobble was judging noise; the recall gap is not.

## Wave-2 holdout, MoA arms (composer-2.5 + cursor-grok-4.6-high + mimo-v2.5)

Mixture proposers on the DS v4-pro spine (`MOA_WHEN=always`, reducer/merge on
the tier model; harness members ride the provider registry, budget cap
governs the API member only). Two independent replicates of the SAME config,
different sessions:

| replicate | wins | recall | precision | actionability | judgment set |
|---|---|---|---|---|---|
| MoA r1 | 5—24 (1 tie) | 0.29 / 0.42 | 0.80 / 0.79 | 0.76 / 0.88 | `goal_v13moa_cgm_wave2_sonnet` |
| MoA r2 (final, 30/30) | 5—25 | 0.29 / 0.43 | **0.83** / 0.79 | 0.79 / 0.88 | `goal_moa_cgm_wave2_sonnet` |

MoA matches the better single-model arms on wins and slightly beats the
baseline on precision, but recall (~0.29) is the worst of any arm — mixing
weaker proposers dilutes coverage rather than compounding it.

## Conclusion of the cursor-model campaign

No cursor-served configuration — Composer, Grok-4.5, Grok-4.6, or the
three-model MoA — beats CC+Opus 5 on the holdout under the strict Sonnet
judge. Every arm lands inside DeepSeek's replicate band (10—20 … 3—27).
Precision is consistently competitive (several arms ≥ baseline);
**strict-credit recall (~0.29–0.35 vs ~0.42–0.56) is the universal gap**,
unchanged from the DS-only campaign. The remaining lever on record is the
coverage-driven second investigation round (RFC q3).

## Earlier gates, judge = GPT-5.6 Sol 272K High (not comparable to Sonnet rows)

| gate | arm | wins | judgment set |
|---|---|---|---|
| val (dev gate, 5 PRs) | DS v4-pro, v13 pipeline | **8—7** (first win) | `goal_v13_val` |
| test (5 PRs) | DS v4-pro, v13 pipeline | 7—8 | `goal_v13_test` |
| wave-2 holdout | DS v4-pro r1, v13 pipeline | 14—16 | `goal_v13_wave2` |
| wave-2 holdout | MiMo-v2.5, v13 pipeline | 2—27 | `goal_mimo_wave2` |

Under GPT-5.6 the DS arm reached parity (val+test 15—15; wave-2 precision
0.748 > 0.672 for the first time). The Sonnet re-score revised that story:
GPT-5.6 credits recall leniently. **Cross-judge numbers must never be pooled.**

## Cost (generation, per item, wave-2 holdout)

| arm | mean $/item | mean wall |
|---|---|---|
| CC + Opus 5 baseline | $3.58 | 547 s |
| DS v4-pro (v13 api) | $0.78–0.79 | 1139–1322 s |
| MiMo-v2.5 (v13 api) | $0.43 | 1728 s |
| Composer-2.5 (v13-cb) | subscription | 397 s |
| Grok-4.5 (v13-cb) | subscription | 496 s |
| Grok-4.6 (v13-cb) | subscription | 1111 s |
| MoA r1 (mixture) | $0.33 API + subscription | 1195 s |
| Composer-2.5 / Grok-4.5 (harness) | subscription | 177 / 284 s |

## Contamination ledger (grok skill-leak incidents, 2026-08-14)

The grok family (4.5 and 4.6 — never Composer) actively hunts and reads the
copilot's own `imreview` review-methodology skill during review sessions,
across three locations (`~/.claude/skills/`, `~/.agents/skills/`,
`~/.cursor/skills/`), ignoring prompt-level bans. Countermeasure history:
prompt ban → defeated; dot-rename of the dirs → defeated (grok lists parents
/ mines its own transcripts for the renamed name); only moving all copies
into non-listable, permission-000 quarantine outside any skills path closed
the vector (consensus close time 23:30; `~/.cursor` copy's plain path was
live until its 21:45 rename — multi-session consensus, mtime-evidenced).

Per-arm status (audits = trace grep for `imreview` / `.agents/skills` /
`.cursor/skills`; read attempts on absent/unreadable paths are harmless):

- **Composer harness**: pr5884 benign self-read only. **Composer v13-cb**:
  benign classes only (audit relative-path false-positive — since fixed in
  `providers/audit.py` — own-run-dir and installed-package reads). CLEAN.
- **Grok-4.5 harness**: 9/10 items read SKILL.md — disqualified
  (`INVALID`-prefixed dirs). **Grok-4.5 v13-cb**: clean (dead-path attempts
  only; pr5840 regenerated once after reading the `~/.agents` copy).
- **Grok-4.6 v13-cb r1**: 9/10 skill-read → arm quarantined
  (`INVALID_skillleak_copilot_cb_grok46`). **r2**: plain-`~/.cursor`-path
  reads succeeded pre-21:45 → tainted, kept for the ledger
  (`QUARANTINE_skillleak_r2/r3` subdirs hold the item history). **r3**
  (peer session, post-closure): canonical.
- **MoA r1**: pr5884 read the hidden `~/.cursor` name → quarantined and
  regenerated post-closure (regen trace clean; the packed `trace.json.gz`
  bundles the old run's events — check `runs/pr5884/run-20260814-233136-*`
  for the artifact's own trace). Other 9 items clean. **MoA r2** (peer):
  pr5509 quarantined twice; attempt-3 landed post-closure, verified clean
  by its own run-dir trace — set complete at 30/30.
- Restore ledger (owner: user / peer sessions): `~/.eval-quarantine/
  {claude,agents}-imreview` (chmod 000) → `~/.claude/skills/imreview`,
  `~/.agents/skills/imreview`; `/data/zhoutaichang/.skill-vault/
  cursor-imreview` → `~/.cursor/skills/imreview`. Restore only after ALL
  cursor-backend arms across sessions are done.

## Standing caveats

1. **Generation-replicate variance is huge** (DS 10—20 vs 3—27 same config).
   Never quote a single replicate as *the* number.
2. **Judge dependence**: GPT-5.6 vs Sonnet flip conclusions; standing
   protocol judge = claude-sonnet-5.
3. **Precision is solved; strict-credit recall is the open gap** across
   every generator and the MoA.
4. gap_hit scored 0.00 for every arm and the baseline on wave-2 under Sonnet.
5. v13-cb arms report no per-token cost (subscription) and `tok_out=0`
   (cursor-agent does not expose usage in these sessions); wall time and
   verdicts are the comparable dimensions.

## Raw data

- Verdicts: `eval/dataset/judgments/<set>/pr*.r*.json` (+ per-set
  `JUDGE_REPORT.md`); quarantined items in `QUARANTINE_*`/`INVALID_*` dirs.
- Review artifacts: `eval/dataset/arms/<arm>/pr*.md` (+ `.cost.json`,
  traces; harness arms also `.events.jsonl` locally, gitignored)
- Baseline: `eval/dataset/baselines/claudecode_opus5/`
- Campaign narrative: `doc/EVAL-goal-strict-vs-opus5.md`, RFCs
  `doc/RFC-strict-review-deep-engine.md`, `doc/RFC-provider-registry.md`,
  GitHub issue #72, PR #71.
