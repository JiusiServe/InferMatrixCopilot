# ci/buildkite.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~253 · 边缘（CI provider 客户端） · refactor-status: ok`

## 职责
rebase 引擎受守卫构建生命周期所注入的 `CIClient` —— 定界到单条 pipeline 的
Buildkite REST 客户端。

## 公开契约
`BuildkiteCI(token, org, pipeline, build_env?, request?, ignore_branch_filters=False)`；
协议方法 `create_build / get_build / find_builds_by_meta / cancel_build /
get_job_log / list_jobs / retry_job`；采纳/基线查询 `builds_for_commit`、
`latest_builds`；异常 `BuildkiteError`。`request`（`RequestFn`）可注入（测试
fake 绕开 urllib）。

## 不变量
- **A5**：org、pipeline、build env 全部来自 adapter（`ci.org` + `rebase.ci.*`）
  —— 这里不点名任何仓库、pipeline 或队列。
- **归一化在这个边界发生**：build dict 的 `id` 是 build **number** 的字符串
  （REST 按 number 寻址，UUID 不可路由），`web_url` 兜底拼出 —— `ci_loop`
  的 op 台账因此存跨进程重启仍可解析的 id。
- **逐调用点的错误契约**：变更类调用与身份查询（create/cancel/
  find_builds_by_meta/retry 非 400/builds_for_commit/latest_builds）在意外
  响应上**抛** `BuildkiteError` —— op 标记 created 之前必须先看到失败，恢复/
  采纳必须升级而不是猜（API 错误绝不当"无匹配"）；轮询读（`get_build`→`{}`、
  `get_job_log`→`""`）**降级**不中止监控（**E2**；最终 reconciliation 裁决）。
- `create_build` 只把**一种**响应转成类型化拒绝：422 + "branches have been
  disabled" → `BuildCreationRefused`（round loop 据此报 schedule-only 指引，
  **B1** 路由的原料）；其余 4xx 一律 `BuildkiteError` —— 那条指引在运维性
  错误（401/403/404…）上会误导。
- adapter 显式 opt-in（`rebase.ci.ignore_branch_filters`）才在 create 上发送
  `ignore_pipeline_branch_filters`（schedule-only pipeline 的官方补救；step
  级 branch filter 依然生效）；默认**绝不发送**。
- `list_jobs` 两路读取（/jobs 端点 → build 内嵌 jobs），两路都不可读时**抛**
  —— 取数失败必须与"确实没有 job"可区分，否则 API 故障期间的 reconciliation
  会静默通过。
- `retry_job` 的 400 = 该 job **类型**不可重试（`(None, False)`，归 ignorable）；
  其他失败一律抛 —— API 故障绝不被当成代码失败去派发变更 agent。

## 边界 —— 不属于这里
不含轮次/监控/失败分类（`rebase_engine/ci_loop`）；不含推送
（`rebase_engine/push_to_ci`）；同头 schedule 构建的**采纳决策**在
`ci_loop.run_ci_rounds` + `rebase.v3_ci`，这里只提供查询面。

## 依赖（允许）
stdlib 的 `json`/`urllib`；`BuildCreationRefused` 从 `rebase_engine.ci_loop`
惰性 import（类型化拒绝定义在消费方）。

## 扩展点
新的 provider 客户端 = 实现同一 `CIClient` 协议的**新文件**，不是这里的分支。

## 测试
`test_ci_wiring.py`（注入 RequestFn：归一化、逐调用点错误契约、branch-filter
opt-in 默认关、BuildCreationRefused 只认 422+disabled、list_jobs/retry_job）。

## 重构备注
干净。保持"变更抛 / 轮询降级"的逐调用点契约稳定 —— `create_build_guarded`
与最终 reconciliation 都押在它上面。对 `ci_loop.BuildCreationRefused` 的
惰性 import 是一条轻微的向内依赖（边缘 → rebase_engine）；接入第二个
provider 时把这个异常类型上提到共享的 CI 契约模块。
