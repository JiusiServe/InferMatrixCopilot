---
title: "MiniMax H3 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5737", vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization_quality.py, recipes/MiniMaxAI/MiniMax-H3.md]
confidence: high
---

# MiniMax H3 规则

只有 `MMH3-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| online FP8、`ignored_layers`、component prefix | `MMH3-1a` | `pipeline_minimax_h3.py::_resolve_component_quant_config` → `MiniMaxH3DiTModel` linear prefix |
| grouped QKV、fused MLP、weight loader、TP | `MMH3-1a` | `minimax_h3_transformer.py::MiniMaxH3DiTModel.load_weights` → active vLLM loader |
| FP8 quality、audio metric、layerwise offload | `MMH3-1b` | quantization quality test → recipe/support matrix → nightly lane |

## MMH3-1a — component namespace 与 checkpoint transform 必须在 active loader 前闭合

- 触发：修改 H3 online FP8 覆盖范围、`ignored_layers`、linear prefix、QKV/MLP checkpoint
  变换或 TP loader。
- 强制：pipeline 先把 structured quantization config 解析到 `transformer` component，再构造
  DiT；因此内部 prefix 是 `blocks.*`、`token_refiner.*` 等 component-relative 名称，不带
  `transformer.`。每个 eligible linear 显式传 prefix/quant config，patch、timestep、final
  projection 显式保持非量化。grouped-QKV reorder 与 fused `fc1` gate/up split 在
  `MiniMaxH3DiTModel.load_weights()` 先完成，再调用当前 parameter 的 active weight loader，
  让 TP shard 与 FP8 `online_process_loader` 看到最终布局。
- 禁止：用 parent prefix 代替 exact leaf `ignored_layers`；一边已 resolve component、一边仍
  要求 `transformer.`；在 linear 构造后包掉 active loader，或把 reorder/split 放到 FP8
  wrapper 之后。
- 验收：枚举默认 quantized/full-precision prefix 集合，逐个验证 exact ignored leaf；QKV
  与 gate/up sentinel 断言传给 active loader 的顺序和 shard id，至少覆盖 TP 与 online FP8。
  ^[PR #5737]

## MMH3-1b — joint video/audio quality 与 offload 兼容性必须一起验收

- 触发：改变 H3 FP8 layer scope、kernel/loader、quality threshold、offload 或 nightly lane。
- 强制：H3 online FP8 与 layerwise offload 当前标为 incompatible；resident FP8 可与 TP、VAE
  tiling 组合。BF16/FP8 A/B 使用同一 immutable checkpoint、prompt、seed、size、frames、
  steps 与并行/资源设置；joint output 同时检查 video LPIPS 和 32 kHz audio 的 spectral
  cosine/RMS ratio。PSNR、MAE 与 peak memory 是 report-only 指标，不能冒充 gate。
- 禁止：只验视频就宣称 H3 joint-output quality；把一次 22% memory observation 写成稳定
  上界；让 FP8+layerwise offload 到 Cutlass kernel 才因 flattened-weight stride 失败。
- 验收：当前 2x H100 case 的 gates 是 LPIPS <= 0.20、audio spectral cosine >= 0.80、
  RMS ratio 在 0.50–2.00，且 sample rate 为 32000；单测还要证明 phase-tolerant metric
  接受相移但拒绝 spectral drift。 ^[PR #5737]

共享 component quantization、checkpoint mapping 与 quality evidence 见
[Diffusion rules](../../components/diffusion/rules.md)。
