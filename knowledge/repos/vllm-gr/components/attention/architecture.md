---
title: Beam attention runtime architecture
created: '2026-09-30'
updated: '2026-09-30'
type: architecture
tags:
- vllm-gr
- attention-runtime
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/attention/backends/beam_attn_gpu.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/attention/backends/beam_attn_metadata.py
---

# Beam attention runtime architecture

## Responsibilities and boundary

GPU/NPU beam attention execution and the metadata that describes ordinary, prefix and suffix query/cache layouts.

## Source and entrypoints

- `vllm_gr/v1/attention/backends/beam_attn_gpu.py`
- `vllm_gr/v1/attention/backends/beam_attn_metadata.py`

## Data flow

Metadata partitions standard and beam queries and supplies cache geometry. GPU attention evaluates standard queries and prefix/suffix beam attention, merges their states and writes into the caller-owned output. Platform and FlashAttention-version branches can have different shape and ownership contracts.

## Direct review map

Read `vllm_gr/v1/attention/backends/beam_attn_metadata.py` for query indices and cache geometry, then `beam_attn_gpu.py` for prefix/suffix kernels, LSE layouts and output writes. Check ordinary and grouped queries, supported FlashAttention versions, causal suffix lengths and caller output ownership. Inspect platform-specific peers before extending a GPU conclusion to NPU.

Focused tests: `tests/test_beam_attention_metadata.py`.

## Validation

Use the target head's declared dependency versions and test selectors. Bind evidence to that head; a missing native build or incompatible environment is a validation gap.

See the [owner entry](_index.md) and [component map](../_index.md) for neighboring boundaries.
