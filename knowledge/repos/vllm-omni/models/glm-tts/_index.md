---
title: "GLM-TTS（AR + flow-matching DiT 流式 TTS）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/glm_tts/, vllm_omni/deploy/glm_tts.yaml, vllm_omni/config/pipeline_registry.py]
---

# GLM-TTS

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 正式名称 GLM-TTS,无别名、无变体有据。AR registry:
  `GLMTTSForConditionalGeneration`
  →（`glm_tts`, `glm_tts`, `GLMTTSForConditionalGeneration`）;
  家族目录 `vllm_omni/model_executor/models/glm_tts/`（8 个文件）。
- pipeline key `glm_tts`：stage 0 AR（Llama 基座,LLM_AR,latent;stop token
  为 "👂" id 59253,代码注释称按 tokenizer 动态解析校验）→ stage 1
  `glm_tts_dit`（LLM_GENERATION,音频）。
- 依赖共享模块：[Config 组件](../../components/config/architecture.md);
  vocoder 为家族内 `HiFTWrapper`/`Vocos2DWrapper` + `ConvRNNF0Predictor`。

## 结构与 serving

- 关键文件：`glm_tts.py`（61 KB,AR + MM processor）、`glm_tts_dit_wrapper.py`
  （57 KB,`CUDAGraphGLMTTSDiTWrapper`——**按 bucket 捕获 DiT CUDA graph,
  eager 兜底**）、`glm_tts_dit.py`（ConvNeXtV2/AdaLayerNormZero blocks）、
  `text_frontend.py`（文本归一化）、`voice_clone.py`。
- stage 交接：`stage_input_processors/glm_tts.py` 的 `ar_to_dit` 与
  `ar_to_dit_async_chunk`。
- deploy `glm_tts.yaml` 未 pin checkpoint;`async_chunk: true`,
  SharedMemoryConnector 渐进分块 `codec_chunk_frames: [25, 50, 200]` +
  0.1 s crossfade;stage 0 bf16、stage 1 **float32**（注释：Euler ODE 10×2
  趟会累积半精度嘶声）且 `use_dit_cuda_graphs: true`;RAS 采样
  `hf_overrides`（`sample_method: ras` + top-k/p 窗口）;标注 1×A40 验证
  （~16.6 GiB）。

## 什么时候查这里

- 审查 GLM-TTS 的 DiT CUDA-graph bucket、渐进分块流式或精度（fp32 stage 1）
  改动;想改 stage 1 精度先看 YAML 注释的 hiss 依据。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
