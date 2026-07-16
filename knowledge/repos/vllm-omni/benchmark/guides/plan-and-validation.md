# Plan / Validation 入口

本文件只保留路由。日常先按任务类型打开对应专题页；不要整篇读历史 runbook。

| 任务 | 读这个 |
|------|--------|
| 写 plan、判断 feature 是否可用、选择 e2e vs fake/unit | [实现与功能验证](../../../../framework/planning/guides/implementation-validation.md) |
| 产品对标、最低 parity、产品书、roadmap、版本目标拆分 | [product_loop_planning.md](../../../../framework/planning/guides/product-loop-planning.md) |
| benchmark 口径、探索/smoke/sweep 区分、scope lock、结果命名 | [benchmark scope](benchmark-scope.md) |
| 远端长测配置验证、复用既有脚本、profiler 不污染 steady-state | [remote_long_run.md](../../../../framework/remote/guides/remote-long-run.md) |
| AR graph / profiling 诊断机制、d-step 分析、PR 远端验证闸门 | [benchmark guides](./_index.md) |
| 新模型 / execution path / public 字段 / multimodal payload / perf PR 开发前 mini spec | [mini_spec.md](../../../../framework/planning/guides/mini-spec.md)，review/merge 前再读 [reviewer_lens_audit.md](../../../../framework/review/guides/reviewer-lens-audit.md)；mini-spec appendix 和 design gates 在 [reviewer_lens_gates.md](../../../../framework/review/guides/reviewer-lens-gates.md) |

硬规则摘要：

- Plan 阶段先 trace lifecycle，再给方案。
- 产品对标 / parity / roadmap 先写用户可感知闭环，再拆 atomic issue / PR / sub-agent。
- 功能验证默认打真实 e2e 路径；fake/unit 不能证明全栈可用。
- Benchmark 先锁被测版本、测量补丁、被测路径、有效指标。
- 用户给出 PR 或“这个规格”时，先读该 PR/config/runner/result JSON 锁 source of truth，再回答或开跑。
- L2/L4 拆分先定义证据边界：L2 CPU/mock 功能 shape guard，L4 真实权重 accuracy/perf/profiling。
- 已有成功脚本或 runbook 时先复用，禁止从零手写等价 runner。
- 非平凡模型适配、execution path、public 字段或 perf PR，开发前先写 mini spec；不能把后续 review 当第一道语义检查。
