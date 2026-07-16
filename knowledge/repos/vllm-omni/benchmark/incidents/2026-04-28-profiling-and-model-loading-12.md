# 2026-04-28 — HF 模型 CFG 2D attention_mask 传给 SDPA 报错

- 编号：`inc-2026-04-28-profiling-and-model-loading-12`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：HF 模型 CFG 2D attention_mask 传给 SDPA 报错
- 影响范围：repos/vllm-omni/benchmark

**症状**：修完 RoPE 后新报错 `The expanded size of the tensor (1) must match the existing size (2) at non-singleton dimension 3`
**根因**：transformers 4.57.1 的 `UnbatchedClassifierFreeGuidanceLogitsProcessor.get_unconditional_logits()` 传 2D `[1, N]` padding mask 给模型 forward，SDPA 期望 4D `[B, 1, Q, K]` mask
**解法**：在 SDPA 调用前加 guard：`if attention_mask is not None and attention_mask.ndim == 2: attention_mask = None`
**对未来的提醒**：CFG unconditional 路径的 attention_mask 格式和正常路径不同，SDPA attention 需要做 ndim 检查
