# 2026-04-28 — diff_infer_steps 参数不是 generate_image 的 kwarg

- 编号：`inc-2026-04-28-profiling-and-model-loading-14`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：diff_infer_steps 参数不是 generate_image 的 kwarg
- 影响范围：repos/vllm-omni/benchmark

**症状**：`generate_image(diff_infer_steps=10)` 传了但模型跑了 50 步（默认值）
**根因**：`diff_infer_steps` 是 `generation_config` 的属性，不是 `generate_image` 的 kwarg。pipeline 从 `gen_config.diff_infer_steps` 读取
**解法**：`model.generation_config.diff_infer_steps = 10`
**对未来的提醒**：HF 模型的 diffusion 参数在 `generation_config` 里，不在 `generate_image` kwargs 里
