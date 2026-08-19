<!-- 模板：模型架构页 —— 哪些是**这个模型自己的**，哪些是从共享组件继承的。
     按需拉取，不是 always-on。
     路径：repos/<repo>/models/<model>/architecture.md
     填掉 <...>，在同级 _index.md 里注册，然后删掉本注释。
     示例：knowledge/repos/vllm-omni/models/hunyuan-image3/architecture.md -->
---
title: "<Model> 架构"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: architecture
tags: [<repo>, models, <model>]
sources: [<path/to/model/>]
---

# <Model> 架构

## 模型专有部分与共享模块的边界

<!-- 这一页能说的最有用的一件事。reviewer 需要知道哪些缺陷归这里、哪些归共享组件。 -->

| 这一部分 | 归属 | 说明 |
|---|---|---|
| <transformer / VAE / tokenizer / prompt path> | **本模型** `<path.py>` | <why it is model-specific> |
| <denoise loop / scheduling / serving entry> | 共享 [`components/<module>`](../../components/<module>/architecture.md) | <what it inherits unchanged> |

## 配置、checkpoint 和兼容范围

- 注册键：`<registry key>`（`<registry.py>`）
- checkpoint 兼容：<versions / layouts that load, and the ones that do not>
- 已知不兼容：<explicit list — this is what reviews check against>

## 从输入到输出的主要流程

<request> → <preprocess> → <AR/DiT stage> → <postprocess> → <output>.
<Name the real functions in order.>

## 怎样验证功能、精度和性能

- 功能：<command>
- 精度：<the baseline and its tolerance — a number, not "looks right">
- 性能：<the benchmark and the expected range>

## 当前布局（<branch> @ <commit-sha> 复核）

<!-- 钉住 commit，理由同组件模板。 -->
