---
title: "MAGI-2 Preview model owner"
created: 2026-10-06
updated: 2026-10-06
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #7206", vllm_omni/diffusion/models/magi2/]
---

# MAGI-2 Preview

- 触发：MAGI-2本地routedMoE、derivedweightcache、BF16kernel/launch或modelcheckpoint加载。
- 源码：`diffusion/models/magi2/mh_moe.py`、`fused_moe_kernels.py`、`modeling_magi2.py`。
- [BF16 routed MoE规则](rules.md)：eligibility、cache失效、head/routing/numerical/launch验收。
- EP/framework通信归shared distributed owner，attention/其他modelfamily不得从此fusedcontract外推。
