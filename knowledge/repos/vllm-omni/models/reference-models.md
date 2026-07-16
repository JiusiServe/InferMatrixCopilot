---
title: "新模型适配的钦定参照（GLM-Image / BAGEL / Qwen-Omni 指针）"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/registry.py, vllm_omni/config/pipeline_registry.py, vllm_omni/deploy/]
---

# 新模型适配的钦定参照

树内多处把这几个模型当"照抄基准"（blessed precedent）引用，但它们此前没有落脚页。
本页按参照用途给出源码/配置入口；**当某个模型出现第一条模型专属稳定结论时，升级为
独立 `models/<模型>/` 目录**（LTX-2、Qwen-Omni 已因此建目录）。以下路径在
`main @ 5c390096` 验证存在。

## GLM-Image — AR+DiT 多 stage 的 IT2I 精度参照

- 何时照抄：做 AR→DiT 桥接、IT2I 行为对齐时（hunyuan 的
  [it2i-gap](hunyuan-image3/guides/it2i-gap.md) 与
  [ar-dit-bridge 历史](hunyuan-image3/history/_index.md) 均以它为基准）。
- 入口：AR 侧 `model_executor/models/glm_image/`（`GlmImageForConditionalGeneration`）；
  diffusion 侧 `diffusion/models/glm_image/`（`GlmImagePipeline`，
  `pipeline_glm_image.py`）；stage 衔接 `stage_input_processors/glm_image.py`；
  pipeline key `glm_image`；deploy `vllm_omni/deploy/glm_image.yaml`。

## BAGEL — 统一模型多形态部署参照

- 何时照抄：一个模型要支持多种 stage 拓扑/思考形态时——pipeline registry 里同时有
  `bagel`、`bagel_think`、`bagel_single_stage` 三个 key，deploy 有
  `bagel.yaml`/`bagel_think.yaml`/`bagel_single_stage.yaml` 三份。
- 入口：AR 侧 `model_executor/models/bagel/`（`OmniBagelForConditionalGeneration`）；
  diffusion 侧 `diffusion/models/bagel/`（`BagelPipeline`）；stage 衔接
  `stage_input_processors/bagel.py`。
- 相关硬规则：多 stage 共卡显存预算见
  [Config 规则 CONF-1a](../components/config/rules.md)（Bagel 正是案例）。

## Qwen2.5/3-Omni — thinker/talker 多 stage 全家桶参照

- 已有独立目录：[qwen-omni](qwen-omni/_index.md)（I2T blessed pattern、
  异步运行时的官方 worked example）。

## 相关

- 语义验收（plumbing≠语义）见
  [model-adaptation-guardrails](../review/guides/model-adaptation-guardrails.md)。
