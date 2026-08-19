# profiles/establish.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~107 · profile（Stage 0–1.5 helper） · refactor-status: ok`

## 职责
确定性的建立期 helper。

## 公开契约
`fact_id`、`build_doc_corpus`、`is_redundant`、`extract_directives`、
`scan_modules`、`HUMAN_DOC_NAMES`。

## 不变量
- `is_redundant`（对 README+docs 做 6 词 shingle）会丢弃任何**仓库自己的文档已经写过**
  的 briefing 行（ETH 研究那条规则，**D5**）。
- `scan_modules` 是确定性的、按语言索引的，跳过非代码目录。
- `extract_directives` 限制行长（只收短祈使句）。

## 边界 —— 不属于这里
纯确定性 helper —— 不含 LLM、不写 store、不含 step 逻辑。

## 依赖（允许）
仅 stdlib。

## 测试
`test_profile_steps.py`（冗余过滤、模块扫描、指令抽取）。

## 重构备注
纯函数 —— 易测、易复用。冗余过滤器是承载 ETH 研究结论的关键防线；**保持它确定性**。

## 精简 —— **K2**（共享语言规则）—— 已完成
本模块曾经拥有 `LANGUAGE_SUFFIXES`，那是按语言规则集的三份副本之一
（另两份在 `review._sweep_targets` 和 `repo_map`）。数据现在住在叶子模块
`profiles/languages.py`，藏在小访问器（`suffixes` / `symbol_re` / `sweep_re`）
之后并从那里消费；这个符号已从本模块的公开契约中消失。按设计保留的一点：
**未知语言产出空的模块扫描，而不是猜测**。
