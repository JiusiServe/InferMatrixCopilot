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

> **READ THIS BEFORE THE RAW MEANS BELOW.** The `recall` / `precision`
> columns are each side's raw rubric mean, and comparing them ACROSS
> judgment sets is not a valid test: the baseline's own recall mean reads
> .335 / .338 / .416 across three wave-4 sets that scored the *same*
> baseline reviews — ±.08 of pure judge drift, larger than the differences
> under study. The correct statistic pairs the two candidates inside each
> verdict (one judge call scores both) and clusters replicates by item;
> `paired_analysis.py` computes it. Under that test **no wave-4 config's
> recall or precision differs significantly from the baseline** (table
> below). An earlier revision of this file claimed "precision ABOVE
> baseline" from the raw means; that claim is withdrawn — the paired
> interval includes zero.

### Paired, item-clustered effect sizes (wave-4, `paired_analysis.py`)

Δ = arm − baseline within each verdict, replicates averaged per item,
95% t-CI over the 10 items.

| config | Δrecall [95% CI] | Δprecision [95% CI] | win share |
|---|---|---|---|
| v15 r1 | −.075 [−.184, +.035] | +.029 [−.022, +.080] | .33 |
| v15 r2 (flash cheap seats) | −.056 [−.175, +.064] | +.022 [−.027, +.071] | .37 |
| v16 (Fable adversary/round-2) | −.080 [−.169, +.010] | −.006 [−.069, +.058] | .22 |
| Composer cursor-backend | −.081 [−.206, +.044] | −.045 [−.095, +.005] | .17 |
| **pooled DS-core (90 verdicts)** | **−.070 [−.161, +.021]** | **+.015 [−.025, +.055]** | .31 |
| v16 on wave 5 (fresh, pre-registered) | −.019 [−.068, +.031] | +.005 [−.058, +.069] | .20 |
| **v16 POOLED wave 4+5 — PRIMARY** | **−.049 [−.097, −.001]** ✱ | **−.000 [−.041, +.040]** | .21 |

✱ **The pre-registered primary analysis (`goal-eval/PREREG-wave5.md`,
20 items, 60 verdicts): the recall CI excludes zero.** Per the decision
rule fixed before the data existed — "CI entirely below 0 → the recall
deficit is real; report it as measured and stop claiming parity" — the
v16 arm's recall IS below the baseline, by −.049 (about five points of
rubric recall), while its precision sits exactly at parity (−.000). The
result is marginal (upper bound −.001) and should be read as "a real but
small deficit", not a large one. Also fixed in advance and honored: no
third wave is being run.

Every interval spans zero: on 10 items the campaign can state *parity
within measurement precision*, not superiority in either direction. The
pooled point estimates (recall −.07, precision +.015) are the best guess,
and the aggregate recall gap is carried by 3 of 10 items (pr5723 −.20,
pr5756 −.27, pr5978 −.27); the other 7 sit within ±.06 of zero. At the
observed item-level sd (.127), resolving a .07 difference at 95%/80% power
needs ~32 items — hence the wave-5 extension rather than another 10-item
verdict.

| gate | arm | wins | recall | precision | note |
|---|---|---|---|---|---|
| wave-3 attempt 1 | v14 | 2—28 | .207 / .371 | .788 / .843 | INVALID as a design measure: pass finals died at the 16k token ceiling on 7/10 items; planner broken |
| wave-3 attempt 2 | v14+fixes | 5—25 | .231 / .424 | .790 / .824 | machinery healthy; pr5853 swept 3-0 (r .65/.18); loss localized to duties-vs-GT mismatch → forensics |
| wave-4 (clean) | v15 | 10—20 | .261 / .335 | .816 / .787 | raw means only — see the paired table above (Δprecision +.029, CI includes 0). Arm wins the GT-richest items (5864 GT=17, 5958 GT=20, 5608 swept) |
| wave-4 replicate 2 (first attempt) | v15 | INVALID | — | — | DeepSeek 402 Insufficient Balance mid-sweep; stubs judged as empty; quarantined (`INVALID_apierror_goal_v15r2_holdout4_sonnet`); rerun landed after recharge (next row) |
| wave-4 replicate 2 | v15 (DS api, cheap seats on v4-flash) | 11—19—0 | .283 / .338 | .800 / .778 | independent replicate of r1: same sweeps (5608, 5958), same 4 mid-size losers, same sign on both paired deltas — the CONFIGURATION replicates even though neither delta is individually significant |
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

Standing conclusion (post wave-5, pre-registered):

**The recall deficit is real and small; precision is at parity.** The
pre-registered 20-item pooled measurement gives v16 Δrecall −.049
[−.097, −.001] and Δprecision −.000 [−.041, +.040]. So the campaign's
final answer to its own question is: the arm does NOT beat CC+Opus 5 on
both means — it matches on precision and trails on recall by about five
rubric points — while costing roughly a third as much ($0.86–0.97/item
vs $3.09). Head-to-head win share .21 is worse than the rubric gap
implies because the judge weights recall heavily.

