# engine/steps/rebase_ext.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~101 · step 库（委托） · refactor-status: ok`

## 职责
`rebase.run_external` —— 向 locked 的 5 阶段编排器做**受监控的子进程委托**
（**包装，而非重写**）。

## Steps
`rebase.run_external`（script/write_workspace）。

## 不变量
- **零回归**：它**不重新实现**那条流水线。
- 把父进程的 `state.json` 流式送进 RunTrace；**陈旧状态守卫**防止上一次 run 的
  `phase=done` 掩盖本次崩溃；失败被分类成升级材料。
- 点名父包（被允许的仓库字面量，泄漏上限为 1）。

## 边界 —— 不属于这里
自身不含 rebase 逻辑；除委托给 `rebase/monitor` 外不做解析。

## 依赖（允许）
`rebase/monitor`、`engine/step`、`._common`；stdlib 的 asyncio/subprocess。

## 测试
`test_rebase_monitor.py`（它驱动的那个 monitor）。

## 重构备注
可以接受。那一个仓库字面量（`"vllm-omni-rebase-agent"`）是**设计使然**的委托文本 ——
**不要过早模板化**；如果将来真的包装了第二个外部编排器，再把名字抽到 adapter。
