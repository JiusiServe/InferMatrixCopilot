---
title: "LTX-2.5 DiffVAE 规则"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, ltx2, diffusion]
sources: ["PR #6189", "PR #7000", recipes/LTX/LTX-2.5.md, vllm_omni/diffusion/models/ltx2/ltx2_components.py, vllm_omni/diffusion/models/ltx2/ltx2_conditioning.py, vllm_omni/diffusion/models/ltx2/ltx2_diffusion_decoder.py, vllm_omni/diffusion/models/ltx2/ltx2_diffusion_decoder_distributed.py, vllm_omni/diffusion/models/ltx2/ltx2_latents.py, vllm_omni/diffusion/models/ltx2/ltx2_request.py, vllm_omni/diffusion/models/ltx2/ltx2_runtime.py, tests/diffusion/models/ltx2/test_ltx2_output_cuda.py, tests/diffusion/models/ltx2/test_ltx2_pipeline.py, tests/diffusion/models/ltx2/test_ltx2_vae.py]
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

### LTX-3 — LTX decoded-video transport 必须在设备端量化且保持 presentation 与 profiler 边界

- 触发：修改 LTX-2/2.3/2.5 decoded-video finalization、`output_type="np"`、worker/IPC transport，或
  LTX diffusion-pipeline profiler wrapping。
- 强制：fast path 只接受 floating-point RGB `BCTHW` decoded video；detach 后仅当
  `video_processor.config.do_normalize` 为真时在 decoder output dtype 中 denormalize，始终 defensive
  clamp 到 `[0, 1]`，再在该 dtype 中 scale/round 并直接转为 contiguous `uint8` `BTHWC`，随后由既有
  post-process boundary 一次 `detach().cpu().numpy()` 交付。该 boundary 只接受 contiguous RGB `BTHWC`
  uint8；非 `np` output type 继续走 `VideoProcessor.postprocess_video`。profiler targets 必须同时覆盖
  `video_processor.postprocess_video` 与 `_prepare_video_output_for_transport`；I2V 替换 video processor 后，
  profiler 启用时必须重新 wrap 前者。
- 禁止：为量化 materialize 全帧 `.float()` CUDA temporary、改变 latent/generation，或让 non-`np` output
  走 uint8 fast path；不得把 `do_normalize=False` 的 out-of-range clamp 当作 legacy parity，或把 H200
  的精确 shape/配置性能结果、LTX similarity matrix 外推为一般硬件、吞吐或兼容性结论。
- 验收：CPU 覆盖 dtype/normalization、shape/dtype/contiguity、无效 BCTHW/RGB/floating contract 与 profiler
  rewrap；CUDA 覆盖 BF16/FP16、normalize true/false 的 device-side contiguous BTHWC uint8 和一次 D2H
  对比。有效 `[0, 1]` 的 `do_normalize=False` 输入须与 unclipped legacy path 比较；另测 intentional
  out-of-range defensive clamp。FP32 presentation bytes 必须 exact，BF16/FP16 相对 legacy FP32
  presentation 最多相差一个 uint8 level；官方 similarity 仅是本 PR 所报 LTX matrix 的限定证据。^[PR #7000]
