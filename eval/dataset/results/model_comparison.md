# Model comparison — Strict pipeline vs Claude Code + Opus 5

## v14/v15 recall campaign (2026-08-15) — waves 3-4, judge = claude-sonnet-5

Post-cursor-campaign iteration: teacher-trace distillation (Claude Fable 5 on
the train split, `baselines/teacher_fable5/`) + wave-2 forensics produced the
v14/v15 pipeline (doc/RFC-review-recall-v14.md): investigation duties
(claim ledger, sibling contrast, PR-numbers falsification, merge audit,
producer census, test/gate epistemics, differential parity), a docs
claims-audit/IA pass, archaeology tools (diff_stat/file_at_base/show_commit/
search_history/calc — bridged to harness backends), a coverage-driven
second round (per-hunk seeds), ranked verification ledger, and machinery
fixes (truncated-final retries, reducer failure-path collapse, gray-zone
planner un-broken — its 400-token cap had silently failed on every gray
item since the official reasoning model landed).

Wave 3 (holdout3) hosted two DISCLOSED gate attempts, then was opened for
forensics (spent). Wave 4 (holdout4, build_wave4.py) is the clean gate.
All rows: DS v4-pro generator, 3 judge replicates, arm—baseline wins and
rubric means (arm / baseline).

| gate | arm | wins | recall | precision | note |
|---|---|---|---|---|---|
| wave-3 attempt 1 | v14 | 2—28 | .207 / .371 | .788 / .843 | INVALID as a design measure: pass finals died at the 16k token ceiling on 7/10 items; planner broken |
| wave-3 attempt 2 | v14+fixes | 5—25 | .231 / .424 | .790 / .824 | machinery healthy; pr5853 swept 3-0 (r .65/.18); loss localized to duties-vs-GT mismatch → forensics |
| **wave-4 (clean)** | **v15** | **10—20** | **.261 / .335** | **.816 / .787** | **precision ABOVE baseline on a fresh holdout; recall ratio .78 (v13/v14 fresh splits: .55–.75). Arm wins the GT-richest items (5864 GT=17, 5958 GT=20, 5608 swept)** |
| wave-4 replicate 2 (first attempt) | v15 | INVALID | — | — | DeepSeek 402 Insufficient Balance mid-sweep; stubs judged as empty; quarantined (`INVALID_apierror_goal_v15r2_holdout4_sonnet`); rerun landed after recharge (next row) |
| wave-4 replicate 2 | v15 (DS api, cheap seats on v4-flash) | 11—19—0 | .283 / .338 | .800 / .778 | replicates r1: precision above baseline in BOTH independent replicates; same items sweep (5608, 5958) and the same 4 mid-size items lose. Pooled 60 verdicts: 21—39, r .272/.336, p .808/.783 |
| wave-4 (same gate) | v16 (v15 + Fable adversary/round-2 via claude-code backend) | 6—23—1 | .336 / .416 | .800 / .805 | best fresh-split arm recall of the campaign (ratio .81); precision parity. Train probe had shown BOTH means above (9—11, r .627/.625, p .805/.772) — did not transfer. Baseline drift across the three wave-4 sets on identical mds: opus r .335/.338/.416 (±.08) now exceeds the arm deltas being chased |
| wave-4 (same gate) | v15 via cursor backend (Composer 2.5) | 4—24—2 | .283 / .364 | .765 / .810 | subscription; contamination sweep clean (0 skill refs, all traces); swept pr5958 (r .61/.33); recall ratio matches DS (.78), precision trails — the wave-2 pattern (Composer carries recall, DS carries precision) reproduces on the v15 pipeline |

Cost on wave-4: v15 $0.97/item vs baseline $3.09/item (3.2× cheaper);
cursor row on subscription. Baseline disclosure: pr5720/pr5864 carry a
benign self-read audit flag (Claude Code's own large-tool-result spool;
recorded in their cost.json). Judgments: `goal_v14_holdout3_sonnet`,
`goal_v14r2_holdout3_sonnet`, `goal_v15_holdout4_sonnet`,
`goal_v15r2b_holdout4_sonnet`, `goal_v15cb_holdout4_sonnet`,
`goal_v16f_holdout4_sonnet`, `goal_v16rs_train_sonnet`, `goal_v16f_train_sonnet`.
Replicate-2 config note: planner + promotion on v4-flash (owner
direction), generator/verify/reducer unchanged on v4-pro.

Standing conclusion (post v16): pooled over wave-4's three DS-core
submissions (90 verdicts: v15 r1, v15 r2, v16) the arm is 27—62—1 with
pooled precision .805 vs .790 (above) and pooled recall .293 vs .363
(ratio .81). Fable in the adversary/round-2 seats buys the best
fresh-split recall (v16 .336, and it reproduced the pr4870 GOLD-gap
catch in-pipeline on train) at precision parity; the v15 all-DS config
holds precision above instead. Strictly-better-on-both-means on one
fresh gate is NOT demonstrated, and measured baseline judge drift
(±.08 recall on identical mds across sets) now bounds what any further
single-split submission can show — a pre-registered pooled/larger gate
or a full-Fable generator run are the remaining honest levers.

# Cursor-model campaign (2026-08-14/15) — wave-2

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
