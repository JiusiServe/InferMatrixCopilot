# 每次运行的 metrics.json —— 消费契约

> 面向**外部消费方**（review-bot 看板、统计脚本）的稳定字段契约。生产方是
> `src/infermatrix_copilot/metrics.py::collect_run_metrics`；指标口径的推导过程见
> [`../evaluation/`](../evaluation/README.md)。本页只回答一个问题：**看板能信哪些
> 字段、怎么读。**

## 位置与生命周期

- 路径：`~/.infermatrix-copilot/runs/run-<ts>-<uuid6>/metrics.json`，与
  `RUN_REPORT.md` 同目录。
- **尽力而为**：指标计算失败绝不打断 run —— 消费方必须容忍文件缺失。
- BLOCKED 的 run 也会产出 metrics（`status` 字段说明终态）。

## 兼容性规则

- 顶层 `"schema": 1`。**字段只增不删、语义不变**；破坏性变更必须提升 `schema`。
  消费方按 `schema` 判断兼容，遇到不认识的字段一律忽略。
- 多个数值字段可为 `null`（下文逐个说明何时、为何）。**`null` 是"拒绝编造"，
  不是 0** —— 看板对 `null` 要显示"未知"，不能当零聚合。

## 字段

### 顶层

| 字段 | 含义 |
|---|---|
| `run` | run 目录名（`run-<ts>-<uuid6>`） |
| `task_kind` | 任务类型（`pr_review` / `pr_debug` / `issue_answer` / …）——**跨 kind 的 Q 不可直接比较**（权重表不同） |
| `status` | 终态字符串 |
| `catq` / `tus` | 综合指标 `Q·S/C` 及其变体；**q 或 cost_index 任一为 `null` 时为 `null`** |

### `quality` —— Q

| 字段 | 含义 |
|---|---|
| `q` | 加权质量分 [0,1]，只对**已知**分量加权 |
| `components` | 各分量得分；自动可测的分量之外（如需评审 GT 的 `recall_w`），只有 eval/反馈管道合并后才存在 |
| `weight_coverage` | 已知分量占总权重的比例——**看板必须与 `q` 一起展示**：coverage 低的 q 是小样本口径 |
| `partial` | `true` = q 是不完整口径（coverage < 1） |
| `abstained` | `true` = run 诚实弃权（恢复现场并上报），q 取该 kind 的弃权基线分而非 0 |

### `cost` —— C

| 字段 | 含义 |
|---|---|
| `usd` | 模型花费 + CI 机时折算。**计价完整的条件：`source="spans"` 且 `cost_partial=false`**（见下——"完整"不等于"发票级精确"） |
| `source` | `"spans"` = 逐请求按各自模型计价（权威）；`"events"` = 无 trace 时的事件和（估算回退），两者绝不混用 |
| `cost_partial` | `true` = 有请求的模型**查不到真实价格**（`unpriced_calls` > 0），`usd` 只是下界 |
| `cost_index` | 归一成本指数（≥1，越低越好）；`cost_partial` 时**故意置 `null`**——宁缺不编 |
| `unpriced_calls` / `llm_calls` | 未计价请求数 / 总请求数 |
| `input_tokens` / `output_tokens` / `cache_read_tokens` / `cache_creation_tokens` | token 计数（含缓存维度） |
| `minutes` / `ci_minutes` | 墙钟分钟 / CI 机时分钟 |
| `by_role` | 按角色（lens/reducer/planner/…）的花费分解 |
| `usd_ref` / `min_ref` | 该 kind 的成本归一参考值（`cost_index` 的分母口径） |

**"这笔钱怎么读"要同时看两个字段**：`source="spans"` 且 `cost_partial=false` 表示
**计价完整**——每笔请求都按其模型的单价计了价；单价来自配置覆盖或内置价目表，
价目表对部分模型是列表/家族近似价，所以这仍是"按牌价的完整核算"，不是发票级
精确值。`source="events"` 的 `usd` 是无 trace 时的粗估回退，展示时必须标"≈"；
`cost_partial=true` 的 `usd` 是下界（有请求查不到任何单价），标"≥"。订阅制
harness 后端（`STRICT_BACKEND` ≠ `api`）的请求没有真实单价：其 span 的模型查不到
价格时走同一条 `unpriced_calls`/`cost_partial` 路径——所以消费方**不需要**额外
区分后端，上面两个字段已经覆盖。

### `timings`

各步骤（fetch/gate/review/report…）的 `dur_s`，外加
`time_to_first_result_s`——首个 agent 步骤完成相对 run 起点的秒数，批处理 run
里最接近"首个有用结果"的量。

### `risk` 与 `signals`

| 字段 | 含义 |
|---|---|
| `risk.incidents` | 按严重级（catastrophic/severe/moderate/minor）的事件计数 |
| `risk.safety_multiplier` | S ∈ (0,1]，乘进 CATQ |
| `signals.escalations` / `pushes` / `posted` / `steps_completed` | 升级次数 / 请求推送次数 / 外发工件次数 / 完成步骤数 |

## 看板最小消费集

1. 逐 run 行：`task_kind`、`status`、`quality.q`（旁标 `weight_coverage`）、
   `cost.usd`（按 `source` 与 `cost_partial` 标注：`events` → "≈"，
   `cost_partial` → "≥"）、`timings.time_to_first_result_s`、`risk.incidents`。
2. 聚合口径：同 kind 内聚合；`null` 剔除而非按 0；`partial` 的 q 单列或加标记。
3. 稳定排序键用 `run`（其时间戳前缀单调）。
