---
title: "Pi0"
created: 2026-09-04
updated: 2026-09-04
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/pi0/, vllm_omni/deploy/pi0.yaml]
confidence: high
---

# Pi0

## 正式名称与别名

- 知识树 owner：`models/pi0`；上游目录 `pi0`。
- pipeline registry key：`pi0`（`vllm_omni/config/pipeline_registry.py`）。
- registry 登记的 architecture / stage key：`Pi0Pipeline`。

## 源码路径

共 5 个文件：

- `vllm_omni/diffusion/models/pi0/`
- `vllm_omni/deploy/pi0.yaml`

## 依赖的共享代码模块

- `vllm_omni/diffusion/data/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/request/` → [diffusion](../../components/diffusion/_index.md)

## checkpoint、尺寸与量化

- `pi0.yaml`：π0 (Pi-Zero) VLA deploy: single diffusion stage. Topology (PI0_PIPELINE) is declared in vllm_omni/diffusion/models/pi0/pipeline_pi0.py. 配置：`pipeline: pi0`；`async_chunk: false`；`dtype: float32`。

## 什么时候查这里

只查 Pi0 专有的行为、常量、注册入口和验证合同。

## 不放什么

上面列出的共享模块的执行、调度、加载或 serving 合同属于
[components](../../components/_index.md)，这里只链接不复制；registry 快照和别名
清单见 [模型 catalog](../catalog.md)；一次性历史默认不落盘。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 该模型的硬门禁规则 | 尚未沉淀；由逐 commit 同步命中该 owner 时在 `rules.md` 建立 |

| 遇到 Pi0 专有的观测预处理、flow-matching、attention、动作输出或 OpenPI parity 问题 | [Pi0 硬门禁规则](rules.md) |