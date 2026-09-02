---
title: "MiniCPM-o 4.5"
created: 2026-07-20
updated: 2026-09-02
type: index
tags: [vllm-omni, models, model-executor]
sources: ["PR #3642", "PR #5382", "PR #5638", "PR #5869", "PR #6154", "PR #6170", "PR #6318", vllm_omni/model_executor/models/cosyvoice3/code2wav_core/hifigan.py, vllm_omni/model_executor/models/minicpmo_4_5/]
confidence: high
---

# MiniCPM-o 4.5

## 名称、源码与部署

- 正式名称：MiniCPM-o 4.5；仓库目录/注册 key 使用 `minicpmo_4_5`。
- 模型：`vllm_omni/model_executor/models/minicpmo_4_5/`，包含 LLM、TTS wrapper 和
  pipeline；输入处理在 `model_executor/stage_input_processors/minicpmo_4_5_omni.py`。
- 配置与入口：`config/pipeline_registry.py`、`deploy/minicpmo_4_5.yaml`、
  `minicpmo_4_5_3gpu.yaml`、`minicpmo_4_5_8x4090.yaml`。
- 共享 owner：[Model Executor](../../components/model-executor/_index.md)、
  [Config](../../components/configuration/_index.md) 和 [Serving](../../components/serving/_index.md)。

## 版本与 stage 边界

MiniCPM-o 多个版本共享通用 `MiniCPMO` architecture 名称，4.5 不能仅靠 architecture
集合相交识别，必须结合 config/version predicate。4.5 pipeline 把 LLM/thinker 结果通过
runtime bridge 交给 TTS stage，再包装为 `OmniOutput.multimodal_outputs`；deploy 变体改变
资源拓扑，不改变数据合同。

Code2Wav 在所有平台使用树内 `MiniCPMO45Token2wav`。CUDA 可显式开启 DiT estimator +
Campplus TensorRT；这是可关闭的局部加速，不替换 encoder/HiFT，也不会自动启用
Step-Audio2 的 token2wav。engine cache/profile 与 fallback 门禁见 MCPMO-1c。

四份 bundled deploy 在 CUDA 上另默认开启 HiFT graph：只 capture pre-iSTFT 子图，按 connector
chunk/cache shape 预捕并限量 lazy capture，且不服从 stage `enforce_eager`；非 CUDA 回 eager。
shape、显存、并发与部分-graph 性能证据边界见 MCPMO-1d。

Thinker 的 Whisper/APM audio encoder 仍构造 dense `[B,1,T,T]` mask；chunk mask 已用
broadcasted query/key index 代替逐 row Python fill，但不改变 chunk/left-context/lookahead
边界，也不消除 O(T²) storage。语义与证据门禁见 MCPMO-2b。

描述直达源码与模型专有门禁见 [rules](rules.md#direct-代码快速入口)；新模型语义验证见
[model validation](../../review/guides/model-validation.md)。

## 什么时候查这里

- 审查 MiniCPM-o 4.5 registry、remote-code gate、TTS dependency、Code2Wav TensorRT/HiFT graph、
  batch/stage handoff 或 native duplex session。
- 问题位于共享 bridge/batching 时转到
  [Model Executor rules](../../components/model-executor/rules.md)。
