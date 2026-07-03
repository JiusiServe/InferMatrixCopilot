---
name: ci-debug-root-cause
description: CI debugging — prefer the deepest root-cause line over surface symptoms (APIConnectionError/EngineDeadError are usually consequences, not causes)
trigger: pr_debug / grouped CI failure analysis
modules: [pr_debug]
status: active
created_at: 2026-07-03
run_count: 0
---

## Diagnose
A CI log shows several error lines: connection/engine-death errors near the
end and an ImportError/AssertionError earlier.

## Fix
Chase the EARLIEST deep failure (traceback root), not the last symptom; fix
that and re-derive whether the symptoms disappear. Commit one fix per root
cause with the signature in the message.

## Verification
The failing test/import reproduces before the fix and passes after.

## Anti-patterns
- "Fixing" APIConnectionError by adding retries when an import upstream broke
  the engine.
