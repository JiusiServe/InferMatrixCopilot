---
title: vLLM-GR component map
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
- components
sources: []
---

# vLLM-GR components

## When to use this entry

Select the stable source owner for a GR runtime or packaging change.

## Outside this map

Repository identity and supported versions belong to the [repository entry](../_index.md); generic procedures belong to [general review](../../../general/review/_index.md).

## Contents

| Task | Entry | Source scope |
|---|---|---|
| EngineCore beam scheduling | [engine-core](engine-core/_index.md) | `vllm_gr/v1/engine/` |
| Rust BeamProc runtime | [beam-proc](beam-proc/_index.md) | `rust/beam-proc/` |
| OpenAI beam serving | [serving](serving/_index.md) | `vllm_gr/entrypoints/` |
| Beam attention runtime | [attention](attention/_index.md) | `vllm_gr/v1/attention/` |
| Native packaging and validation | [packaging](packaging/_index.md) | `setup.py` |
