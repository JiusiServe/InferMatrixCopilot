---
title: "MiniMax H3 encoder state rules"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #6710", vllm_omni/diffusion/models/minimax_h3/encoder.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/vae.py, tests/diffusion/models/minimax_h3/test_minimax_h3_encoder_sdpa.py]
confidence: high
---

# MiniMax H3 encoder state rules

## MMH3-1n — Qwen3-VL encoder 的 cuDNN SDPA override 必须恢复原状态

- 触发：修改 `MiniMaxH3Qwen3VLEncoder.encode_ids`、cuDNN SDPA backend flag、text-encoder TP，或 text-encoder→VAE 的执行边界。
- 强制：本提交已捕获 `torch.backends.cuda.cudnn_sdp_enabled()` 的精确布尔值，并用 `finally` 在 `_encode()` 或 `hidden.cpu()` 失败及正常返回后恢复该值；文本编码期间仍启用 cuDNN SDPA。`text_encoder_tp_size` 小于 DiT world size 时，只有 encoder ranks 运行该调用；restore 防止它们将进程级 policy 留给随后所有 rank 参与的 VAE。该修复不为 video VAE 选择 Flash 或 cuDNN，VAE backend policy 仍须由各 rank 显式且对称地配置。
- 禁止：只在初始 false 状态测试，恢复成硬编码 false，或把 CPU mock 的 flag assertion 描述成 cuDNN kernel、GPU output 或 multi-rank VAE parity 验证。当前实现仍在进入 `try` 前调用 `enable_cudnn_sdp(True)`；故 `_encode()`/`.cpu()` 失败时的泄漏已修复，但 enable 与 `try` 之间的中断或异常窗口仍是未关闭的 process-global-state limitation。将 enable 移入 `try` 是未来 hardening，不是本提交已提供的保证。
- 验收：CPU unit tests 分别以初始 false/true 覆盖成功与 `_encode()` 抛错，断言 override 内为 true、退出后等于初始值；它们只证明 Python-level global-state save/restore。要声称 GPU kernel 或 SP/PP rank-policy parity，另在目标 CUDA 拓扑上观察每个相关 rank 的状态和实际 VAE execution。^[PR #6710]
