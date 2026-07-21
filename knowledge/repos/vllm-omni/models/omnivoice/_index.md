---
title: "OmniVoice（离散扩散 TTS,AR/diffusion 双注册）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/model_executor/models/omnivoice/, vllm_omni/diffusion/models/omnivoice/, vllm_omni/deploy/omnivoice.yaml]
---

# OmniVoice

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 离散扩散 TTS：Qwen3 backbone 对 8 个 codebook 做 32 步迭代 unmask,
  HiggsAudioV2 风格 RVQ/DAC 解码到 24 kHz。
- **双注册**：AR registry `OmniVoiceModel`（`model_executor/models/omnivoice/`）;
  diffusion registry `OmniVoicePipeline`（别名 `OmniVoice`,
  `diffusion/models/omnivoice/pipeline_omnivoice.py`,post
  `get_omnivoice_post_process_func`）。
- pipeline key `omnivoice` 是**单 stage DIFFUSION** 包装
  （`execution_type=DIFFUSION`,`model_arch="OmniVoicePipeline"`）——与多数
  单 stage diffusion 家族不同,它在 `OMNI_PIPELINES` 里有显式入口。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)、
  `vllm_omni/utils/speaker_cache`。

## 结构与 serving

- diffusion pipeline 直接 import AR 目录的 `OmniVoiceGenerator`/
  `OmniVoiceDecoder`/`RuleDurationEstimator`,一次 `forward()` 完成
  文本→unmask→8-codebook token→DAC 解码;可选
  `transformers.HiggsAudioV2TokenizerModel` import 有 guard。
- `omnivoice_generator.py`（39 KB）带 `_OmniVoiceCUDAGraphForward`;无
  stage_input_processor（单 stage 无交接）。
- deploy `omnivoice.yaml` 未 pin checkpoint;`enforce_eager`、
  `dtype: float32`、`distributed_executor_backend: mp`。
- **未决**：AR-registry 入口 `OmniVoiceModel` 何时被走到无法仅从源码判定
  （服务路径是单 DIFFUSION stage,docstring 暗示两 stage LLM_AR 形态）——
  断言其是否使用前需 live 验证。另注:`OmniVoice` 只是架构别名,不是独立
  变体。

## 什么时候查这里

- 审查 omnivoice 的双注册、unmask 步数/codebook 或 speaker cache 改动。
- 共享 RNG/graph 规则见 [Diffusion rules](../../components/diffusion/rules.md)。
