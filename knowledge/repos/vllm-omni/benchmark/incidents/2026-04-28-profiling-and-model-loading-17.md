# 2026-04-28 — monkey-patch F.scaled_dot_product_attention 没生效

- 编号：`inc-2026-04-28-profiling-and-model-loading-17`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：monkey-patch F.scaled_dot_product_attention 没生效
- 影响范围：repos/vllm-omni/benchmark

**症状**：替换了 `torch.nn.functional.scaled_dot_product_attention`，但模型代码里的诊断 print 没出现
**根因**：模型文件用 `import torch.nn.functional as F` 后直接调 `torch.nn.functional.scaled_dot_product_attention(...)`，monkey-patch `F.scaled_dot_product_attention` 不影响已绑定的引用
**解法**：直接 patch 模型源文件（snapshot + cache 两个位置），加 print 语句
**对未来的提醒**：monkey-patch 标准库函数对 `trust_remote_code` 模型不可靠，直接改源文件更稳
