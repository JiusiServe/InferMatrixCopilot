---
title: Rust BeamProc runtime entry
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
- distributed
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/beam-proc/src/worker/io_worker.rs
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/beam-proc/src/worker/beam_worker.rs
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:rust/beam-proc/src/main.rs
---

# Rust BeamProc runtime

## When to use this entry

Rust BeamProc process, worker queues, beam decisions, and the BP side of CE and API-server communication.

Source scopes: `rust/beam-proc/`, `rust/ce-transport/`, `rust/examples/`.

## Outside this owner

Other source owners are listed in the [component map](../_index.md); repository identity and version constraints belong to the [repository entry](../../_index.md).

## Contents

| Task | Entry | Purpose |
|---|---|---|
| Trace source, data flow and validation | [Architecture](architecture.md) | Pinned source map and compact Direct review map |

Focused tests: `tests/test_beamproc_scheduler_unit.py`.
