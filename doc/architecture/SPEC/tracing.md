# tracing.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~652 · portable span-tree recorder · refactor-status: oversized`

## Responsibility
Record a run as a tree of timing spans, with zero external dependencies.

## Functionality
OpenTelemetry-*shaped* spans (`trace_id`, `span_id`, `parent`, `start`, `end`,
`attributes`) appended to a JSONL file, one line per span, written at close.

## Public contract
`span(...)` (context manager), the module-level tracer accessors, and the
JSONL record shape.

## Invariants (**E1**, **E3**)
- **Write at span close, append-only.** A killed run keeps every span that had
  finished — the reason this is not an in-memory tree flushed at exit.
- **Sync and asyncio both safe.** `span()` is a plain context manager usable
  around `await`; parent/child nesting is carried through `contextvars` and
  copied per task, so **parallel agents get independent, correct trees** rather
  than interleaving into one.
- **Zero external dependencies** — deliberately not the OTel SDK. The shape is
  compatible; the dependency is not taken.
- `create()` is wrapped in `span("llm")` to record TTFT, tokens and concurrency.
- Distinct from `run_trace.py`: this is **timing**, that is **facts**. Neither
  enters a prompt by default.

## Scope — not here
No fact recording (`run_trace.py`); no metrics computation (`metrics.py`); no
export protocol.

## Dependencies (allowed)
stdlib only (`contextvars`, `json`, `time`, `threading`).

## Tests
`test_tracing.py`, `test_trace_pack.py`.

## Refactor notes
At ~652 LOC it is the largest leaf module. The span model, the JSONL writer and
the process-global tracer plumbing are three separable concerns if it grows.
