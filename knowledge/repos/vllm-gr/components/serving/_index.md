---
title: OpenAI beam serving entry
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
- serving
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/serving_engine.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/serving_models.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/beam_search_patch.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/beam_proc_manager.py
---

# OpenAI beam serving

## When to use this entry

OpenAI-facing beam request and response handling, BeamProc startup, API-server final delivery, metrics and cancellation.

Source scopes: `vllm_gr/entrypoints/`.

## Outside this owner

Other source owners are listed in the [component map](../_index.md); repository identity and version constraints belong to the [repository entry](../../_index.md).

## Contents

| Task | Entry | Purpose |
|---|---|---|
| Trace source, data flow and validation | [Architecture](architecture.md) | Pinned source map and compact Direct review map |

Focused tests: `tests/test_serving_beam_lifecycle.py`, `tests/test_serving_models_beamproc_startup.py`, `tests/test_prometheus_beam_search_metrics.py`.
