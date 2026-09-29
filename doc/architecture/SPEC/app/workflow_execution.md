# app/workflow_execution.py — workflow execution boundary

<!-- verified-against: 2026-09-26 -->

`WorkflowExecution` runs an already selected playbook with the caller's
current LLM dependency. It rechecks the repository context before starting,
owns the run and shared knowledge locks,
initializes tracing and notification, seeds executor state with checkout and
adapter policy, and drives `Executor` through `run_guarded`. It returns an
immutable `ExecutionResult` containing the exit code and blocked reason.

A losing run lock leaves active run artifacts untouched. A failed knowledge
lock releases an acquired run lock. A caller-provided lock stays owned by the
caller. Finalizers and locks run on every executor outcome, including failure.
The application owns planning, confirmation, durable reservation, and the
reserved worker's terminal `run_status.json` write. CLI and MCP transports do
not belong in this module.

`Copilot._execute` remains the compatibility entry point and records
`last_run_dir`/`last_blocked_reason` from the returned result. Existing run
state keys, traces, exit codes, and checkpoint behavior stay stable.
