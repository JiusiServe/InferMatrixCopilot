---
title: "PersonaPlex streaming 表与 codec 输入合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, models]
sources: ["PR #7850", "PR #7480"]
confidence: high
---

# PersonaPlex streaming 表与 codec 输入合同

## PPLEX-HOIST-1a — 逐层外提只共享 step 内不变量

- 触发：修改 temporal/Mimi streaming stack 的 RoPE 与 RingKV position 计算。
- 强制：每 step 按当前逐行 offset、seq_len、active、head_dim/max_period 与 ring capacity 构建一次表并传各层；per-ring start_offset elastic mask 仍在各自 complete 中应用。complete 的可选表参数省略时从自身 end_offset 构造，standalone 调用保持有效，encoder/decoder 状态各自独立。
- 禁止：把 per-ring mask 一同外提，或用 module/class cache 混合独立 encoder/decoder offset；改变 ring 的 delta<=0 位置约定。
- 验收：用 frozen pre-change implementation 在同次运行对比 torch.equal，覆盖 per-row 漂移、inactive、wrap/recycle 与真实 layer 权重；不以跨版本预存 cos/sin 充当 bitwise oracle。 ^[PR #7850]

## PPLEX-CODEC-DELTA-1a — delta 直接消费，full payload 每请求只消费一次

- 触发：修改 PersonaPlexCode2Wav async_chunk、payload 去重或 finished cleanup。
- 强制：async_chunk 的每块 delta 原样交 streaming decoder，不存完整 CPU code history；同步 full payload 仅在有 request ID 时按 request consumed 标记去重。on_requests_finished 清除标记与 codec slot，使同 ID 新请求可重新消费；缺 ID 保留不去重行为。
- 禁止：用历史前缀 torch.equal 推断 suffix，误删连续相同值的合法 delta；重复 decode 同一 full payload，或结束后遗留 consumed 标记。
- 验收：长序列 delta 每块调用一次 decoder，连续相同 code 两块都消费；full payload 跨 forward 只消费一次，finished 后同 ID 可再次消费。 ^[PR #7480]
