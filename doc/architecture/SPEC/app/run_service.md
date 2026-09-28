# app/run_service.py —— 规范

<!-- verified-against: 2026-09-28 -->

`RunService` is the durable application boundary shared by the embedded
Strict SDK and MCP transport. It owns policy-checked reserve/start, one
serialized worker, isolated child launch, startup/orphan reconciliation,
readiness, bounded status/result polling, and repository-scoped knowledge
reads. Construction and polling require no CLI or MCP module import.

Reservation and run ID containment go directly through `RunReservation`,
not the workflow `Copilot` facade. `Copilot` remains for playbook readiness
and workflow execution; it does not mediate the service's reserve or poll
paths.

Reservations return `(run_id, created)` and enqueue only newly created runs.
The worker launches an isolated subprocess with posting and pushing disabled,
then reconciles the persisted status. A run can survive host restart; closing
a service only removes its liveness token and must not cancel a durable child.
The child rechecks repository/path/read-only policy against the same explicit
roots as the parent. Polling an unknown valid run ID reports `unknown`;
malformed or escaping IDs fail validation. Structured results and capped
report pages remain available after terminal status.

`mcp_server.CopilotMCP` remains a compatibility alias. The MCP server owns
tool registration and protocol error projection, while the SDK owns typed
request/result projection. Neither transport owns the run queue.

## 2026-09-28 Knowledge snapshot pinning
When `reserve_strict_review` / `reserve_quality_review` CREATE a reservation,
they record the current `KnowledgeView` in `<run>/knowledge.json`: snapshot id,
manifest tree hash, and resolved real paths (never the `active` symlink). An
idempotent retry does not rewrite it. `_launch` sets the child's
`KNOWLEDGE_DIR` and `KNOWLEDGE_ROOT` from that record, so a run that executes
later (queued, or relaunched after a restart) still reviews with the knowledge
active at reservation. If the pinned snapshot was pruned, the run is marked
`failed`; it never silently switches knowledge. Without a snapshot root the
run is pinned to this server's effective `knowledge_dir` (reported as `packaged`,
or `unverified` for a custom directory), with `KNOWLEDGE_ROOT` removed from the
child's environment. Runs reserved before pinning
existed have no record and use the process default.
