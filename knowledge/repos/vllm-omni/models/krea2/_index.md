---
title: "Krea 2"
created: 2026-07-20
updated: 2026-07-20
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #4730", vllm_omni/diffusion/models/krea2/]
confidence: high
---

# Krea 2

## 名称与范围

- 模型目录：`vllm_omni/diffusion/models/krea2/`。
- 主要实现：`pipeline_krea2.py`、`krea2_transformer.py`；注册在
  `vllm_omni/diffusion/registry.py`。
- 共享依赖：[Diffusion component](../../components/diffusion/_index.md) 的 loader、cache、
  worker 与 serving bridge。

## 配置、checkpoint 与流程

Krea 2 pipeline 从 checkpoint 的 `model_index.json` 与 `vae/config.json` 得到组件和
scale 配置，加载 text encoder、VAE、tokenizer、scheduler 与 transformer。text encoder
和 VAE 必须使用统一目标 dtype；只需要 VAE config 时必须精确获取文件，不能下载整套
权重。当前 loader 预期可直接加载的 Diffusers layout；raw/upstream checkpoint 是否可用
必须单独验证。

请求经 text encoder 形成多层 hidden-state stack，进入 transformer denoise，再由 VAE
decode 输出图像。模型专有门禁见 [rules](rules.md)；公开入口矩阵见
[model adaptation guardrails](../../review/guides/model-adaptation-guardrails.md)。

## 什么时候查这里

- 审查 Krea 2 loader dtype、config-only fetch、offline/online 或 capability claim。
- 共享 checkpoint/parallel 问题转到 [Diffusion rules](../../components/diffusion/rules.md)。
