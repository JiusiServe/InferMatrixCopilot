# providers/completion.py — one native completion

<!-- verified-against: 2026-10-08 -->

`complete_native` shares transport invocation, stop thresholds, pacing,
native events, partial failure snapshots, receipt finalization and optional
Copilot capture between `HarnessLLM` and knowledge model calls. It performs no
retries. An unsupported spend threshold refuses before dispatch. Cancellation
before dispatch remains distinguishable from an interrupted billed call.

Callers retain explicit model/effort, schema and JSON validation, independent
model-family policy and fallback authorization. HarnessLLM keeps its configured
harness model selection. Knowledge archives preserve original input, output
and native evidence receipts; unknown costs remain unknown to the provider
and are conservatively accounted by the caller's budget policy.
