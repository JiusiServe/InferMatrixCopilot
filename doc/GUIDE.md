# InferMatrixCopilot 指南

一份文档覆盖两类读者：**操作者**（用它审 PR、修 CI、答 issue，不读 `src/`）
和**维护者**（改这个仓库本身）。按结构组织——概览、功能、使用、开发、
playbook、step、tool、性能——与 [`CODE_TOUR`](architecture/CODE_TOUR.md) 的数据流视角互补：
那份文档回答"数据怎么流"，这份回答"有哪些东西、各自在哪、怎么用"。

> 配套：[`DESIGN.md`](architecture/DESIGN.md) 为什么这么设计 ·
> [`SPEC/`](architecture/SPEC/README.md) 每个源文件不能破坏什么 ·
> [`README`](../README.md) 安装与 MCP 入口 · [`DEVELOPMENT`](../DEVELOPMENT.md) 文档地图。

---

## 目录

1. [概览](#1-概览)
2. [功能](#2-功能)
3. [使用指南（操作者）](#3-使用指南操作者)
4. [开发指南（维护者）](#4-开发指南维护者)
5. [Playbooks](#5-playbooks)
6. [Steps](#6-steps)
7. [Tools](#7-tools)
8. [性能对比](#8-性能对比)

---

## 1. 概览

### 1.1 一个仓库，两个产品

最容易混淆的一点先说清楚：这个仓库里住着两个形态不同的产品，共用一套知识和
治理，但执行路径几乎不重叠。

| | **Direct / MCP** | **Strict / CLI** |
|---|---|---|
| 谁读代码 | 宿主 Agent 自己的模型 | InferMatrixCopilot 配置的模型 |
| 入口 | `/imreview` `/imdesign` `/imcifix` `/imupdate` | `infermatrix-copilot -p "…"` |
| 用到 playbook / step | **完全不用** | 全用 |
| 服务端跑模型 | 否（零模型、零状态） | 是（隔离子进程） |
| 需要 API Key | 否 | 是（或订阅制 harness 后端） |
| 典型耗时 | 同步一次调用 | 5–12 分钟 |

Direct 是默认形态：MCP 服务端把"该看哪些知识、该守哪些门"作为**结构化数据**
返回给宿主，宿主用自己的模型完成阅读和判断。Strict 才走下面 §5–§7 描述的
执行主脊。**看到 playbook、step、tool 这些词时，说的都是 Strict 侧。**

### 1.2 三条数据流

```
第一条 · 执行主脊（Strict / CLI，一个任务从左到右）
  终端串 → intent → TaskSpec → planner → Playbook → executor → steps → 产物
                                (reuse>adapt>generate)    (共享 state 字典)

第二条 · 知识平面（正交叠加，每次 run 读入 / 写出）
  profile briefing · skills · debug memory · repo_map
  读宽写窄：agent 只能提案 candidate，人类晋升

第三条 · MCP 服务端（宿主入口，非交互）
  宿主 → thin_mcp_server ─┬→ Direct：同步返回知识路由 + 治理契约（主脊不参与）
                          └→ Strict：预约 run_id → 隔离子进程 → 轮询取结果
```

### 1.3 三条边界

贯穿全部三条流，不是流程的某一段：

- **信任边界**——指令只来自终端输入（只有 `intent.py` 这一个入口）；抓取回来的
  diff / issue / CI 文本一律包在 `<untrusted_data>` 里，永远不会成为指令。
- **权限边界**——`tier`（爆炸半径）由 `kind` 推导，不是字段。用户措辞和模型输出
  都无法扩权。
- **知识边界**——`knowledge/` 和 `adapters/` 是数据面；仓库、组件、模型的具体规则
  不允许硬编码进 `src/`（由 `test_repo_neutral_core` 强制）。

### 1.4 规模

92 个 Python 文件 / ~19.5k 行（`src/`）· 9 个 playbook · 38 个注册 step ·
457 页知识 · 59 个测试文件。目标仓库是 vLLM-Omni（adapter zero）。

---

## 2. 功能

### 2.1 四个宿主 Skill（Direct）

| Skill | 做什么 | 边界 |
|---|---|---|
| `imreview` | 审 PR 或本地改动：固定 PR 快照 → 取知识路由 → 读源码 + 跑验证 → 带文件行号的结论 | 默认只在当前对话输出，不发 GitHub |
| `imdesign` | 写代码前的协同设计：问题、现状、方案、接口变化、实施步骤、验证计划、风险 | 不自动改代码 |
| `imcifix` | 从 issue 出发，本地复现 → 最小修复 → 针对性验证 | 不 commit / push / 开 PR / 发评论 |
| `imupdate` | 上游发版后，对比新旧版本，更新模型清单、registry、deploy、路径路由、source pin | 只改知识，不动目标仓库 |

Codex 用 `$imreview`，Claude Code / Cursor 用 `/imreview`。

### 2.2 七种任务 kind（Strict / CLI）

| kind | tier | 只读 | 做什么 |
|---|---|---|---|
| `pr_review` | L2 | ✅ | PR 评审 |
| `issue_answer` | L2 | ✅ | 起草 issue 回复 |
| `issue_filter` | L2 | ✅ | issue 批量分类路由 |
| `repo_profile` | L2 | ✍️ 知识 | 建立仓库 profile |
| `pr_debug` | L1 | ✍️ | CI 失败分组 → 修复 → 增量 push |
| `pr_rebase` | L1 | ✍️ | fork-aware checkout → rebase → 验证 → with-lease push |
| `repo_rebase` | L0 | ✍️ | 夜跑全量 rebase（委托给已有 5 阶段编排器） |

tier 语义：**L0** 只能原样复用 locked playbook；**L1** 可用已审核 playbook 改编；
**L2** 允许现场生成计划——而 generate 路径**结构上**不可能包含 write/push step。

### 2.3 质量与成本机制

- **多 lens ensemble**——评审扇出成多个视角（logic / behavior / contracts…），
  逐条 keep/drop/dup 裁决后确定性合并；零产出的 lens 单独重问一次而不是整组重跑。
- **审查深度自适应**——确定性规则先裁明确案例（小而低风险 → light 单遍；大或
  高风险路径 → full 全 ensemble），只有灰区花一次小 LLM 调用，且该调用**只能选
  standard 或 full**：PR 内容说服不了 planner 降级。
- **双路径 mode**——`eco`（默认，便宜模型）/ `performance`（显式要求才升级），
  与 `tier` 正交：便宜模型永不放大任务权限。
- **五种后端**——`api`（Anthropic/OpenAI 兼容）+ 四个 harness：`cursor`、
  `claude-code`、`codex`（订阅制）、`deepseek`（dsh，唯一 API-keyed 的 harness）。
  harness 会话通过 MCP tool bridge 拿回 copilot 自己的工具，每次调用仍过
  `tools.dispatch`。
- **MoA**（Mixture-of-Agents）——lens/draft 提案可跑在异构成员上，预算在代码里
  硬封顶（先原子 `reserve()` 保守上界，结算时替换实际用量）。

---

## 3. 使用指南（操作者）

### 3.1 安装

**作为宿主 Skill（Direct，最常用）：**

```bash
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

./install-mcp.sh                              # macOS / Linux
./install-mcp.sh --repo-path /path/to/vllm-omni
install.cmd --repo-path D:\path\to\vllm-omni  # Windows
```

安装器识别本机的 Codex / Claude Code / Cursor，注册 MCP 与四个 Skill，并创建
`~/.infermatrix-copilot/.env`。未识别到已知 Agent 时生成标准
`infermatrix-copilot.mcp.json` 供其他 MCP 客户端导入。装完**重启 Agent**。

**作为独立 CLI（Strict）：**

```bash
bash install.sh          # 建 venv + editable 安装 + ./infermatrix-copilot 包装器 + 跑 doctor
bash install.sh --uninstall   # 只删自己创建的东西，不碰 .env
```

### 3.2 配置

密钥、机器路径、本地 checkout 只放 `~/.infermatrix-copilot/.env`，**不要提交**。

```bash
# 模型后端（Direct 不需要；Strict 必需其一）
ANTHROPIC_API_KEY=...        # 或 OPENAI_API_KEY
ANTHROPIC_BASE_URL=          # 可选，代理或兼容网关
LLM_PROVIDER=anthropic       # 两种 Key 都填时才需要指定
STRICT_BACKEND=              # 空=api；或 cursor / claude-code / codex / deepseek

# 模型分层
AGENT_MODEL=claude-sonnet-5  # 默认推理模型
ECO_MODEL= / PERFORMANCE_MODEL=      # 双路径两档（各有独立 BASE_URL / API_KEY）
REVIEWER_MODEL= / INTENT_MODEL=      # patch reviewer / 意图分类

# 目标仓库
REPO_PATHS={"vllm-omni": "/path/to/vllm-omni"}   # JSON：仓库名 → 本地路径
DEFAULT_REPO=vllm-omni
MCP_REPO_ALLOWLIST=          # MCP 侧允许的仓库集

# 写出闸门——默认全关，想要外部写入时才手动打开
ALLOW_PUSH=0                 # 1 = 允许 git push（仍只 --force-with-lease，永不推保护分支）
ALLOW_POST=0                 # 1 = 允许发 PR 评论 / issue 回复
```

配置不完整时，`review` 会直接返回缺少的项目，**不会**启动一个注定失败的后台任务。

### 3.3 确认装好了

宿主的 MCP 页面里应能看到 `infermatrix-copilot` 已连接；Codex 也可以
`codex mcp list`。CLI 侧：

```bash
infermatrix-copilot doctor            # 逐项 ✓/✗，失败即给出唯一修复命令
infermatrix-copilot doctor --json     # 供 CI
infermatrix-copilot doctor --probe    # 每档模型 1-token 实探（唯一付费检查）
```

doctor 只读、只打印密钥名不打印值。

### 3.4 Direct 怎么用

```text
$imreview https://github.com/vllm-project/vllm-omni/pull/5172   # Codex
/imreview                                                        # 当前 PR / 本地改动
/imupdate vllm-omni                                              # 也接受路径、别名、URL
```

宿主没主动调用时，直接说："Use InferMatrixCopilot in Direct mode to review this PR."

一次 `imreview` 的过程：固定 PR 快照并**在 60 秒内**先报 head SHA / CI /
mergeability → 调用 `review(mode="direct")` → 拿到 ≤3 条知识路由（含内嵌
`quick_map`，3.5k 封顶）+ `execution_budget`（硬顶）+ checklist → 并行读源码、
跑验证 → `validate_direct_review` 完成门 → 输出**单条**合并结论。

要跑 Strict 就明说："Use InferMatrixCopilot in Strict mode to review …"，
拿到 `run_id` 后用 `get_review_status` / `get_review_result` 轮询。

### 3.5 CLI 怎么用

```bash
infermatrix-copilot                              # 默认进对话式 REPL
infermatrix-copilot -p "review pr 4830"          # 一次性命令
infermatrix-copilot -p "review pr 4830" --plan-only   # 只看计划不执行
infermatrix-copilot -p "profile the repo" --yes       # 跳过确认（headless）
infermatrix-copilot --resume                     # 从首个未完成 step 重入
infermatrix-copilot --playbook profile-consolidate --yes   # 直接点名 playbook（含 candidate）
infermatrix-copilot --playbook pr-debug --report-only --task-param limit=5
infermatrix-copilot -p "review pr 4830" --performance      # 升到高性能模型档
infermatrix-copilot --no-chat                    # 用朴素命令 REPL 代替对话界面
```

REPL 内置 `/status`、`/logs`、`/playbooks`。复合命令（"… then review it"）会被切分成
有序队列并延续 PR/issue 引用。

**写操作一律需要确认**：`confirm_required` 由 kind 推导，只读 kind 之外都要过
确认门；`--yes` 才跳过。

### 3.6 产物在哪

```
~/.infermatrix-copilot/runs/run-<ts>-<uuid6>/
    RUN_REPORT.md         每个交付物恰好一次 + checkout 注记 + 待裁决 skill candidate
    DIAGNOSTICS.md        逐 step 诊断
    run_trace.jsonl       仅追加的事实记录
    progress.json         step 检查点（--resume 的依据）
    metrics.json          CATQ 成本/质量指标
    ESCALATION.md         仅在被阻塞时出现
~/.infermatrix-copilot/worktrees/<repo>-pr<n>/   PR 评审用的 PR-time checkout
adapters/<repo>/profile/                          仓库 profile
```

### 3.7 安全默认值一览

| 行为 | 默认 | 打开它需要 |
|---|---|---|
| git push | dry-run | `ALLOW_PUSH=1` **且** PushPolicy 允许 **且** 非保护分支 |
| 发 PR 评论 / issue 回复 | 关 | `ALLOW_POST=1` **且** 调用显式传 `post=true` |
| force push | 仅 `--force-with-lease` | 无法放宽 |
| 脏工作树 | 拒绝启动 | 先清理 |
| 未知仓库 | 生成 DRAFT adapter 后停下 | 人工审核后激活 |
| 高风险 manifest 段（`repo`/`upstream`/`push`） | agent 写入被拒 | 只能人工改 |

---

## 4. 开发指南（维护者）

### 4.1 代码地图

```text
src/infermatrix_copilot/
  intent.py  task_spec.py        终端串 → 受治理的 TaskSpec
  cli/                           entry / copilot（编排核）/ doctor / utils
  chat.py  ui.py                 对话式前门与终端 chrome
  engine/
    planner.py                   reuse > adapt > generate + 能力匹配
    executor.py                  ★ 共享 state、检查点/resume、扇出、typed failure
    step.py  registry.py         step 类型词汇与"名字→handler"解析
    steps/                       38 个 step 的实现（@step 自注册）
    agent_runtime/               runner / dispatch / ensemble / moa / knowledge / utils
  providers/                     ★ 五种后端的统一注册表（api + 四个 harness）
  tool_bridge.py                 harness 会话拿回 copilot 工具的 MCP 桥
  tools.py  scopes.py            原子能力与权限（每次调用的门）
  push.py                        ★ 全库唯一 push choke point
  review/                        条件式 Patch Review + 审查深度 planner
  profiles/  memory/             知识平面：profile store / skills / debug memory
  thin_mcp_server.py             ★ 默认 MCP：Direct 路由 + Strict 入口
  mcp_server.py  run_status.py   Strict 后台任务、状态、结果
  mcp_policy.py                  MCP 安全闸（边界 + 子进程各跑一次）
  llm.py  config.py  tracing.py  后端封装 / Settings / span 树
playbooks/*.yaml                 工作流定义（数据，不是代码）
adapters/<repo>/                 manifest（人工门禁）+ profile（证据门禁）
knowledge/                       通用 / 仓库 / 组件 / 模型知识（457 页）
doc/architecture/SPEC/                        与 src 文件一一对应的"不能破坏什么"
test/                            59 个离线测试文件
```

### 4.2 会静默损坏的四条不变量

改代码前先记住这四条——它们坏掉时不会报错，只会让行为悄悄退化。

1. **`state_updates` 契约**（`engine/executor.py`）。step 之间只通过一个共享
   `state` 字典交接。**任何被后续 step 消费的键，必须经 `outputs.state_updates`
   发布**，否则 `--resume` 会在恢复时丢掉它——表现为莫名其妙的 BLOCKED（缺
   `diff_text`）或 FORBIDDEN（PushPolicy 退回默认的 deny-all）。扇出的 updates 由
   `_merge` 提升到顶层；`when:` 条件遇未知键**大声阻塞**而不是静默跳过。
2. **`tier` 是推导出来的**（`task_spec.py`）。它是 `kind` 的 property，不是字段。
   不要为了方便加一个可写的 tier/权限字段——那等于把提权入口交给自然语言。
3. **`guard_push` 是唯一出口**（`push.py`）。所有对外写入必须经过它，
   `engine/steps/pr/publish.py` 是它唯一的调用点。新增任何 push 能力都要走这里。
4. **核心必须仓库中立**。`src/` 里不允许出现仓库名、模块名、领域 prompt、绝对
   路径——这些只能住在 `adapters/<repo>/` 或 `knowledge/`。核心 prompt 可以说
   *怎么审查*，只有 profile 能说*这个仓库是什么*。`test_repo_neutral_core` 用一份
   只能变短的泄漏清单封顶。

### 4.3 常见改动从哪里开始

| 要改什么 | 主要位置 | 最少验证 |
|---|---|---|
| Direct 返回内容或路由 | `thin_mcp_server.py`、Direct Skill | `test_thin_mcp_server.py`、`test_imreview_output_contract.py` |
| Strict 启动 / 轮询 / 发布门禁 | `mcp_server.py`、`mcp_policy.py` | `test_mcp.py` |
| 模型、Key、Base URL | `config.py`、`llm.py` | `test_llm_providers.py`、`test_tier_split.py` |
| 新增后端 | `providers/`（注册表 + transport） | `test_providers.py` + 对应 `test_provider_*.py` |
| 工作流步骤 | `playbooks/*.yaml`、`engine/steps/` | 对应 step 测试 + playbook 加载测试 |
| 新仓库支持 | `adapters/<repo>/`、`knowledge/repos/<repo>/` | adapter 测试 + 知识检查 |
| 评审质量 | `engine/steps/review/`、`review/planner.py` | `test_review_*.py`、`test_agent_ensemble.py` |
| 安装或发布包 | `scripts/install_mcp.py`、`pyproject.toml` | installer 测试 + wheel 内容检查 |

**加一个 step**：在 `engine/steps/*.py` 写 handler，用
`@step(name, kind, risk, description)` 装饰（自注册，不用改中央注册表），
把被消费的键经 `state_updates` 发布，补一个护栏测试。

**加一个 task kind**：`task_spec.py`（kind + tier）→ 写 playbook yaml →
intent hint → chat enum。planner / executor 不动。

**加仓库知识**：用类型化 patch op 写 profile fact，或加一个 skill。三条注入面
都有硬上限（briefing 350 词 / 每个 SKILL.md body 1,500 字符 / `review.md`
4,000 字符），超出**静默丢弃**——改完先量字符数。

### 4.4 本地开发与验证

```bash
python -m pip install -e ".[dev,mcp]" ruff build
PYTHONPATH=src python -m pytest        # 59 个测试文件
python -m ruff check .
git diff --check
```

改了知识文件额外跑：

```bash
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

改了发布包：`python -m build --wheel`，并确认 wheel 里含 `knowledge/`、
`_runtime/playbooks/`、`_runtime/adapters/`、`_runtime/skills/`——只验证源码
checkout 证明不了这件事（`test_packaged_runtime.py` 只断言 pyproject 的**文本**）。

CI（`.github/workflows/test.yml`）跑上面全部检查，外加把 wheel 装进干净 venv 验证
四棵数据树确实随包发布。**注意：CI 目前只是信号，不是合并门禁**——要让它真正挡住
合并需要在仓库 Settings 里把 `suite` job 设为 required status check。

### 4.5 护栏测试：你不能破坏的行为

| 测试 | 固定的不变量 |
|---|---|
| `test_v2_p0.py::test_repo_neutral_core` | `src/` 仓库字面量被泄漏清单封顶 |
| `test_v2_p0.py::test_resume_restores_state_handoffs` | `state_updates` 契约 |
| `test_capabilities.py` | 能力匹配；locked rebase 不泄漏 |
| `test_profile_store.py::test_stability_gate_and_history` | stable fact 永不丢证据 |
| `test_profile_steps.py::test_profile_agent_applies_gated_facts` | 无证据的 fact 被拒 |
| `test_p3_machinery.py::test_judge_reports_but_never_mutates` | profile judge 只读 |
| `test_agent_runtime.py`（参数化 dispatch） | `kind=="agent"` ⇒ 统一运行时治理 |
| `test_agent_runtime.py::test_unparseable_after_repair_is_salvaged_as_escalation` | 非空失败答复被抢救 |
| `test_agent_loop.py::test_final_round_nudge_follows_tool_results` | 收尾提示排在 tool_result 之后 |
| `test_agent_ensemble.py::test_render_verdict_calibration` | 仅已验证的 blocker/major 阻塞 |
| `test_agent_ensemble.py::test_zero_yield_lens_gets_one_retry` | 零产出 lens 单独重问 |
| `test_moa.py` | MoA 预算台账封顶；密钥永不落 trace |
| `test_review_step.py::test_review_salvaged_when_agent_escalates_with_comments` | 带 comments 的 escalate 被抢救 |
| `test_pr_steps.py::test_fetch_diff_pins_pr_time_checkout` | 评审树 pin 到 PR head |
| `test_memory.py::test_skill_touch_increments_usage` | 用量先验累计 / debug memory 写入 |
| `test_push_and_steps.py` | `guard_push` 语义 |
| `test_mcp.py` | 篡改防御、单写者对账、分页、只读工具集 |

### 4.6 知识树的编辑规矩

增删移任何知识页之前，先读 `doc/knowledge/CONTRIBUTING.md`，再读**恰好一个**匹配的
贡献主题（`doc/archive/PLAN-knowledge-reorg.md` 是已归档历史，不是现行契约）。要点：

- 每条结论按**用途 + 代码 owner** 双重路由；PR 学习只能产出可执行规则，写进最近
  owner 的 `rules.md`。
- 原始 PR 材料是仓库外的临时输入，规则批次验证通过后**必须删除**。
- 不要新增 PR case / history / result / incident 页，也不要把异构 owner 合并成一个
  大杂烩页面。现存的 `incidents/`、`history/`、`results/` 是遗留物，不是新知识的
  合法去处。
- 评测生成的用例、隐藏标签、预测、判分、run 报告属于 `eval/`，不属于产品知识树。
- 每个现行 rules 页都要更新最近的 `_index.md`。
- 整批改完后跑两个 validator（见 §4.4）。

---

## 5. Playbooks

Playbook 是**数据**（`playbooks/*.yaml`），不是代码。`PlaybookStore.find(kind, repo,
capabilities)` 负责召回：精确 repo 优先；`repos: []` 的仓库无关 playbook 仅当
`requires ⊆ capabilities` 才匹配；**candidate 永不被自动召回**（只能
`--playbook <name>` 点名）。

### 5.1 全部 9 个

| playbook | ver | status | kind | repos | requires |
|---|---|---|---|---|---|
| `pr-review` | 6 | active | `pr_review` | 任意 | `repo.path` |
| `pr-debug` | 2 | active | `pr_debug` | 任意 | `repo.path` |
| `pr-rebase` | 2 | active | `pr_rebase` | 任意 | `repo.path` |
| `issue-answer` | 2 | active | `issue_answer` | 任意 | `repo.path` |
| `issue-triage` | 2 | active | `issue_filter` | 任意 | `repo.path` |
| `repo-profile` | 1 | active | `repo_profile` | 任意 | — |
| `repo-rebase-v3` | 1 | **locked** | `repo_rebase` | 任意 | `modules`, `upstream.fork_tracking`, `ci.provider` |
| `profile-consolidate` | 1 | candidate | `repo_profile` | 任意 | `repo.path` |

### 5.2 各自的 step 链

**`pr-review`** — 评审主线。`agent.review_diff` 内部才是多 lens ensemble。

```
pr.fetch_diff → pr.gate_check → agent.review_diff → [post] pr.post_review → report.final_summary
```

**`pr-debug`** — `report_only` 时停在分组，成为独立可用的只读 triage。

```
workspace.guard_clean → pr.checkout_branch → pr.fetch_ci_failures → pr.group_failures
  → [not report_only] agent.debug_group (foreach failure_groups)
  → [not report_only] review.patch_gate → [not report_only] ci.push → report.final_summary
```

**`pr-rebase`** — push 只针对 PR head 分支，force 仅 with-lease。

```
workspace.guard_clean → pr.checkout_branch → pr.rebase_onto_base → pr.analyze_diff
  → agent.verify_module (foreach affected_modules)
  → [not report_only] review.patch_gate → [not report_only] ci.push → report.final_summary
```

**`issue-answer`** / **`issue-triage`**

```
issue.fetch → agent.draft_issue_answer → [post] issue.post_answer → report.final_summary
issue.fetch → agent.triage_issues → report.final_summary
```

**`repo-profile`** — Stage 0–1.5，对目标仓库只读，只写 `adapters/<repo>/`，产出是 DRAFT。

```
profile.fingerprint → profile.structure_scan → profile.ingest_docs
  → [not report_only] agent.profile_repo → report.final_summary
```

**`profile-consolidate`** — Stage 4，**设计上就是 candidate**：对 planner 不可见，
只能显式或定时触发，让"重写"留在有节奏的独立层里（个人 agent 的教训：连续重写会
腐蚀记忆）。

```
profile.fingerprint → profile.detect_drift → profile.decay_stale
  → [not report_only] agent.profile_consolidate → profile.judge → report.final_summary
```

**`repo-rebase-v3`**（locked）— 全仓库 rebase 引擎：rebase_engine 全量合并后的
原生管线，仓库中立（能力门控召回）。2026-08-25 业主令 PR6+PR7 一体切换：晋升
v3，删除委托版 v2 与 native-v1。L0 原样复用，永不改编或重新生成。四档
`rebase_mode`（report_only / local_ci / remote_ci / full）经 `when:` 门控步骤：

```
rebase.v3_prelude → guard(_check) → v3_knowledge_prep
  → [report_only] v3_scan
  → [full] v3_wheel → v3_assign → v3_module_rebase (foreach wave1_modules)
      → v3_wave_gate → v3_module_rebase (foreach wave2_modules)
  → [本地测试] v3_test_loop → v3_precommit
  → [push] v3_push_gate → [远端 CI] v3_ci
  → [full] v3_phase5_report → v3_curate → v3_compare
  → report.final_summary → v3_finalize
```

### 5.3 生命周期

```
candidate ──人工晋升──▶ active ──▶ locked        回滚 = git revert
   ▲                                  │
   └──────────── retired ◀────────────┘
```

- **locked** 拒绝改编（planner 抛错而不是悄悄改）。
- **candidate** 对 `find()` 不可见，只能点名运行——晋升前的验证期就靠这个。
- 每个 playbook 带 `provenance`（谁创建、来源），改编产生的新版本要经 plan review 门。

---

## 6. Steps

38 个 step 在 `engine/steps/` 就地 `@step` 自注册（`rebase_native.py` / `issue.py` /
`pr/publish.py` 里有几个用 `register_step` 直接注册）。每个 step 声明两个属性：

- **kind**——`deterministic`（17）· `agent`（8）· `script`（7）· `validation`（3）·
  `report`（3）。`kind == "agent"` 是有语义的：它意味着这个 step 走统一的
  `run_agent_step` 运行时治理（dispatch context、证据围栏、scope、结构化输出契约、
  完整 trace），由一个参数化测试钉死。
- **risk**——`read` · `knowledge` · `write_workspace` · `push` · `report`。

失败是**值不是异常**：`StepResult.failure` 是六种 `FailureKind` 之一，
BLOCKED / ESCALATE / FORBIDDEN 会通知并停机，只有 RETRYABLE 会有界重试。

### 6.1 deterministic（17）— 不花模型调用

| step | risk | 做什么 |
|---|---|---|
| `workspace.guard_clean` | read | 脏工作树拒绝启动 |
| `analysis.diff_summary` | read | 廉价 diffstat + 越界/全量写标志 |
| `pr.fetch_diff` | read | 取 PR diff；内含 **PR-time checkout**（把评审树 pin 到 PR head） |
| `pr.gate_check` | read | draft / merge-state / failing-checks 门禁报告 |
| `pr.checkout_branch` | read | fork-aware 检出 PR head，推导 PushPolicy |
| `pr.analyze_diff` | read | 改动文件 → 受影响模块（adapter 映射） |
| `pr.fetch_ci_failures` | read | 收集失败的 check（可注入，离线可测） |
| `pr.group_failures` | read | 按根因签名分组；超硬上限则升级 |
| `issue.fetch` | read | 取 issue |
| `profile.fingerprint` | knowledge | Stage 0 指纹；未知仓库产出 DRAFT adapter 后停下 |
| `profile.structure_scan` | knowledge | Stage 0 模块草稿（**永不覆盖**已声明模块） |
| `profile.ingest_docs` | knowledge | 摄入 AGENTS.md/CLAUDE.md 式人工指令（文档冗余行丢弃） |
| `profile.detect_drift` | read | Stage 4 漂移报告——刷新材料，绝不自动修 |
| `profile.decay_stale` | knowledge | Stage 4 休眠衰减：未确认的 fact 转 stale（排除但**不删**） |
| `rebase.prelude` | read | 父运行时设置 + wave 列表 |
| `rebase.phase2_prepare` | read | 预检 curator + phase-2 进度初始化 |
| `rebase.phase2_finalize` | read | 两个 wave 完成后推进父标记 |

### 6.2 agent（8）— 走统一运行时治理

| step | risk | 做什么 |
|---|---|---|
| `agent.review_diff` | read | 证据锚定的两阶段评审：工具循环调查草稿 → verify-and-rewrite 编辑轮 |
| `agent.draft_issue_answer` | read | 起草 issue 回复（含 close/keep-open/duplicate-of-#N 处置槽） |
| `agent.triage_issues` | read | 批量分类路由 |
| `agent.debug_group` | write_workspace | 修一个失败组的根因并提交；成功后写回 debug memory |
| `pr.rebase_onto_base` | write_workspace | rebase 到最新 base；冲突交给受治理 agent 或 abort+升级 |
| `agent.profile_repo` | knowledge | Stage 1：推导非显然、**必须引证据**的 profile fact |
| `agent.profile_consolidate` | knowledge | Stage 4：**唯一**允许 rewrite/merge 的层，强制稳定性门禁 |
| `profile.judge` | read | Stage 4 只读审计 → JUDGE_REPORT.md，findings 只呈现不自动应用 |

### 6.3 script（7）— 委托或对外写

| step | risk | 做什么 |
|---|---|---|
| `ci.push` | **push** | 受门禁的 push（PushPolicy ∧ 保护分支双闸，默认 dry-run） |
| `pr.post_review` | **push** | 单条 GitHub review + inline threads（显式 post 标志 + `ALLOW_POST`） |
| `issue.post_answer` | **push** | 发布 issue 回复（同样双闸） |
| `rebase.phase4` | **push** | 父 Phase 4（push + Buildkite CI），走 copilot 的 push guard |
| `rebase.run_external` | write_workspace | 委托给已有 5 阶段编排器（locked 流水线） |
| `rebase.phase1` | write_workspace | 父 Phase 1（init） |
| `rebase.module_rebase` | write_workspace | 单模块 rebase，委托父仓库自己的 `node_rebase_module` |

> 全库只有这 4 个 `risk == "push"` 的 step，全部经 `push.py::guard_push`。

### 6.4 validation（3）与 report（3）

| step | kind | risk | 做什么 |
|---|---|---|---|
| `review.patch_gate` | validation | read | 条件式 patch review，push 前 fail-closed |
| `agent.verify_module` | validation | read | 逐模块 rebase 损伤检查——纯 LLM 建议，**不是**受治理 agent step |
| `rebase.phase3` | validation | write_workspace | 父 Phase 3（本地流水线测试 + SDK debug 循环） |
| `report.final_summary` | report | report | 写 `RUN_REPORT.md` + `DIAGNOSTICS.md` |
| `rebase.phase5` | report | report | 父 Phase 5 最终摘要 + 运行后 curator |
| `rebase.compare_with_locked` | report | report | `COMPARISON.md`：原生 run vs locked 基线（晋升证据） |

---

## 7. Tools

"工具"在这个仓库里指**三个不同的面**，混为一谈正是 Direct/Strict 混淆的起点。

### 7.1 内置 agent 工具（6 个，沙箱内）

给 Strict 侧 agent step 用，定义在 `tools.py::TOOLS`。

| 工具 | 说明 |
|---|---|
| `read_file` | **窗口化**读取（每次 48k 字符，用 `offset` 翻页） |
| `write_file` | 写/覆盖文件 |
| `edit_file` | 精确一次匹配的文本替换 |
| `list_dir` | 列目录 |
| `grep` | 递归搜索。pattern **默认按字面量匹配**，要正则得传 `regex:true` |
| `run_shell` | 执行命令，stdout/stderr 各截断返回 |

**一条铁律：每一次工具调用都过 `tools.dispatch`**，检查 `ToolScope`（允许哪些工具）
和 `PathScope`（允许写哪些路径）并记 trace，三种结果——允许 / 拒绝 / 越界但记录。
agent 永远看不到 scope 不允许的工具（`tool_definitions_for` 按 scope 过滤）。

> `read_file` 为什么必须窗口化：整文件读会吹爆会话历史、倍增未缓存 token、把对话
> 推出可靠缓存长度。这不是保守，是实测过的成本项。

### 7.2 Step 提供的工具（按需注入）

由具体 step 在 dispatch 时追加，已被该 step 审核过：

- **只读 gh**——`gh_pr_view`、`gh_issue_view`、`gh_issue_timeline`、`gh_ci_read`
- **知识**——`skill_search`、`memory_search`、`skill_update_candidate`
  （**只能提案 candidate**，人类晋升）
- **结构**——`repo_map`（按查询排序、有字符预算的符号索引；由 agent 主动拉取，
  绝不散文注入）
- **考古**（v14 新增，只读）——`diff_stat`、`file_at_base`、`show_commit`、
  `search_history`、`calc`

harness 后端通过 `tool_bridge.py` 以 MCP 形式拿到这些工具，每次调用仍然回到
`tools.dispatch`——所以换后端不会绕过权限闸。跨进程的 candidate 写入是**故意
没有开放**的。

### 7.3 MCP 工具（7 个，面向宿主）

`thin_mcp_server.py` 暴露给 Claude Code / Codex / Cursor：

| 工具 | 说明 |
|---|---|
| `review(target, repo, mode, post, review_depth, title, body, changed_files, repo_path)` | Direct 返回 ≤3 条知识路由 + 治理契约；Strict 返回 `run_id` |
| `validate_direct_review(subtraction_signal, subtraction?, minimality_proof?, final_comment_count, evidence_head_sha)` | Direct 最终输出前的**完成门** |
| `get_review_status(run_id)` | Strict 后台任务的步骤与进度 |
| `get_review_result(run_id, offset)` | 轮询 Strict 结果，按 `next_offset` 分页 |
| `update_knowledge(repo)` | 只返回知识贡献入口，**不是** `imupdate` 的发版审计器 |
| `doc_search(query, repo, limit)` | 搜索模型/组件知识 |
| `doc_read(path, repo, offset)` | 读取搜索到的知识页（24k/页） |

两点值得注意：

- `validate_direct_review` 是**机械的结构检查**——它验证形状（`none` 不得附带证据；
  `triggered` 需要减法项或最小性证明；恰好 1 条最终评论；`evidence_head_sha` 必须是
  本次固定的 head），它**不验证证据真伪**。server 管不住宿主的模型，所以把"该怎么
  审"编码成结构化字段随返回值下发，再用完成门机械验收。
- `mcp_policy.py` 在**边界**（server）和**子进程**（权威）各跑一次：kind 必须 ∈
  `READ_ONLY_KINDS`，`post` 硬置 False，repo 必须在 allowlist，未知 params 剥除。
  允许集直接引用 `task_spec.py` 的 `READ_ONLY_KINDS`，永不与代码漂移。

---

## 8. 性能对比

> **数据日期 2026-08-17。** 后端矩阵是本仓库变动最快的数据（过去一周重写三次），
> 引用前请以 `eval/dataset/results/model_comparison.md` 为准；本节的方法论和结论
> 结构比具体数字更耐久。

### 8.1 一句话结论

**在 recall 上落后 CC + Opus 5 基线约五个 rubric 点，precision 打平，成本约为其
三分之一。** 这个结论由预注册的 20 项测量给出，此前一次"优于基线"的宣称已被撤回。

### 8.2 主结论（v14→v16，预注册）

判官 claude-sonnet-5，盲配对，3 replicate，对同一批冻结快照上的 pinned Opus 5 基线。
Δ = arm − baseline，在**每条 verdict 内部配对**、按 item 聚类。

| 统计量 | 值 | 触发的决策规则 |
|---|---|---|
| **Δrecall** | **−.049 [−.097, −.001]** | CI 整体低于 0 → 缺口**真实存在**，停止宣称 recall 打平 |
| **Δprecision** | **−.000 [−.041, +.040]** | CI 含 0 → 打平 |

成本 $0.97/item vs 基线 $3.09/item。

这个 recall 缺口是**边缘且集中**的：上界 −.001；20 个 item 里 6 个偏向 arm、4 个在
±.02 以内，而单个 item（pr5978，−.37）贡献了约三分之一的缺口。按预注册的规则，
**没有跑第三个 wave**。

### 8.3 测量纪律（本节最值得保留的部分）

这份报告的中期版本本来会宣称"在新 holdout 上 precision 高于基线"。该结论**被撤回**，
因为原始均值支撑不了它：三组 wave-4 judgment 对**同一批**基线评审打分，基线 recall
均值分别是 .335 / .338 / .416——±.08 的纯判官漂移，比所有被研究的效应都大。

三条推论，都超出这次战役本身：

1. **绝不拿一组 judgment 里 arm 的均值去比另一组里 baseline 的均值。** 要在 verdict
   内部配对（同一次判官调用同时给两个候选打分，它的宽严自然抵消）。
2. **同一个 item 的多个 replicate 不是独立观测。** 10 items × 3 replicates 对 CI 来说
   是 n=10 而不是 n=30；当成 30 会把标准误低估约一倍。
3. **花掉 holdout 之前先算功效。** 在实测的 item 级 sd（.103–.127）下，分辨 .05 的
   差异需要约 32–38 个 item。wave 4 的 10-item 门根本无法回答它被用来回答的问题——
   三个配置是对着一个测不出来的标准提交的。

配套落地的三道流程闸（2026-08-17，每道对应一次真实事故）：manifest 记录**解析后**
的设置而非 env 字符串（一个默认值在底下变了，15 项探针实际跑成三厂商混合而 artifact
里看不出来）；余额预检**拒绝启动**而不是跑到一半死（三天两次 402，空账户变成 rc=3
桩再被判成零分）；混合门覆盖 MoA 路径（此前只检查 `REVIEW_LENS_BACKENDS`）。

### 8.4 两个受支持的配置

| 配置 | 特点 | 什么时候用 |
|---|---|---|
| **v15**（默认，全 DS） | 偏 precision，~$1/item | 走量的日常评审 |
| **v16**（`REVIEW_LENS_BACKENDS` 把 Fable 路由进 adversary + 第二轮） | 偏 recall，每 item 多两次 harness 会话 | 高风险 PR——漏掉缺陷的代价高于多一条噪声评论 |

配置效应**在符号上可复现**，即使单个 delta 不显著：v15 在两次独立生成里都偏
precision（+.029 / +.022）；v16 拿到新 split 上最好的 recall（.336），并且是唯一在
流水线内部复现 GOLD 缺口捕获的配置。

### 8.5 后端矩阵（2026-08-17）

五个后端，一张注册表（`providers/registry.py`）。`api` 是原有路径被收编进同一注册表
的结果——用 `api` 时行为逐字节不变。

| 后端 | kind | 凭据 | 能力 | 状态 |
|---|---|---|---|---|
| `api` | api | `.env` 里的 Key | 完整（我们自己的工具循环） | 基线路径，behavior 平价棘轮 |
| `cursor` | harness | 订阅（cursor-agent CLI） | `mcp_tools` `usage_reporting` | 已实测 |
| `claude-code` | harness | 订阅（claude CLI） | 五项能力最全（含 `builtin_tools_off` `max_turns` `cost_reporting`） | 订阅认证下实测 |
| `codex` | harness | 订阅（codex CLI） | `mcp_tools` `sandbox_read_only` `usage_reporting` | 仅离线测试（开发机无 ChatGPT 登录） |
| `deepseek`（dsh） | harness | **API Key**（唯一 api-keyed 的 harness，走 SDK 无 PATH 二进制） | `mcp_tools` `sandbox_read_only` `system_prompt` | 最新加入 |

**同一批 10 个 train item 上的后端冠军是 api/DeepSeek 核心，不是 Composer：**

| 配置 | Δrecall [95% CI] | Δprecision [95% CI] | win share |
|---|---|---|---|
| v17ds train（api/DeepSeek，10 项） | **+.024 [−.030, +.077]** | **+.016 [−.061, +.093]** | .47 |
| v17ds pooled（15 项） | −.004 [−.056, +.049] | −.008 [−.078, +.062] | .38 |
| v17cb train（Composer 2.5 / cursor） | −.052 [−.165, +.061] | −.097 [−.215, +.021] | .20 |
| v17cb val（Composer 2.5 / cursor，5 项） | −.003 [−.222, +.215] | −.040 [−.322, +.242] | .40 |

val 一度把 Composer 排在前面，那是小样本幻觉：n=5、区间 ±.22，而 train 的 item 方差
紧四倍（sd .075 api vs .158 cursor）。Composer 的分散来自大摆动（pr4970 +.317 对
pr4923 −.233），api arm 则在十项里有七项落在 ±.06 内。

**读这张表时必须知道的三件事：**

- 这两个 split 已经被整个战役迭代过，是 probe 不是 gate，**不能支撑关于新数据的
  结论**；每个 CI 都跨零，结果是"n=15 下测量精度内的打平"，不是"更优"。
- val（−.059）与 train（+.024）**符号相反**，pooled 的 −.004 是在平均一个真实的
  split 差异；val 的缺口几乎由 `pr4893` 一项承担（DeepSeek −.250，Composer −.267）。
  同一个 item 在两个不同模型下几乎同样失败，说明那是**流水线缺陷而非模型缺陷**。
- 2026-08-16 曾报告"转换修复没能缩小 recall 缺口"（pooled −.050），该测量被一次
  非预期的厂商混合污染；同样 10 项从 −.052（污染）变成 +.024（干净），摆动 +.076，
  **原结论已撤回**。

### 8.6 成本与时延（wave-2 holdout，每 item）

| arm | $/item | 墙钟 |
|---|---|---|
| CC + Opus 5 基线 | $3.58 | 547 s |
| DS v4-pro（api） | $0.78–0.79 | 1139–1322 s |
| MiMo-v2.5（api） | $0.43 | 1728 s |
| Composer-2.5（harness） | 订阅 | 177–397 s |
| Grok-4.5 / 4.6（harness） | 订阅 | 284–1111 s |
| MoA r1（混合） | $0.33 API + 订阅 | 1195 s |

harness 后端快 2–4 倍且吃订阅，但每项都记到 `tok_out=0`——harness 会话不向 span
记账暴露 token，所以它们的成本优势是**假定的，不是测出来的**。这是刻意不伪造：
metrics 记 source 为 `subscription`，绝不编造 USD。

### 8.7 一个污染教训

grok 家族（4.5 和 4.6，Composer 从未出现）会在评审会话中**主动搜索并读取 copilot
自己的 `imreview` 评审方法论 skill**。相关 arm 已进污染台账并作废。跑 cursor 系
评测前，三份 skill 副本必须移出 `$HOME` 并在事后恢复。

### 8.8 继任者从哪里开始

1. **缺口是一类 item，不是一个水平差。** 三分之一的 pooled 缺口来自单个 item；
   wave-3 forensics 已命名了复发类别（test/gate 认知论、文档信息架构、CI 经济性）。
   修这一类比再来一轮通用 duties 划算。
2. **先给 gate 编预算，再改流水线。** 10 个 item 上测出来的任何东西在这个量级都
   不可解释。
3. **唯一没试过的杠杆是全程用强生成器。** Fable 占两个 seat 时产出了本战役最好的
   recall 和唯一一次流水线内 GOLD 缺口捕获；Fable 占满所有 seat 估算 ~$10–20/item
   （成本故事反转），已被明确 scope 并**刻意没跑**。

---

*本文档覆盖到 2026-08-17 的 `rfc/strict-review-deep-engine` 分支状态。
数字类内容以 `eval/dataset/results/` 与 `doc/evaluation/EVAL-*.md` 为准。*
