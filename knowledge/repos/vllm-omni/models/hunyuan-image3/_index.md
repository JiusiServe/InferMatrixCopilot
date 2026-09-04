---
title: "HunyuanImage3"
created: 2026-07-10
updated: 2026-09-05
type: index
tags: [vllm-omni, models, hunyuan-image3]
sources: ["PR #5541", "PR #6563", "PR #4048", vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py, vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py, vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_tokenizer.py, vllm_omni/diffusion/models/hunyuan_image3/request_layout.py]
---

# HunyuanImage3

- 常见别名：`HunyuanImage3`、`hunyuan_image3`
- 适用范围：HunyuanImage3 的模型结构、配置、checkpoint、对齐和专有流程

## 什么时候查这里

- 问题只属于 HunyuanImage3，而不是多个模型共用的代码模块。

## 不放什么

- 多模型共享的 diffusion、serving 或 model-executor 机制。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 修改公开入口、prompt、AR→DiT、`model_extras`、shared task examples、条件图、size 或 seed | [开发快速入口和 rules](rules.md#direct-开发快速入口) |
| Scheduler-managed paged KV、prepared layout、CFG logical prefix、Hunyuan Q/K/V spans 或空 hash 边界 | [shared paged KV control plane](../../components/diffusion/paged-kv-control-plane.md) |
| 理解模型和 vLLM-Omni 代码地图 | [architecture](architecture.md) |
| HF 接入常见偏差 | [HF alignment pitfalls](hf-alignment-pitfalls.md) |
| 运行 HF baseline | [HF baseline runbook](hf-baseline-runbook.md) |
| 对齐 HF 与 Omni 输出 | [HF/Omni alignment method](hf-omni-alignment-method.md) |
| 调查 img-to-img 差距 | [it2i gap](it2i-gap.md) |
| 核对官方 prompt 格式 | [official prompt format](official-prompt-format.md) |
| 运行 image generation demo | [run image-gen demo](run-image-gen-demo.md) |
| 调查模型专有错误 | [incidents](incidents/_index.md) |
| 查询已结束的历史分析 | [history](history/_index.md) |
