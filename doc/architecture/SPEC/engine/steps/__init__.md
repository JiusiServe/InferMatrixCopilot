# engine/steps/__init__.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~34 · step 库聚合 · refactor-status: ok`

## 职责
为了**注册副作用**而 import 每个 step 模块，并暴露 `register_builtin_steps`。

## 功能
import `_common` + 全部 8 个领域模块（rebase 侧现为 `rebase_v3` + `rebase_knowledge`；
从而运行它们的 `@step`/`register_step` 装饰器，
填充 `_common._COLLECTED`）；`register_builtin_steps` 把这份集合冲刷进一个
`StepRegistry`。

## 公开契约
`register_builtin_steps(registry) -> registry`。

## 不变量
- import 这个包会把所有 step **恰好注册一次**（靠模块缓存）；对每个全新 registry，
  `register_builtin_steps` 是幂等的（**A4**）。
- **这份 import 列表就是 step 模块的权威集合** —— 新的 step 模块必须加到这里才会被发现。

## 边界 —— 不属于这里
不含 step 逻辑；除冲刷之外不含注册策略。

## 依赖（允许）
`engine/registry`、`._common`，以及那 8 个 step 模块。

## 扩展点
新的 step 领域模块 → 加进这份副作用 import 列表。

## 测试
每次 `register_builtin_steps(StepRegistry())` 调用都会覆盖（冒烟：45 个 step）。

## 重构备注
可以考虑自动发现（遍历这个包）以去掉手工 import 列表 —— 但显式 import **可 grep**，
且拼错时会大声失败，所以当前形式是可以接受的。若保持手工，这份列表 + `_COLLECTED`
就是"到底存在哪些 step"的唯一来源。
