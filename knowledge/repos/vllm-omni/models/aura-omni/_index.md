---
title: "Aura-Omni（4-stage 语音助手组合管线)"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/aura_omni/, vllm_omni/deploy/aura_omni.yaml, vllm_omni/config/pipeline_registry.py]
---

# Aura-Omni

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 正式 owner：aura_omni 家族；pipeline key `aura_omni`。AR registry 架构
  `AuraQwen3VLForConditionalGeneration` →（`aura_omni`, `qwen3_vl`）。
- 源码：`vllm_omni/model_executor/models/aura_omni/`（仅 3 个文件——本家族
  以**组合**为主,只有 stage 1 有家族自有模型代码）。
- 依赖共享模块：qwen3_tts 家族的 talker/code2wav 与其 stage 处理器
  （[qwen3-tts](../qwen3-tts/_index.md)）、[Config 组件](../../components/config/architecture.md)。

## 结构与 serving

- 4 stage：Qwen3-ASR（LLM_AR, 文本）→ AURA/Qwen3-VL（LLM_AR, 最终文本）→
  Qwen3-TTS talker（LLM_AR, latent, stop 2150）→ `Qwen3TTSCode2Wav`
  （LLM_GENERATION, 音频）。stage 2–3 直接复用 qwen3_tts 的
  `talker2code2wav_*` 处理器;家族自有处理器 `asr2aura`/`aura2tts`
  （`stage_input_processors/aura_omni.py`）。
- `qwen3_vl.py` 是 config 兼容 shim：AURA checkpoint 经 `auto_map` 带远程
  `Qwen3VLConfig`,`get_hf_config` 接受结构兼容的远程 config,
  `get_hf_processor` 强制上游 `Qwen3VLProcessor`（checkpoint 缺少其声明的
  `processing_qwen3_vl.py`）。
- deploy `vllm_omni/deploy/aura_omni.yaml`：**尾部家族中唯一 pin 了
  checkpoint 的**——Qwen/Qwen3-ASR-1.7B + aurateam/AURA +
  Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice;全部 GPU 0;`async_chunk: false`
  （ASR→AURA→TTS 语义依赖）;stage2→3 SharedMemoryConnector 码流 +
  `decode_cudagraph_capture_sizes`;NPU 覆盖 stage 2 `enforce_eager`。
- 注意：`AURA_OMNI_PIPELINE.model_arch="Qwen3ASRForConditionalGeneration"`
  不在 `_OMNI_MODELS`,依赖上游 vLLM `_VLLM_MODELS` 合并解析（pin 上未验证
  上游确实注册该架构）。

## 什么时候查这里

- 审查 aura_omni 拓扑、config shim 或 stage 复用改动;qwen3_tts 侧行为变化会
  直接影响本家族 stage 2–3。
- 新模型注册点清单见 [dev/adding-a-model](../../dev/guides/adding-a-model.md)。
