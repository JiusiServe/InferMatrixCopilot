# 贡献入口

本页只是手工维护知识树的短入口，不再承载全部细则。先按任务选一篇专题，不要每次落盘都读完整套规范。

本目录以 `zuiho-kai/claude-workflow-starter` 的贡献流程为内容和目录规范来源；
vendored 后的批量整理还必须遵守 [知识重组计划](../doc/PLAN-knowledge-reorg.md) 的
owner-scoped inventory、union-first 和证据保留约束。[SCHEMA.md](SCHEMA.md) 只补
frontmatter、标签和溯源元数据，不能据此发明第二套知识结构。

向 `zuiho-kai/claude-workflow-starter` 这个公开上游提交 commit 时使用 DCO sign-off（`git commit -s`）。第三方接入后按自己的贡献政策保留、修改或删除这条要求。

## 正在做什么

| 任务 | 只需继续读 |
|---|---|
| 判断内容放 `general/`、`repos/`、component、model 还是 `local/` | [目录与归属](contributing/layout.md) |
| 新增 `_index.md`、`rules.md`、`architecture.md` 或普通页面 | [页面与索引](contributing/page-rules.md) |
| 复盘、提炼规则或确实需要保留错题 | [复盘与错题](contributing/incidents.md) |
| 文件太长、目录太挤、dev 要拆前后端或模块/模型长大 | [何时拆分](contributing/scaling.md) |
| 新增、移动、重命名、删除 Markdown，或准备提交 | [同步与校验](contributing/validation.md) |

所有专题入口见 [contributing 索引](contributing/_index.md)。

## 最短落盘流程

1. 确认真实仓库和最近 owner；位置不确定时，本次专题选择 [目录与归属](contributing/layout.md)。
2. 按上表只选一篇与当前动作匹配的专题；不要为了保险横向通读。
3. 写正文，同时更新最近 `_index.md`；不预建空目录或占位页面。
4. 用户要求复盘时先把稳定结论写进最近 owner 的 `rules.md`；错题可有可无。
5. 对照本页“交付前五项”检查链接、索引、隐私和拆分阈值，然后运行：

```powershell
python tools/check_knowledge_tree.py
```

## 不能放宽的 P0

- 只保留一套正式知识树，不建 `_private/`、兼容副本或第二套私人索引。
- 机器地址、账号、cache、venv、token、密钥和用户绝对路径只属于 Git 忽略的 `local/`；密码、token 和私钥正文不写入文件。
- 一条知识只有一份正文，其他入口只链接；不复制类似规则。
- 长期知识只写本仓库的 `general/`、`repos/` 和贡献规范，不推进系统、全局或个人 memory。
- 仓库、模块、模型和机器规则不互相继承；当前任务只加载真正命中的 owner。
- 新增、移动、重命名、拆分或删除 Markdown 时，必须在同一修改中更新索引和所有链接。
- 按内容角色落盘：可执行不变量进入最近 owner 的 `rules.md`，操作方法进入 guide，
  稳定边界进入 architecture，复杂证据按既有 raw-layer 角色保存。不得把不同模型、
  组件、benchmark 和 review 内容压成一篇 catch-all 页面。
- 评测 cases、hidden labels、predictions、judgments 和 run reports 属于 `eval/`，
  不得混入产品知识树或 adapter 默认 briefing。

## 交付前五项

- [ ] 位置符合内容 owner，没有把工作主题和代码模块套娃。
- [ ] 最近 `_index.md` 能找到新页面，旧路径没有残留有效链接。
- [ ] 可执行结论已进 `rules.md`，错题没有变成默认必读入口。
- [ ] 没有公开机器信息、凭据、私人路径或本地临时产物。
- [ ] `python tools/check_knowledge_tree.py` 和 `python tools/check_wiki_lint.py`
  都通过，并已检查当前完整 diff。
