# providers/completion.py — one native completion

<!-- verified-against: 2026-10-09 -->

`complete_native` shares transport invocation, stop thresholds, pacing,
native events, partial failure snapshots, receipt finalization and optional
Copilot capture between `HarnessLLM`, knowledge model calls and improvement
judges. It performs no
retries. An unsupported spend threshold refuses before dispatch. Cancellation
before dispatch remains distinguishable from an interrupted billed call.

Callers retain explicit model/effort, schema and JSON validation, independent
model-family policy and fallback authorization. HarnessLLM keeps its configured
harness model selection. Knowledge archives preserve original input, output
and native evidence receipts; unknown costs remain unknown to the provider
and are conservatively accounted by the caller's budget policy.

The actual transport dispatch uses `budgeting.call_budget` with a harness
request. `sent` changes immediately before `complete`; trusted returned usage
or partial native usage is retained even if validation fails. Account storage,
prices and settlement remain in explicitly bound domain budgets. There is one
final receipt after validation. `capture=True` uses the ordinary harness trace;
a capture options dictionary may override its provider label and add result
metadata, allowing judges to use the same capture path.

Native judges use this function with provider-level controls: Cursor/Codex/
Claude reject tool events and unknown content blocks; ZCode retains its
existing oversized-prompt attachment read plus scratch-root containment audit.
Whole read-only repository sessions use `json_session`, whose schema,
permissions and repair contract differ from a tool-less completion.

Tests: `test_provider_completion.py`, `test_improve_p2.py`,
`test_kb_spend_cap.py` and `test_shared_budgeting.py`.
