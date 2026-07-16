# 2026-04-28 — torch.profiler 包整个 generate_image() → 23GB+ trace 爆炸

- 编号：`inc-2026-04-28-profiling-and-model-loading-13`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：torch.profiler 包整个 generate_image() → 23GB+ trace 爆炸
- 影响范围：repos/vllm-omni/benchmark

**症状**：profiler 导出 trace 时 RSS 涨到 250GB，trace 文件 23GB+，chrome://tracing 打不开
**根因**：`with profile(...): model.generate_image(...)` 把 AR prefill（1234 tokens × 33 layers × MoE）+ AR decode + diffusion 全录进去了。80B 模型即使只跑 13s，kernel 调用量也是百万级
**解法**：monkey-patch pipeline 的 `progress_bar` context manager，在 `__enter__` 里 `prof.__enter__()`，`__exit__` 里 `prof.__exit__()`，精确只包 denoising loop → 1.2GB trace（79MB gz）
**对未来的提醒**：大模型 profiling 必须精确控制 profiler 范围。不要包整个推理流程，只包目标阶段（如 denoising loop）。用 monkey-patch 注入 profiler 比改源码更灵活
