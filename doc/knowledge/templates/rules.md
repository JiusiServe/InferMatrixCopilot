<!-- 模板：always-on 门禁页。这个 owner 下的**每一个任务**都会把它作为 briefing
     加载，所以它是预算，不是写叙述的地方。填掉 <...>，在同级 _index.md 里注册本页，
     然后删掉本注释。
     参照 knowledge/repos/vllm-omni/components/configuration/rules.md 与
     models/hunyuan-image3/rules.md —— 打开任一篇即可看到填好的样子。 -->
---
title: "<Owner> 硬门禁"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: rule
tags: [<tag-from-SCHEMA.md>]
sources: [<PR #NNNN>, <path/to/source.py>, <sibling-guide.md>]
---

# <Owner> 硬门禁

只在<明确的触发条件：修改 X、审查 Y、调试 Z>时使用本页。<可选：第一次读先看
[<入门 guide>](<guide>.md)；需要执行时再看 [<操作 guide>](<guide>.md)。>

只有<加粗项目或表格第一列中的 `<PREFIX>-数字字母`>是可审计规则 ID；章节标题只是
分组，不计入 ID，解释性文字和链接也不计。

## Direct 代码快速入口

<!-- 已发布的每个 vLLM-Omni 组件 rules.md 都以这一节开头。它正是让一页规则能被
     "一遍读完就能用"的东西：读者按 意图 → 规则组 → 首批要打开的源码 定位，而不是
     通读整页。下面的 -0a 规则说明这张表怎么用，请保留。 -->

- **<PREFIX>-0a — 先用意图选行，再用 diff 验证范围。** 只合并下表命中的规则和源码
  入口，不在动手前手工枚举整页。命中多行时取并集，不能只选看起来最接近的一行。
  PR 描述只负责导航，冲突时以 live diff 和 consumer 为准。
- **<PREFIX>-0b — 命中源码后停止文档导航。** 打开第一批源码后沿 producer→consumer
  审查；只有调用链跨 owner 或具体未知量阻塞时，才多打开一个 owner 或 guide。

| 正在做什么 | 精确规则组 | 第一批 live 源码 |
|---|---|---|
| <intent phrase, the words a PR title would use> | `<group-name>`：`<PREFIX>-1a`–`1c` | `<path.py>::{<fn>,<fn>}` → `<next.py>::<fn>` |
| <second intent> | `<group-name>`：`<PREFIX>-2a` | `<path.py>::<fn>` |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次<该 owner 的>审查 | `<PREFIX>-1a`, `<PREFIX>-1b` |
| `<group-name>` | <the specific trigger> | `<PREFIX>-2a` |

## 规则

### <PREFIX>-1a <short name>

- 触发：<when this applies — an observable condition, not a vibe>
- 必须：<the required action>
- 禁止：<the forbidden action>
- 验收：<the exact check that proves compliance — a command, a file:line, a test>

<!-- ID 约定：由 owner 推出的 3-4 字母稳定前缀，然后一位数字表示组、一个字母表示
     组内第几条。目前在用：CONF（configuration）、SERV（serving）、DIFF（diffusion）、
     EXEC（model-executor）、HY3（hunyuan-image3）、VOMNI-CFG（仓库级 config）。
     **已发布的 ID 永不重新编号** —— 评审和 incident 会引用它；要淘汰就 retire。 -->
