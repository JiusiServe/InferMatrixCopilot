# cli/ —— 规范

<!-- verified-against: 2026-08-26 -->

`LOC ~1240（6 个文件） · 接口 + 编排门面 · refactor-status: ok`

## 职责
flag CLI 与 `Copilot` 门面：解析 → 过门 → 执行；并持有 run 目录、RunTrace、notifier
和 metrics 的接线。它曾是一个 406 行的模块；现在是一个把 argparse/REPL 接线与编排器
分开的包。

## 包内布局（一个文件一个关注点）
- `__init__.py` —— 只再导出 `Copilot`、`main`（见下方公开面）；无逻辑。
- `__main__.py` —— `python -m infermatrix_copilot.cli` 的对等入口。
- `copilot.py` —— `Copilot` 编排器（resolve/run_task/run_playbook/run_queue/
  resume_last/_execute + 内置命令）。
- `entry.py` —— `argparse`、`_handle_line`、`main`（把 argv/stdin 变成对 `Copilot`
  的调用）。
- `utils.py` —— 纯格式化器：`parse_task_params`、`format_metrics_line`。
- `doctor.py` —— 预检诊断（2026-07 新增）：逐项 ✓/✗，每个失败给出**唯一**确切的修复命令。
- 子命令：`doctor` 与 `migrate-knowledge`（PR4d 部署期知识迁移；**显式 owner
  动作，零 LLM**，需 `--repo <name>`，支持 report-only；见 RUNBOOK）。

## 公开契约（可从 `infermatrix_copilot.cli` import）
`main(argv)`；`Copilot`（`resolve`、`run_task`、`run_playbook`、`run_queue`、
`resume_last`、`status`、`logs`、`playbooks`、`_execute`、`_adapter_for`、
`_resolve_repo_path`）。再导出的 `__init__` 让 `infermatrix_copilot.cli:main`
（entry point）和 `from infermatrix_copilot.cli import Copilot` 保持不变。

## 不变量
- `resolve` 把能力（adapter + REPO_PATHS）喂给 planner。
- 确认之前先过 plan-review 门；除非 `--yes`，`confirm_required or requires_review`
  时触发确认（`_gate_and_confirm`，K6）。
- **plan-review 门在无人时失败关闭（C6）。** `block` 永远停机；非 `lgtm` 的其余裁决
  （`revise`、`unavailable`）只是**呈现**给人看——真正把门的是随后的 `[y/N]`。因此
  `--yes` 抹掉那个人时，同一裁决必须改为停机，而不是凭一个已经不存在的确认放行。
  交互路径不变（照旧打印裁决再问确认）。反例是实测出来的：一次无法解析的评审回复
  让四个后端里的三个把同一份 pr-rebase 计划一路跑到推送门，而评审回复解析正常的那个
  后端**阻断**了它。
- `_execute` 是**唯一**的执行路径（task / 显式 playbook / resume）。
- 仓库知识（保护分支、高风险模块）由 adapter 进入 run state（**A5**）；
  被阻塞 → 退出码 3（`BLOCKED_EXIT`）。
- `--playbook` 是运行 candidate 的**唯一**方式。
- **rebase_mode 是带权威写回的**：`params.rebase_mode` 在过门前经
  `rebase_engine.modes` 解析并写回（`mode_state_flags` 决定 `when:` 门），
  冲突抛 `ModeConflictError` —— review 上下文向 reviewer 说明该模式下
  哪些 step 会跑。
- **每仓库知识锁（SHARED）持有整个 run 的生命周期**：run 之间不互斥，
  只与 `migrate-knowledge` 的 EXCLUSIVE 锁互斥 —— 迁移绝不与活跃 run 并发。
- **`doctor` 只读，且永不打印密钥的值** —— 只打印它的名字。除非传 `--probe`，
  否则它不做任何付费 LLM 调用；`--probe` 是唯一的付费检查（每个已配置档位一个 token）。
  `--json` 供 CI 使用，而**在没有凭据时以非零码退出正是 CI 里的预期状态**。
- **`--performance` 是抬高模型档位的唯一方式**；默认是 `eco`。
  **抬高档位永远不会扩大权限**（`tier` 仍然由 `kind` 推导）。
- CLI 主路径在**创建 run 目录之前**过门，所以被放弃的计划不留下任何东西。
  MCP 的预约形状（先建、后规划）是**刻意不同**的 —— 见 `mcp_server.md`。

## 边界 —— 不属于这里
不含 step 逻辑、不含仓库知识字面量、不含 LLM prompt。**只做编排接线。**

## 依赖（允许）
`engine/*`、`playbooks/*`、`intent`、`task_spec`、`adapters/base`、`push`、
`review/reviewer`、`notify`、`run_trace`、`config`、`ui`、`chat`。
**任何下层都不得 import 它**（**§ARCH.4.2**）。

## 扩展点
新 REPL 命令 → `_handle_line`（entry.py）；新的 run 接线 → `_execute`（copilot.py）；
新的纯格式化器 → utils.py。

## 测试
`test_cli.py`、`test_phase_b.py`、`test_chat.py`、`test_ui.py`。

## 重构备注
拆分**已完成**（它曾是内聚拆分候选）。`Copilot` 类完整留在 `copilot.py`，
好让 resolve→execute 的流程能在一个文件里读完；只有 argparse/REPL 前端（`entry.py`）
和两个纯格式化器（`utils.py`）搬了出去。K6（`_gate_and_confirm`）已完成，挂在类上。
