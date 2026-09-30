---
title: EngineCore beam scheduling architecture
created: '2026-09-30'
updated: '2026-09-30'
type: architecture
tags:
- vllm-gr
- scheduler
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/engine/core.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/engine/engine_core_patch.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/engine/wire.py
---

# EngineCore beam scheduling architecture

## Responsibilities and boundary

Python EngineCore admission, beam state and cache ownership, scheduler replies, and the CE side of the BeamProc wire boundary.

## Source and entrypoints

- `vllm_gr/v1/engine/core.py`
- `vllm_gr/v1/engine/engine_core_patch.py`
- `vllm_gr/v1/engine/wire.py`

## Data flow

EngineCore patches register GR request types, initialize beam state before upstream startup, and start CE I/O at most once. Engine outputs go to BeamProc; returned beam plans enter the scheduler before newer API input. Child creation, aborts and terminal cleanup belong to the EngineCore scheduler.

## Direct review map

Read `vllm_gr/v1/engine/core.py` for plan application, child admission, wire encoding and terminal cleanup. Read `engine_core_patch.py` for initialization and shutdown ownership, and `wire.py`/`types.py` for the registered request contract. Follow the live CE-to-BP sender and BP-to-CE reply path together; transport changes also touch the BeamProc owner.

Focused tests: `tests/test_beam_request_unit.py`, `tests/test_beamproc_scheduler_unit.py`.

## Validation

Use the target head's declared dependency versions and test selectors. Bind evidence to that head; a missing native build or incompatible environment is a validation gap.

See the [owner entry](_index.md) and [component map](../_index.md) for neighboring boundaries.
