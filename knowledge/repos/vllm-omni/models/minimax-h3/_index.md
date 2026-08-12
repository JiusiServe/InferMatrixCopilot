---
title: "MiniMax H3"
created: 2026-08-04
updated: 2026-08-04
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #5691", "PR #5699", "PR #5709", vllm_omni/diffusion/models/minimax_h3/]
confidence: high
---

# MiniMax H3

## 名称与范围

- 正式 owner：`MiniMaxH3Pipeline` / `MiniMaxAI/MiniMax-H3`。
- checkpoint 分区：`FL2VA` 服务 T2VA/FL2VA；`Ref2VA` 服务 image+audio 或
  multi-video Ref2VA。
- 主要源码：`vllm_omni/diffusion/models/minimax_h3/`；注册入口在
  `vllm_omni/diffusion/registry.py`。
- 共享依赖：[Diffusion rules](../../components/diffusion/rules.md)、
  [Serving rules](../../components/serving/rules.md) 和 [CI rules](../../ci/rules.md)。

## 什么时候查这里

- 修改 H3 task/reference matrix、frame/audio/latent shape、text-encoder TP、专有 loader、
  reference audio fallback 或 joint video/audio accuracy oracle。
- 问题属于共享 attention backend、HTTP artifact 生命周期或 CI 选择器时，回到上面的
  component owner，不把共享合同复制到模型页。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| task/conditioning、数值 shape、并行 topology、权重加载、音频 fallback 或 accuracy evidence | [MiniMax H3 规则](rules.md) |