The deficit is concentrated, not diffuse: over the 20 pooled items, 6
are positive for the arm, 4 are within ±.02, and a single item (pr5978,
−.37) contributes about a third of the pooled gap.

## v17 CORRECTED probe (2026-08-17) — MoA off, val + train, judge = claude-sonnet-5

Supersedes the v17-moa rows below. Same code (`ae1b6f1`), same items, same
judge, `MOA_WHEN=off` verified through resolved settings and confirmed by
0 `moa_dispatch` events across all 15 traces.

| config | Δrecall [95% CI] | Δprecision [95% CI] | win share |
|---|---|---|---|
| v17ds val (5 items) | −.059 [−.202, +.085] | −.057 [−.256, +.141] | .20 |
| **v17ds train (10 items)** | **+.024 [−.030, +.077]** | **+.016 [−.061, +.093]** | .47 |
| **v17ds pooled (15 items)** | **−.004 [−.056, +.049]** | **−.008 [−.078, +.062]** | .38 |
| v17cb val — Composer 2.5 via cursor backend | −.003 [−.222, +.215] | −.040 [−.322, +.242] | .40 |
| v17cb train — Composer 2.5 via cursor backend | −.052 [−.165, +.061] | −.097 [−.215, +.021] | .20 |

**Backend champion on the same 10 train items: the api/DeepSeek core, not
Composer.** api +.024 recall / +.016 precision against cursor −.052 / −.097.
Val had put Composer ahead (−.003 vs −.059) and that was a small-sample
mirage: n=5 with a ±.22 interval, against train's 4× tighter item variance
(sd .075 api vs .158 cursor). Composer's spread is driven by swings —
pr4970 +.317 against pr4923 −.233 — where the api arm moves within ±.06 on
seven of ten items. The v15 ordering (Composer behind DeepSeek) did NOT
invert; the val row simply could not resolve it.

Both Composer runs are contamination-clean: 0 `imreview` references across
packed traces including IO blobs, with all three skill copies vaulted
off-$HOME for the duration and restored afterwards.

**Correction to the entry below.** On 2026-08-16 this document reported
"the conversion fixes did not close the recall gap" from a pooled −.050.
That measurement was contaminated by an unintended vendor mixture. On train,
the same 10 items go **−.052 (contaminated) → +.024 (clean)**, a swing of
+.076. The claim was an artifact of the contamination and is withdrawn.

The corrected reading: on these two SPENT splits the arm sits at parity —
pooled Δrecall −.004, Δprecision −.008, both intervals straddling zero and
both point estimates within a half-percent of the baseline. Train alone is
the first 10-item split in the campaign with BOTH deltas positive.

Three standing caveats, none of them removable by more analysis:

* val and train have been iterated on for the whole campaign. This is a
  probe and `goal-eval/PROBE-v17-conversion.md` pre-registered it as one; it
  cannot support a claim about fresh data.
* Every CI spans zero. "Parity within measurement precision at n=15" is the
  result, not superiority.
* val (−.059) and train (+.024) disagree in sign. Pooling them to −.004
  averages a real split difference; `pr4893` alone carries val's deficit
  (−.250 on the DeepSeek arm, −.267 on Composer).

`pr4893` failing near-identically under two different models is a PIPELINE
defect rather than a model one, and it is diagnosable from artifacts already
on disk.

Composer 2.5 on the same v17 code reaches Δrecall −.003 on val, inverting
the v15 ordering where Composer trailed DeepSeek (−.081 vs −.075). At n=5
with a ±.22 interval this does not establish Composer above DeepSeek; the
two intervals overlap almost entirely. Composer is 2–4× faster (350–680s vs
1000–2900s per item) and rides the subscription, but every item logged
`tok_out=0` — harness sessions do not surface tokens to span accounting — so
its cost advantage is assumed, not measured.

## v17 conversion-fix probe (2026-08-16) — val + train, judge = claude-sonnet-5

Pre-registered in `goal-eval/PROBE-v17-conversion.md` before generation.
**A probe on already-spent splits, not a measurement**: val and train have
been iterated on all campaign, so these rows say whether the conversion
fixes do what they were built to do — they say nothing about the holdout.
Arm = HEAD `ae1b6f1`, core-only (Fable-5 quota still exhausted, so the v16
adversary/round-2 routing was deliberately NOT applied rather than run into
dead seats again).

⚠ **The rows below are NOT the arm they are named for.** `MOA_WHEN=off` was
set explicitly on every arm v13–v16 and was omitted from this launch, so
`moa_when` fell through to its code default `"full"` and mixture-of-agents
ran on 12 of the 15 items: investigator + behavior went to `mimo-v2.5`,
adversary + verification to `qwen3.6-plus` (which returned 403
AccessDenied.Unpurchased on 24 of its 27 attempts and fell back to DeepSeek).
Measured by the model on each `agent_dispatch` that produced usable output:
**DeepSeek 155 outputs (89.1%), mimo-v2.5 16 (9.2%), qwen3.6-plus 3 (1.7%)**
— so DeepSeek still wrote ~90% of the work, and the two member figures are
UPPER BOUNDS because `BudgetedLLM` silently reruns individual calls on the
tier model when the $1.50 per-run MoA budget is refused, without relabelling
the lens. (An earlier revision of this section claimed 24% for mimo, inferred
from seat names rather than measured; that was wrong by ~2.6x.) These
rows are retained as **v17-moa (unintended vendor mixture)**; the corrected
core-only measurement is `goal_v17ds_*_sonnet`. See the amendment in
`goal-eval/PROBE-v17-conversion.md`.

