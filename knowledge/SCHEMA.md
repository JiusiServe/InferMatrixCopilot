# SCHEMA — 页面元数据与生命周期

规定 `general/` 与 `repos/` 下**沉淀层**页面的 YAML frontmatter、标签分类法和归档
规则（LLMWiki 机制）。目录归属与页面写法仍以 [贡献规范](contributing/_index.md)
为准；本文件只补充元数据机制，不重复目录规范。`repos/jianghan-roleplay-data-pipeline/`
整棵子树暂不适用（保持原样）。

## 分层

- **原始证据层（不可改写）**：`incidents/`、`history/`、`results/` —— 只读、被引用、
  永不删除或压缩；正文实质（发现、证据、数字、经过）不再编辑。这些文件**不加**
  frontmatter，元数据在正文字段（编号/归属/状态/搜索词/影响范围）。
- **沉淀层**：`rules.md`、`guides/`、`architecture.md`、`overview.md`、`_index.md`
  等 —— 携带 frontmatter，结论引用证据层。

## Frontmatter（沉淀层必填）

```yaml
---
title: 页面标题
created: YYYY-MM-DD      # 上游首次提交日期（来源 doc/reorg-audit/baseline/dates.tsv）
updated: YYYY-MM-DD      # 最近实质更新日期
type: rule | guide | architecture | index
tags: [来自下方分类法]
sources: []              # 结论的证据来源：incidents/... 相对路径、PR 号、file:line
confidence: high | medium | low   # 可选：结论的证据强度（单一来源/有争议时标注）
contested: true                   # 可选：存在未解决矛盾时
contradictions: [相对路径]         # 可选：与本页冲突的页面
---
```

## 标签分类法

新标签必须先加入此表再使用（防止标签蔓延）：

- 归属：`general`、`vllm-omni`
- 工作主题：`review`、`ci`、`docs`、`git`、`debug`、`benchmark`、`environment`、
  `remote`、`agents`、`planning`、`dev`
- 代码/模型轴：`components`、`models`、`diffusion`、`model-executor`、`serving`、
  `hunyuan-image3`

## 溯源标记

沉淀层段落引用具体事故/PR 时，段落末尾加 `^[incidents/...]` 形式的来源标记；
页面级证据在 frontmatter `sources:` 列出。每个沉淀层页面至少链接 2 个相关页面
（相对 Markdown 链接，不用 wikilink）。

## 归档（永不删除）

被取代或重复的页面移入根 `_archive/<原路径>`：从所在 `_index.md` 注销、入链标注
"（已归档）"、幸存页面链接归档页。`_archive/` 不参与索引/链接校验。

## 校验

```bash
python tools/check_knowledge_tree.py   # 目录/索引/链接/错题/敏感信息
python tools/check_wiki_lint.py        # frontmatter/标签/孤页/陈旧度
```
