# engine/registry.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~31 · 引擎底座 · refactor-status: ok`

## 职责
`StepRegistry`：名字 → `StepSpec` 的映射 —— **名字字符串解析到 handler 的唯一地点**。

## 功能
`register` / `get` / `__contains__` / `names`。

## 公开契约
`StepRegistry`，带上述方法。

## 不变量
- 重复注册直接抛错；对未知名字调用 `get` 会连同**已注册集合**一起抛出
  （**大声失败，绝不静默**）。

## 边界 —— 不属于这里
只做存储/查找 —— 不执行、不含策略、不自我填充（填充由
`steps.register_builtin_steps` 负责）。

## 依赖（允许）
`engine/step`。

## 扩展点
不需要；它就是一个容器。

## 测试
多数测试通过 `register_builtin_steps` 间接覆盖。

## 重构备注
极简且正确。**不要**在这里加过滤/策略 —— 那属于 planner（负责选择）和 store
（负责校验引用）。
