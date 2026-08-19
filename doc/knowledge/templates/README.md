# 知识页模板

仓库根目录 `knowledge/` 那棵精选 wiki 的**可直接复制骨架**。
工作流、决策树和门禁规则在
[`../writing.md`](../writing.md)；**这些文件是骨架的唯一
副本** —— 那份文档链接到这里而不是再抄一遍，因为上一版正是两份副本，最终漂移成了
两套。

这些文件住在 `knowledge/` **之外**，所以不过 wiki 门禁（否则它们的占位符会直接失败）。
把其中一个复制到正确的 owner 目录，填掉 `<...>` 占位符，删掉开头的
`<!-- TEMPLATE -->` 注释，在最近的 `_index.md` 里注册这一页，然后校验。

## 什么情况用哪个文件

| 复制这个 | 用来创建 | 放到 |
|---|---|---|
| [`_index.md`](_index.md) | 一个目录的路由表 | 任何新建的主题/组件/模型目录 |
| [`repo-index.md`](repo-index.md) | 一个**仓库**入口索引 | `knowledge/repos/<repo>/_index.md` |
| [`rules.md`](rules.md) | 一个 always-on 门禁页 | 最近的 owner 目录 |
| [`architecture-component.md`](architecture-component.md) | 共享模块的架构页 | `repos/<repo>/components/<module>/architecture.md` |
| [`architecture-model.md`](architecture-model.md) | 模型架构页 | `repos/<repo>/models/<model>/architecture.md` |
| [`guide.md`](guide.md) | 方法 / how-to 页 | 组件或模型 owner 根目录；工作主题集合可用 `guides/` |
| [`incident.md`](incident.md) | 一次复盘记录 | `<owner>/incidents/YYYY-MM-DD-short-name.md` —— **仅**在通过三项准入门禁后 |

## 每个模板对照的那篇实页

模板编码的是 vLLM-Omni 树**已经在遵守**的约定。占位符含义不清时，去打开实页 ——
它才是 ground truth，这个目录不是：

| 模板 | 去读这篇已发布的页面 |
|---|---|
| `rules.md` | [`components/configuration/rules.md`](../../../knowledge/repos/vllm-omni/components/configuration/rules.md) · [`models/hunyuan-image3/rules.md`](../../../knowledge/repos/vllm-omni/models/hunyuan-image3/rules.md) |
| `_index.md` | [`components/_index.md`](../../../knowledge/repos/vllm-omni/components/_index.md) |
| `repo-index.md` | [`repos/vllm-omni/_index.md`](../../../knowledge/repos/vllm-omni/_index.md) |
| `architecture-component.md` | [`components/diffusion/architecture.md`](../../../knowledge/repos/vllm-omni/components/diffusion/architecture.md) |
| `architecture-model.md` | [`models/hunyuan-image3/architecture.md`](../../../knowledge/repos/vllm-omni/models/hunyuan-image3/architecture.md) |
| `incident.md` | [`ci/incidents/`](../../../knowledge/repos/vllm-omni/ci/incidents/_index.md) |

## 已发布的树强制的三条约定

1. **`rules.md` 以 Direct 代码快速入口开头。** vLLM-Omni 现有的 12 个 owner 规则页
   （5 个 component + 7 个 model）全都如此：意图 → 规则组 → *第一批 live 源码*，
   写成 producer→consumer 链。没有它，读者必须消化整页才能找到真正适用的那 3 条规则。
2. **规则 ID 带 owner 前缀，且永不重新编号。** 一个 owner 一个前缀：vLLM-Omni 在用
   `CONF`、`SERV`、`DIFF`、`EXEC`、`SCHED`、`VOMNI-CFG`、`HY3`、`COSMOS`、`FLUX2`、
   `KREA`、`MCPMO`、`MING`、`Q3TTS`，另有 afd-plugin 的 `AFD` 和通用 `REV`。新 owner
   起新前缀，不复用别人的。评审和 incident 会引用这些 ID，所以只能 retire 一个 ID，
   不能改派。
3. **`_index.md` 的 frontmatter 是必填，不是可选。** 全树 123 个索引页里，109 个沉淀层
   索引全部带着它，`check_wiki_lint.py` 在沉淀层强制它。只有证据层
   （`incidents/`、`history/`、`results/`）的 14 个索引不带。

## 复制之后

```bash
python knowledge/tools/check_knowledge_tree.py    # 结构 / 索引 / 链接 / incident
python knowledge/tools/check_wiki_lint.py         # frontmatter + 标签分类法
```

两个都必须打印 0 错误（提醒需要人判断，不是必须清零）。
**没有被任何 `_index.md` 链接的页面会在第一个检查里失败。**
