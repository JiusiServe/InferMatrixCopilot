---
title: "Diffusion 测试替身与类型契约"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #8418"]
confidence: high
---

# Diffusion 测试替身与类型契约

## DIFF-FIXTURE-1a — streaming executor 替身须保留实际消费的状态与类型

- 触发：修改 `_PipelineBackedEngine`、executor liveness watcher 或 streaming output 测试的 payload/queue helper。
- 强制：替身提供被实际路径读取的 `is_dead` 初值、failure callback 与 health-check 接口，保留已有 streaming 断言和 CPU collection。修复类型收窄时先绑定 `dict.get()` 结果再 `isinstance`，非 dict payload/metadata 仍返回空 dict；queue 构造的类型参数与其真实输出一致。
- 禁止：遗漏 watcher 读取的属性；以删除 streaming 断言、改 CI 路由或跳过变更文件 mypy 解决 fixture 失败；由这次类型改写推断其他合法写法一概错误。固定 `is_dead=False` 只覆盖存活路径，不能证明 fatal teardown 已被测试。
- 验收：目标 streaming module 的 `core_model and cpu` pytest 与变更文件 mypy 门禁通过；若同时宣称死亡处理 coverage，另使替身进入死亡分支并断言 `DIFFUSION_PROC_DEAD` 与 teardown。^[PR #8418]
