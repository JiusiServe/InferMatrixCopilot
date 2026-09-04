---
title: "LTX-2 家族（含 LTX-2.3/2.5）"
created: 2026-07-16
updated: 2026-09-04
type: index
tags: [vllm-omni, models, ltx2]
sources: [vllm_omni/diffusion/models/ltx2/, vllm_omni/diffusion/registry.py, recipes/LTX/LTX-2.md, recipes/LTX/LTX-2.5.md]
---

# LTX-2 家族（含 LTX-2.3/2.5）

- 常见别名：`LTX-2`、`LTX-2.3`、`LTX-2.5`、`ltx2`；这些 checkpoint 版本共用同一
  源码模块，但 LTX-2.5 的视频 decode 默认使用 DiffVAE。
- 厂商/模型：Lightricks；22B 参数文本→视频+音频生成（T2V/I2V，48kHz 同步音频，
  768x512 可达 20+ 秒）；Diffusers 格式 checkpoint `dg845/LTX-2.3-Diffusers`
- 源码：`vllm_omni/diffusion/models/ltx2/`（纯 diffusion，无 AR stage）
- registry：`LTX2Pipeline` 统一 LTX-2/LTX-2.3 的 one-stage T2V/I2V；
  `LTX2DistilledPipeline` 统一 distilled two-stage T2V/I2V；DMD2 仍由
  `LTX2T2VDMD2Pipeline`/`LTX2I2VDMD2Pipeline` 提供。旧的 LTX23、ImageToVideo 和
  TwoStages registry names 已删除，没有兼容 alias。
- 官方 recipe 已合并为 `recipes/LTX/LTX-2.md`；已删除的
  `recipes/LTX/LTX-2.3.md` 不能继续作为 source 或事实依据。
- 依赖共享 [Diffusion 组件](../../components/diffusion/_index.md)

## 什么时候查这里

- 问题只属于 LTX-2/2.3/2.5（pipeline、decoder、分辨率/帧数语义、graph 模式、性能基线）。

## 不放什么

- 多模型共享的 diffusion 执行机制（放 components/diffusion）。
- 通用 benchmark 方法（放 `general/benchmark/`）。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 模型结构、serving 方式与已有性能/精度证据 | [architecture](architecture.md) |
| LTX-2.5 DiffVAE 选择、artifact、并行或最小几何约束 | [LTX-2.5 decoder rules](rules.md) |
