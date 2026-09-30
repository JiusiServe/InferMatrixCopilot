# improve/ —— 规范（元改进引擎）

<!-- verified-against: 2026-09-30 -->

`设计：/data/zhoutaichang/copilot/meta-improvement-engine-design.md v1（GPT-6 sol 批准 2026-09-29） · refactor-status: building (P0–P1 已落地)`

## 职责
面向任意 trace/1 工作流的"取证—实验—提案"循环。**只提案**：引擎的写权限限于追加自己的 trace/1 记录、
写自己的账本目录、在影子环境跑实验；产线变更一律走 PR。

## 模块
| 文件 | 阶段 | 作用 |
|---|---|---|
| `enroll.py` | P0 | 工作流声明（`workflows/*.yaml` + `IMPROVE_WORKFLOWS_DIRS`）：kind/unit/item_key/fingerprint.covers/capture/shadow_tools；未声明 = Tier 1 |
| `fingerprint.py` | P0 | 声明式配置指纹（playbook sha、settings、prompt 文件哈希、routing、`resolved_models`、tools、knowledge_snapshot、copilot_sha）；覆盖项缺失 → 无指纹、记 `fingerprint_missing` |
| `shadow.py` | P0 | 影子四层边界：`harden_scope`（严格 extra、读围栏）、`shadow_env`/`make_executables_dir`/`assert_boundaries`（凭据与可执行白名单）、`make_shadow_clone`（`--shared` 独立克隆、无 remote、钉住的 base ref）、`smoke` |
| `staging.py` | P0 | 隔离前的条目快照：`stage_item` 复用 `pr.fetch_diff` 的钉住取数，写 `item_staged` 记录；任一必需输入不可得即拒绝 |
| `reader.py` | P1 | trace/1 → 工作单元（按 `context.unit_id`，RB/知识服务记录回退到 `run_id:step`）；窗口按 JSONL 日期文件读取 |
| `lints.py` | P1 | Tier 1 的 17 条确定性 lint（L01–L17，每条带版本与出处）；`Baseline` 稳健 z（MAD 下限 = 中位数的 10%）；L13 隔离 |
| `ledger.py` | P1 | 每工作流 JSON 账本：周期统计、基线样本、提案状态机（open → experiment-registered → supported/neutral/refuted/underpowered → landed/closed；30 天无人触碰 → stale）、hold、通道活性；每次变更同时写 `decision` |
| `cycle.py` | P1 | 周期：preflight（`improve_enabled` 是 kill switch）→ lints + 基线 → 账本 + Tier 1 提案（lint 恶化 ≥1.5× 且 ≥3 单元）→ stale 清扫 → 报告（`reports/cycle-*.md/json`）+ `decision(type=cycle)`；`is_due`/`maybe_run_weekly` 是周度槽位 |
| `cli.py` | P0/P1 | `improve migrate-index|rebuild-index|rollback-index|compare-index|verify-index|cycle|ledger|lints` |

## 接入点
- 执行器：`settings.trace_store_root` 非空时绑定 store 并为每步绑定单元上下文；`settings.improve_shadow` 下拒绝非 read/report 步骤。
- `tools.dispatch` / `LLM.create` / `HarnessLLM.create` / `run_harness_step` / MCP bridge：全保真采集。
- `kb serve` 调度器：每 tick 调 `_improve_cycle()`，周度槽位到达即跑一次周期（与知识服务同一租约、异常隔离）。
- 任务种类 `workflow_improve`（L2，READ_ONLY_KINDS）；playbook `workflow-improve`（preflight → lint → ledger → report）。

## 不变量
- P1 周期永远 dry-run：提案只在账本与 trace 里，不上 GitHub（P4）。
- 引擎自身的记录（`playbook=workflow-improve`）是下一周期的 Tier 1 单元（自登记）。
- lint 只读 trace，不调模型；无证据形态的 lint 不猜。

## 测试
`test_improve_p0.py`、`test_improve_p0b.py`、`test_improve_p1.py`。
