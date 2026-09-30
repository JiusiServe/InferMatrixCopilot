---
title: OpenAI beam serving architecture
created: '2026-09-30'
updated: '2026-09-30'
type: architecture
tags:
- vllm-gr
- serving
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/serving_engine.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/serving_models.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/beam_search_patch.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/entrypoints/openai/beam_proc_manager.py
---

# OpenAI beam serving architecture

## Responsibilities and boundary

OpenAI-facing beam request and response handling, BeamProc startup, API-server final delivery, metrics and cancellation.

## Source and entrypoints

- `vllm_gr/entrypoints/openai/serving_engine.py`
- `vllm_gr/entrypoints/openai/serving_models.py`
- `vllm_gr/entrypoints/openai/beam_search_patch.py`
- `vllm_gr/entrypoints/openai/beam_proc_manager.py`

## Data flow

Serving creates beam requests and communicates with EngineCore. The BeamProc manager owns executable startup and readiness; serving consumes engine/BP results and turns them into API responses. Request cancellation, iterator failure and terminal result cleanup must retain their user-visible behavior.

## Direct review map

Read `serving_engine.py` for request ownership, beam result consumption, final cleanup and metrics; `beam_search_patch.py` for upstream API signatures and streaming delegation; `serving_models.py` and `beam_proc_manager.py` for native process startup. Check stream options, error and cancellation paths against the supported vLLM version rather than an unrelated installed release.

Focused tests: `tests/test_serving_beam_lifecycle.py`, `tests/test_serving_models_beamproc_startup.py`, `tests/test_prometheus_beam_search_metrics.py`.

## Validation

Use the target head's declared dependency versions and test selectors. Bind evidence to that head; a missing native build or incompatible environment is a validation gap.

See the [owner entry](_index.md) and [component map](../_index.md) for neighboring boundaries.
