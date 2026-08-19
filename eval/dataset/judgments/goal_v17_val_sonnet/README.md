# RELABELLED — v17-moa (unintended vendor mixture), not v17 core-only

This directory is named `v17` but does NOT hold the arm that name implies.

`MOA_WHEN=off` was set explicitly on every arm from v13 through v16. The
launch that produced this data omitted it, so `moa_when` fell through to its
code default of `"full"` (config.py:345) and mixture-of-agents ran on every
full-depth PR review — 12 of the 15 items here. Round-1 lenses were
dispatched to three vendors instead of one: investigator + behavior to
`mimo-v2.5`, adversary + verification to `qwen3.6-plus`, reducer on tier.

## How much of the work was actually not DeepSeek

Attributed by the model recorded on each `agent_dispatch`, counting only
dispatches that produced usable output:

| model | attempts | productive outputs | output tokens |
|---|---|---|---|
| `deepseek-v4-pro` | rest + all fallbacks | **155 (89.1%)** | 2,298,061 (89.3%) |
| `mimo-v2.5` | 30 | 16 (9.2%) | 183,047 (7.1%) |
| `qwen3.6-plus` | 27 | 3 (1.7%) | 94,497 (3.7%) |

**DeepSeek still wrote ~90% of the review work**, and the two member figures
are UPPER BOUNDS. `BudgetedLLM.create` (moa.py:215-227) reserves an estimated
cost per LLM call and, when the reservation is refused, silently reruns that
call on the tier model while the lens keeps its original dispatch label. With
`moa_max_usd = $1.50` against per-item spend of $0.85–1.66, that budget trips
partway through most items, so an unknown share of the "member" rows above
was in fact DeepSeek. The trace cannot resolve it: only the dispatch carries a
model, and the per-call fallback emits none.

(An earlier version of this file claimed 24%, inferred from seat names. That
inference ignored both `/retry` seats and the per-call budget fallback, and
was wrong by roughly 2.6x.)

`qwen3.6-plus` returned `403 AccessDenied.Unpurchased` on 24 of its 27
attempts — that subscription is not active. 104 minutes of this run went to
member attempts that were then discarded and redone.

Kept rather than deleted: the data is real and the MoA behaviour it captures
is worth having. The directory names are also left alone on purpose — every
verdict's `_roles` block records the arm directory name, so renaming would
leave that provenance pointing at a directory holding different data.

The corrected measurement, same code (`ae1b6f1`) and same items with
`MOA_WHEN=off` verified through resolved settings, lives in
`copilot_v17ds_*` / `goal_v17ds_*_sonnet`. See
`goal-eval/PROBE-v17-conversion.md` for the pre-registered amendment.
