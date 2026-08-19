# engine/steps/rebase_native.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~397 · step 库（候选的原生 rebase） · refactor-status: ok`

## 职责
夜跑 rebase 的**候选**原生分解版本，import 父包自己的阶段 wrapper 与
`node_rebase_module`。

## Steps（9 个）
`rebase.prelude`、`rebase.phase1..phase5`、`rebase.phase2_prepare`、
`rebase.module_rebase`、`rebase.phase2_finalize`、`rebase.compare_with_locked`。

## 公开契约（可从 `engine.steps.rebase_native` import）
`_RUNTIME`（按进程记忆化的父运行时；测试 fixture 会清掉它）。

## 不变量
- **对 planner 不可见**（只存在于 candidate playbook `repo-rebase-native`）。
- phase-4 的 push 在 copilot 的推送守卫之后；env 导出被记 trace（`env_exported`）。
- **委托给父包的函数** —— 不重新实现各阶段。
- 点名父包（被允许的仓库字面量，泄漏上限为 6）。

## 边界 —— 不属于这里
不含晋升逻辑；不重新实现 rebase。**只是 wrapper。**

## 依赖（允许）
`rebase/monitor`、`adapters/base`（wave 交叉核对）、`engine/step`、`._common`；
以及外部的 `agent.*` 包（惰性 import，ImportError → BLOCKED）。

## 测试
`test_rebase_native.py`。

## 重构备注
**按设计**与父包耦合 —— 那 6 个仓库字面量和那些父包 import 是**委托面，不是坏味道**。
它用命令式方式注册（工厂/直接 handler 混用）—— 这是 `@step` 被认可的例外。
**只有在推进晋升路径（candidate → active → locked）时才动它。**
