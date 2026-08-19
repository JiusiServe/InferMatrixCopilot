# engine/steps/profile.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~387 · step 库（profile 流水线） · refactor-status: split-candidate`

## 职责
仓库 profile 的建立（Stage 0–1.5）+ Stage-4 维护 step。

## Steps（8 个）
建立期：`profile.fingerprint`、`profile.structure_scan`、`profile.ingest_docs`
（deterministic/knowledge）、`agent.profile_repo`（agent/knowledge）。
Stage-4：`profile.detect_drift`（deterministic/read）、`profile.decay_stale`
（deterministic/knowledge）、`agent.profile_consolidate`（agent/knowledge）、
`profile.judge`（agent/read）。

## 不变量
- 对未知仓库，`fingerprint` 起草一个 `status: draft` 的 adapter（人工门）；
  `structure_scan` **绝不覆盖**已声明的模块。
- `agent.profile_repo` 产出的**无证据 fact 会被 store 拒绝**；经冗余过滤；
  **禁止概览式内容**。
- `agent.profile_consolidate` 是**唯一**的 rewrite/merge 层；LLM 的 op 必须通过
  store 的稳定性门（**D3/D4**）。
- `profile.judge` **绝不调用 `apply_ops`**（只读，**D2**）。
- 无 LLM 的路径会记一条 `capability_gap`，并只运行确定性阶段。

## 边界 —— 不属于这里
不含 store 内部机制（那是 `profiles/store`）；不含建立期 helper
（那些在 `profiles/establish`/`consolidate`）。

## 依赖（允许）
`adapters/base`、`profiles/*`、`engine/step`、`._common`、`..agent_runtime`。

## 测试
`test_profile_steps.py`、`test_p3_machinery.py`。

## 重构备注
一个文件里装了**两条生命周期**。**建议拆分**：`steps/profile_establish.py`
（fingerprint/structure_scan/ingest_docs/profile_repo）与
`steps/profile_maintain.py`（detect_drift/decay_stale/consolidate/judge）。
它们只共享 `_adapter_from_state`（→ 挪进 `._common` 或一个小的 `profiles` helper）
和 store —— 没有交叉 import。指导性 prompt 常量可以按 `steps/*_prompts.py` 的约定
放到评审 prompt 旁边。

## 精简 —— **K3**（这里是最大的一处样板收敛）
本文件的守卫重复最密集：**7** 处 `_adapter_from_state` +
`isinstance(..., StepResult)` 守卫、**6** 处 `ProfileStore(adapter.profile_dir)`
构造、**3** 处无 LLM 的 `capability_gap` 块。改用 `._common` 的
`adapter_or_result`/`@needs_adapter`、`store_for(adapter)`、`no_llm_gap(...)`。
**仅此一个文件预计可省约 25–35 行。** 必须保留：每个 step 的名字/行为、store 的那些门
（D3/D4）、以及 `capability_gap` 事件（E2）。
**不要让 helper 掩盖掉 `profile.judge` 的只读性。**
