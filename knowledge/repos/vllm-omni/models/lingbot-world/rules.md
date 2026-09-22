---
title: "LingBot World session lifecycle 规则"
created: 2026-09-22
updated: 2026-09-22
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #6533", "PR #6838", vllm_omni/diffusion/models/lingbot_world/pipeline.py]
---

# LingBot World session lifecycle 规则

## LBW-1a — AR 流式 VAE decode 状态必须按 session 持有并计入 admission

- 触发：修改 LingBot/Wan 系 AR-Diffusion `post_decode`、streaming VAE decode、`SupportsStreamingDecode`，或 `model_owned_state_bytes_per_session`。
- 强制：每个 `session_id`（与 `request_id` 同键）持有独立 `StreamingDecodeState`；chunk 间复用同一 temporal cache；`reset_ar_diffusion_session`/`close_ar_diffusion_session` 一并释放。`model_owned_state_bytes_per_session` 必须计入 decoder 按分辨率声明的常驻字节，不能只算 image condition。会走 VAE tiled decode 的 shape 不得冒充可跨 chunk 线程 cache。
- 禁止：把 temporal cache 留在共享 VAE 模块上跨 session 覆写；块级独立 decode 却声称 timeline 连续；漏报 decode state 导致 admission 低估显存。
- 验收：覆盖跨 chunk 连续性、session 隔离、release、非流式/tiling fallback，以及 admission 字节随 H×W 缩放不随 session 长度增长。^[PR #6533]

## LBW-1b — AR 条件编码历史必须会话持有、双份计入并在终止边界释放

- 触发：修改 AR-Diffusion realtime/stepwise 条件编码、Wan VAE encoder cache、session admission 字节预算，或 temporal RoPE 超出预计算表。
- 强制：跨 block 推进时保留 causal encoder history（committed + in-flight），每 session 只驻留当前 condition block 与有界 cache；admission 必须计入两份 encoder history 与 streaming-decode 字节。reset/close 必须释放 encoder cache。超出预计算 RoPE 表的 temporal 位置按绝对位置即时算 cos/sin，不得扩张常驻表。条件编码要求 unpatched、非 tiled Wan encoder。
- 禁止：用固定像素/latent 帧上限冒充无界 realtime；只预算 self-KV 而漏算 encoder cache；在失败 block 后提交 pending history；把本变更写成已解决共享 paged-KV 长度上限。
- 验收：因果条件递进、session 隔离/清理、失败不提交、内存会计、tick/stepwise 一致，以及 RoPE 越界且 cache 尺寸固定。^[PR #6838]
