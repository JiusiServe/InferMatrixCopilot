---
title: "Mage-VL experimental architecture"
created: 2026-09-05
updated: 2026-09-05
type: architecture
tags: [vllm-omni, models, model-executor]
sources: ["PR #6537", vllm_omni/experimental/fullduplex/mage_vl/adapter.py, vllm_omni/experimental/fullduplex/mage_vl/serving/backend.py, vllm_omni/experimental/fullduplex/mage_vl/serving/server.py, recipes/Microsoft/Mage-VL.md]
confidence: high
---

# Mage-VL experimental architecture

## Transport → adapter → backend

Client sends shared duplex `input.append`: optional text plus encoded MP4 video data (`video_base64` and
segment/timing metadata) to standalone `WS /v1/mage-vl/duplex`. The FastAPI server owns bearer authentication,
session-ID validation, concurrent-session/message bounds, idle timeout, cancellation and lease cleanup. It advertises
only `{text, video}` input and `{text}` output, matching the checked-in Transformers backend.

`MageVLDuplexAdapter` owns per-session bounded causal visual windows, pending query/gate decision, event
de-duplication and gate tasks. `MageVLDuplexRuntime` is a small shared-runtime subclass that watches deferred gate
completion while the reader remains available for cancellation. The common response/cancellation/close mechanics belong
to [SERV-6h](../../components/serving/rules-session-lifecycle.md).

`MageVLTransformersBackend` materializes the encoded MP4 temporarily, applies the remote-code processor, runs the
StreamMind gate or generation, and serializes access to the shared checkpoint. `frames` samples decoded frames. The
optional `codec` backend requires `ffmpeg`, `ffprobe`, and `cv-preinfer` from `codec-video-prep>=0.2.5`; absent
`cv-preinfer` is a startup error with `frames` as the fallback.

## Boundary

The adapter has generic codec-window abstractions, but the production Transformers transport accepts encoded video
only. Image or opaque `codec_window` must not be advertised as production capabilities. This is not a native vLLM
executor, pipeline, deploy profile, or unified route.^[PR #6537]
