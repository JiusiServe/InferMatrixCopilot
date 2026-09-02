---
title: "Diffusion attention 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5887", vllm_omni/config/omni_config.py, vllm_omni/config/stage_config.py, vllm_omni/diffusion/attention/backends/flash_attn.py, vllm_omni/diffusion/data.py, vllm_omni/engine/arg_utils.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/cli/serve.py]
confidence: high
---

# Diffusion attention 规则

## DIFF-1f — deterministic flag 只对构造时选定的 local dense FA 生效

- 触发：修改 `--fa-deterministic`、diffusion config projection 或 local `FLASH_ATTN` dispatch。
- 强制：direct CLI 经 engine args/AsyncOmniEngine 传播到 `OmniDiffusionConfig`，attention impl 在构造
  时捕获；true 只在 dense unmasked `flash_attn_func` 传 `deterministic=True`，false 必须省略 kwarg
  保留 library default。structured deploy 必须由 `_DiffusionConfigProjection` 显式拥有字段。
- 禁止：把该 flag 描述成全 FlashAttention、跨平台或运行时动态 toggle。piecewise、packed-varlen、
  masked-varlen、dense-varlen fallback 以及 XPU/NPU path 不消费 kwarg，启用时只能 warning once。
- 验收：direct CLI 与 structured/deploy config 分别做 true/false 端到端传播；dense true/false 精确断言
  kwarg，每条 non-dense path 断言不传且只警告一次，构造后改 config 不得被误认为立即生效。目标 pin
  遗漏 `_DiffusionConfigProjection.fa_deterministic`，所以其派生 config/stage-engine field set 会过滤
  structured path；现有 accuracy fixture 只证明 direct CLI wiring。^[PR #5887]
