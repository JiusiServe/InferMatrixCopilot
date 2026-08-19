# review/reviewer.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~89 · 评审（裁决） · refactor-status: ok`

## 职责
只读的 patch/plan 评审裁决。

## 公开契约
`run_patch_review(llm, diff_text, summary, fired_rules, model) -> verdict`；
`run_plan_review(llm, playbook_doc, task, model) -> verdict`。

## 不变量（**C6**）
- 没有 reviewer LLM 时返回 `unavailable`（**缺少 reviewer 不等于静默放行**）。
- reviewer 输出无法解析时降级为 `revise`。
- 除 `lgtm`/`pass` 之外一律视为**未通过**。

## 边界 —— 不属于这里
它不是评审 **step**（那是 `engine/steps/review.py`）；不含触发逻辑；不构建 diff。

## 依赖（允许）
`llm`；评审 prompt 就住在这里。

## 测试
`test_review.py`。

## 重构备注
**fail-closed 就是那条不变量** —— 绝不要新增"reviewer 缺失/失败却返回通过"的路径。
如果 plan review 和 patch review 分歧变大，再拆成两个文件；今天它们共享同一个
fail-closed 形状，理应住在一起。
