---
title: Beam attention runtime entry
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
- attention-runtime
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/attention/backends/beam_attn_gpu.py
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:vllm_gr/v1/attention/backends/beam_attn_metadata.py
---

# Beam attention runtime

## When to use this entry

GPU/NPU beam attention execution and the metadata that describes ordinary, prefix and suffix query/cache layouts.

Source scopes: `vllm_gr/v1/attention/`.

## Outside this owner

Other source owners are listed in the [component map](../_index.md); repository identity and version constraints belong to the [repository entry](../../_index.md).

## Contents

| Task | Entry | Purpose |
|---|---|---|
| Trace source, data flow and validation | [Architecture](architecture.md) | Pinned source map and compact Direct review map |

Focused tests: `tests/test_beam_attention_metadata.py`.
