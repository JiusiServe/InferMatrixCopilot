# 2026-04-27 — HF_HUB_CACHE 覆盖 HF_HOME 导致 server 600s 超时

- 编号：`inc-2026-04-27-profiling-and-model-loading-03`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：HF_HUB_CACHE 覆盖 HF_HOME 导致 server 600s 超时
- 影响范围：repos/vllm-omni/benchmark

**症状**：server 启动后 GPU 全程 0 MiB，600s 超时，模型从未加载
**根因**：Docker 镜像设了 `HF_HUB_CACHE=/models/hub`，优先级高于 `HF_HOME=/home/models`
**解法**：进容器后 `unset HF_HUB_CACHE`
**提醒**：`HF_HUB_CACHE` 和 `TRANSFORMERS_CACHE` 都要 unset，不能只 unset 一个
