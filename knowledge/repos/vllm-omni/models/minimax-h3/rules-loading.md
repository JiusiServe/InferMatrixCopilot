---
title: "MiniMax H3 加载规则"
created: 2026-09-02
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5706", "PR #5737", "PR #5824", vllm_omni/diffusion/models/minimax_h3/encoder.py, vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py]
confidence: high
---

# MiniMax H3 加载规则

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

NPU INT8 online 同样复用 component-relative prefix 与 active loader：BF16 checkpoint 在逐层
load 完成时 dynamic quantize，text encoder、VAE 和非 eligible projection 保持未量化；
`ignored_layers` 必须能用 fused owner 名（如 `blocks.0.attn.qkv_proj`）精确跳过。NPU
`QuantBatchMatmulV3` 的 65535 output 限制只按 per-partition width 判断，超限 layer 回退
`UnquantizedLinearMethod`，更高 TP 可能让同一层重新满足 INT8。^[PR #5706]

## MMH3-1f — text encoder eager load 必须证明每个 source shard 完整

- 触发：修改 H3 Qwen3-VL text encoder 的 checkpoint 映射、QKV/gate-up fused loader、保留层
  集合，或 pipeline 对 eager component 的 loaded-name 上报。
- 强制：按实际 fused module 预置 expected source 集合，并按 shard id 分别记录 q/k/v 与
  gate/up；缺单个 source、整组零 source 或任何 plain retained parameter 都在启动时
  `RuntimeError`。pipeline 只有在 encoder 自身完成此验证后，才可把其全部 parameter 上报给
  runner strict check；额外 unknown checkpoint key 可告警跳过，因为不会留下 model parameter
  未初始化。
- 禁止：任一 source 命中后用 fused target name 宣称完整；只 warning 后保留 `torch.empty`
  行继续执行；把 encoder 的完整性保证外推给同样 eager 构造、但尚无等价验证的 video/audio VAE。
- 验收：distinct sentinel 数值逐段核对 q/k/v（含 GQA 非等宽）与 gate/up 行布局；分别覆盖每个
  source 缺失、整组缺失和 plain parameter 缺失。真实 checkpoint 的 index/name coverage 可证明
  映射覆盖，但未执行真实完整加载时，不能声称 shape/dtype/full-load 已回归；本改动本身
  未改变 shape/dtype handling。共享 fused-loader 门禁见
  [EXEC-2b](../../components/model-executor/rules-loader-contract.md#exec-2b-fused-shard-必须按-source-完整性与布局数值闭环)。^[PR #5824]
