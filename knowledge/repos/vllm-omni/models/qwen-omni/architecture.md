---
title: "Qwen-Omni 家族拓扑与性能结论"
created: 2026-07-16
updated: 2026-07-16
type: architecture
tags: [vllm-omni, models, qwen-omni]
sources: [docs/design/qwen3_omni_tts_performance_optimization.md, docs/design/module/async_omni_architecture.md, vllm_omni/model_executor/models/registry.py]
---

# Qwen-Omni 家族拓扑与性能结论

以下事实在 `main @ 5c390096` 复核。

## Stage 拓扑

- **Qwen3-Omni**（原生多模态理解 + 语音生成）三 stage：**Thinker**（多模态理解 +
  文本生成）→ **Talker**（含 Talker-MTP / code predictor 路径，把语义/文本表征转
  codec token）→ **Code2Wav**（codec token 解码为波形）。
- **Qwen3-TTS**（轻量 TTS）两 stage：**Talker（AR decoder）**→ **Code2Wav
  （vocoder）**。
- **Qwen2.5-Omni**：registry 注册 Thinker/Talker/Token2Wav（含 DiT 变体）架构名；
  `qwen2_5_omni_thinker_only` pipeline 提供纯理解形态——hunyuan 架构页把
  `qwen2_5_omni_thinker.py` 标为 **I2T blessed pattern**（新模型 I2T 适配的照抄
  基准）。
- Qwen3-Omni 的 pipeline 由 resolver（`models/qwen3_omni/pipeline.py::
  resolve_qwen3_omni_pipeline`）按 checkpoint 结构动态决定，而不是冻结的
  `PipelineConfig` 字面量。

## 官方性能优化结论（docs/design/qwen3_omni_tts_performance_optimization.md）

两模型共享同一多 stage 设计，叠加同一组优化：**batching**（逐 stage 提升 GPU
利用率）、**CUDA Graph**（降低 CPU launch 开销与 decode 抖动）、**async chunk +
流式输出**（跨 stage 重叠计算与通信、增量出音频，同时改善 TTFP 与 E2E）。
对 HF Transformers（离线单请求）的实测（Qwen3-Omni @A100）：E2E 336.10s → 23.78s
（~93%↓）、TTFP 336.10s → 0.934s（~99.7%↓）、RTF 3.776 → 0.32（~12×）。
（Qwen3-TTS @H200 的并发曲线见原文；数字随版本漂移，引用前复核。）

## 运行时参照

家族是 `docs/design/module/async_omni_architecture.md` 分层运行时（API →
Engine → Orchestration → Communication → Execution）的官方 worked example；
相关共享机制：talker 的 prefix-cache 关键 key 合同见
[Scheduler 规则 SCHED-1a](../../components/scheduler/rules.md)，`talker_mtp`
路由与 runner 预处理合同见
[Model Executor](../../components/model-executor/rules.md)。

## 已有证据索引（只链接）

- CI 事故（qwen3_omni prefix caching 用例等）见 [ci incidents](../../ci/incidents/_index.md)。
- 小 token 预算挂 GPU 的案例（`test_qwen3_omni_expansion.py`）见
  [Scheduler 规则 SCHED-2a](../../components/scheduler/rules.md)。

源码会变化，具体类名和行号在改代码前必须以目标仓库当前版本为准。
