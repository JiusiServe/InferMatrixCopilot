<!-- 模板：共享模块架构页 —— 稳定的职责与数据流，按需拉取（**不是** always-on）。
     不允许只有标题的空壳页。
     路径：repos/<repo>/components/<module>/architecture.md
     填掉 <...>，在同级 _index.md 里注册，然后删掉本注释。
     示例：knowledge/repos/vllm-omni/components/diffusion/architecture.md -->
---
title: "<Module> 共享架构"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: architecture
tags: [<repo>, components, <module>]
sources: [<path/to/module/>]
---

# <Module> 共享架构

## 负责什么

`<path/to/module/>` <one paragraph: what this module owns end to end.>

## 不负责什么

- <adjacent concern> 由 <other owner> 负责。
- <adjacent concern> 由 <other owner> 负责。

## 当前子模块布局（<branch> @ <commit-sha> 复核）

<!-- **钉住你核对时用的 commit**，已发布的页面就是这么做的。没有 pin 的架构页
     日后无法复核，而这一页型正是代码移动时最容易悄悄漂移的那一种。 -->

| 子模块 | 职责 | 主要入口 |
|---|---|---|
| `<path.py>` | <what it does> | `<fn>` / `<class>` |

## 数据怎样流动

<producer> → <transform> → <consumer>. <Name the real functions; a reader should
be able to open them in order.>

## 怎样验证

- <the command or test that proves the described flow still holds>
