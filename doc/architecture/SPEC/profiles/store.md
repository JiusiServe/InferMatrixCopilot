# profiles/store.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~268 · profile（精选层） · refactor-status: ok`

## 职责
精选事实库：**类型化 patch op 是唯一写入面**，配上溯源/稳定性门禁和按通道分类的渲染。

## 公开契约
`ProfileStore(root)`；`apply_ops(ops, tier, actor) -> 逐 op 的拒绝原因`；
`active(channel?, module?)`；`render_briefing(budget)`；`render_report()`。
`Fact`；`RUN_OPS`/`CONSOLIDATE_OPS`；`CHANNELS`、`KINDS`、`SOURCES`、
`STABLE_CONFIRMATIONS`、`BRIEFING_WORD_BUDGET`。

## 不变量
- op 是**唯一**的变更路径；畸形/被禁的 op **逐条**拒绝（绝不抛异常）；档位不对的 op
  被拒（**D4**）。
- `add_fact` 需要正文 + 证据；重复 id 视为一次**确认**（**D3**）。
- `rewrite_fact` 绝不让某条 fact 变成无证据；**稳定**（≥3 次确认）的 fact 不得丢弃已
  引用的证据；被取代的正文进 `history`（**D3**）。
- `merge_facts` 留下一个指针存根（**绝不删除**）；`mark_stale` 只排除、保留以备审计。
- `render_briefing` 只发出 active 的 briefing 通道 fact，**确认次数多的在前**，
  并处于硬性词预算之下（**D5**）。
- 每条被接受的 op → `ops_log.jsonl`；`save()` 会重新渲染 `PROFILE_REPORT.md`。

## 边界 —— 不属于这里
不含 LLM、不扫描仓库、不含 step 逻辑。

## 依赖（允许）
`pyyaml`；stdlib。

## 测试
`test_profile_store.py`。

## 重构备注
它是 D3/D4 的参考实现 —— **不要**在 `apply_ops` 之外新增变更路径。每个 `_op_*` 都是
一个小校验器；保持它们可以被**逐条拒绝**。op 种类增加时，继续用
`RUN_OPS`/`CONSOLIDATE_OPS` 作为档位门。这是从个人 agent 的 store 移植过来的 ——
保持两者在概念上对齐。
