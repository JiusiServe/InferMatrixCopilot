---
title: vLLM-GR repository entry
created: '2026-09-30'
updated: '2026-09-30'
type: index
tags:
- vllm-gr
sources:
- JiusiServe/vllm-gr@a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee:README.md
---

# vLLM-GR repository entry

## When to use this entry

Repository: `JiusiServe/vllm-gr`; aliases `vllm-gr` and `vllm_gr`.
Default branch: `main`. Source map baseline: `a05103dc16c7b8dfd2213b73c5ee2d4f28cb6fee`.
The baseline supports vLLM `0.22.1` and vLLM-Ascend `0.22.1rc1`; inspect the target revision's own constraints before validation.
This repository implements generative recommendation inference, including OneRec beam/catalog paths, Pangu passthrough and GPU/NPU execution.

## Outside this entry

Repository-independent review procedures belong to [general review](../../general/review/_index.md).
vLLM-Omni model and diffusion assumptions belong to that repository and do not apply here.
This map describes the pinned main branch; new transports and APIs must be verified from the reviewed head.

## Contents

| Task | Entry | Boundary |
|---|---|---|
| Select a source owner and focused tests | [Components](components/_index.md) | EngineCore, BeamProc, serving, attention and packaging |

Direct owner signals and source scopes are declared in `_routes.yaml`; adapter aliases and briefing live in `adapters/vllm_gr/manifest.yaml`.
