# 20-case PR-review evaluation — full rerun with complete traces

3 generation replicates x 20 `pr_review` items (10 train / 5 val / 5 test) x 3 judge replicates = 180 blind pairwise verdicts against the recorded `claudecode_opus48` baseline (never rerun). Judge: `claude-sonnet-5`, tool-less, randomized X/Y order — a third model, distinct from both arms. Metric definitions reused unchanged from `eval/dataset/judge_val.py`.

**Configuration**: `MOA_WHEN=off`, `PR_CONTEXT_MODE=no_discussion`, `REVIEW_DEPTH=auto`, `ALLOW_POST=0`/`ALLOW_PUSH=0`, full trace capture (`AGENT_TRACE_IO_FULL=1`). MoA off matches the A1 arm in `doc/EVAL-goal-report.md`, so the val slice stays comparable.

## Leakage controls (asserted per item, not assumed)

1. `PR_CONTEXT_MODE=no_discussion` — the human review discussion IS the ground truth, so it is excluded from the prompt.
2. PR-time checkout — every PR item's report asserts `PR-TIME TREE` with the head SHA from `expected_pr_heads.json`, frozen independently before generation. `pr.fetch_diff`'s live-checkout fallback returns success, so rc=0 alone would not catch a contaminated tree.
3. Head SHAs were re-resolved for all 20 PRs before the campaign: **zero drift** on the 5 val PRs carried over from the val campaign.
4. `pr_review` is a read-only kind, so no skill/profile/debug-memory writeback; skill-candidate files were digest-snapshotted before and after.

## Quality — replicate means ± sd across replicates

Per split, never pooled: train is the adaptation stream, val the promotion gate, test the frozen holdout.

| slice | n | recall | precision | actionability |
|---|---|---|---|---|
| all | 20 | 0.430 ± 0.018 | 0.777 ± 0.026 | 0.767 ± 0.019 |
| train | 10 | 0.431 ± 0.015 | 0.787 ± 0.016 | 0.791 ± 0.030 |
| val | 5 | 0.468 ± 0.044 | 0.745 ± 0.049 | 0.693 ± 0.043 |
| test | 5 | 0.392 ± 0.053 | 0.790 ± 0.038 | 0.792 ± 0.037 |

### vs the recorded A1 val numbers (`doc/EVAL-goal-report.md`)

| dim | this campaign (val) | A1 (val) | Δ |
|---|---|---|---|
| recall | 0.468 ± 0.044 | 0.520 ± 0.021 | -0.052 |
| precision | 0.745 ± 0.049 | 0.800 ± 0.034 | -0.055 |
| actionability | 0.693 ± 0.043 | 0.731 ± 0.062 | -0.038 |

Both sides are 5-item slices with replicate sds of 0.02-0.07, so differences under ~0.1 sit inside judge+generation noise (`eval/ANALYSIS.md`: ±0.1 per single run).

### gap_hit — the three GOLD latent-gap items

History proves human review missed something in each. **One item per split**, so each cell is a 1-item measurement, not a rate.

| item | split | hit rate over replicates |
|---|---|---|
| pr4870 | train | 0.000 ± 0.000 |
| pr4810 | val | 0.889 ± 0.192 |
| pr4834 | test | 1.000 ± 0.000 |

## Cost and latency

| arm | items | rc=0 | USD (attempt-incl.) | wall s mean/median/p95 |
|---|---|---|---|---|
| copilot_v4_pr20_r1 | 20 | 20 | $4.109 | 434 / 417 / 814 |
| copilot_v4_pr20_r2 | 20 | 20 | $3.476 | 371 / 358 / 664 |
| copilot_v4_pr20_r3 | 20 | 20 | $3.675 | 400 / 408 / 647 |
| baseline:claudecode_opus48 (recorded) | 20 | - | $29.152 | 233 / 184 / 415 |

Generation costs **$3.75 per 20-item replicate** vs the baseline's **$29.15** for the same 20 PRs — **7.8x cheaper**. Judging costs more than generating: ~$11 per replicate at $0.185/verdict.

Wall-clock is the only latency metric here; per-role span sums are service time and are never summed into it (concurrent lenses would double-count).

## Trace corpus

- **61 run dirs, 0 incomplete** — every run carries `trace.jsonl` (spans + `run_meta` header), `run_trace.jsonl` (RunTrace events) and `events.jsonl` (full request/response payloads).
- 1,885 LLM calls · 22,509,549 input / 2,750,162 output tokens.
- **400 MB** of payloads + 0.9 MB of spans.
- Gate (`goal-eval/verify_traces.py`): per run, `llm.request == llm.response == llm` span count, and token totals agree across events.jsonl / trace.jsonl / metrics.json.
- Retried items (one extra run dir each, cost counted): {'r1': {'pr4816': 2}}.
- `eval/dataset/arms/*/runs/` is gitignored: the corpus is local-only.

## Caveats

- **Retrospective synthesis under thread visibility**, not blind pre-resolution maintenance — same framing as the val campaign.
- Evidence is asymmetric and not claimed otherwise: the baseline ran against post-merge `main` with the discussion reachable; these arms run PR-time trees with the discussion excluded.
- Same-family judge for neither arm (Sonnet-5 vs DeepSeek arm / Opus baseline), but the baseline is cross-family to the judge's own lineage.
- Test-split items were scored and reported as aggregates only; item content and judge rationales were not read, so the holdout stays usable for future error analysis.
- Cost/latency are NOT comparable to `EVAL-goal-report.md`'s: different item mix (20 PRs vs 5 PRs + 5 issues) and payload-write overhead.

