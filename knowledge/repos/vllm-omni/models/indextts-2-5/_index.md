---
title: "IndexTTS 2.5"
created: 2026-09-02
updated: 2026-09-02
type: index
tags: [vllm-omni, models]
sources: ["PR #5957", vllm_omni/config/pipeline_registry.py, vllm_omni/deploy/indextts2_5.yaml, vllm_omni/model_executor/models/registry.py, vllm_omni/model_executor/models/indextts2/, vllm_omni/model_executor/stage_input_processors/indextts2.py, vllm_omni/entrypoints/openai/tts_adapters/indextts2.py, recipes/IndexTeam/IndexTTS-2_5.md]
confidence: high
---

# IndexTTS 2.5

- registry/pipeline key：`indextts2_5`；architecture 为
  `IndexTTS25TalkerForConditionalGeneration` 与 `IndexTTS25S2MelDecoder`，复用 versioned
  IndexTTS2 implementations。
- 两 stage、同卡、non-streaming pipeline：AR talker 生成完整 semantic codes，S2Mel CFM/DiT +
  EnhancedCodec + BigVGAN 输出 22.05 kHz mono audio。标准 deploy 使用 code-only
  `use_gpt_latent=false`，Stage 1 必须等 request-end full payload；async chunk 不适用。
- 支持 reference/uploaded named voice、emotion controls、multilingual frontend 与 native speed；精确
  拓扑与 versioned conditioning 见 [architecture](architecture.md)，请求、bundle、payload、性能和
  验证边界见 [rules](rules.md)。

## 路由

- IndexTTS 2.5 模型、codec、S2Mel、tokenizer、recipe：本 owner。
- shared TTS HTTP/streaming adapter：[Serving](../../components/serving/_index.md)。
- request-end payload snapshot 与 runner：[Model Executor](../../components/model-executor/_index.md)。
- full-payload admission：[Scheduler](../../components/scheduler/_index.md)。
