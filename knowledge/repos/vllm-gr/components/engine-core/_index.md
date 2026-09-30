---
title: EngineCore beam scheduling entry
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
- scheduler
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/engine/core.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/engine/engine_core_patch.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/engine/wire.py
---

# EngineCore beam scheduling

## When to use this entry

Python EngineCore admission, beam state and cache ownership, scheduler replies, and the CE side of the BeamProc wire boundary.

Source scopes: `vllm_gr/v1/engine/`, `vllm_gr/v1/core/`.

## Outside this owner

Other source owners are listed in the [component map](../_index.md); repository identity and version constraints belong to the [repository entry](../../_index.md).

## Contents

| Task | Entry | Purpose |
|---|---|---|
| Trace source, data flow and validation | [Architecture](architecture.md) | Pinned source map and compact Direct review map |

Focused tests: `tests/test_beam_request_unit.py`, `tests/test_beamproc_scheduler_unit.py`.
