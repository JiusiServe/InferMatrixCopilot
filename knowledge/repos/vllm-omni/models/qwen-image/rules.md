---
title: "Qwen-Image 实现规则"
created: 2026-09-02
updated: 2026-10-10
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5887", tests/e2e/accuracy/test_qwen_image.py, "PR #6110", vllm_omni/diffusion/models/qwen_image/qwen_image_transformer.py, "PR #5586", "PR #7513", "PR #8699"]
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

## QWENIMG-1d — CUDA eager RoPE 必须走激活 dtype 的 RotaryEmbedding

- 触发：修改 Qwen-Image `_qwen_image_qk_norm_rope` 的 CUDA/eager 分支、`RotaryEmbedding` 调用，或把 RoPE 放进 regional compile。
- 强制：所有设备的 eager 路径在 RMSNorm 之后使用 `RotaryEmbedding`；`cos`/`sin` 由 `torch.real`/`torch.imag` 得到并 cast 到激活 dtype（BF16）。这是 pipeline 对 Diffusers 的路径。fused kernel 可以继续对照 FP32 complex multiply，但那不是 eager CUDA 路径。
- 禁止：在 eager CUDA 上恢复 `_apply_qwen_image_rotary_emb` 或其它 FP32 复数乘。该 helper 能在单元测试里对齐 Diffusers `apply_rotary_emb_qwen(..., use_real=False)`，但 Inductor 不能 codegen 复数算子，且会把 Omni↔Diffusers pipeline PSNR 打到门限以下。不要用 `--enforce-eager` 掩盖，也不要为迁就 helper 去降 pipeline gate。
- 验收：`use_fused=False` 对所有设备对照 `RotaryEmbedding`；fused 测试单独对照 FP32 complex reference。eager CUDA 与 fused reference 不得再共用同一个 expected。^[PR #7513]

## VLLM-OMNI-PR8699-QWEN21-SIGMA-GRID — checkpoint 预设 sample_sigmas 必须按请求>模型>回退优先级贯通到步数解析

- 触发：为 native `nn.Module` pipeline（如 `QwenImage21Pipeline`）接入 checkpoint `model_index.json` 中的预设 `sample_sigmas` 网格，或修改 `OmniDiffusionConfig.enrich_config` 的 extras 提取、`prepare_timesteps` 的 sigmas 回退、pre-process hook 的请求级注入、`default_num_inference_steps` 或 `sigmas` 的 extra_body 白名单。
- 强制：保持与 upstream diffusers #14950 一致的优先级：请求级 `sigmas` > 模型级 `sample_sigmas` > `linspace(1.0, 1/num_inference_steps, num_inference_steps)` 回退；网格生效时总步数由 `len(sigmas)` 决定，显式 `num_inference_steps` 被忽略。`enrich_config` 的提取条件按实现是 `self.extras.get("sample_sigmas") is None`：extras 缺失该键或显式为 `None` 时都会写入 checkpoint 网格，即显式 `None` 同样会被覆盖；只有非 `None` 的显式 extras 值胜出。请求未携带 sigmas 时，pre-process hook 必须把预设网格注入为请求级 `sigmas`，使 `StepScheduler._get_total_steps` 与 cache backends 经既有 `len(sigmas)` 路径解析正确总步数；runner 的 cache-refresh 路径经 `default_num_inference_steps` 解析步数。`sigmas` 只能通过既有多模型 extra_body 白名单机制（同 LTX2）按请求开放，并在 chat 与 images/generations 两条路径生效。
- 禁止：让 `enrich_config` 覆盖用户显式提供的非 `None` extras 值，或把提取判定改成键存在性/truthiness 检查（现状以 `is None` 判定，显式 `None` 会被 checkpoint 网格覆盖，语义不同）；省略 hook 注入导致 step-wise 执行与缓存按调用方步数（如示例默认 50）而非网格步数（8）解析；网格生效时仍让 `num_inference_steps` 参与步数决定；绕过白名单机制向请求开放调度参数。
- 验收：CPU 单测覆盖 extras 三种情形（从 model_index 提取、缺失不写入、显式非 `None` extras 不被覆盖）与 `prepare_timesteps` 优先级（请求 sigmas 胜出、config 网格决定步数并压过 `num_inference_steps`、无网格回退 linspace）；断言请求未携带 sigmas 时步数解析等于网格长度；extra_body `sigmas` 在 `/v1/chat/completions` 与 `/v1/images/generations` 均可覆盖默认网格。Turbo 的 CFG=1 用法与 Qwen Research License 属 checkpoint 使用约束，不是本规则的验收对象。^[PR #8699]

<!-- kb:rule status=active since=v0.30.0 -->
