# app/reservation.py — durable run reservation

<!-- verified-against: 2026-09-26 -->

`RunReservation` owns run ID generation and containment, explicit checkout
authorization, request persistence, initial queued status, and idempotent
retry. Importing it does not load the workflow orchestrator, CLI, or MCP
transport. It holds settings but no worker, planner, executor, or model.

The persisted `request.json` and status schema, run ID format, and 0600
request permission remain compatible. Keyed reservations lock the key and
return `(run_id, created)`: a resolvable run is reused, while a queued run
orphaned before launch may be reclaimed once. A key with a different spec
fails; an unkeyed request creates a new run. The child validates the frozen
request again before executing it.

`contained_run_dir` rejects malformed IDs and paths escaping `run_root`.
Polling may request `must_exist=False` to report a valid but unknown ID;
execution requires an existing directory. `RunService` calls this service
directly, and `Copilot` preserves its old reservation methods as delegates.
