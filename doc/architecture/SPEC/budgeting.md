# budgeting.py — shared budget arithmetic and call lifetime

<!-- verified-against: 2026-10-08 -->

`request_cost_bound`, `reservation_fits`, `settlement_charge` and
`valid_token_counts` contain storage-independent amount rules. Unknown,
invalid or failed billing retains the full reservation; trusted completed
billing may settle at its actual amount. Callers choose fixed accounting.

`reserved_call(acquire, finish)` acquires before dispatch and invokes finish
in a propagating finally. Callers own durable reservation IDs, locking,
cross-period settlement and idempotent receipts. No lock spans model execution.
Initialization, maintenance and self-improvement keep their existing stores
and ceilings. MoA is outside this migration.
