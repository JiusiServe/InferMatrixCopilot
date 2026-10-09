---
title: "LingBot World"
created: 2026-09-04
updated: 2026-10-09
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

固定源码版本的模型目录有 7 个文件：`__init__.py`、`pipeline.py`、
`transformer.py`、`dmd_block.py`、`camera.py`、`actions.py` 与 `utils.py`。
分别从 pipeline 的请求/stepwise 入口、DMD block runner 和 camera/action 解析开始核对。

## 依赖的共享代码模块

- `vllm_omni/experimental/ar_diffusion/` → [AR 分页几何](../../components/diffusion/rules-ar-paging-geometry.md)、[系统运行时](../../components/diffusion/rules-system-runtime.md) 与 [tick/事件提交](../../components/model-executor/rules-bridge-batch.md)
- `vllm_omni/diffusion/models/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/distributed/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/model_loader/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/layers/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/data/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/forward_context/` → [diffusion](../../components/diffusion/_index.md)
- `vllm_omni/diffusion/profiler/` → [diffusion](../../components/diffusion/_index.md)

## checkpoint、尺寸与量化

- checkpoint：`robbyant/lingbot-world-v2-14b-causal-fast-diffusers`；registry key 为 `LingBotWorldCausalDMDPipeline`。
- stepwise serving 显式选择 `vllm_omni/deploy/lingbot_world_v2_stepwise.yaml`；模型没有自动选用的默认 deploy config。
- 新补内容按 [固定源码版本 9cf443a7bb24d6b8007981311466d769ec13b3d8](https://github.com/vllm-project/vllm-omni/tree/9cf443a7bb24d6b8007981311466d769ec13b3d8/vllm_omni/diffusion/models/lingbot_world) 核对；不改变仓库级 release baseline。

## 什么时候查这里

只查 LingBot World 专有的行为、常量、注册入口和验证合同。

## 不放什么

上面列出的共享模块的执行、调度、加载或 serving 合同属于
[components](../../components/_index.md)，这里只链接不复制；registry 快照和别名
清单见 [模型 catalog](../catalog.md)；一次性历史默认不落盘。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| checkpoint 固定形状、首图/文本/camera 数据流、DMD 与模型/共享 owner 边界 | [架构](architecture.md) |
| offline、stepwise/WebSocket、SE3 controls、配置、FP8 与 realtime 验证口径 | [运行与验证](execution-validation.md) |
| 该模型的硬门禁规则 | [模型规则](rules.md)：session VAE decode、condition history 与模型专有合同 |
| paged KV 容量、K/V 独立存储、单 request stepwise rollout 与 warmup | [系统运行时](../../components/diffusion/rules-system-runtime.md)：`DIFF-4o`、`DIFF-4aa`、`DIFF-4ab`、`DIFF-4ad` |
| kernel 合法 page、ragged sink/recent window、scratch 与固定 block-table width | [AR 分页几何](../../components/diffusion/rules-ar-paging-geometry.md)：`DIFF-15a`–`DIFF-15c` |
| deprecated tick 的 session/event/request identity、失败与提交 | [跨 stage bridge](../../components/model-executor/rules-bridge-batch.md)：`EXEC-1l` |
