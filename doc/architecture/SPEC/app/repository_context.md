# app/repository_context.py — repository context boundary

<!-- verified-against: 2026-09-26 -->

`RepositoryContextResolver.for_spec` produces the checkout, planner
capabilities, protected branches, and high-risk modules for one `TaskSpec`.
The frozen `spec.repo_path` wins over ambient `REPO_PATHS` and the adapter
path. The resulting immutable `RepositoryContext` is passed from planning to
execution and re-resolved before execution starts; a change blocks the run.

Only genuine adapter absence permits compatibility behavior. With no adapter,
capabilities are unknown (`None`) when a checkout exists and empty otherwise.
A known adapter with a missing, unreadable, malformed, or mismatched manifest
raises `AdapterError`. Malformed checkout or policy fields also raise
`AdapterError`; no execution path silently substitutes the default policy.

The resolver owns no planner, executor, persistence, or transport behavior.
`Copilot` retains its older path and adapter helpers as delegates. Tests in
`test/test_repository_context.py` cover checkout precedence, policy
propagation, malformed manifests, and context drift.
