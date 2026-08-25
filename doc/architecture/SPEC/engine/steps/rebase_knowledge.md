# engine/steps/rebase_knowledge.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~354 · step 库（v3 知识尾段） · refactor-status: ok`

## 职责
v3 playbook 的 Rev 8 §2.2 流水线尾段（`phase5_report → curate → compare` →
通用 report），外加首个 agent 写入之前的 schema 准备步。

## Steps（4 个）
| step | kind/risk | 发布 / 产物 |
|---|---|---|
| `rebase.v3_knowledge_prep` | deterministic/knowledge | `state_updates: knowledge_prepped`；debug store 升到 schema v2 |
| `rebase.v3_phase5_report` | deterministic/read | `FINAL_SUMMARY.md`（模块/本地测试/远端 CI，全读自 substate） |
| `rebase.v3_curate` | script/knowledge | debug-memory curation + watchdog 收割/晋升；`PROMOTION.md`；substate `curation` |
| `rebase.v3_compare` | report/read | 关账知识 attest + `COMPARISON.md`；substate `knowledge.close/drift`、`comparison` |

## 不变量
- **A4**：四个 step 全部 `@step(...)` 就地自注册；**B2**：`knowledge_prep`
  经 `state_updates` 发布 `knowledge_prepped`。
- `ensure_schema_v2()` 只有**三个**受认可的可写维护入口：知识迁移 CLI、
  `v3_knowledge_prep`、`v3_curate`（belt）—— 入口普查由测试钉死；
  report_only 到不了 prep（它的 stores 全程只读）。
- `phase5_report` 在 curate **之前**运行、只读 substate —— curation 永远
  没机会掩盖 run 实际做了什么。
- curate 只写 copilot **runtime** store —— 父 read-compat 层与 adapter 树
  绝不被写（**D2**）；watchdog 决策收割**恰好一次**（state log 的身份集是
  去重权威；`_repo_run_dirs` 按 task.json 定界到本仓库的 run dirs，跨仓库
  扫描会互相污染）；skill 候选与晋升摘要落 `PROMOTION.md` 人类策展面
  （**D1**）。curation 失败是**类型化的 run 失败**（**B1** —— 知识库损坏
  不得藏在绿色报告后面）。
- compare 的关账 attest：父层 close digest 必须与 prelude 的开账块一致，
  否则 `drift` 记入 substate 并记 `knowledge_provenance` trace（**E1**），
  §8 比较 gate-ineligible —— v3 从不写父层，漂移 = 外部干扰。
- 声明了却展不开的知识层（env var 未设）→ BLOCKED（**B1**）—— 与 prelude
  同一条"绝不知识裸奔"规则（`_knowledge_layer_paths`）。
- 提供的 baseline（task param `baseline_status`）是**裁决输入**：不可读 →
  类型化失败；baseline 绿而本 run 非 done（failed/skipped/missing 同罪）→
  BLOCKED needs-human（soak 的 investigate-don't-average 契约）。

## 边界 —— 不属于这里
不含 curation 算法（`memory/curator`）、attest 实现
（`rebase_engine/knowledge_attest`）、watchdog 学习本体
（`testing/watchdog_learn`）；不写最终通用报告（`report.final_summary`）。

## 依赖（允许）
`engine/step`、`._common`；惰性的 `memory/{curator,debug_memory,skills,paths}`、
`testing/watchdog_learn`、`rebase_engine/knowledge_attest`、`adapters/base`；
以及兄弟模块 `.rebase_v3` 的三个 helper（见重构备注）。

## 测试
`test_curator.py`（curation 分歧钉扎、恰好一次收割、schema 入口普查、
phase5/compare 的 drift 与 baseline 裁决）。

## 重构备注
从 `rebase_v3.py` 拆出的尾段，内聚良好 —— 但它 import 兄弟 step 模块
`rebase_v3` 的三个 helper，是 **A2 的字面违例**；把它们下沉 `._common`
（或一个 v3 共享 helper 模块）即可让两边都干净。`_knowledge_layer_paths`
与 prelude 的展开检查是刻意的同规则双份 —— 合并时必须保留"声明未展开 =
BLOCKED"。
