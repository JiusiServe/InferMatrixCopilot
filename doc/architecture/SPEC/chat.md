# chat.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~497 · 接口（对话式 REPL） · refactor-status: split-candidate`

## 职责
Claude-Code 风格的对话式 REPL（配置了 LLM 时的默认形态）：一个持续的对话，
既回答问题，也通过工具执行工作。

## 功能
`SYSTEM_PROMPT`（仓库中立，插值 `default_repo`）；`TOOL_DEFS`
（run_task/run_playbook/get_status/get_logs/read_run_report/list_playbooks/
repo_read/repo_grep/resume_run）；`ChatSession`（**永不切开工具对**的历史裁剪、
流式输出、工具往返、会话记录）；以及读取囚笼。

## 公开契约
`chat_repl(copilot, assume_yes, handle_builtin)`；`ChatSession.turn`。

## 不变量
- 它是**前端，不是第二条执行路径**：最终汇入 `run_task`/`run_playbook`，
  走**同一套**门；**无法扩大权限**。
- `repo_read`/`repo_grep` 被囚禁在已配置的仓库根 + run 根内；`.env*` 一律拒绝。
- 抓取回来的 GitHub 内容**始终是数据**（在 step 内部处理）（**C7**）。
- 历史裁剪**绝不切开 tool_use/tool_result 对** —— 被切开的一对会让整个请求直接失败。
- 会话记录落在 `~/.infermatrix-copilot/sessions/`；`--no-chat` 回退到朴素命令 REPL。

## 边界 —— 不属于这里
自身不含规划/执行逻辑；不含仓库知识字面量（prompt 经 `default_repo` 中立化）。

## 依赖（允许）
`cli.Copilot`（仅 TYPE_CHECKING）、`run_trace`、`task_spec`、`ui`。

## 扩展点
新的对话工具 → 一条 `TOOL_DEFS` 条目 + 一个 `_dispatch_tool` 分支，**受囚笼约束、
且尊重各道门**。

## 测试
`test_chat.py`。

## 重构备注
混了三个关注点：工具 schema/注册（`TOOL_DEFS`）、读取囚笼、回合循环。
**建议拆分**：`chat_tools.py`（定义 + `_dispatch_tool` + 囚笼）与
`chat.py`（会话/回合循环）。读取囚笼（`_allowed_roots`/`_check_read`）具有通用价值 ——
如果还有别的面需要受囚笼的读取，可考虑提升为一个小的共享 helper。
