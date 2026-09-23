---
title: "Aura-Omni（4-stage 语音助手组合管线）"
created: 2026-07-21
updated: 2026-09-23
type: index
tags: [vllm-omni, models, model-executor, serving]
sources:
  [
    "PR #7633",
    vllm_omni/model_executor/models/aura_omni/,
    vllm_omni/model_executor/models/aura_omni/duplex/,
    vllm_omni/model_executor/stage_input_processors/aura_omni.py,
    vllm_omni/deploy/aura_omni.yaml,
    vllm_omni/config/pipeline_registry.py,
    docs/user_guide/examples/online_serving/aura_omni.md,
    tests/model_executor/models/aura_omni/test_aura_omni_duplex_history.py,
    tests/engine/duplex/test_session_runner.py,
  ]
confidence: high
---

# Aura-Omni

以下事实在合入 [PR #7633](https://github.com/vllm-project/vllm-omni/pull/7633)
后的 `main` 复核（含 duplex plugin、SessionHistory、Stage1 投影与 barge-in 清理）。

## 名称、源码与部署

- 正式名称 Aura-Omni（AURA 语音助手管线）；pipeline key `aura_omni`。
- AR registry：`AuraQwen3VLForConditionalGeneration` →（`aura_omni`, `qwen3_vl`,
  `AuraQwen3VLForConditionalGeneration`）。
- 源码：`vllm_omni/model_executor/models/aura_omni/`（`pipeline.py`、`qwen3_vl.py`
  shim、**`duplex/`** plugin／history／capabilities／data_plane）。
- 阶段桥：`stage_input_processors/aura_omni.py`（`asr2aura` / `aura2tts`）。
- Deploy：`vllm_omni/deploy/aura_omni.yaml`（pin ASR + AURA + Qwen3-TTS
  checkpoint；尾段复用 qwen3_tts Talker/Code2Wav）。
- 共享 owner：[Qwen3-TTS](../qwen3-tts/_index.md)、
  [Model Executor](../../components/model-executor/_index.md)、
  [Serving](../../components/serving/_index.md)、
  [Configuration](../../components/configuration/_index.md)。

## 结构与 serving

- **四段**：Stage0 Qwen3-ASR → Stage1 AURA Thinker → Stage2 Talker → Stage3
  Code2Wav。Stage2–3 复用 qwen3_tts 处理器；家族自有桥只在 ASR↔AURA↔TTS。
- **Realtime duplex**：`/v1/realtime?duplex=1`；`AuraDuplexPlugin` 负责
  `plan_append`、`decide_output`、Stage1 `project_intermediate_output`、
  concurrent turn、TTS extras。上游用户文档：
  `docs/user_guide/examples/online_serving/aura_omni.md`。
- `qwen3_vl.py` 仍是 config 兼容 shim：接受结构兼容的远程 `Qwen3VLConfig`，
  processor 强制上游 `Qwen3VLProcessor`。
- **Silent id**：duplex plugin 常量对齐 **AURA v1** `151669`；AURA_v2 streaming
  Omni 使用另一套 id，不得混用（规则组 AURA-1f）。

## 什么时候查这里

- 审查 `aura_omni` 拓扑、duplex plugin、Stage1 投影 / metrics、barge-in 与
  draining TTS、SessionHistory 裁剪、silent token、sentence-TTS env、
  OmniInteract 风格 streaming 报表暖机。
- qwen3_tts Talker/Code2Wav 行为变化会直接影响本家族 Stage2–3 → 先读
  [qwen3-tts rules](../qwen3-tts/rules.md)。
- 共享 duplex session / warmup transport 合同 →
  [serving session lifecycle](../../components/serving/rules-session-lifecycle.md)。

## 不放什么

- 本机绝对路径、GPU 编号、演示端口、私有 handoff 长文。
- MiniCPM native duplex adapter 专用合同（见 [minicpm-o-4-5](../minicpm-o-4-5/_index.md)）。
- 通用 Realtime wire defaults / `session.update` ACK 时机（见 serving 组件规则，
  例如 Issue #7636 / PR #7996 一类共享修复）。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 可审计硬门禁（投影、metrics、barge-in、history、silent、暖机、env） | [rules](rules.md) | `AURA-1a` … `AURA-1h` |
| Talker / Code2Wav 共享规则 | [qwen3-tts rules](../qwen3-tts/rules.md) | 尾段家族 |
| 新模型注册清单 | [adding-a-model](../../components/configuration/adding-a-model.md) | 配置组件 |
