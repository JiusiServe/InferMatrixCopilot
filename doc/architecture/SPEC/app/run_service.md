# app/run_service.py —— 规范

<!-- verified-against: 2026-09-26 -->

`RunService` is the durable application boundary shared by the embedded
Strict SDK and MCP transport. It owns policy-checked reserve/start, one
serialized worker, isolated child launch, startup/orphan reconciliation,
readiness, bounded status/result polling, and repository-scoped knowledge
reads. Construction and polling require no CLI or MCP module import.

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
