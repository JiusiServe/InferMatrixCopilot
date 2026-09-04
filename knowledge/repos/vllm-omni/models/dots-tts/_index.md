---
title: "dots.tts"
created: 2026-09-04
updated: 2026-09-05
type: index
tags: [vllm-omni, models, serving]
sources: ["PR #6174", vllm_omni/model_executor/models/dots_tts/, vllm_omni/deploy/dots_tts.yaml, vllm_omni/transformers_utils/configs/dots_tts.py, tests/e2e/offline_inference/test_dots_tts_expansion.py]
confidence: high
---

# dots.tts

## 正式名称与别名

- 知识树 owner：`models/dots-tts`；上游目录 `dots_tts`。
- pipeline registry key：`dots_tts`（`vllm_omni/config/pipeline_registry.py`）。
- registry 登记的 architecture / stage key：`dots_tts_talker`。

## 源码路径

共 8 个文件：

- `vllm_omni/model_executor/models/dots_tts/`
- `vllm_omni/deploy/dots_tts.yaml`
- `vllm_omni/transformers_utils/configs/dots_tts.py`

## 依赖的共享代码模块

- `vllm_omni/model_executor/models/` → [model-executor](../../components/model-executor/_index.md)
- `vllm_omni/config/stage_config/` → [configuration](../../components/configuration/_index.md)

## checkpoint、尺寸与量化

- `dots_tts.yaml`：dots.tts deployment config (single-stage AR talker). Conservative first-integration settings: eager execution, no CUDA Graphs, no batched side-path optimizations yet — see voxcpm2.yaml for 配置：`async_chunk: false`；`dtype: bfloat16`。

## 什么时候查这里

只查 dots.tts 专有的行为、常量、注册入口和验证合同。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| weekly offline E2E scaffold、prompt/queue/noise oracle | [rules](rules.md) |

## 不放什么

上面列出的共享模块的执行、调度、加载或 serving 合同属于
[components](../../components/_index.md)，这里只链接不复制；registry 快照和别名
清单见 [模型 catalog](../catalog.md)；一次性历史默认不落盘。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 该模型的硬门禁规则 | 尚未沉淀；由逐 commit 同步命中该 owner 时在 `rules.md` 建立 |