| config | Δrecall [95% CI] | Δprecision [95% CI] | win share |
|---|---|---|---|
| v17-moa val (4 items — see quarantine) | −.047 [−.108, +.013] | −.073 [−.240, +.094] | .29 |
| v17-moa train (10 items) | −.052 [−.130, +.026] | +.036 [−.030, +.101] | .33 |
| **v17-moa pooled (14 items, exploratory)** | **−.050 [−.104, +.003]** | **+.005 [−.056, +.065]** | .32 |

Reference rows on the identical items: `goal_v13_val` on the same 4 items
was +.038 recall / +.013 precision; `goal_v16f_train_sonnet` (the one split
where the Fable seats actually ran, 15/15 live) was +.002 / +.033.

**The conversion fixes did not close the recall gap.** Pooled −.050 is the
same number the pre-registered holdout produced (−.049), from three
independent splits. Precision is at parity (+.005). No CI here excludes
zero, so nothing is *resolved* — but "unchanged at −.05" is now the reading
supported by wave 4+5, val, and train alike.

Two confounds are inseparable in the train row and must not be papered
over: v17 both gained the conversion fixes and lost the two Fable seats
v16 had. The train comparison therefore measures "core-only + conversion
fixes" against "core + Fable", not the fixes alone.

What the judges say the losses are made of (rationales, blinding resolved):

* The arm's evidence discipline is rated **higher**, repeatedly — "more
  rigorously evidence-cited", "more trustworthy even though it covers
  slightly less ground"; arm precision runs .75–.90. Recall is the whole
  gap, as it has been since v13.
* **Right region, wrong axis**: on pr4804 the arm "only glances off the
  v2-collision issue via a differently-framed 'broad except' critique"; on
  pr5009 its "flagship finding instead targets a different scope axis".
* **The cap-8 comment budget binds on the items we lose.** Four items hit
  the cap AND spilled into an "additional observations" appendix the judge
  called truncated (pr4859: "treatment of the language-removal and +2
  threads is thin, tacked onto a truncated appendix"). Those 4 average
  −.100 Δrecall; the other 10 average −.031. Same conversion-failure class
  already fixed once — real findings routed out of the scored channel,
  this time by the budget rather than by the `[resolved]` block.
* **The dedupe gap costs precision on both splits**, as predicted in the
  probe doc and deliberately left unfixed to avoid config selection:
  "padded with redundant near-duplicate 'validated' entries and less
  scannable". Every full-depth item emits exactly 14 Validated lines; arm
  artifacts run 13–20k chars against the baseline's 5–11k.
* **`suggestion` blocks cut both ways.** They won replicates outright
  ("edges ahead on actionability via literal suggested-diff code blocks"),
  but on pr4810 they lost two of three: a `major` finding shipped with "a
  suggested code fix that inverts the guard", and a regex fix that
  "directly contradicts its own stated reasoning". A wrong claim welded to
  an applyable diff is refutable in a way a hedged one is not. Rendering
  bug found alongside: the blocks emit broken indentation and "wouldn't
  apply cleanly".
* The `skill candidates awaiting curation` section is being judged as
  review content ("an irrelevant 'skill candidates' section") — pipeline
  exhaust leaking into the scored artifact.

New defect found by this probe, and the most expensive one: a DeepSeek
400, "The `content[].thinking` in the thinking mode must be passed back to
the API", hit **8 of the 15 items, 14 times total**. Most items absorbed it
through retries — losing whole passes silently, the same shape as the
empty-final leak. On pr4825 it fired four times and killed the run
outright; that item is quarantined
(`INVALID_apierror_goal_v17_val_sonnet`) and reported MISSING per the
probe's decision rule, never scored as a zero. The runner had already
spent its one retry. Separately, `run_campaign_pipelined.py` judged the
`(no RUN_REPORT.md — rc=3)` stub and printed `complete: 5/5 ok` — a
blocked artifact must never reach the judge.

What each configuration buys, measured on the same gates:
* **v15 (all-DS)** — precision-leaning (Δp +.029/+.022 across two
  independent wave-4 replicates, same sign both times); $0.97/item.
* **v16 (Fable in adversary + second round)** — recall-leaning: it holds
  the best fresh-split recall of the campaign and is the only
  configuration that reproduced the pr4870 GOLD latent-gap catch inside
  the pipeline. It trades v15's precision lean away (Δp −.000).
* **Composer cursor-backend** — subscription-priced breadth proposer,
  measurably worse precision (Δp −.045); not a closer.

Power note for successors: at the observed item-level sd (.103),
resolving a .049 difference at 95%/80% needs ~38 items. This
measurement (20) resolves it only because the effect landed at the
boundary; a smaller effect would need a larger gate, and no 10-item
split can settle anything in this range.

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
