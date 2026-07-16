# 2026-04-28 — patch 了错误的 cache 路径

- 编号：`inc-2026-04-28-profiling-and-model-loading-18`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：patch 了错误的 cache 路径
- 影响范围：repos/vllm-omni/benchmark

**症状**：patch 了 `/mnt/models/modules/transformers_modules/...` 但模型实际加载的是 `/root/.cache/huggingface/modules/transformers_modules/...`
**根因**：不同环境下 transformers modules cache 路径不同，取决于 `HF_HOME` / `TRANSFORMERS_CACHE` / 默认值
**解法**：看 traceback 里的实际文件路径，patch 那个路径。同时 patch snapshot 源文件防止被覆盖
**对未来的提醒**：先跑一次看 traceback 确认实际加载路径，再 patch
