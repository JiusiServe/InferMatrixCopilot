# 2026-04-23 — 没做侦察 + judge 模型未预下载

- 编号：`inc-2026-04-23-profiling-and-model-loading-01`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：没做侦察 + judge 模型未预下载
- 影响范围：repos/vllm-omni/benchmark

## 原文件说明

# Error Book: Profiling & 模型加载

**症状**：跑了 4 小时才跑通；judge 报 `LocalEntryNotFoundError`
**根因**：没做侦察 + `HF_HUB_OFFLINE=1` 下 judge 模型遗漏
**提醒**：accuracy test 涉及 generate + judge 两个模型，都要预下载
