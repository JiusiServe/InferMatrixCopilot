# app/workflow_execution.py — workflow execution boundary

<!-- verified-against: 2026-10-09 -->

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

The asynchronous `execute(...) -> RunOutcome` is the shared bound-workflow
kernel for application runs, knowledge initialization and maintenance. It owns
a newly acquired run lock, Executor and guarded cleanup; an injected lock stays
with its caller. Optional runtime injection is never serialized. Fingerprints
and cached-output validation are forwarded to Executor. `run` retains repository
authorization, knowledge locks, notifications, UI and exit-code conversion.
This entry point grants no additional RunService or SDK publication authority.

Application composition binds `improve.execution` before constructing the
Executor. Adopted settings, workflow fingerprints, active-release handlers and
shadow authorization stay outside the task-independent kernel. The registry and
LLM settings are copied per run; the shared instances are never mutated.
