# budgeting.py — shared budget arithmetic and call lifetime

<!-- verified-against: 2026-10-09 -->

`request_cost_bound`, `reservation_fits`, `settlement_charge`,
`valid_token_counts` and `usage_cost` contain storage-independent amount rules.
Token-based pricing requires complete, nonnegative integer input/output facts
and valid supplied cache facts; missing or malformed usage is unknown, while
explicit zero usage is a valid zero. Unknown billing retains the full
reservation. Callers choose prices, fixed accounting and failure policy.

`reserved_call(acquire, finish)` acquires before dispatch and invokes finish
in a propagating finally. Callers own durable reservation IDs, locking,
cross-period settlement and idempotent receipts. No lock spans model execution.
Initialization, maintenance and self-improvement keep their existing stores
and ceilings. The mechanism does not replace their journals or domain receipts.

`bind_call_budget(key, acquire, finish)` installs an explicit account in a
`ContextVar`. A nested binding replaces the same key; distinct keys compose.
Passing `acquire=None` temporarily disables that account. Async tasks and
`asyncio.to_thread` propagate the context; ordinary worker pools must bind or
copy it explicitly.

`call_budget(request)` acquires every bound account before yielding shared call
facts (`sent`, `reply`, `usage`, `outcome`). It finishes each acquired account
once, including when a later reservation, dispatch or another finalizer fails.
The caller marks `sent` immediately before dispatch and records known usage
before downstream validation or callbacks. This function chooses neither a
model nor a budget, and does not infer that an unknown bill is free.

API `LLM.create`, native `complete_native`, whole harness steps and read-only
JSON sessions publish dispatch facts through this seam. Weekly improvement
governance binds its durable account. MoA binds its existing per-run account
without a client wrapper; unknown sent calls consume their reservation,
never-sent calls release it, repeated identical settlement is idempotent, and
actual overruns are recorded in full and stop further member calls. Model
targets continue to come from `ResolvedTarget`/`LLM.for_target`.

Harness member usage is reported separately from the API MoA dollar cap.
`deepseek` harness calls are API-keyed; no supported per-call dollar upper bound
is currently established for that route. A harness label or a legacy zero
counter must not be reported as measured zero spend.

Tests: `test_shared_budgeting.py`, `test_moa.py`, `test_tier_split.py`,
`test_improve_p2.py`, `test_improve_p3.py`, `test_llm_providers.py`,
`test_provider_completion.py`, `test_json_session.py` and `test_kb_spend_cap.py`
exercise nested accounts, refusal/finalization, unknown usage, paid failures,
duplicate receipts, actual overrun and native budget termination offline.
