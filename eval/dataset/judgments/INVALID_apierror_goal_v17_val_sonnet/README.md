# QUARANTINED — not a measurement

`pr4825`, v17 val probe, 2026-08-16.

The arm's generation was **blocked twice** (both run dirs under
`arms/copilot_v17_val/runs/pr4825/`) by a DeepSeek 400:

    The `content[].thinking` in the thinking mode must be passed back to the API.

`run_copilot_arm.py` retried once, hit the same error, and wrote an
`(no RUN_REPORT.md — rc=3)` stub as `pr4825.md`. `run_campaign_pipelined.py`
saw a non-empty `.md`, judged it, and printed `complete: 5/5 ok`. The judge
did the right thing with what it was handed — "Y's run crashed before
producing any review content", arm scored 0.0/0.0/0.0 on all three
replicates — but those three verdicts measure an API fault, not a review
capability, and averaging them into the arm would have moved pooled val
Δrecall by roughly a tenth of a point on its own.

`PROBE-v17-conversion.md` fixed the handling in advance: regenerate once,
then report as MISSING — never silently drop it from the denominator, and
never score a crash as a zero. The retry was already spent by the runner, so
the item is reported missing and val is analysed at n=4 with this stated.

Two defects this exposed, both recorded for the next iteration:
1. The thinking round-trip 400 is not rare — 6 of the 7 items generated at
   the time it was found hit it at least once; the others absorbed it via
   retries, losing whole passes silently.
2. The pipeline must refuse to judge a blocked artifact instead of reporting
   `5/5 ok`.
