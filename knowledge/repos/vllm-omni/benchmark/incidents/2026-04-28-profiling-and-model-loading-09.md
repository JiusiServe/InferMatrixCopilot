# 2026-04-28 — pip install torchvision 把 torch 升级到不兼容版本

- 编号：`inc-2026-04-28-profiling-and-model-loading-09`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：pip install torchvision 把 torch 升级到不兼容版本
- 影响范围：repos/vllm-omni/benchmark

**症状**：`RuntimeError: The NVIDIA driver on your system is too old (found version 12080)`
**根因**：`pip install torchvision`（不 pin 版本）拉了最新 torchvision，连带把 torch 从 2.7.0 升到 2.11.0（需要 CUDA 13），和 12.8 驱动不兼容
**解法**：安装时必须同时 pin torch 和 torchvision 版本：`pip install torch==2.8.0 torchvision==0.23.0`
**对未来的提醒**：永远不要单独 `pip install torchvision`，必须和 torch 一起 pin 版本
