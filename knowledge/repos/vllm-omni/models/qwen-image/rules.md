---
title: "Qwen-Image 实现规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5887", tests/e2e/accuracy/test_qwen_image.py]
confidence: high
---

# Qwen-Image 实现规则

## QWENIMG-1a — accuracy gate 必须先证明同 seed repeatability

- 触发：修改 Qwen-Image accuracy threshold、regional compile 或 fixture 的 deterministic opt-in。
- 强制：accuracy fixture 显式启用 shared [DIFF-1f](../../components/diffusion/rules-attention.md) 的
  dense FA flag；先以相同 seed 多次比较 Omni↔Omni 唯一性，再用独立 gate 比较 Omni↔Diffusers。
- 禁止：从单次跨实现 SSIM/PSNR 推断 nondeterminism 已消失；把 accuracy-only opt-in 当成普通 serving
  默认；用跨实现系统偏差解释同实现双稳态，或反向混淆两者。
- 验收：regional compile + dense FA 下固定完整请求至少重复运行多次，先断言同实现输出稳定，再执行
  SSIM≥0.97、PSNR≥30 的跨实现 gate。PR 的 L20X run 为 0.960/28.188，未通过恢复后的两个 gate；
  合并后评论仍报告 0.958，因此目标证据不能证明 flake 已消除。^[PR #5887]
