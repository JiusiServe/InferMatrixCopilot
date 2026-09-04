---
title: "Qwen-Omni 家族（Qwen2.5-Omni / Qwen3-Omni / Qwen3-TTS）"
created: 2026-07-16
updated: 2026-09-04
type: index
tags: [vllm-omni, models, qwen-omni]
sources: ["PR #5073", "PR #5671", "PR #5976", vllm_omni/model_executor/models/qwen2_5_omni/qwen2_5_omni_thinker.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni_moe_thinker.py, vllm_omni/model_executor/models/registry.py, vllm_omni/model_executor/models/qwen2_5_omni/pipeline.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py, vllm_omni/config/pipeline_registry.py, vllm_omni/deploy/qwen3_omni_moe.yaml, docs/design/qwen3_omni_tts_performance_optimization.md]
---

# Qwen-Omni 家族（Qwen2.5-Omni / Qwen3-Omni / Qwen3-TTS）

- 常见别名：`qwen2_5_omni`、`qwen3_omni_moe`、`qwen3_tts`（家族目录：同一 thinker/
  talker/code2wav 谱系的多个 checkpoint/代际，按别名规则共用本目录）
- 源码模型族（`main @ e04210d6` 验证）：`model_executor/models/qwen2_5_omni/`、
  `qwen3_omni/`、`qwen3_tts/`；pipeline registry key `qwen2_5_omni`、
  `qwen2_5_omni_thinker_only`、`qwen3_omni_moe`（resolver
  `resolve_qwen3_omni_pipeline`，位于 `models/qwen3_omni/pipeline.py`，由
  `pipeline_registry.py:86/:100` 引用）、`qwen3_tts`
- deploy YAML：`qwen2_5_omni.yaml`（1×H100 验证）、`qwen3_omni_moe.yaml`
  （2×H100 验证）、`qwen3_omni_moe_mori_intranode.yaml`、`qwen3_tts.yaml`
  （+ `_forced_aligner`、`_high_concurrency` 变体）
- Qwen2.5 thinker-only 的 ModelOpt NVFP4 W4A4 checkpoint 支持、stage sub-config、Talker
  ingress/internal width 与硬件/accuracy 证据边界归下方 architecture 入口。
- Qwen3-Omni 的 MUSA ModelOpt FP8 边界是 Thinker 保留量化、Talker/Code2Wav 通过 deploy
  overlay 显式清除 root quantization metadata，并仅关闭不安全的 Talker-MTP FULL graph
  wrapper；精确三态与验证边界归下方 architecture 入口。
- vLLM 0.27 后 upstream 与 Omni registry 有同名 architecture：Omni 必须覆盖全局 entry；plain
  `vllm serve` 缺 `model_stage` 时 Qwen2.5/Qwen3 默认 thinker，Qwen3 thinker 在非 staged 模式返回
  bare tensor，只有 staged talker consumer 才请求 captured layers；共享验收见
  [EXEC-1e](../../components/model-executor/rules-bridge-batch.md#exec-1e-upstream-registry-重名时-omni-override-与-plain-vllm-forward-必须同时成立)。^[PR #5976]
- 官方历史文档：`docs/design/module/archive/async_omni_architecture.md`（以 Qwen3-Omni 为
  worked example 的分层运行时快照，非 active spec）、
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
| Qwen3-Omni Thinker MRoPE、CUDA compilation custom-op boundary 或固定种子音频回归 | [Qwen-Omni rules](rules.md) |
