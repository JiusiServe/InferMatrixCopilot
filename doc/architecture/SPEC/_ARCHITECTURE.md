# 00 —— 架构、范围、功能

## 1. 这个系统是什么

一个 playbook 驱动的仓库维护 copilot，服务 vLLM-Omni（按设计，也服务任何建立了
profile 的仓库）。它把一条自然语言或 flag 命令，变成一条**受治理、可 resume、
可审计**的已审核 step 流水线，并在被阻塞时**升级而不是猜测**。

## 2. 功能（任务 kind）

**恰好存在七种任务 kind**；每种都有一个**任何输入都无法改变**的爆炸半径 **tier**
（见 `task_spec.py`）：

| Kind | Tier | 只读 | 做什么 |
|---|---|---|---|
| `repo_rebase` | L0 | 否 | 把 fork rebase 到上游（委托给 locked 的 5 阶段编排器） |
| `pr_rebase` | L1 | 否 | 把 PR 分支重放到它最新的 base 上 |
| `pr_debug` | L1 | 否 | 诊断并修复 PR 上失败的 CI |
| `pr_review` | L2 | 是* | 证据锚定的 inline 评审 |
| `issue_answer` | L2 | 是* | 起草一份 issue 回答 |
| `issue_filter` | L2 | 是* | 分流/打标/路由 issue |
| `repo_profile` | L2 | 否** | 建立/刷新一个仓库的 profile |

\* 除非设置了显式的 `post` 意图，否则只读。\*\* 读取目标仓库，但把知识写进
`adapters/<repo>/`。

tier（DESIGN `§3.2`）：**L0** 原样复用 locked playbook；**L1** 改编已审核 playbook
（受 plan-review 门禁）；**L2** 可以退化到生成，**但只对只读 kind**。

## 3. 三层 + 引擎底座

```
 接口层   cli/ / chat.py / ui.py              自然语言与 flag -> 一个分派器
     │
 任务层   task_spec.py / intent.py            自然语言 -> TaskSpec（tier 由 kind 定）
     │
 规划层   engine/planner.py / playbooks/      reuse > adapt > generate
     │
 引擎层   engine/{step,registry,executor}     跑 step：检查点、foreach、
     │     engine/agent_runtime.py            类型化失败、受治理 agent
     │     agent_loop.py, tools.py, scopes.py
     │
 Step 库  engine/steps/*                      已审核的 step 库
     │
 边缘     adapters/, ci/, profiles/            仓库知识与能力
          review/, memory/, run_trace, notify, metrics   跨切服务
          scopes.py, push.py                   纯安全原语
```

代码上是三层（接口 / 任务+规划 / 引擎+Step），架在一层仓库知识与跨切服务的**边缘**
之上。设计里的 "Target 层" **不是**一个代码层：它的任务定义职责由 `TaskSpec` +
`Playbook` 承担，而它唯一存活下来的产物 —— 推送授权 —— 就是 `push.py` 这个安全原语
（`scopes.py` 的兄弟）。

- **引擎是底座，不是流水线。** 它提供已审核的 step 库、与任务无关的执行保证
  （检查点/resume、类型化失败路由、scope 强制、升级、RunTrace），以及一个
  plan→execute 循环。**它不持有仓库知识，也不允许 planner 去编排原始工具。**
- **知识住在边缘。** 仓库专属事实（模块、CI、prompt、约定、推送策略）住在
  `adapters/<repo>/`（manifest + profile），**绝不在核心里**。
  **增加一个仓库是边缘的增量，不是核心的改动。**

## 4. 依赖规则（被强制的分层）

import **只能向下、向外**。以下是一次改动不得违反的、已被验证的约束：

1. 叶子边缘包（`profiles/`、`ci/`、`adapters/`、`review/`、`memory/`）和安全原语
   （`scopes.py`、`push.py`）**不得** import `engine/`。是引擎依赖它们。
2. 接口层（`cli/`、`chat.py`）**不得**被任何下层 import。
   `chat.py` 只可以在 `TYPE_CHECKING` 下引用 `cli.Copilot`。
