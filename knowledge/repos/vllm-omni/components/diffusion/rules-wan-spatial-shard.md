---
title: "Wan VAE spatial-shard 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #6062", vllm_omni/diffusion/distributed/autoencoders/wan_spatial_shard.py, tests/diffusion/distributed/test_wan_spatial_shard.py]
confidence: high
---

# Wan VAE spatial-shard 规则

## DIFF-3b — trimmed global extent 必须可逆地 reshard 为固定 local shape

- 触发：修改 Wan VAE spatial-shard height/width split、gather/trim/reshard、attention wrapper、padding
  或保存的 `SpatialShardContext`。
- 强制：reshard 使用 process group 的相对 rank，并在存在 context 时先验证它与 context rank 一致；
  不一致必须在 slicing 前 fail-fast。设 `actual_extent=x.shape[dim]`，则
  `start=min(rank*local_extent, actual_extent)`，valid extent 同时受 context 推导的有效长度和
  `actual_extent-start` 约束。`narrow` 后不足 `local_extent` 的尾部补零，使每 rank shape 相同；
  空 trailing shard 必须成为合法的 zero-length slice + full zero padding，而不是越界 offset。
- attention wrapper 在 global gather 后把目标 extent clamp 到实际 gathered extent；attention 输出在
  split axis 上必须保持这个 trimmed extent，否则报告 group rank、split axis、local/gathered/trimmed/
  output extent 和 context 后失败，禁止把改变后的 extent 继续按旧边界 reshard。
- 禁止：仅把 valid length clamp 为零却保留越界 start；让最后一 rank 返回短 tensor；混用 global rank
  与 group-relative rank；假设 attention 永远 shape-preserving 而无 guard；只测 height 后外推 width。
- 验收：height/width 都覆盖 world size 大于 extent 的 empty tail、不能整除的 partial tail 和常规 extent；
  拼接所有固定 local shards 并 trim 后必须逐值重建输入。另覆盖 context/group rank mismatch 与 attention
  shrink/expand。CPU slicing tests 只证明边界数学；collective/halo correctness 仍需多 GPU height/width 对
  single-process reference，生产 pipeline smoke 另验证真实 VAE patch/caller。^[PR #6062]
