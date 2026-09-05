---
title: "Speech 输出采样率规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #6553", docs/serving/speech_api.md, vllm_omni/entrypoints/openai/audio_utils_mixin.py, vllm_omni/entrypoints/openai/protocol/audio.py, vllm_omni/entrypoints/openai/serving_speech.py, vllm_omni/entrypoints/openai/tts_adapters/base.py, vllm_omni/entrypoints/openai/tts_adapters/qwen3_tts.py, tests/entrypoints/openai_api/test_audio_format.py, tests/entrypoints/openai_api/test_serving_speech.py, tests/e2e/online_serving/test_qwen3_tts_customvoice_expansion.py]
confidence: high
---

# Speech 输出采样率规则

## SERV-9b — speech `sample_rate` 必须由 adapter capability 限定

- 触发：public speech request `sample_rate`、TTS adapter capability、audio encoding 或 streaming output。
- 强制：protocol 只接受 positive int；是否支持由 adapter capability 决定。Qwen3-TTS 只接受 `{8000,24000}`，
  omitted 使用 native 24k，其他 adapter 对 supplied value reject。Qwen non-streaming encoding 前 resample；
  batch default 可被 item override。streaming 只支持 mono integer downsample，保持 persistent filter state、
  source-rate consistency 与 flush tail，target header/meta 只在 audio 后发出且 first audio 必须有 source sr。
- 禁止：upsample、16k/stereo/general adapter support，或据 server-side resampling 声称降低模型生成 latency/cost。
- 验收：Qwen native/8k、other adapter reject、batch override、streaming chunk continuity/tail/source mismatch/
  first-audio source-sr failure。CPU/DSP 与单一 expansion fixture 不证明跨硬件音质、TTFB 或带宽收益。^[PR #6553]
