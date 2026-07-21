<!-- TEMPLATE: a shared-module architecture page ->
     knowledge/repos/<repo>/components/<module>/architecture.md.
     Synthesis-layer page: frontmatter is REQUIRED (check_wiki_lint.py) —
     type: architecture; created/updated = YYYY-MM-DD; tags from knowledge/SCHEMA.md.
     No title-only stubs. Link it from the sibling _index.md, then delete this comment. -->
---
title: "<Module> 架构"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: architecture
tags: [<tag-from-SCHEMA.md>]
sources: []
---

# <Module> 架构

## 职责和边界

- <what this module owns; what it explicitly does NOT own>

## 主要源码和调用入口

- `<local/path/to/source>` — <role>
- 测试入口：`<path/to/test>`

## 数据怎样流动

- <producer> → <what it emits> → <consumer>

## 怎样验证

- <the command / check that proves the boundary still holds>
