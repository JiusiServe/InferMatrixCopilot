# rebase/monitor.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~159 · 边缘（外部流水线监控） · refactor-status: ok`

## 职责
为 locked 的 `rebase.run_external` 委托，读取并分类父编排器的状态。

## 公开契约
`build_command`、`parse_parent_state`、`summarize_progress`、`diff_progress`、
`classify_failure`、`build_escalation`。

## 不变量
- 对父进程的 `state.json` **只读**。
- 把退出码 + 状态分类成**类型化失败** + 升级材料。
- **感知陈旧状态** —— 上一次 run 的 `phase=done` **绝不能**掩盖这一次 run 的崩溃。
- 点名父包/路径（被允许的仓库字面量，泄漏上限为 1）。

## 边界 —— 不属于这里
不运行也不重新实现 rebase；不含推送逻辑；不发通知（那是 `notify`）。

## 依赖（允许）
仅 stdlib 的 `json`/`subprocess`。

## 测试
`test_rebase_monitor.py`。

## 重构备注
内聚的监控/分类单元。这里的基线签名比较，正是 `ci/normalize` 模块**当初写出来就是为了
不去继承**的已知弱点 —— 如果将来要收紧这个 monitor 的分类，请**复用 `ci/normalize`**，
而不是再实现一遍字符串比较。
