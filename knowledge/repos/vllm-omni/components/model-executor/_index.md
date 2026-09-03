---
title: "Model Executor"
created: 2026-07-10
updated: 2026-09-04
type: index
tags: [vllm-omni, components, model-executor]
sources: []
---

# Model Executor

- 源码入口：`vllm_omni/model_executor/`（layers、model_loader、models、stage_input_processors）、
  `vllm_omni/model_extras/`（模型专有请求/prompt 转换）、`vllm_omni/worker/`（gpu_*_worker、
  gpu_*_model_runner、mixins）、`vllm_omni/inputs/`（runner 输入预处理）和设备平台层
  `vllm_omni/platforms/<cuda|musa|npu|rocm|xpu>/`
- 源码校验：以上路径均已在 `main @ 596c16a5` 验证存在；stage 配置已经迁移到
  `vllm_omni/deploy/`，NPU/XPU 等平台可继续拥有自己的 worker 覆盖
- 测试入口：共享 runner 行为看 `tests/worker/`，具体模型 consumer 看 `tests/model_executor/`
- 主要职责：AR/LLM stage、stage 配置、并行与设备启动、runner 到模型的输入预处理合同和跨阶段数据桥接

## 什么时候查这里

- 调查模型执行 stage、stage config、并行度、设备映射或 worker 启动。
- 修改 runner `preprocess`、`_omni_*` 逐行 metadata、`talker_mtp`、chunked-prefill phase 或共享输入处理合同。
- 调查 AR 到 diffusion 的共享桥接。

## 不放什么

- diffusion denoise loop 的共享实现。
- 某个模型独有的 prompt、checkpoint 或 attention 逻辑。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解共享职责和阶段边界 | [architecture](architecture.md) |
| 根据 PR 描述直达 stage config、runner preprocess、stage runtime、bridge/batch 或 loader 的规则组与第一批源码 | [rules 与代码地图](rules.md) |

| runtime info、跨 stage payload、batch 与 request RNG 合同 | [跨 stage bridge 与 batch 合同](rules-bridge-batch.md) |