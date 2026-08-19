# providers/audit.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~109 · 侦测型控制（运行后会话审计） · refactor-status: ok`

## 职责
对已完成的 harness 会话做容纳性违规审计 —— 服务于那些**没有预防型控制可用**的后端。

## 功能
给定该会话的工具事件，检查文件读取是否停留在容纳根内（PR-time worktree + run 目录），
以及只读 scope 下是否出现过 write/edit 调用。**返回 findings；从不修改任何东西。**

## 公开契约
`SessionAudit`（`ok`、`tool_calls`）、`contained_in(path, roots)`、
`audit_events(events, *, roots, ...)`。

## 不变量（**C1**、**C2**、**E2**）
- **侦测型，不是预防型** —— 它是工具治理决策**公开声明的兜底**。它服务于内置工具无法
  关闭的 cursor-agent。**它不阻止任何事，它只报告。**
- **findings 必须浮现，绝不静默丢弃。** 违规交给调用方记 trace 并渲染进 RUN_REPORT。
  一次静默的审计**比没有审计更糟**，因为它暗示存在一个其实并未生效的控制。
- **只放产品策略。** 评测臂在其之上叠加了一条额外的"不得访问 PR 讨论"规则；那是
  ground-truth 泄漏问题，不是产品问题，**刻意不住在这里**。
- **一条有记录的豁免：** cursor-agent 会把 MCP 工具的**结果**缓存进它按项目划分的状态
  目录，再用自己的原生读工具读回来（`_CLI_TOOL_SPOOL`）。那次读回正是桥输出被消费的
  方式，**不是外泄** —— 没有这条豁免，每个用了桥的会话都会被误报（实测发现）。

## 边界 —— 不属于这里
不做强制；不调用厂商；不含评测专属规则。

## 依赖（允许）
仅 stdlib。一个叶子分析模块。

## 测试
经 `test_provider_cursor.py` 覆盖。

## 重构备注
从 `eval/dataset/run_cursor_arm.py` 产品化而来 —— 当初正是这项检查抓到了一次真实的越界
读取（`~/.claude/skills/...`）。**保持它纯粹**，这样评测臂和产品路径的判断不会分叉。
