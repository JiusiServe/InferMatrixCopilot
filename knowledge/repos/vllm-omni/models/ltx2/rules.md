---
title: "LTX-2.5 DiffVAE 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, ltx2, diffusion]
sources: ["PR #6189", recipes/LTX/LTX-2.5.md, vllm_omni/diffusion/models/ltx2/ltx2_components.py, vllm_omni/diffusion/models/ltx2/ltx2_diffusion_decoder.py, vllm_omni/diffusion/models/ltx2/ltx2_diffusion_decoder_distributed.py, vllm_omni/diffusion/models/ltx2/ltx2_latents.py, vllm_omni/diffusion/models/ltx2/ltx2_request.py, vllm_omni/diffusion/models/ltx2/ltx2_runtime.py, tests/diffusion/models/ltx2/test_ltx2_vae.py]
confidence: high
---

# LTX-2.5 DiffVAE 规则

### LTX25-1 — LTX-2.5 的 decoder、统计量与 artifact 必须作为同一版本化合同维护

- 触发：修改 LTX-2.5 full/distilled one- or two-stage pipeline 的视频 decoder、`ltx2_use_conv_vae`、
  latent normalization、Native sidecar 或 component residency。
- 强制：LTX-2.5 默认构造 canonical Native DiffVAE；仅布尔 `ltx2_use_conv_vae=true` 可在启动时
  opt into ConvVAE，I2V encoding 仍使用 ConvVAE。provided latent 的 normalize 与 decode 前的
  denormalize 必须从实际视频 decoder 取得 mean、std 和 scaling factor。Native decoder 与独立
  sidecar 先查 model root；Hub fallback 使用 artifact repository 自己的 pinned revision，不能把
  Diffusers model revision 跨仓库复用。DiffVAE 初始化必须要求 runtime `kernels==0.14.1`、支持的
  NATTEN Hub kernel 和可操作的失败说明。
- 禁止：让 ConvVAE statistics 处理 DiffVAE latent；将非布尔 opt-in 静默转换；把 local primary model
  path 误当成独立 sidecar 必须离线；使用未 pin 的 canonical Native artifact，或向用户建议不存在的
  production FlexAttention fallback。
- 验收：覆盖 full/distilled profile 的默认和 ConvVAE opt-in、非布尔拒绝、Native decoder strict
  conversion、active-decoder statistics、local-first/repository-scoped revision routing，以及缺少 NATTEN
  runtime prerequisite 的 actionable error。^[PR #6189]

### LTX25-2 — DiffVAE 请求边界与分布式 decode 必须显式 fail-closed

- 触发：修改 LTX-2.5 decode、`vae_parallel_mode`、tiling、request resolution validation 或 request RNG。
- 强制：DiffVAE request validation 从首个 decoder-stage kernel 推导最小 latent H/W，并在 denoising 前
  拒绝不足的 geometry；ConvVAE opt-in 保留其原有边界。分布式 DiffVAE 只接受 `vae_parallel_mode='tile'`。
  stages 1–3 在所有参与 rank 上处理完整 low-resolution feature volume，只有 stage 4 与 diffusion
  stage 作为 overlapping tile task 分发，rank 0 按 serial reference 顺序 blend/merge。tile split 必须使
  每个 rank 从 rank-0 generator state 出发，并保持与 serial tiled decode 相同的 noise-consumption
  order；只有 active decoder 确认 collective decode 时非输出 rank 才参与。
- 禁止：让不足 geometry 在 NATTEN/decode 中变成 HTTP 500；静默接受 height/width shard mode；按 rank
  placement 改变固定 seed 的 tile noise，或用 ConvVAE 的 distributed-state 判定 DiffVAE collective。
- 验收：覆盖 early geometry rejection 与 ConvVAE control、tile positive/non-tile negative modes、serial
  RNG-order parity，以及 output/non-output rank 在 collective/non-collective decode 的分支。^[PR #6189]