3. `engine/step.py` 是基础词汇：它**只能**依赖 `run_trace`。
   不含任何任务或仓库专属内容。
4. `engine/steps/*` 编排工具与边缘包；它们经 `engine.agent_runtime` 到达 agent 运行时。
   **step 不得被引擎底座 import**（step 位于其上）。
5. 跨 step 的共享 helper 住在 `engine/steps/_common.py` —— step 模块
   **不得互相 import**（旧的 `pr_steps -> builtin_steps` 延迟 import 已被移除，
   **不得回来**）。

## 5. 范围

**在范围内：** 上面七种任务 kind；单一编排引擎；仓库 profile 的建立/维护；
对话式 + flag 两种 CLI；经 profile 支持多仓库；安全护栏（plan/patch review、
scope 强制、推送守卫、升级）；逐 run 指标。

**刻意在范围外：** 重新实现夜跑 rebase（它是**被委托的，包装而非重写**）；
一个通用 agent 框架；从应用内部跑付费评测（评测 harness 是 `eval/` 里的离线机器）；
成为 CI/forge adapter 所声明之外的 forge；存储密钥（只有 `.env`，被 git 忽略，
**绝不提交**）。

## 6. 数据与产物（ground truth）

- **逐 run** —— `~/.infermatrix-copilot/runs/run-<ts>/`：`run_trace.jsonl`
  （仅追加的事实）、`progress.json`（step 检查点）、`RUN_REPORT.md`、`metrics.json`、
  `ESCALATION.md`（仅在被阻塞时），外加 step 专属产物
  （`rebase_status.json`、`COMPARISON.md`、证据归档）。
- **逐仓库（知识）** —— `adapters/<repo>/`，**两个信任层**（DESIGN §V2.3.0）：
  **Tier 1 —— manifest** `manifest.yaml`（人工撰写、人工门禁：身份/路径/push/ci ——
  **agent 不得自行编辑**的安全配置），以及
  **Tier 2 —— profile** `profile/`（agent 建立、证据门禁：`profile.yaml`、
  `PROFILE_REPORT.md`、`JUDGE_REPORT.md`、`ops_log.jsonl`，以及按需建立的
  `format.yaml`/`review.md`/…）+ `skills/`、`store/debug_memory.db`、`repo_map/` 缓存。
  （容器是一个仓库 *adapter*，里面装着一份 *manifest* + 一份 *profile* ——
  2026-07-11 由 "plugin" 更名而来。）
- **治理规则：** RunTrace/证据是**不可变层**；profile 是架在它之上的**精选层**。
  **fact 概括证据，绝不取代证据。**

## 7. 安全模型（纵深防御）

五道相互独立、按"与"叠加的门 —— 一次改动可以**加强**但**不得移除**其中任何一道：

1. **tier 由 kind 定** —— 自然语言/用户文本永远无法扩大权限（`_CONSTRAINTS.md` C1）。
2. **plan review** —— 改编/生成出来的计划在执行前先被评审；
   生成路径在**结构上**被禁止包含 write/push step。
3. **ToolScope/PathScope** —— 每次工具调用都过同一个分派器；越界的写**会执行但被记录**，
   **绝不静默**。
4. **patch review** —— 由 7 条风险触发器条件触发，在推送前 **fail-closed**。
5. **推送守卫** —— 唯一 choke point；受保护分支永不被推送；force 只有 with-lease；
   除非 `ALLOW_PUSH=1` 否则 dry-run。

被阻塞的 run 写出 `ESCALATION.md`、发出通知、以退出码 3 结束 ——
**通知，绝不猜测**。

## 8. 仓库不变性（多仓库契约）[部分为计划中]

在一个已建立 profile 的仓库上，质量必须落在参考仓库的**声明区间**内，
且接入一个新仓库需要**对 `src/infermatrix_copilot/` 零改动**。
由以下机制强制：仓库中立的核心（`test_repo_neutral_core`）、按能力匹配的 playbook、
显式的 `capability_gap` 降级、逐仓库的知识命名空间。
由跨仓库评测 + 不变性指数衡量（`eval/invariance.py`）——
**评测战役本身仍是 `[planned]`。**
