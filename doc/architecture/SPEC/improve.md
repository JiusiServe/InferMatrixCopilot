# improve/ —— 规范（元改进引擎）

<!-- verified-against: 2026-09-30 -->

`设计：/data/zhoutaichang/copilot/meta-improvement-engine-design.md v1（GPT-6 sol 批准 2026-09-29） · refactor-status: building (P0–P2 已落地)`

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
| `adapters/__init__.py` | P2 | 结果适配器契约：金标矩阵（`match()` → recall 与阶段归因）与 finding 级有效性（`findings()` → precision）两个数据模型不混用；评审级判官分数（`review_scores()`）原样保留；`scores_from` 给每个数字标来源 |
| `gold.py` | P2 | 策展金标集：`gold_id = sha256(item+path+规范化 concern)[:12]`，`draft` 由原始评论生成、只有 `curated` 才被使用，改措辞即新条目，文件 sha 即版本 |
| `judges.py` | P2 | `run_judge`：API 判官走 `LLM.create`，CLI 判官走 `governed_subprocess`（预留判官次数、无工具、空工作区、流中出现工具调用即作废），都写 `model_call` |
| `stats.py` | P2 | 配对、按 item 聚类的 t 区间（移植 `paired_analysis.py`）、所需 item 数、五种标签、Cohen κ |
| `adapters/review_eval.py` | P2 | eval 评审适配器：导入 `judge_val` 配对 verdict 为 `judge_verdict` outcome；`gold_match` 判官（3 票多数、hit 须逐字引用）写 `gold_match` outcome；`match()` 只读记录 |
| `adapters/rb_review.py` | P2 | RB 生产适配器：PR 线程代理标签（accepted/disputed/silent）→ finding 级有效性，`descriptive_only`，无金标、不注册实验 |
| `forensics.py` | P2 | 覆盖矩阵（确定性）、S0–S10 阶段分类法、取证 agent（只读 trace 工具、全部输出围栏为不可信数据、必须引用记录 id）、双家族交叉复核（不一致 = disputed）、整改清单、测量健康 |
| `meta.py` | P2 | 冻结元基准：`eval/dataset/meta/cases`（trace + 人工阶段标签）与 `meta/lints`（注入缺陷样本）的导出与加载 |
| `cli.py` | P0–P2 | `improve migrate-index|rebuild-index|rollback-index|compare-index|verify-index|cycle|ledger|lints|gold draft/check|meta lint-check` |

## 接入点
- 执行器：`settings.trace_store_root` 非空时绑定 store 并为每步绑定单元上下文；`settings.improve_shadow` 下拒绝非 read/report 步骤。
- `tools.dispatch` / `LLM.create` / `HarnessLLM.create` / `run_harness_step` / MCP bridge：全保真采集。
- `kb serve` 调度器：每 tick 调 `_improve_cycle()`，周度槽位到达即跑一次周期（与知识服务同一租约、异常隔离）。
- 任务种类 `workflow_improve`（L2，READ_ONLY_KINDS）；playbook `workflow-improve`（preflight → lint → forensics → ledger → report）。
- `improve.forensics` 步骤：对每个有结果适配器的工作流建覆盖矩阵、用两个模型家族归因每个 miss、产出整改清单；单元数低于 `tier2_min_items` 或无 LLM 时跳过并说明。

## 不变量
- P1 周期永远 dry-run：提案只在账本与 trace 里，不上 GitHub（P4）。
- 引擎自身的记录（`playbook=workflow-improve`）是下一周期的 Tier 1 单元（自登记）。
- lint 只读 trace，不调模型；无证据形态的 lint 不猜。

## 测试
`test_improve_p0.py`、`test_improve_p0b.py`、`test_improve_p1.py`、`test_improve_p2.py`。
