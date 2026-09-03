---
title: "MiniMax Music3"
created: 2026-09-04
updated: 2026-09-04
type: index
tags: [vllm-omni, models, serving]
sources: [vllm_omni/model_executor/models/minimax_music3/, vllm_omni/deploy/minimax_music3.yaml, vllm_omni/deploy/minimax_music3_2gpu.yaml, vllm_omni/entrypoints/openai/tts_adapters/minimax_music3.py, vllm_omni/model_executor/stage_input_processors/minimax_music3.py, vllm_omni/transformers_utils/configs/minimax_music3.py]
confidence: high
---

# MiniMax Music3

## 正式名称与别名

- 知识树 owner：`models/minimax-music3`；上游目录 `minimax_music3`。
- pipeline registry key：`minimax_music3`（`vllm_omni/config/pipeline_registry.py`）。

## 源码路径

共 15 个文件：

- `vllm_omni/model_executor/models/minimax_music3/`
- `vllm_omni/deploy/minimax_music3.yaml`
- `vllm_omni/deploy/minimax_music3_2gpu.yaml`
- `vllm_omni/entrypoints/openai/tts_adapters/minimax_music3.py`
- `vllm_omni/model_executor/stage_input_processors/minimax_music3.py`
- `vllm_omni/transformers_utils/configs/minimax_music3.py`

## 依赖的共享代码模块

- `vllm_omni/model_executor/models/` → [model-executor](../../components/model-executor/_index.md)
- `vllm_omni/config/stage_config/` → [configuration](../../components/configuration/_index.md)

## checkpoint、尺寸与量化

- `minimax_music3.yaml`：MiniMax-Music3 deploy: Stage 0 (AR talker) -> Stage 1 (acoustic decoder), both on one 140 GB card, streaming 200-frame windows over shared memory. 配置：`pipeline: minimax_music3`；`async_chunk: true`。
- `minimax_music3_2gpu.yaml`：MiniMax-Music3 two-GPU layout: AR talker on device 0, acoustic decoder on device 1. Splitting the stages removes the memory-budget compromise of the single-card 配置：`pipeline: minimax_music3`；`async_chunk: true`。

## 什么时候查这里

只查 MiniMax Music3 专有的行为、常量、注册入口和验证合同。

## 不放什么

上面列出的共享模块的执行、调度、加载或 serving 合同属于
[components](../../components/_index.md)，这里只链接不复制；registry 快照和别名
清单见 [模型 catalog](../catalog.md)；一次性历史默认不落盘。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 该模型的硬门禁规则 | 尚未沉淀；由逐 commit 同步命中该 owner 时在 `rules.md` 建立 |
