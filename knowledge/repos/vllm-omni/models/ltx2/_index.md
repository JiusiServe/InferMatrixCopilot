---
title: "LTX-2 家族（含 LTX-2.3）"
created: 2026-07-16
updated: 2026-08-05
type: index
tags: [vllm-omni, models, ltx2]
sources: [vllm_omni/diffusion/models/ltx2/, vllm_omni/diffusion/registry.py, recipes/LTX/LTX-2.md]
---

# LTX-2 家族（含 LTX-2.3）

- 常见别名：`LTX-2`、`LTX-2.3`、`ltx2`（LTX-2.3 是同一源码模块下的新 checkpoint/
  版本，按 checkpoint 别名规则共用本目录）
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

- 问题只属于 LTX-2/2.3（pipeline、分辨率/帧数语义、graph 模式、性能基线）。

## 不放什么

- 多模型共享的 diffusion 执行机制（放 components/diffusion）。
- 通用 benchmark 方法（放 `general/benchmark/`）。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 模型结构、serving 方式与已有性能/精度证据 | [architecture](architecture.md) |
