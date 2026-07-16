# 2026-05-05 — Rebase cr/pr3107-fix → vllm-omni main (45 commits) 不修 painterly

- 编号：`inc-2026-05-05-painterly-conditioning-ablation-01`
- 归属：`repos/vllm-omni/models/hunyuan-image3`
- 状态：仅历史
- 搜索词：Rebase cr/pr3107-fix → vllm-omni main (45 commits) 不修 painterly
- 影响范围：repos/vllm-omni/models/hunyuan-image3

## 原文件说明

# Painterly bug — conditioning 路径排除链

painterly 调查中**证明 painterly 不在 conditioning 路径上**的三步链：rebase main → 全链路数值审计 → cond_vae/cond_vit 双消融。这一系列实验都"没修"painterly，但**排除了一大片嫌疑**。根因和总览见 [Painterly 错题索引](_index.md)。

---

**实验**：cr/pr3107-fix 落后 vllm-omni `origin/main` 45 个 commit，rebase 到最新 main（包括 #3285 timestep_embedding 共享重构 / #3082 Remove Entrypoint Hijack for vLLM 0.20.0 / #3327 #3302 #3307 FA backend 修复 / #3304 Z-Image RMSNorm / #3325 NPU 0.20.0 align 等），4-GPU IT2I 同 prompt + seed=42 重跑。

**结论**：painterly 视觉**完全保留**，跟 baseline 不可区分。

**对未来的提醒**：painterly 已确认**不在 vllm-omni 这 45 个 main commit 范围内**。下次别再花时间 `git log origin/main..HEAD` 找精度修复 commit。bug 必然在：(a) cr/pr3107-fix 自己的 21 个适配 commit，(b) vllm 0.20.0 / torch 2.11 / cuDNN 13 这些非 vllm-omni 组件，(c) 或 vllm-omni AR/DiT 跨进程架构本身。Branch 已 push 到 `TaffyOfficial/vllm-omni:cr/pr3107-rebased` 备查。

---
