# RELABELLED — v17-moa (unintended vendor mixture), not v17 core-only

This directory is named `v17` but does NOT hold the arm that name implies.

`MOA_WHEN=off` was set explicitly on every arm from v13 through v16. The
launch that produced this data omitted it, so `moa_when` fell through to its
code default of `"full"` (config.py:345) and mixture-of-agents ran on every
full-depth PR review — 12 of the 15 items here.

Round-1 lenses were dispatched to three vendors instead of one:

| lens | assigned to | outcome |
|---|---|---|
| investigator | `mimo-v2.5` | 7 ok, 5 failed |
| behavior | `mimo-v2.5` | 7 ok, 5 failed |
| adversary | `qwen3.6-plus` | **0 ok, 12 failed** (403 AccessDenied.Unpurchased) |
| verification | `qwen3.6-plus` | **0 ok, 12 failed** (same) |

**24% of productive round-1 lenses were written by `mimo-v2.5`**, and 104
minutes of the run went to member attempts that were discarded and redone.

Kept rather than deleted: the data is real and the MoA behaviour it captures
is worth having. The directory names are also left alone on purpose —
every verdict's `_roles` block records the arm directory name, so renaming
would leave that provenance pointing at a directory holding different data.

The corrected measurement, same code (`ae1b6f1`) and same items with
`MOA_WHEN=off` verified through resolved settings, lives in
`copilot_v17ds_*` / `goal_v17ds_*_sonnet`. See
`goal-eval/PROBE-v17-conversion.md` for the pre-registered amendment.
