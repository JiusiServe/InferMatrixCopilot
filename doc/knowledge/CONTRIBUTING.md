# 知识写入入口

本页是**人工写入**知识树的短入口，不承载全部细则。先按任务选一篇专题，不要每次落盘都读完整套规范。

## 先确认你在哪条路径上

知识只由这三条路径更新。**目标仓库不会向本仓库提 PR** —— 它的 owner 走 `[Knowledge]`
issue，由维护者转成第 3 条路径。

| 路径 | 触发 | 谁写 | 细则在哪 |
|---|---|---|---|
| **`imupdate`** | 上游发版或目录变化 | agent 产出、人工审核 | [发版漂移审计](../contributing/release-maintenance.md) |
| **运行中的 agent** | 复盘、记录一条教训 | agent **只能提 candidate**，人工晋升 | [writing.md §2](writing.md) + `SPEC/memory/skills.md` |
| **人工** | 维护者沉淀一条规则 | 维护者（可源自一条 `[Knowledge]` issue） | **本页以下全部内容** |

**下面的「最短落盘流程」是第 3 条路径的流程。** 前两条各有自己的产出与门禁：
`imupdate` 只更新机器已经证明的结构事实（release baseline、model catalog、source
map、SHA pin、adapter manifest），不做 owner 归属判断，也不生成或改写规则；运行中的
agent 只提 candidate。落盘位置和页型选择属于人工路径，两个校验器**三条路径共用**。

现行契约只有四样：本页、[contributing/](contributing/_index.md)、[SCHEMA.md](SCHEMA.md)
和两个校验器。[知识重组计划](../archive/PLAN-knowledge-reorg.md) 是已归档的历史记录，
不是目录契约；批量整理仍按 owner 分批、同义结论 union-first 合并。SCHEMA 只补
frontmatter、标签和溯源元数据，不能据此发明第二套知识结构。

## 正在做什么

| 任务 | 只需继续读 |
|---|---|
| 判断内容放 `general/`、`repos/`、component、model 还是 `local/` | [目录与归属](contributing/layout.md) |
| 新增 `_index.md`、`rules.md`、`architecture.md` 或普通页面 | [页面与索引](contributing/page-rules.md) |
| 从 PR/review 复盘并提炼规则 | [复盘与规则摄取](contributing/incidents.md) |
| 文件太长、目录太挤、dev 要拆前后端或模块/模型长大 | [何时拆分](contributing/scaling.md) |
| 新增、移动、重命名、删除 Markdown，或准备提交 | [同步与校验](contributing/validation.md) |
| 改动 vLLM-Omni 的 owner 页、SHA pin 或 `sources:` | [同步与校验](contributing/validation.md) 的发版审计一节 |

所有专题入口见 [contributing 索引](contributing/_index.md)。

## 最短落盘流程

1. 先确定内容的最近 owner 和目标目录，再选载体：硬门禁进 `rules.md`，稳定职责和数据流进 `architecture.md`，展开方法进 `guides/`。已有文件不能反过来证明 owner。
2. 按上表只选一篇与当前动作匹配的专题；位置不确定时选择 [目录与归属](contributing/layout.md)，不要为了保险横向通读。
3. 写正文，同时更新最近 `_index.md`；父级只增加路由，不复制正文，不预建空目录或占位页面。
4. 用户要求复盘时，动笔前先完成[语义分流台账](contributing/incidents.md#动笔前的语义分流台账)，不能先打开 `rules.md` 再把不适合的内容往外搬。硬门禁进 `rules.md`，稳定职责和数据流进 `architecture.md`，非硬门禁方法进 `guides/`，一次性历史默认不落盘；incident 只有通过三项准入门禁才创建。
5. 对照本页“交付前五项”检查链接、索引、隐私和拆分阈值，然后运行：

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

## 不能放宽的 P0

- 只保留一套正式知识树，不建 `_private/`、兼容副本或第二套私人索引。
- 机器地址、账号、cache、venv、token、密钥和用户绝对路径只属于 Git 忽略的 `local/`；密码、token 和私钥正文不写入文件。
- 一条知识只有一份正文，其他入口只链接；不复制类似规则。
- 长期知识只写本仓库的 `general/`、`repos/` 和贡献规范，不推进系统、全局或个人 memory。
- 仓库、模块、模型和机器规则不互相继承；当前任务只加载真正命中的 owner。
- 新增、移动、重命名、拆分或删除 Markdown 时，必须在同一修改中更新索引和所有链接。
- PR/review 学习只能落可执行规则：完整 diff、评论、thread、commit 和回放输出只在
  整理时进入 Git 忽略的临时目录；批次结束必须删除。正式树只更新最近 component 或
  model owner 的 `rules.md` 及必要索引，不新增 PR case/history/result/incident 页面。
- 非 PR 学习的既有 guide/architecture 继续按原 owner 维护；不得把不同模型、组件、
  benchmark 和 review 内容压成一篇 catch-all 页面。
- 评测 cases、hidden labels、predictions、judgments 和 run reports 属于 `eval/`，
  不得混入产品知识树或 adapter 默认 briefing。

## 交付前五项

- [ ] 位置落在内容的**最近 owner**，owner 证据是稳定边界（源码目录 / 维护职责 /
  测试 / 运行流程），没有把工作主题和代码模块套娃。
- [ ] 最近 `_index.md` 能找到唯一正文，旧路径没有残留有效链接；父级和其他入口只链接，没有复制正文。
- [ ] 语义分流台账已完成；`rules.md` 候选逐条通过 purity audit，方法、架构和历史证据没有混入。
- [ ] 没有公开机器信息、凭据、私人路径或本地临时产物。
- [ ] `python knowledge/tools/check_knowledge_tree.py` 和 `python knowledge/tools/check_wiki_lint.py`
  都通过，并已检查当前完整 diff。
