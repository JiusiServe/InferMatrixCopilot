# engine/steps/issue.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~338 · step 库（issue） · refactor-status: ok`

## 职责
issue 抓取、起草回答与分流两个 agent step，以及受门禁的发布。

## Steps（4 个）
`issue.fetch`（deterministic/read）；`agent.draft_issue_answer`、
`agent.triage_issues`（agent/read，只读 scope）；`issue.post_answer`（script/push）。

## 不变量
- agent step 通过受治理运行时，把主张**锚定在抓取到的文本/代码上**。
- `issue.post_answer` 是**双闸**的（**C5**）。
- `_issue_agent_step` 是共享工厂；两个 `agent.*` handler 用命令式方式注册
  （`register_step`）。
- 起草契约带一个 **disposition 槽**（close / keep-open / duplicate-of-#N / reopen）
  —— 一份没有说明"这个 issue 接下来该**怎么处理**"的分流回答是**不完整的**。
- **未经 gh 验证的"已合并"声明必须带认识论 caveat**，并且即使该 step 升级，
  实质性草稿也会**带着那条 caveat 交付** —— 因为把握不足就扣着真实工作不给，
  对谁都没有帮助。
- `max_agent_iters` 给 grep 密集的分流留出余量。

## 边界 —— 不属于这里
不含 agent 治理内部机制；除 `post_step` 之外不含发布授权。

## 依赖（允许）
`scopes`、`engine/step`、`._common`、`..agent_runtime`。

## 测试
经 issue playbook + `test_agent_runtime` 相关路径覆盖。

## 重构备注
体量合适。`_issue_agent_step` 工厂 + `_render_answer`/`_render_triage` 的模式很干净；
如果出现第三个 issue agent step，**继续用那个工厂**。

## 精简 —— **K4/K7**
`issue.fetch` 用到了"从 state 取"的早返回（K7 `from_state`）和冗长的 `state_updates`
字面量（K4 `published(...)`）。收益不大；**务必保住 B2**。
