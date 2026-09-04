---
title: "DreamID-Omni（已移除的 first-party 支持）"
created: 2026-07-21
updated: 2026-09-04
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #6357"]
---

# DreamID-Omni — historical tombstone

PR #6357 removed first-party DreamID-Omni support at `main @ aeb348d8`: its
`DreamIDOmniPipeline` registry entry and pre/post-processing registration, the
`vllm_omni/diffusion/models/dreamid_omni/` implementation, model tests, setup
script, documentation, and the shared `x_to_video_audio` example are gone.

At the immediately preceding snapshot (`40dcfdbb`), the removed implementation
was a custom Wan2.2-based audio/video identity pipeline with an external
`dreamid_omni` dependency. This is historical context only: do not treat it as a
current registry target, supported checkpoint, runnable example, or review owner.
For the remaining Wan family, use [Wan2.2](../wan2-2/_index.md); for shared
runtime behavior, use [Diffusion](../../components/diffusion/_index.md).^[PR #6357]
