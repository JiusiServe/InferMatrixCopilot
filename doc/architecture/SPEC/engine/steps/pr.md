# engine/steps/pr/ —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~1100（6 个文件） · step 库（PR） · refactor-status: ok`

## 职责
受守卫的推送、只读的 PR 抓取/门禁、PR rebase、PR debug、受门禁的评审发布。
它曾是一个 484 行的模块；现在是一个按关注点拆开的包。

## 包内布局（一个文件一个关注点）
- `__init__.py` —— 对各子模块做副作用 import（`@step`/`register_step` 注册）；
  再导出 `extract_signature`。无逻辑。
- `fetch.py` —— 只读抓取：`pr.fetch_diff`、`pr.gate_check`。
- `rebase.py` —— `pr.checkout_branch`、`pr.rebase_onto_base`、`pr.analyze_diff`、
  `agent.verify_module`。
- `debug.py` —— `pr.fetch_ci_failures`（+ `_enrich_ci_logs`）、`pr.group_failures`、
  `agent.debug_group`。
- `publish.py` —— 对外写入（risk=push）：`ci.push`、`pr.post_review`。
- `utils.py` —— 纯函数 `extract_signature`（及其正则）。

## Steps（11 个）
`ci.push`（script/push）；`pr.fetch_diff`、`pr.gate_check`、`pr.checkout_branch`、
`pr.analyze_diff`、`pr.fetch_ci_failures`、`pr.group_failures`（deterministic/read）；
`pr.rebase_onto_base`、`agent.debug_group`（agent/write_workspace）；
`agent.verify_module`（validation/read）；`pr.post_review`（script/push）。

## 公开契约（可从 `engine.steps.pr` import）
`extract_signature`（由 `utils` 再导出；供测试使用）。

## 不变量
- `ci.push` 把全部安全判断委托给 `guard_push`（**C4**）。
- **`pr.fetch_diff` 把评审树 pin 到 PR head**（`_pr_time_checkout`）：head sha 取自
  最后一个 commit 的 oid，`git fetch origin pull/N/head`（对**开放和已合并**的 PR 都
  有效），detached worktree 复用于 `~/.infermatrix-copilot/worktrees/`。
  它经 `state_updates` 发布 `repo_path` / `checkout_note`，于是**每个 lens 调查的都是
  PR 那一刻的代码**，而不是本地 checkout 恰好停在哪个分支。失败时降级回 live checkout，
  并带**响亮**的注记加一条 `capability_gap` trace。
- **`pr.post_review` 只发一条 GitHub review + inline thread**，且先把每条发现的位置
  对照已抓取的 diff 校验过 —— **绝不是一串独立评论**。
- `diff_text` 和 `gate_report` 都可以经 state 注入，因此网络之下的每条路径都可离线测试；
  `gh` 不可用时降级为 BLOCKED，**绝不崩溃**。
- `pr.checkout_branch` 把推导出的 `PushPolicy` **序列化后发布**（**B2**）——
  在推送处 resume 时**绝不能**看到那个 deny-all 的默认值。
- `pr.rebase_onto_base`：由受治理 agent 解冲突，或 abort+升级（**工作区始终被还原**）。
- `pr.fetch_ci_failures` 经 profile 选定的 CI provider 富化日志，否则记一条
  `capability_gap`（**E2**）；`pr.group_failures` 按**归一化后**的签名分组。
- `pr.post_review` 是**双闸**的（**C5**）。

## 边界 —— 不属于这里
不含推送授权逻辑（那是 `push`）；不含 CI 日志抓取机制（那是 `ci/providers`）；
不含 agent 治理（那是 `agent_runtime`）。

## 依赖（允许）
`scopes`、`push`、`ci/*`、`adapters/base`（analyze）、`engine/step`、`.._common`、
`..agent_runtime`。

## 测试
`test_pr_steps.py`、`test_push_and_steps.py`、`test_ci_and_repo_map.py`
（注意：`test_ci_and_repo_map` monkeypatch 的是 `pr.debug._gh`，
即 `pr.fetch_ci_failures` 绑定 `gh` 的那个子模块）。

## 重构备注
拆分**已完成**。各子模块只共享 `._common` 的 helper，所以拆分**没有制造交叉 import**。
读/写轴是显式的：`fetch` 只读，`publish` 装着两个 risk=push 的 step。
K3/K4/K7 的精简（require_repo/published/from_state）已在各子模块落地。
`_enrich_ci_logs` 保持为通往 `ci/providers` 的**薄接缝**。
