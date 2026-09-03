---
title: "FLUX.2 规则"
created: 2026-07-20
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #4645", "PR #5136", vllm_omni/diffusion/models/flux2/flux2_transformer.py, "PR #5910"]
confidence: high
---

# FLUX.2 规则

只有 `FLUX2-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| FLUX.2 pipeline/transformer | FLUX2-1b | `diffusion/registry.py::_DIFFUSION_MODELS["Flux2Pipeline"]` → `diffusion/models/flux2/pipeline_flux2.py::Flux2Pipeline`、`flux2_transformer.py::Flux2Transformer2DModel` |
| Mistral text encoder、FP8、component namespace | FLUX2-1a | `diffusion/models/mistral_encoder/` → component quantization selector/loader |
| meta parameter、CPU offload、BF16 baseline | FLUX2-1b | FLUX.2 component loader/materialization 路径 → `Flux2Pipeline` |
| SP auto-padding、`mask_sp_padding`、dense/varlen | [SPPAD-1a](../../components/diffusion/rules-sp-padding.md#sppad-1a-padding-mask-是显式正确性性能策略不是无损优化) | Flux2 `_sp_plan` → forward context → `hidden_states_mask` → attention |

FLUX.1 和 FLUX.2-Klein 不自动归到本页；必须由描述/registry key 明确命中对应 owner。

## FLUX2-1a — Mistral text encoder FP8 保留 component namespace

- 触发：为 FLUX.2 Mistral text encoder 增加或修改在线量化。
- 强制：`text_encoder` 量化配置独立于 transformer/VAE 解析，完整
  `text_encoder.language_model...` 前缀一路到 component selector；只向 attention/MLP
  的 weight-bearing linear 传量化配置。
- 禁止：量化 embedding 或 LM head；裁掉 `text_encoder` 前缀后再匹配；因为 transformer
  未量化就把 text encoder 配置清空。
- 验收：text-encoder-only FP8 下 transformer/VAE 保持 BF16，目标 linear 被量化，
  embedding/head 未量化，TP 构造与加载均通过。 ^[PR #5136]

## FLUX2-1b — meta 初始化与 CPU offload 分别守住加载和资源边界

- 触发：FP8 参数从 meta device 初始化，或单卡加载保留 BF16 transformer。
- 强制：未物化参数不得提前 `.to(cuda)`；CPU offload 作为避免瞬时/峰值 OOM 的资源
  前提，在 baseline/candidate 对称启用并在质量 case 旁说明。
- 禁止：把 offload 当成 FP8 质量收益；用不同 step 数或加载条件验证测试阈值。
- 验收：meta parameter 完成量化物化后再迁移；运行与测试完全一致的 10-step case，
  LPIPS 阈值由该 case 直接产生。 ^[PR #5136]

共享 component-quantization 合同见 [Diffusion rules](../../components/diffusion/rules.md)；
加载器 upstream 边界见 [loading drift](../../rebase/upstream-api-drift-loading.md)。
