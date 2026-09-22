---
title: "Scheduler shared lifecycle 规则"
created: 2026-09-22
updated: 2026-09-22
type: rule
tags: [vllm-omni, components, scheduler]
sources: ["PR #5461"]
---

# Scheduler shared lifecycle 规则

## SCHED-6a2 — AR 与 generation 的共享生命周期只能有一个 canonical 实现

- 触发：把 AR/generation scheduler 的 I/O、输出包装、finish 或统计逻辑移入
  `OmniSchedulerMixin`，或修改该 mixin 及任一 scheduler 的 shared hook。
- 强制：两类 scheduler 共用 pending connector/chunk 输入处理、wait queue restore、
  `OmniSchedulerOutput` 包装、失败 KV load 的 terminal output、finished IDs、队列清理、
  stats/events 和 finish cleanup；`NewRequestData` 转成 Omni 结构时逐字段无损，并保留已经
  是 Omni 类型的 fast path。AR 的 synthetic-abort 等差异策略必须作为显式参数留在调用点。
- 禁止：把共享生命周期复制回两个 subclass；重建 `NewRequestData` 时只挑当前已知字段；
  在 mixin 内按 scheduler 类型隐式猜差异策略；失败 KV load 只改状态而不发 terminal output。
- 验收：同一组 contract 测试分别驱动 AR 与 generation 输入路径；断言 base dataclass 的
  每个字段均被转交、现有 Omni entry 保持 identity、失败 KV load 终止输出、finished ID/
  stats/events/cleanup 一致，并单独验证显式 abort policy。 ^[PR #5461]
