---
title: "PersonaPlex"
created: 2026-09-02
updated: 2026-09-06
type: index
tags: [vllm-omni, models, model-executor]
sources: ["PR #4771", vllm_omni/model_executor/models/personaplex/, vllm_omni/model_executor/models/personaplex/duplex/, vllm_omni/deploy/personaplex.yaml]
confidence: high
---

# PersonaPlex

## 名称、注册与范围

- 正式模型 `nvidia/personaplex-7b-v1`，是 Moshi-based full-duplex S2S；目标 pin
  `e788ef6e` 的实现标为 experimental。
- AR registry 新增 `PersonaPlexTalkerForConditionalGeneration` 和
  `PersonaPlexCode2Wav`，都位于 `model_executor/models/personaplex/`；pipeline registry
  key 是 `personaplex`，默认 deploy 是 `personaplex.yaml`。
- checkpoint 的 `config.json` 为空；`engine/arg_utils.py::_ARCH_TO_MODEL_TYPE` 必须从上述
  architecture 回填 `model_type=personaplex`，再注册本地 `PersonaPlexConfig`。
- 两个入口必须区分：标准 omni engine 的 talker→code2wav staged pipeline，以及
  `/v1/realtime?duplex=1` unified engine path；`personaplex/serving/` 的 standalone server
  只是兼容面，不能证明 unified path 可用。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| stage、frame、codec/session 状态和 serving 边界 | [architecture](architecture.md) |
| frame accounting、de-delay、lease、greedy/config 门禁 | [rules](rules.md) |

## 什么时候查这里

- 审查 PersonaPlex registry/config、Mimi codec、async-chunk handoff、duplex admission、
  session cleanup 或 WebSocket reconnect。
- 共享 full-duplex 生命周期转到 [Serving rules](../../components/serving/rules.md)，共享
  runner hook/config projection 转到 [Model Executor rules](../../components/model-executor/rules.md)。
