# metrics.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~493 · 跨切（测量） · refactor-status: oversized`

## 职责
计算并持久化逐 run 的 `metrics.json`（CATQ = Q·S/C）。

## 功能
读取该 run 的 trace/产物；计算 Q（按 kind 在**已知**分量上加权的质量）、
S（由 incident 得出的安全系数）、C（RQS3e 式的对数成本，基于 USD + 墙钟对参考预算）；
写出 `metrics.json`。

## 公开契约
`collect_run_metrics(run_dir, settings, status) -> {quality, risk, cost, catq}`。

## 不变量
- **E3**：metrics 是关于一次 run 的**事实**，且**绝不能把这次 run 搞坏** ——
  每个失败都被捕获并记 trace（`metrics_error`）；**run 的成败与 metrics 无关**。
- Q **只使用已知分量**（重新归一化，并标 `partial`）；judged/GT 稍后合并，
  **绝不编造**；被升级的 run 记安全弃权分。
- incident 来自显式事件 + 既有的 out_of_scope/tool_refused/patch_review-revise。
- **成本绝不编造。** harness 后端不向 span 记账暴露 token（每项都是 `tok_out=0`），
  所以来源被记为 `subscription`，**不发明 USD** —— 这正是 harness 的成本优势
  **是假设而非测量**的原因（`providers/base.md`）。

## 边界 —— 不属于这里
**不影响控制流。只做测量。**

## 依赖（允许）
`config`、`run_trace`（读事件）；价格表住在这里。

## 扩展点
新的质量分量 / 成本项 → 用**仅限已知**的规则扩展对应的子计算；
把参考预算记录在 `config` 里。

## 测试
`test_metrics.py`。

## 重构备注
最大的跨切文件；三个子指标（Q、S、C）+ 价格表 + CATQ 组装挤在一个模块里。
**建议拆分**：`metrics/quality.py`、`metrics/safety.py`、`metrics/cost.py`、
`metrics/__init__.py`（组装 + `collect_run_metrics`）。那些 `[planned]` 的
gh 反馈 / 推送后 CI 收集器应当作为**新文件**落进那个包，而不是追加到这里。
