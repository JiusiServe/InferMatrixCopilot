---
title: "MRv2 attention capture 边界规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #8422"]
confidence: high
---

# MRv2 attention capture 边界规则

## EXEC-ATTN-BOUND-1a — capture query bound 必须区分 mixed FULL 与 separate decode

- 触发：修改 MRv2 `OmniModelState.prepare_attn` 的 capture metadata、CUDA graph mode 或 multimodal embedding 的 request boundaries。
- 强制：仅在 capture、没有显式 `max_query_len` 且 graph mode 不使用 separate routine 时，把 mixed FULL 的 bound 提升到 token bucket 的最坏情况；separate decode 保持其 uniform query bound，已有显式 bound 和 runtime metadata 保持原语义。传给 multimodal embedding 的 `query_start_loc_np` 只取当前 `num_reqs + 1` 个 boundary。
- 禁止：用 capture dummy 的平均每行长度约束 mixed replay；把 separate decode 的 FA3 GQA capture 扩成 bucket query；把预分配 boundary array 的旧尾部作为当前 request。
- 验收：真实 FA3 覆盖 `FULL_AND_PIECEWISE`/`FULL_DECODE_ONLY` 的 capture 与 replay，并分别断言 mixed worst-case、uniform decode 和显式 bound；mixed multimodal batch 断言只读取当前请求边界。CPU shape/stub 检查不能替代 kernel replay。^[PR #8422]
