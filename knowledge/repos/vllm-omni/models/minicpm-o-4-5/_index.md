---
title: "MiniCPM-o 4.5"
created: 2026-07-20
updated: 2026-07-20
type: index
tags: [vllm-omni, models, model-executor]
sources: ["PR #3642", vllm_omni/model_executor/models/minicpmo_4_5/]
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
  [Config](../../components/config/_index.md) 和 [Serving](../../components/serving/_index.md)。

## 版本与 stage 边界

MiniCPM-o 多个版本共享通用 `MiniCPMO` architecture 名称，4.5 不能仅靠 architecture
集合相交识别，必须结合 config/version predicate。4.5 pipeline 把 LLM/thinker 结果通过
runtime bridge 交给 TTS stage，再包装为 `OmniOutput.multimodal_outputs`；deploy 变体改变
资源拓扑，不改变数据合同。

模型专有门禁见 [rules](rules.md)；新模型语义验证见
[model validation](../../review/guides/model-validation.md)。

## 什么时候查这里

- 审查 MiniCPM-o 4.5 registry、remote-code gate、TTS dependency、batch 或 stage handoff。
- 问题位于共享 bridge/batching 时转到
  [Model Executor rules](../../components/model-executor/rules.md)。
