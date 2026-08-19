# 知识库文档

关于**怎么写和维护** `knowledge/` 那棵精选 wiki 的一切，都在这个目录里。
**知识本身不在这里** —— 它在仓库根的 [`knowledge/`](../../knowledge/)，
那里现在只剩数据面：`general/`（通用经验）+ `repos/`（逐仓库知识）。

> **为什么分开：** `knowledge/` 曾经既装知识页、又装"怎么写知识页"的规范。
> 前者是**数据**（被 `doc_search`/`doc_read` 检索、随 wheel 发布、由校验器扫描），
> 后者是**文档**（人类读一遍就去动手）。两者的读者、生命周期和校验规则都不同，
> 混在一起会让每个打开 `knowledge/` 的人先踩过一层不该读的规范。

## 知识由谁更新

只有三条路径。**目标仓库（vLLM-Omni）不会向本仓库提 PR** —— 它的模块/模型 owner 提
`[Knowledge]` issue（`.github/ISSUE_TEMPLATE/knowledge-rule.yml`），由维护者转成第 3 条。

| 路径 | 什么时候 | 谁写 | 入口 |
|---|---|---|---|
| **`imupdate`** | 上游发版、目录变化、registry/deploy/路径路由/source pin 过期 | agent 产出、人工审核 | [`../contributing/release-maintenance.md`](../contributing/release-maintenance.md) |
| **运行中的 agent** | 复盘、"记一条教训" | **只能提 candidate**，晋升是人工动作 | [`writing.md`](writing.md) |
| **人工** | 维护者沉淀一条规则或修订页面 | 维护者 | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

三条路径**共用**同一套落盘位置判断、页型选择和两个校验器 —— 差别只在谁触发、
以及产出在生效前要过哪道门。

## 该读哪一篇

| 你要做什么 | 看这篇 |
|---|---|
| 第一次写知识页 —— 决策树、页型、copilot 怎么消费、两道门禁 | [`writing.md`](writing.md) |
| 需要**有约束力**的那条规则（与上面冲突时以它为准） | [`CONTRIBUTING.md`](CONTRIBUTING.md) → [`contributing/`](contributing/_index.md) |
| 直接开写，要现成骨架 | [`templates/`](templates/README.md) |
| 看一遍填好的中文实操走查 | [`maintainer-walkthrough.md`](maintainer-walkthrough.md) |
| frontmatter、标签分类法、生命周期 | [`SCHEMA.md`](SCHEMA.md) |
| 三个端到端的贡献示例 | [`samples/`](samples/) |
| 知识树长什么样、有哪些入口 | [`tree-map.md`](tree-map.md) |
| 这棵树从哪来、授权与同步边界 | [`../architecture/KNOWLEDGE.md`](../architecture/KNOWLEDGE.md) |

## 两个校验器

它们仍然住在被校验的那棵树旁边（`knowledge/tools/`），因为它们是**代码**，不是文档：

```bash
python knowledge/tools/check_knowledge_tree.py    # 结构 / 索引 / 链接 / incident
python knowledge/tools/check_wiki_lint.py         # frontmatter + 标签分类法
```

两个都必须打印 0 错误（提醒需要人判断，不要求清零）。注意它们**跨树读取本目录**：
树校验器在这里检查 `CONTRIBUTING.md` 的长度门，wiki lint 从 `SCHEMA.md` 读标签分类法
—— 搬动这两个文件时**必须同时改那两处路径**。

`repos/vllm-omni/` 那一片还有**第三道门**，两个校验器看不见它：owner 入口页、正文里的
SHA pin 和 `sources:` 由 `tools/audit_vllm_omni_release.py` 按 release baseline 对账，
任何触及该切片的 PR 都会在 CI 里跑 `enforce`。见
[同步与校验 §发版审计](contributing/validation.md#vllm-omni-页面还有一道发版审计)。
