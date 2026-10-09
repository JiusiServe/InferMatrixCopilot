---
title: "team 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7783"]
confidence: high
---

# team 审查规则

## JW-TEAM-CANCEL-1a — follow-up 等待在途 cancel 收尾，并保持等待有界

- 触发：修改带 cancel-in-flight 跟踪的 TeamManager 拆除链和 team_helpers follow-up 投递；当前实现位于 dev-stable。
- 强制：在 settle/stop/finalize 全程维护按 session 累计的在途计数和完成 Event；wrapper 的 finally 清除取消抑制并解除跟踪。follow-up 在检测到在途 cancel 后有界等待，再沿既有归一化/interact 路径继续；超时或计数/Event 失配如实返回未确认收尾。
- 禁止：最后一个并发 cancel 结束前提前释放等待者；异常后遗留 cancel 标记；把超时误报为已收尾或无限等待。
- 验收：覆盖慢 settle、异常退出、并发 cancel、超时和计数/Event 失配；已开始的新世代不得被迟到 cancel 拆掉。^[PR #7783]
