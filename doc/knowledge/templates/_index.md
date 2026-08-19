<!-- 模板：目录路由表。任何含 Markdown 的目录都需要一个，且每个同级页面和子目录
     都必须被它**恰好链接一次** —— 未注册的页面会让 check_knowledge_tree.py 失败。
     填掉 <...>，然后删掉本注释。
     示例：knowledge/repos/vllm-omni/components/_index.md -->
---
title: "<Human title>"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: index
tags: [<tag-from-SCHEMA.md>]
sources: []
---

# <Human title>

<!-- 这里的 frontmatter 是**必填**：`_index.md` 属于沉淀层，check_wiki_lint.py 会
     对它强制 title/created/updated/type/tags。已发布的 123 个 _index.md 里有 109 个
     带着它。 -->

## 什么时候查这里

- <one line: when a task should open this directory — and, if it is a
  disambiguation index, say that it is the LAST resort, e.g. "仅在 PR 描述和
  Direct 路由都不能确定 owner 时查本页">

## 不放什么

- <what belongs elsewhere> → `<other/owner/path>`

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| <symptom / task> | [<page>](<page>.md) | <one-line scope> |
| <a child area> | [<child>](<child>/_index.md) | <one-line scope> |

<!-- 路由到**下一页**就停。一个诱导读者通读整棵子树的索引，会让每个打开它的任务
     都付出代价。当存在更重的页面（architecture.md、长 guide）时，写明**什么时候
     不要**打开它 —— 例如"需要解释稳定数据流时再进入 architecture.md，不要当成
     review 的默认前置阅读"。 -->
