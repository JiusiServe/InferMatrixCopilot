---
title: "Qwen-Omni 家族（Qwen2.5-Omni / Qwen3-Omni / Qwen3-TTS）"
created: 2026-07-16
updated: 2026-07-16
type: index
tags: [vllm-omni, models, qwen-omni]
sources: [vllm_omni/model_executor/models/registry.py, vllm_omni/config/pipeline_registry.py, docs/design/qwen3_omni_tts_performance_optimization.md]
---

# Qwen-Omni 家族（Qwen2.5-Omni / Qwen3-Omni / Qwen3-TTS）

- 常见别名：`qwen2_5_omni`、`qwen3_omni_moe`、`qwen3_tts`（家族目录：同一 thinker/
  talker/code2wav 谱系的多个 checkpoint/代际，按别名规则共用本目录）
- 源码模型族（`main @ 5c390096` 验证）：`model_executor/models/qwen2_5_omni/`、
  `qwen3_omni/`、`qwen3_tts/`；pipeline registry key `qwen2_5_omni`、
  `qwen2_5_omni_thinker_only`、`qwen3_omni_moe`（resolver
  `resolve_qwen3_omni_pipeline`，位于 `models/qwen3_omni/pipeline.py`，由
  `pipeline_registry.py:86/:100` 引用）、`qwen3_tts`
- deploy YAML：`qwen2_5_omni.yaml`（1×H100 验证）、`qwen3_omni_moe.yaml`
  （2×H100 验证）、`qwen3_omni_moe_mori_intranode.yaml`、`qwen3_tts.yaml`
  （+ `_forced_aligner`、`_high_concurrency` 变体）
- 官方文档：`docs/design/module/async_omni_architecture.md`（以 Qwen3-Omni 为
  worked example 的分层运行时 spec）、
  `docs/design/qwen3_omni_tts_performance_optimization.md`（性能优化实录）

## 什么时候查这里

- 问题只属于 Qwen-Omni/TTS 家族（thinker/talker 拓扑、talker_mtp、code2wav、
  TTS 性能口径）。

## 不放什么

- 共享 runner/预处理合同（放 components/model-executor）；共享调度与 prefix cache
  （放 components/scheduler）。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| stage 拓扑、代际差异与官方性能优化结论 | [architecture](architecture.md) |
