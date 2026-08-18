<!-- TEMPLATE: a model architecture page ->
     knowledge/repos/<repo>/models/<model>/architecture.md.
     Synthesis-layer page: frontmatter is REQUIRED (check_wiki_lint.py) —
     type: architecture; created/updated = YYYY-MM-DD; tags from knowledge/SCHEMA.md.
     No title-only stubs. Link it from the sibling _index.md, then delete this comment. -->
---
title: "<Model> 架构"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: architecture
tags: [<tag-from-SCHEMA.md>]
sources: []
---

# <Model> 架构

## 模型专有部分与共享模块的边界

- 专有：<model-specific code>
- 依赖的共享模块：[<module>](../../components/<module>/_index.md)

## 配置、checkpoint 和兼容范围

- 正式名称 / 别名：<name> / <aliases>
- checkpoint、尺寸、量化差异：<...>

## 从输入到输出的主要流程

- <input> → <preprocess> → <core> → <output>

## 怎样验证功能、精度和性能

- 功能：<check>
- 精度：<baseline + metric>
- 性能：<workload + metric>
