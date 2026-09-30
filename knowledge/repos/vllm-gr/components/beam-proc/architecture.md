---
title: Rust BeamProc runtime architecture
created: '2026-09-30'
updated: '2026-09-30'
type: architecture
tags:
- vllm-gr
- distributed
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/beam-proc/src/worker/io_worker.rs
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/beam-proc/src/worker/beam_worker.rs
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/beam-proc/src/main.rs
---

# Rust BeamProc runtime architecture

## Responsibilities and boundary

Rust BeamProc process, worker queues, beam decisions, and the BP side of CE and API-server communication.

## Source and entrypoints

- `rust/beam-proc/src/worker/io_worker.rs`
- `rust/beam-proc/src/worker/beam_worker.rs`
- `rust/beam-proc/src/main.rs`

## Data flow

The process owns worker and I/O managers. I/O decodes CE messages, dispatches them to beam workers and publishes plans or final results. CE replies and API-server final-result delivery are distinct channels. Changes to native CE transport must also inspect the live Python caller and the CE wire contract.

## Direct review map

Read `rust/beam-proc/src/main.rs` for process startup and shutdown; `worker/io_worker.rs` for framing, worker routing and result delivery; `worker/beam_worker.rs` for beam state, selection and terminal output. Inspect the pinned `rust/Cargo.toml` and lockfile before using native dependency APIs. Review the enabled transport path and partial-startup cleanup separately from the default path.

Focused tests: `tests/test_beamproc_scheduler_unit.py`.

## Validation

Use the target head's declared dependency versions and test selectors. Bind evidence to that head; a missing native build or incompatible environment is a validation gap.

See the [owner entry](_index.md) and [component map](../_index.md) for neighboring boundaries.
