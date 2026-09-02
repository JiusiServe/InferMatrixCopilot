---
title: "Qwen3-TTS"
created: 2026-07-20
updated: 2026-09-02
type: index
tags: [vllm-omni, models, serving, qwen-omni]
sources: ["PR #5157", "PR #5608", vllm_omni/entrypoints/openai/serving_speech.py, vllm_omni/platforms/npu/models/qwen3_tts_tokenizer_v2.py, vllm_omni/platforms/npu/layers/rotary_embedding.py]
confidence: high
---

# Qwen3-TTS

## 名称与范围

- 正式 owner：Qwen3-TTS serving、ref audio、artifact cache 请求语义与模型专有 NPU patch。
- serving 入口：`vllm_omni/entrypoints/openai/serving_speech.py`。
- NPU tokenizer patch：`vllm_omni/platforms/npu/models/qwen3_tts_tokenizer_v2.py`；共享
  RoPE layout helper 在 `vllm_omni/platforms/npu/layers/rotary_embedding.py`，此 pin 上只
  证明 Qwen3-TTS consumer。
- 共享请求/cache 合同见 [Serving rules](../../components/serving/rules.md)。

## 什么时候查这里

- 审查 `x_vector_only_mode`、ICL、`ref_audio` artifact-only reuse、engine 存活性，或 NPU
  tokenizer RoPE 的 BNSD/BSND shape fallback。
- 描述直达源码与具体不变量见 [Qwen3-TTS rules](rules.md#direct-代码快速入口)；模型家族结构见
  [Qwen-Omni](../qwen-omni/_index.md)。
