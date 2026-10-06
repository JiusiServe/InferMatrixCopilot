---
title: "Fish Speech S2 Pro streaming 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #8422"]
confidence: high
---

# Fish Speech S2 Pro streaming 规则

## FISH-STREAM-1a — 自适应 chunk 使用绝对 emitted-frame frontier

- 触发：修改 Fish Speech async chunk processor、initial/steady chunk policy 或 backlog 驱动的 chunk-size 切换。
- 强制：以 request-owned `emitted_frames` 记录已发送帧的绝对边界，chunk size 只决定何时发出；每次覆盖全部 pending span，并带有界 left context。完成时 flush 整个尾部，只发送一次 terminal；状态放在 `request_payload` 的私有、不与输入 payload 字段冲突的 key 下，沿 connector completion/cancellation 生命周期回收。
- 禁止：用 chunk 次数乘当前 chunk size 推导已发送边界；切换策略后重发或跳过帧；完成后重复 terminal；仅缩小并发掩盖 frontier 错误。
- 验收：参数化 steady、finish 时降档、midstream 升档与振荡策略，包含/不包含 initial chunk、list/tensor payload，剔除 left context 后每个原始 frame 恰好出现一次，尾部和 terminal 完整。^[PR #8422]
