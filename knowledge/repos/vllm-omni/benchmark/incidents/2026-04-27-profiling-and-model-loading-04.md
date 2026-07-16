# 2026-04-27 — async_chunk=True 默认值导致 HunyuanImage3 启动 ValueError

- 编号：`inc-2026-04-27-profiling-and-model-loading-04`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：async_chunk=True 默认值导致 HunyuanImage3 启动 ValueError
- 影响范围：repos/vllm-omni/benchmark

**症状**：`ValueError: Pipeline 'hunyuan_image_3_moe' has async_chunk=True in deploy but no stage declares a next-stage input processor`
**根因**：`DeployConfig.async_chunk` 默认 `True`；HunyuanImage3 没有 deploy YAML；DIT_ONLY 单阶段 pipeline 没有 next-stage processor
**解法**：创建 `vllm_omni/deploy/hunyuan_image_3_moe.yaml`（`async_chunk: false`），或加 `--no-async-chunk`
**提醒**：单阶段 diffusion 模型没有 deploy YAML 时必须加 `--no-async-chunk`
