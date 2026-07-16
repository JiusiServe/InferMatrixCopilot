# Diffusion

- 源码入口：`vllm_omni/diffusion/`
- 主要职责：多个 diffusion 模型共用的 pipeline、执行循环、scheduler 接入和运行机制

## 什么时候查这里

- 根因位于共享 diffusion 代码，可能影响多个模型。
- 调查 denoise loop、diffusion runner、scheduler 或共享 attention 执行机制。

## 不放什么

- HunyuanImage3 独有 pipeline、配置和 checkpoint 问题；这些放模型目录。
- 通用 benchmark 方法；这些放 `framework/benchmark/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解共享职责和数据流 | [architecture](architecture.md) |
