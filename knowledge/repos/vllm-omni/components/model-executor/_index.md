# Model Executor

- 源码入口：`vllm_omni/model_executor/`、`vllm_omni/worker/` 和平台专属 `vllm_omni/platforms/*/worker/`
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
| 修改 runner 预处理合同、逐行 phase、MTP 路由、stage 并行度、设备映射或启动校验 | [rules](rules.md) |
