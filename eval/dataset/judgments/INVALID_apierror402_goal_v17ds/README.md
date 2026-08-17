# QUARANTINED — DeepSeek 402 Insufficient Balance, 2026-08-17

The corrected (MoA-off) v17 run stopped mid-sweep when the DeepSeek account
ran out of balance at 10:49. Three items died as
`(no RUN_REPORT.md — rc=3)` stubs: pr4816 (val), pr4926 and pr4977 (train).

Two verdicts (`pr4977.r1`, `pr4977.r2`) were produced against the pr4977 stub
before the judges were stopped. They score an empty artifact against a real
baseline review and are quarantined here. The stub artifacts themselves are
moved to `arms/INVALID_apierror402_v17ds_stubs/` so a resumed sweep
regenerates those items instead of skipping them (the runner skips any
existing non-empty `.md`).

This is the second 402 of the campaign; the first invalidated wave-4
replicate 2 on 2026-08-15 (`INVALID_apierror_goal_v15r2_holdout4_sonnet`).

Surviving clean items in this run: val pr4810, pr4825, pr4837, pr4893;
train pr4817, pr4923, pr5009. All seven verified MoA-free by the
contamination gate. They are NOT a measurement — 7 of 15 items, with the
missing 8 non-random (they are whichever items the sweep had not reached),
so no delta may be computed from them until the run is completed.
