---
title: "Qwen-Image 实现规则"
created: 2026-09-02
updated: 2026-09-08
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5887", tests/e2e/accuracy/test_qwen_image.py, "PR #6110", "vllm_omni/diffusion/models/qwen_image/qwen_image_transformer.py", "PR #5586"]
confidence: high
---

# Qwen-Image 实现规则

## Direct 代码快速入口

| PR 描述信号 | 规则 |
|---|---|
| accuracy/repeatability gate | `QWENIMG-1a` |
| compiled complex RoPE | `QWENIMG-1b` |
| Edit `txt_seq_lens`/RoPE width、negative CFG length | `QWENIMG-1c` |


## QWENIMG-1a — accuracy gate 必须先证明同 seed repeatability

- 触发：修改 Qwen-Image accuracy threshold、regional compile 或 fixture 的 deterministic opt-in。
- 强制：accuracy fixture 显式启用 shared [DIFF-1f](../../components/diffusion/rules-attention.md) 的
  dense FA flag；先以相同 seed 多次比较 Omni↔Omni 唯一性，再用独立 gate 比较 Omni↔Diffusers。
- 禁止：从单次跨实现 SSIM/PSNR 推断 nondeterminism 已消失；把 accuracy-only opt-in 当成普通 serving
  默认；用跨实现系统偏差解释同实现双稳态，或反向混淆两者。
- 验收：regional compile + dense FA 下固定完整请求至少重复运行多次，先断言同实现输出稳定，再执行
  SSIM≥0.97、PSNR≥30 的跨实现 gate。PR 的 L20X run 为 0.960/28.188，未通过恢复后的两个 gate；
  合并后评论仍报告 0.958，因此目标证据不能证明 flake 已消除。^[PR #5887]

## QWENIMG-1b — 复数 RoPE 分量在编译路径使用函数式算子

- 触发：修改 Qwen Image `QwenImageCrossAttention` 的 complex RoPE 频率分解、regional compilation 或 MUSA 执行路径。
- 强制：对 `vid_freqs` 和 `txt_freqs` 使用 `torch.real()`/`torch.imag()` 后再转换为 query 对应 dtype；即使问题由 MUSA 暴露，也保持 CUDA 与其他平台使用同一等价函数式表达式。
- 禁止：在该编译路径恢复 `freqs.real`/`freqs.imag` 属性链，或仅用 `--enforce-eager` 掩盖重复 tensor alias guard；不得把该模型级修复泛化为所有 diffusion RoPE caller 已具备同等保障。
- 验收：以 legacy 属性表达式作为 reference，验证函数式路径的值与 dtype 精确一致；在目标 MUSA 上以 Qwen Image 默认编译配置验证不再出现 `Duplicate tensors found`，并在 CUDA smoke 中确认输出 parity。^[PR #6110]

## QWENIMG-1c — edit path 的 `txt_seq_lens` 必须来自 padded embed width，不得来自 mask token count

- 触发：修改 Qwen-Image Edit pipeline 的 prompt encode、RoPE table length、negative prompt wiring，或 request-batch padding。
- 强制：传给 RoPE / `diffuse()` 的 `txt_seq_lens` 与 `negative_txt_seq_lens` 必须由实际 prompt embed 的 padded width 推导，而不是 `prompt_embeds_mask.sum()` 的 valid-token 数。mask 只表达语义 token 有效区，不能缩短需要为 padded encoder width 构造的 text frequency table。
- 强制：有 negative prompt 且启用 true CFG 时，正负两侧都使用各自 embed width；无 negative prompt 时 negative length 必须是 `None`，不能伪造一个来自正分支 mask 的长度。
- 禁止：在 Edit path 回退到 `mask.sum()`，即使别的 Qwen-Image pipeline 仍正确；或仅以 helper test 证明 RoPE table 正确而不锁定实际 `forward()` call site。
- 验收：以 padded embeds 但较短 valid-token mask 的 request 覆盖 Edit `forward()`，精确断言传入 `diffuse()` 的长度等于 padded width；同时覆盖有/无 negative prompt 的 CFG 分支，防止单侧回归。^[PR #5586]
