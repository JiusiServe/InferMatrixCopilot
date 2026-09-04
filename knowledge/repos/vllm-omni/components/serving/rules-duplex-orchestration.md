---
title: "Serving duplex 编排规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #6529", vllm_omni/engine/orchestrator.py, tests/engine/test_orchestrator_segment_stage_keying.py, tests/engine/test_orchestrator_stage_input_bridge.py]
confidence: high
---

# Serving duplex 编排规则

## SERV-6g — orchestrator streaming segment state 必须按 stage key 隔离

- 触发：orchestrator streaming state、stage metrics、final-output routing、next-stage bridge 或 duplex
  output context 修改。
- 强制：每个 stage 独立拥有 `finished`、`token_ids` 与 `output_metadata`；写入和所有 consumer 都以
  显式 `stage_id` 选择该 slot，未上报的 stage 返回 fresh empty state，不能共享 mutable metadata。
  `new_prompt_len_snapshot` 仍是 request-level，因为它只由不按 stage 读取的 input-bridge context
  消费。
- 禁止：用 request-global flat segment slot 让 diffusion/raw-output poll 覆盖另一 stage；调用 duplex
  context 时省略 stage ID；把 request-level prompt-length snapshot 误迁入 stage slot。
- 验收：多 stage 交错上报 boundary，逐 stage 验证 metrics、final-output、bridge 与 duplex context
  只见自身 token/metadata；覆盖 missing-stage fresh state 与不会经过 raw-output loop 的 diffusion
  branch。^[PR #6529]
