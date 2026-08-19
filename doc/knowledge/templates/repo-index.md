<!-- 模板：**仓库**入口索引 —— 一个仓库切片的正门。
     路径：knowledge/repos/<repo>/_index.md
     这一页是该仓库的 always-on briefing（adapter 的 briefing_docs），所以是**严格
     预算**：只做路由，不写叙述。
     填掉 <...>，在 knowledge/repos/_index.md 里为 <repo> 加一行，把 adapter manifest
     指向该切片，然后删掉本注释。
     示例：knowledge/repos/vllm-omni/_index.md -->
---
title: "<Repo display name> 入口"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: index
tags: [<repo-tag-from-SCHEMA.md>]
sources: []
---

# <Repo display name>

上游：`<org>/<repo>`。开始任何任务先遵守[仓库硬规则](rules.md)。

<!-- 本模板的行都是可选的，按实际存在的目录删改，不要为了套模板造空页：
     `rules.md` 仅当确实存在仓库级门禁时才建（见 writing.md 的目录骨架），
     没有就删掉上面那句；`components/`、`models/`、`review/`、`ci/` 同理，
     哪个目录不存在就删掉对应的行。留着指向不存在文件的链接会让
     check_doc_links 失败，而为了凑链接建占位页是明确禁止的。 -->

## Review 最短路径

<!-- 全树价值最高的一张表：意图 → **唯一**该打开的 owner 页。明确写出"Direct 已
     给出 quick_map 时本页作废"，这样已经拿到路由的宿主就不会再读一遍。 -->

PR title/body 先选择 owner；changed files 只校验实际范围。Direct 已返回精确
`quick_map` 时，不再读取本页、组件总表或模型总表。

| PR 声明目标 | 直接 owner |
|---|---|
| <intent phrase> | [<owner> rules](components/<owner>/rules.md) |
| 明确模型名或 registry key | 直接查看 [models 目录](models/_index.md) |

owner 仍不明确时才看 [components 职责表](components/_index.md)。

## 工作主题

| 任务 | 入口 |
|---|---|
| PR 审查专项 | [review](review/_index.md) |
| CI 和测试配置 | [ci](ci/_index.md) |
| <topic> | [<topic>](<topic>/_index.md) |

## 不放什么

- <machine facts: host, path, account, token, cache> → git-ignored `local/`
- <evaluation cases, labels, judgments, run reports> → `eval/`
