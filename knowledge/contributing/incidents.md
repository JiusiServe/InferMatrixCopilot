# 复盘与规则摄取

## 唯一正式产物是规则

用户要求“复盘”、“总结教训”或“沉淀经验”时，先做四件事：

1. 用 live 证据说明为什么发生；
2. 说明原有规则、校验、测试或路由为什么没发现；
3. 把“下次怎样提前阻止”写进最近 owner 的 `rules.md`；
4. 写出能证明新规则真的会拦住同类问题的最小验收。

PR/review 学习不新增 `incidents/`、`history/`、`results/`、case 页面或 raw archive。
规则一时无法写清时继续在临时目录整理，不得用“先保存原始材料”绕过归纳。
现存错题和历史文件是旧内容，不是新增知识的模板。

正常开工仍从 `_index.md`、`rules.md` 和职责地图进入，不能要求人或 agent 先猜 incident 路径。

“属于某仓库”不等于“写进仓库根规则”。选择落盘位置前必须先通过
[仓库根 `rules.md` 准入门禁](page-rules.md#仓库根-rulesmd-准入门禁)；专项硬约束下沉到
对应工作主题或代码 owner，根规则只负责路由。

## 低成本、完整阅读的摄取流程

1. 用 GitHub API/CLI 在 Git 忽略的临时目录抓取完整 PR body、diff、commit、review、
   inline thread、作者回复和必要 CI 结论；抓取本身不调用模型。
2. 用路径、symbol 和 owner 做确定性路由；不要先运行完整 MCP PR Review。
3. 在临时材料仍完整时列出每条实质 reviewer 结论，逐条映射到最近 component/model
   owner 的稳定规则；同义结论 union-first 合并，不能靠摘要静默丢失细节。
4. 需要高级模型归纳时，每个 owner 批次最多一次无工具 Performance 单次调用；禁止
   ensemble、reducer、judge、仓库漫游和“为了保险”重复 review。
5. 机械检查“所有实质结论 → 规则 ID 或明确不采纳理由”，再运行知识目录和 wiki lint。
6. 只提交 `rules.md`、必要 `_index.md` 和规范修改；无论成功失败都删除临时 raw、
   replay、coverage ledger 和索引。相同 PR/head 不重复学习。

速度优化不能削弱信息覆盖：省掉的是重复模型阅读，不是原始 thread、修复往返、正向
验证或边界条件。最终规则必须包含触发、强制动作、禁止项和最小验收。

## 非 PR 事故的 Incident 准入门禁

PR/review 学习始终不创建 incident。其他事故也默认不创建；不能因为复盘材料很多、内容
已从规则中剔除，或担心“以后也许有用”就增加错题。确需创建时，下面三项必须同时有
具体答案：

- `RULES_DONE`：哪些可执行结论已经写入最近 owner 的规则，哪些稳定职责或数据流已经写入架构；
- `UNPRESERVED_EVIDENCE`：还有什么证据无法由规则、架构或 Git/PR 历史有效承载；
- `FUTURE_QUERY`：未来遇到什么具体问题时会独立查询这份证据。

任一项为空就不创建。用户明确要求保存完整事故记录时可以创建，但仍须先提炼规则，并填写三项准入理由。语义分流是把内容放进正确执行面，不是增加文件数量。

## 非 PR 事故和既有错题放哪里

| 已验证的根因 | 放置位置 |
|---|---|
| 通用 SSH、WSL、PowerShell、文档或 Git 错误 | `general/<对应主题>/incidents/` |
| 某仓库的 CI、benchmark、review 或 remote 流程错误 | `repos/<仓库>/<对应主题>/incidents/` |
| 多模型共用的 diffusion、serving、frontend 或 backend 错误 | `repos/<仓库>/components/<模块>/incidents/` |
| 某模型专有实现、配置或 checkpoint 错误 | `repos/<仓库>/models/<模型>/incidents/` |

根因未查清时默认继续调查，不急着新建错题。用户明确要求保留调查记录时，才暂放最近的仓库主题并标为“待归类”；查清后移到最终 owner，同时修正链接。

一件事故只保留一篇完整正文。其他位置只链接，不复制一份类似记录。

## 文件名、字段和状态

文件名：

```text
YYYY-MM-DD-short-name.md
```

页面开头不用 YAML，直接写人能读懂的字段：

```markdown
# 容器重启后 SSH 连接超时

- 编号：`inc-YYYY-MM-DD-short-name`
- 归属：`general/remote`
- 状态：处理中
- 搜索词：SSH、timeout、container restart
- 影响范围：远端验证
```

状态只使用：

- `待归类`：还不知道最终应该放哪里；
- `处理中`：原因或修复尚未验证；
- `已验证`：原因、修复和证据完整；
- `已提炼`：稳定规则已进 guide、rules 或 architecture；
- `仅历史`：对当前代码已不适用，但仍值得保留。

状态变化不要求移动文件，避免链接反复变化。

## 正文模板

```markdown
# 一句话故障标题

- 编号：`inc-YYYY-MM-DD-short-name`
- 归属：`repos/example/ci`
- 状态：处理中
- 搜索词：……
- 影响范围：……

## 准入理由

- `RULES_DONE`：……
- `UNPRESERVED_EVIDENCE`：……
- `FUTURE_QUERY`：……

## 当时在做什么

版本、任务和必要前提。不写私人地址、token 和用户绝对路径。

## 看到了什么

用户能观察到的现象和最小错误信息。

## 会造成什么影响

失败、错误判断或潜在风险。

## 真正原因

已验证的原因。没有验证时明确写“当前猜测”。

## 怎样修复

实际有效的修改或正确操作。

## 怎样证明修好了

测试命令、实际运行结果或其他证据。

## 下次怎样避免

可以重复执行的检查步骤或规则。

## 相关资料

代码、issue、PR、日志摘要或相关知识页面。
```

## 既有错题维护要求

- 不从新的 PR/review 学习新增错题；先更新最近 owner 的规则。
- 在同一修改中更新所属 `incidents/_index.md`。
- 错题末尾链接“已提炼到”的规则；规则页不复制整篇事故过程。
- 不把聊天流水账、完整长日志、未验证猜测或只有本机路径的记录当长期错题。
- 长日志只保留关键错误和原始产物的可定位来源。
