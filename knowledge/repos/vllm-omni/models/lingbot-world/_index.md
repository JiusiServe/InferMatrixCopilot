---
title: "LingBot World"
created: 2026-09-04
updated: 2026-09-04
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/lingbot_world/]
confidence: high
---

# LingBot World

## 正式名称与别名

- 知识树 owner：`models/lingbot-world`；上游目录 `lingbot_world`。
- registry 登记的 architecture / stage key：`LingBotWorldCausalDMDPipeline`。

## 源码路径

共 5 个文件：

- `vllm_omni/diffusion/models/lingbot_world/`

## 依赖的共享代码模块

- `vllm_omni/experimental/ar_diffusion/` → 无对应 component owner
- `vllm_omni/diffusion/models/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/distributed/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/model_loader/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/layers/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/data/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/forward_context/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/profiler/` → [diffusion](../../components/diffusion/_index.md)

## checkpoint、尺寸与量化

- 上游没有 deploy 预设。pipeline 模块自述：Request-scoped LingBot-World v2 causal DMD pipeline.

## 什么时候查这里

只查 LingBot World 专有的行为、常量、注册入口和验证合同。

## 不放什么

上面列出的共享模块的执行、调度、加载或 serving 合同属于
[components](../../components/_index.md)，这里只链接不复制；registry 快照和别名
清单见 [模型 catalog](../catalog.md)；一次性历史默认不落盘。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 该模型的硬门禁规则 | 尚未沉淀；由逐 commit 同步命中该 owner 时在 `rules.md` 建立 |
