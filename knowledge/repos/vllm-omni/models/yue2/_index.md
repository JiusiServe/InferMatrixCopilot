---
title: "YuE2 模型规则入口"
created: 2026-10-06
updated: 2026-10-06
type: index
tags: [vllm-omni, models, model-executor]
sources: ["PR #8407"]
---

# YuE2 模型规则入口

YuE2 的 AR semantic frames、NAR/VAE synthesis queue 与请求完成边界属于本模型 owner；共享 runner 的输入 hook 只负责按模型 opt-in 转发 metadata。

- [YuE2 synthesis 与完成边界规则](rules.md)

- [请求/native tokenizer 与数值边界](rules-interface.md)
- [SheetSage2 score 与 speech request handoff](rules-score-handoff.md)
