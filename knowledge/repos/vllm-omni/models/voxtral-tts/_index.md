---
title: "Voxtral TTS（Mistral 两 stage 流式 TTS）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/voxtral_tts/, vllm_omni/deploy/voxtral_tts.yaml, vllm_omni/platforms/xpu/stage_configs/voxtral_tts.yaml]
---

# Voxtral TTS

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- Mistral Voxtral TTS。AR registry：`VoxtralTTSForConditionalGeneration`、
  `VoxtralTTSAudioGeneration`、`VoxtralTTSAudioTokenizer` → 家族目录
  `vllm_omni/model_executor/models/voxtral_tts/`（6 个文件）。
- pipeline key `voxtral_tts`：stage 0 `audio_generation`（LLM_AR,tokenizer
  owner,latent）→ stage 1 `audio_tokenizer`（LLM_GENERATION,音频;
  `tts_args.max_instructions_length: 500`）。
- 依赖共享模块：[Config 组件](../../components/config/architecture.md)。

## 结构与 serving

- `cuda_graph_acoustic_transformer_wrapper.py`：把 semantic-logit + n 步
  Euler ODE（含 CFG）按固定 batch size 捕获进 CUDA graph（docstring 注明仅
  FlowMatching）;`voxtral_tts_audio_generation.py` 可选 apex `FusedRMSNorm`。
- stage 交接：`stage_input_processors/voxtral_tts.py`
  `generator2tokenizer_async_chunk`。
- deploy `voxtral_tts.yaml` 未 pin checkpoint;`async_chunk: true`
  SharedMemoryConnector（`codec_chunk_frames: 25`,起始 5）;**两 stage 的
  `tokenizer_mode/config_format/load_format` 都是 `mistral` 且必须一致**
  （YAML 注释）;stage 0 采样 `extra_args.cfg_alpha: 1.2`;标注 1×H20 验证。
- **尾部家族中唯一有 XPU stage 配置**：
  `vllm_omni/platforms/xpu/stage_configs/voxtral_tts.yaml`
  （XPUARWorker + OmniARScheduler）。

## 什么时候查这里

- 审查 voxtral_tts 的 mistral 加载三件套一致性、acoustic CUDA-graph 或
  async-chunk 改动;XPU 路径回归先查这里的 stage 配置。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
