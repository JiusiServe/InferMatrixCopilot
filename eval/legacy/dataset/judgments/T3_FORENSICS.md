# T3 forensics — where the residual gap actually lives (2026-07-12)

Produced by a full trace sweep over arms/copilot_v2_t3_r{1,2,3} (run traces,
ensemble reducer archives, llm spans), all 89 blind judgments' rationales,
ground truth, and baseline outputs. Headline: the residual gap vs the Opus
baseline is dominated by MECHANICAL delivery/policy defects (cited in ~90% of
rationales), not model depth. Ranked punch list -> T4.

## Quantitative anchors
- Lens death CURED: 64/64 lens outputs parsed (7/60 lost at T0).
- Tree mixing CURED: 0/89 candidates cite the wrong checkout.
- Reducer clean: 15/15 replies parsed, drops were correct false-positive
  removals; reducer runs at only ~3.6k in / 4.8k out tokens.
- Candidate yield is the recall bottleneck: 0-4 per lens (never 5+);
  pr4816: 1 candidate TOTAL from 4 lenses x ~20 tool calls, x3 replicates.
- issue4842 blocked 2/3 replicates on iteration exhaustion; r1's final
  665-token end_turn answer was DISCARDED for a missing contract field.
- Hybrid economics: stronger-model verification pass ~$0.10-0.25/item.

## Ranked punch list (fix surface in brackets)
1. RUN_REPORT dedup + diagnostics quarantine [PRODUCT report.py] — review_text
   rendered 3x in 15/15 PR reports; truncated answer_draft copy ends every
   issue doc mid-sentence; blockers/confidence leak into the judged artifact.
2. Verdict calibration [PRODUCT review/utils.py] — minor counted as blocking:
   14/15 REQUEST CHANGES on human-approved PRs (pr4816 precision 0.55 vs 0.98).
3. Issue budget salvage + headroom [PRODUCT+CONFIG] — salvage final end_turn
   text into the draft; budget-2 nudge; higher cap; eval retry on rc=3.
4. "What I validated" section [PRODUCT render + prompts] — GT concerns on
   approved PRs are mostly validation reasoning (pr4837 recall 0.31 vs 0.82);
   the copilot already computes [upstream-verify] notes and discards them.
5. Reducer policy [PRODUCT ensemble] — self-declared-uncertain candidates kept
   at major (pr4810); give the reducer the diff (raise merge evidence cap).
6. Lens candidate-yield floor + zero-yield single-lens re-ask [PROMPTS+PRODUCT].
7. Epistemics lint [PRODUCT] — "merged/verified" claims without a gh call or
   tests_run (issue4891 correctness 0.45 vs 0.83).
8. Issue disposition + thread-engagement slots [KNOWLEDGE+PRODUCT] —
   completeness losses are missing closing moves, not missing diagnosis.
9. (T5, MODEL) scoped stronger-model uncertainty-resolution pass for kept
   blocker/major items only.

Full agent report preserved in the session transcript; representative traces:
arms/copilot_v2_t3_r1/runs/pr4810/run-*/ensemble_agent.review_diff.json
(uncertain-kept-as-major), arms/copilot_v2_t3_r{1,3}/runs/issue4842/run-*/
run_trace.jsonl (exhaustion + discarded answer), arms/copilot_v2_t3_r1/
pr4893.md (triplication).
