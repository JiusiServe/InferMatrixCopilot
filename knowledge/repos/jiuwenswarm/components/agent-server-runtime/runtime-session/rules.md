---
title: "runtime-session 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7782"]
confidence: high
---

# runtime-session 审查规则

## JW-SESSION-META-1a — 装备写入先排空旧元数据，再重读磁盘

- 触发：修改 session_metadata.save_session_equipment 的同步更新路径。
- 强制：需要更新装备时先确认排队元数据写入完成，再 cache_bust 重读、比较并写入；冲刷失败抛错。快照已经一致时允许直接返回，不制造额外写入。
- 禁止：用未排空队列时读到的旧快照覆盖首轮标题和消息计数；忽略冲刷失败继续更新。
- 验收：延迟首条 user record 写入并并发更新装备，最终标题、消息计数与装备均保留；相同快照不额外落盘。^[PR #7782]
