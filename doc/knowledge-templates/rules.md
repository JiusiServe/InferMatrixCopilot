<!-- TEMPLATE: an always-on gate page. Keep it tight — it loads as briefing on
     every task. Give each independent constraint a stable ID (e.g. HY3-2c).
     Link this page from the sibling _index.md, then delete this comment. -->
---
title: "<Owner> 硬门禁"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: rule
tags: [<tag-from-SCHEMA.md>]
sources: []
---

# <Owner> 硬门禁

只在当前任务明确属于 <owner> 时应用本页。先遵守根 `CLAUDE.md` 的通用 P0，再执行这里的专属门禁。

## 场景触发器

| 用户提到 | 必读 | 硬约束 |
|---|---|---|
| <trigger phrase> | [<guide>](guides/<guide>.md) | <what MUST / MUST-NOT happen + how to verify> |

## 规则

### <RULE-ID> <short name>

- 触发：<when this applies>
- 必须：<the required action>
- 禁止：<the forbidden action>
- 验收：<the exact check proving compliance>
