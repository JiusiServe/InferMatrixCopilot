# review/planner.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~307 · review depth selection · refactor-status: ok`

## Responsibility
Choose the review depth (`light` / `standard` / `full`) for one PR.

## Functionality
The 4-lens ensemble is the recall floor for consequential changes but costs
~4× tokens and latency (measured: a 2-file/+60-line PR consumed ~1.1M input
tokens over 4m48s, 97% of it in review). Deterministic rules settle the clear
cases; only the gray zone spends one small LLM call.

## Public contract
`plan_review_depth(...) -> depth`, plus the deterministic classifiers.

## Invariants (**C2**, **B2**)
- **`light` can NEVER come from model output.** The gray-zone call may return
  only `standard` or `full`. This is the anti-prompt-injection property that
  matters here: content inside the PR cannot talk the planner into reviewing
  itself less carefully.
- Depth invariants are enforced in place: `light` ⇒ no lenses;
  `standard` ⇒ 2–3 lenses; `full` ⇒ all.
- Deterministic rules run FIRST and decide the clear cases without a model call
  (tiny + low-risk → light; large or high-risk path → full).
- A playbook's `review_depth` param may pin the depth explicitly, overriding
  the planner.
- **The gray-zone call needs reasoning headroom.** It silently failed on every
  gray item for two campaigns because thinking consumed a 400-token ceiling
  before any JSON could appear — a cap here is a correctness setting, not a
  cost knob.

## Scope — not here
No lens execution (`agent_runtime/ensemble.py`); no rendering; no repo-specific
risk lists (those come from the profile / adapter module map).

## Dependencies (allowed)
`..config`, `..llm`, stdlib. No step imports.

## Tests
`test_review_planner.py`.

## Refactor notes
Note the package split: this file is review DEPTH, while
`engine/steps/review/` holds the review steps themselves. Same word, two
packages — do not merge them.
