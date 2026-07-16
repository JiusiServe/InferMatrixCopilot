# 2026-04-27 — 不能用 CPU 空闲数推算可用 GPU

- 编号：`inc-2026-04-27-remote-ssh-slurm-container-08`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：sinfo、GPU allocation、CPU 空闲数、Slurm
- 影响范围：framework/remote

**症状**：曾尝试根据 `sinfo` 的 CPU 空闲数和某台机器的 CPU/GPU 比例推算“可用 GPU”。

**根因**：CPU、GPU、GRES 和调度策略不是固定比例；节点显示 mixed 或设备显存为空，也不代表当前用户获得了 GPU 使用权。

**解法**：`sinfo` 只用于了解节点和分区状态。实际可用 GPU 以调度器授予的 allocation、job 信息和 `CUDA_VISIBLE_DEVICES` 为准；需要更多资源时重新申请，不使用 allocation 外设备。
