# SCHEMA — 页面元数据与生命周期

规定 `general/` 与 `repos/` 下**沉淀层**页面的 YAML frontmatter、标签分类法和生命周期
规则（LLMWiki 机制）。目录归属与页面写法仍以 [贡献规范](contributing/_index.md)
为准；本文件只补充元数据机制，不重复目录规范。`repos/jianghan-roleplay-data-pipeline/`
整棵子树暂不适用（保持原样）。

## 分层

- **证据层（默认不新增）**：现存 `incidents/`、`history/`、`results/` 是旧树留下的
  材料。PR/review 学习**一律不写**这一层：新的 raw diff、评论、thread、回放和 case 只在
  整理临时目录存在，规则验收后必须删除。非 PR 事故也默认不新增，只有同时满足
  [复盘与规则摄取](contributing/incidents.md#incident-准入门禁) 的三项准入门禁才创建
  `incidents/` 页面；`history/`、`results/` 不再新增。
- **沉淀层**：`rules.md`、`guides/`、`architecture.md`、`overview.md`、`_index.md`
  等 —— 携带 frontmatter，结论通过 `sources:` 引用外部 PR/代码或既有历史页。
- **PR/review 学习产物**：只允许写最近 owner 的 `rules.md` 与必要 `_index.md`；用
  `sources:` 和段尾 PR 引用提供溯源，不保存原始证据副本。

## Frontmatter（沉淀层必填）

`check_wiki_lint.py` 强制的只有前五项（`title`、`created`、`updated`、`type`、
非空 `tags`）；其余为约定字段，写了就必须合法（`confidence` 只能取三值）。

```yaml
---
title: 页面标题
created: YYYY-MM-DD      # 上游首次提交日期（来源 doc/archive/reorg-audit/baseline/dates.tsv）
updated: YYYY-MM-DD      # 最近实质更新日期
type: rule | guide | architecture | index
tags: [来自下方分类法]
sources: []              # 约定字段：incidents/... 相对路径、PR 号、file:line、上游源码路径
confidence: high | medium | low   # 可选：结论的证据强度（单一来源/有争议时标注）
contested: true                   # 可选：存在未解决矛盾时
contradictions: [相对路径]         # 可选：与本页冲突的页面
---
```

`repos/vllm-omni/` 的 `sources:` 另有机器用途：以 `vllm_omni/`、`tests/`、
`benchmarks/`、`docs/`、`.buildkite/` 开头的条目会被发版审计与上游文件列表对账，
上游删除或重命名后报 `stale_knowledge_source`。见
[同步与校验 §发版审计](contributing/validation.md#vllm-omni-页面还有一道发版审计)。

## 标签分类法

新标签必须先加入此表再使用（防止标签蔓延）：

- 归属：`general`、`vllm-omni`、`afd-plugin`
- 工作主题：`review`、`ci`、`docs`、`git`、`debug`、`bug`、`benchmark`、`environment`、
  `remote`、`agents`、`planning`、`dev`、`rebase`
- 代码/模型轴：`components`、`models`、`diffusion`、`model-executor`、`serving`、
  `scheduler`、`distributed`、`config`、`hunyuan-image3`、`ltx2`、`qwen-omni`、
  `plugin-boundary`、`attention-runtime`、`ffn-runtime`、`connectors`、
  `model-integration`、`execution-platforms`、`compatibility`

## 溯源标记

沉淀层段落引用具体事故/PR 时，段落末尾加 `^[incidents/...]` 形式的来源标记；
页面级证据在 frontmatter `sources:` 列出。每个沉淀层页面至少链接 2 个相关页面
（相对 Markdown 链接，不用 wikilink）。

## 被取代页面

先把仍然有效的独有结论合入最近 owner 的幸存页面，再删除被取代或重复页面并修复
入链。Git 历史负责追溯旧版本；`knowledge/` 内不再维护 `_archive/` 副本。

## 校验

```bash
python knowledge/tools/check_knowledge_tree.py   # 目录/索引/链接/错题/敏感信息
python knowledge/tools/check_wiki_lint.py        # frontmatter/标签/孤页/陈旧度
```
