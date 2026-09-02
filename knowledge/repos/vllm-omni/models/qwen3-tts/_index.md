---
title: "Qwen3-TTS"
created: 2026-07-20
updated: 2026-09-02
type: index
tags: [vllm-omni, models, serving, qwen-omni]
sources: ["PR #4958", "PR #5157", vllm_omni/entrypoints/openai/serving_speech.py, vllm_omni/model_executor/models/common/qwen3_code_predictor.py]
confidence: high
---

# Qwen3-TTS

## 名称与范围

- 正式 owner：Qwen3-TTS serving、ref audio 与 artifact cache 请求语义。
- serving 入口：`vllm_omni/entrypoints/openai/serving_speech.py`。
- 共享请求/cache 合同见 [Serving rules](../../components/serving/rules.md)。

## 什么时候查这里

- 审查 `x_vector_only_mode`、ICL、`ref_audio` artifact-only reuse 或 engine 存活性。
- 审查 Qwen3-TTS/Qwen3-Omni 共用 code predictor 的 fused projection、checkpoint 拼装、
  TP 边界或平台 override 时，转到 [Model Executor EXEC-2b](../../components/model-executor/rules.md#exec-2b-fused-shard-必须按布局数值闭环且所有-consumer-委托共享-loader)。
- 描述直达源码与具体不变量见 [Qwen3-TTS rules](rules.md#direct-代码快速入口)；模型家族结构见
  [Qwen-Omni](../qwen-omni/_index.md)。
