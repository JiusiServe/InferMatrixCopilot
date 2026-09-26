# engine/steps/__init__.py —— 规范

<!-- verified-against: 2026-09-26 -->

`LOC ~34 · step 库聚合 · refactor-status: ok`

## 职责
暴露 `register_builtin_steps` 作为唯一的内建 step 模块加载与注册入口；单独
import 本包不会加载写入型 workflow 模块。

## 功能
import `_common` 而不加载领域模块。调用 `register_builtin_steps` 时显式加载
8 个领域模块（rebase 侧为 `rebase_v3` + `rebase_knowledge`），触发各模块的
`@step`/`register_step` 装饰器填充 `_common._COLLECTED`，然后把集合写入给定
`StepRegistry`。

## 公开契约
`register_builtin_steps(registry) -> registry`。

## 不变量
- import 这个包不会加载领域模块；首次组装 registry 才加载全部内建模块。
  Python 模块缓存保证装饰器只运行一次；每个全新 registry 都得到同一集合（**A4**）。
- **`_BUILTIN_MODULES` 就是内建 step 模块的权威集合** —— 新模块必须加入它。

## 边界 —— 不属于这里
不含 step 逻辑；除冲刷之外不含注册策略。

## 依赖（允许）
`engine/registry`、`._common`；只有调用注册函数时才导入那 8 个模块。

## 扩展点
新的 step 领域模块 → 加进 `_BUILTIN_MODULES`。

## 测试
隔离子进程验证 import 惰性；`register_builtin_steps(StepRegistry())` 的现有
组装测试覆盖内建 step 集合。

## 重构备注
保留显式模块列表，避免自动发现把未经审核的 step 带入 registry；模块名拼错在
组装时大声失败。`_BUILTIN_MODULES` + `_COLLECTED` 是内建 step 集合的来源。
