---
title: "Deploy YAML 写作实操"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, dev]
sources: [docs/configuration/stage_configs.md, vllm_omni/deploy/]
---

# Deploy YAML 写作实操

面向"要给模型写/改部署配置"的场景；schema 语义 owner 是
[Config 组件](../../components/config/architecture.md)（本页不复制字段表）。
`main @ 5c390096` 复核。

## 何时需要 YAML，何时 CLI 就够

- bundled 默认：registry 按 `model_type` 自动加载 `vllm_omni/deploy/<model>.yaml`
  ——不给 `--deploy-config`/`--stage-configs-path` 时就用它；只调个别 stage 参数时
  优先 CLI/per-stage override，不新写 YAML。
- 需要新 YAML 的信号：新模型/新 stage 拓扑变体（参照 bagel 的三形态）、平台覆盖
  （`platforms: npu/rocm/xpu`）、connector 拓扑改变、或要固化一组经过验证的资源
  参数（如 voxcpm2 的 KV pin）。
- legacy 未迁移模型仍走 `--stage-configs-path` + `stage_args` schema
  （`model_executor/stage_configs/*.yaml`，如 mimo_audio、step_audio_2、
  hunyuan_video_15、wan2_2 的 dit_fp8 配置）。

## 写作时必查的字段（事故来源）

- **每个共卡 stage 显式 `gpu_memory_utilization`**（缺省 0.9/0.92 是 OOM 事故源，
  [CONF-1a](../../components/config/rules.md)）。
- **单 stage/端到端 pipeline pin `async_chunk: false`**
  （[ci-gotchas](../../ci/guides/ci-gotchas.md) 第 2 条）。
- KV 记账外分配的模型考虑 `kv_cache_memory_bytes` pin（[CONF-2a](../../components/config/rules.md)）。
- 争议以展开后最终配置为准（[CONF-3a](../../components/config/rules.md)）。

## 代表样例（58 份 YAML 中的三类拓扑）

- 单 stage diffusion：不进 `OMNI_PIPELINES`，通常无需 YAML（引擎默认兜底），需要
  固化参数时才写。
- AR+DiT 两 stage：`glm_image.yaml`、`hunyuan_image3_{ar,dit,_moe}.yaml`。
- thinker/talker(+code2wav) 多 stage：`qwen2_5_omni.yaml`（1×H100 验证）、
  `qwen3_omni_moe.yaml`（2×H100 验证）、`qwen3_tts.yaml`（+ 高并发/对齐器变体）。

## 相关

- 字段语义/合并链：[Config architecture](../../components/config/architecture.md)；
  connector 声明：[connector-backends](../../components/distributed/guides/connector-backends.md)。
