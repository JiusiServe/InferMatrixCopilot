# notify.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~112 · 跨切（升级） · refactor-status: ok`

## 职责
"通知，而不是猜测"的出口通道。

## 功能
`Notifier.escalate` 写出 `ESCALATION.md`、发邮件（配置了就走 Resend 或 SMTP）、
把这次升级记进 trace；`BLOCKED_EXIT` = 3。

## 公开契约
`Notifier(settings, run_dir, trace, run_id)`，带 `escalate(reason, phase,
severity, state_summary, artifacts)`；以及 `BLOCKED_EXIT`。

## 不变量
- 被阻塞的 run 会写出 `ESCALATION.md`、发出通知，调用方以退出码 3 结束。
- **升级是一等结果** —— 绝不被当作错误路径吞掉。
- 邮件失败是尽力而为的，**不得**掩盖升级本身。

## 边界 —— 不属于这里
"要不要升级"由 executor 决定（类型化失败路由）—— 本文件只负责**执行通知**。

## 依赖（允许）
`config`、`run_trace`；stdlib 的 `urllib`/`smtplib`。

## 扩展点
新通道（IM/webhook）→ 在这里加一个方法，由它自己的配置字段开关；
保持 `escalate` 是唯一入口。

## 测试
经 `test_engine.py` 的路由 + 升级断言覆盖。

## 重构备注
干净。如果通道变多，引入一个小的 `Channel` 策略列表，而不是在 `escalate` 内部继续
加分支。
