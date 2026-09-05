---
title: "LongCat-Image 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #6222", vllm_omni/diffusion/models/longcat_image/pipeline_longcat_image_edit.py, tests/model_tests/diffusion/model_settings.py, tests/model_tests/diffusion/test_alignment.py]
confidence: high
---

# LongCat-Image 规则

## Direct 代码快速入口

| PR 描述信号 | 规则 |
|---|---|
| Edit request geometry、conditioning resize、latent/decode propagation | `LONGCAT-1a` |

只有 `LONGCAT-数字字母` 是可审计规则 ID。

## LONGCAT-1a — Edit 请求几何必须单一解析并端到端传播

- 触发：修改 `LongCatImageEditPipeline` 的 sampling `height`/`width`、conditioning
  preprocess、latent preparation 或 decode geometry。
- 强制：先解析一对 request geometry（显式 sampling override 优先，否则按输入图像
  aspect ratio 的默认面积计算），以 `vae_scale_factor * 2` 做 minimum-aligned
  normalization，并将该同一对尺寸写回 sampling params、用于 conditioning image 与
  half-size prompt image resize、`check_inputs`、latent/position-ID preparation 和 decode。
- 禁止：在 override 已解析后继续把 source-derived `calculated_height`/`calculated_width`
  传给 conditioning 或 generation；不要把 LongCat Edit 当作可让 conditioning 与 noise
  latents 使用不同空间 geometry 的编辑 pipeline。
- 验收：以非正方形 source 与显式目标尺寸运行 I2I，断言 aligned resolved H/W 同时到达
  preprocess、condition/noise latent packing 和输出；再覆盖未设 override 的 source-AR
  default，以及不会归零的极小或非对齐尺寸。当前 common tiny case 的 source/target 都是
  512×512，只证明旧的 1MP override 失效会被抓到；它没有覆盖非正方形或非对齐 override。
  TeaCache 与 SP+Cache-DiT 也属于不同 acceleration group，不能据此声称 TeaCache+SP 已验证。
  ^[PR #6222]

共享 diffusion request/latent 生命周期见
[Diffusion rules](../../components/diffusion/rules.md)，模型结构入口见
[LongCat-Image index](_index.md)。
