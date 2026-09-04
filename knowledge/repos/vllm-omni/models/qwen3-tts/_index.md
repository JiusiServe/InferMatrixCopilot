---
title: "Qwen3-TTS"
created: 2026-07-20
updated: 2026-09-05
type: index
tags: [vllm-omni, models, serving, qwen-omni]
sources: ["PR #5157", "PR #5202", "PR #5608", "PR #6001", vllm_omni/entrypoints/openai/serving_speech.py, vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py, vllm_omni/model_executor/models/qwen3_tts/segmented_graph_wrapper.py, vllm_omni/model_executor/stage_input_processors/qwen3_tts.py, vllm_omni/model_executor/stage_input_processors/chunk_size_utils.py, vllm_omni/platforms/npu/models/qwen3_tts_tokenizer_v2.py, vllm_omni/platforms/npu/layers/rotary_embedding.py]
confidence: high
---

# Qwen3-TTS

## 名称与范围

- 正式 owner：Qwen3-TTS serving、ref audio、artifact cache、async Code2Wav
  增量解码/状态生命周期、adaptive chunk ramp 与模型专有 NPU patch。事实在 `main @ 4ad455e6`
  复核。
- serving 入口：`vllm_omni/entrypoints/openai/serving_speech.py`。
- NPU tokenizer patch：`vllm_omni/platforms/npu/models/qwen3_tts_tokenizer_v2.py`；共享
  RoPE layout helper 在 `vllm_omni/platforms/npu/layers/rotary_embedding.py`，此 pin 上只
  证明 Qwen3-TTS consumer。
- 共享请求/cache 合同见 [Serving rules](../../components/serving/rules.md)。

## 什么时候查这里

- 审查 `x_vector_only_mode`、ICL、`ref_audio` artifact-only reuse、incremental
  Code2Wav、segmented CUDA Graph、engine 存活性，或 NPU
  tokenizer RoPE 的 BNSD/BSND shape fallback。
- 描述直达源码与具体不变量见 [Qwen3-TTS rules](rules.md#direct-代码快速入口)；模型家族结构见
  [Qwen-Omni](../qwen-omni/_index.md)。
