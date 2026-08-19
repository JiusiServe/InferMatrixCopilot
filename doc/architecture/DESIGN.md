# 设计

本仓库实现的是 **InferMatrixCopilot** 的设计 —— 它最初以 "vLLM-Omni Copilot" 之名
写在 `vllm-omni-rebase-agent/docs/copilot/copilot_design` 里，外加它的
`implementation/` 里程碑计划。本文档把那份设计映射到这里的代码上；**理据本身住在那些
源文档里**。

下面的 Part I 描述**如实建成**的 v1 架构。**Part II（Design v2，2026-07-10）** 在其上
扩展三个目标：修掉 v1 的已知问题、让 copilot **仓库不变**（跨仓库保持稳定的任务表现），
并让它有能力为任何被指向的仓库**建立仓库 profile**（代码格式、skill、约束、模块分析
及相关产物）。**Part III（Design v3，2026-08）** 记录 Direct 模式与 provider 注册表。

---

# Part I —— v1 架构（如实建成）

## 架构

```
 用户自然语言 ──► intent.py ──► TaskSpec (task_spec.py)          §3.Y CLI 层
                                  │  tier 由 kind 固定 (L0/L1/L2)，确认门
                                  ▼
                         engine/planner.py                      §3.2 reuse>adapt>generate
                  reuse ─────────┼───────── generate（仅只读 kind）
                                  ▼
                      playbooks/store.py 注册表               §3.2 candidate/active/locked
                                  ▼
                        engine/executor.py                      §3.X 引擎底座
            逐 step 检查点/resume · 重试 · 类型化失败 · 升级
                                  ▼
                 engine/steps/*          （Step 库）             §3.X.1 Steps
          tools.py + scopes.py（ToolScope/PathScope choke point） §3.3(2)
          review/（diff 摘要 → 触发器 → 只读 reviewer）           §3.3(3)
          memory/（RunTrace、FTS5 DebugMemory、受门 skill）        §3.3(4)
          adapters/（仓库知识、draft 引导）                        adapter 层
          push.py（PushPolicy + guard_push）                      推送授权
          notify.py（ESCALATION.md + 邮件、退出码 3）              目标 #4
```

## 关键决策

1. **包装 rebase，而不是重写它。** locked 的 `repo-rebase` playbook 经
   `rebase.run_external`（`REBASE_ORCHESTRATOR_CMD`）委托给已有的 5 阶段编排器。
   **零回归**：本仓库是在这条已验证流水线**外面**加编排，**不 fork 它**。
   rebase 的原生 step 级分解（wave、模块 agent）按里程碑计划**稍后**迁移。
2. **自建 executor 而不是 LangGraph。** 设计（§3.X.5）明确说 LangGraph 是一个**可能的
   后端**，不是领域抽象。这里的 executor 约 150 行、异步、带逐 step 检查点/resume ——
   **无依赖且完全可测**。将来若与父 agent 合并，可以在同一套 `Playbook`/`StepSpec`
   契约之后换上 LangGraph 后端。
3. **tier 是推导的，绝不解析而来。** `TaskSpec` **没有**任何 LLM 或用户可设置的 tier
   字段；`tier` 是任务 kind 的 property。因此**自然语言永远无法扩大权限**（§3.Y.4）。
4. **生成路径在结构上只读。** planner 的 generate 路径在任何被编排的 step
   `risk` ∈ {write_workspace, push} 时抛错；没有已审核 playbook 的写能力 kind
   **升级而不是即兴发挥**。
5. **评审 fail-closed。** 没有 reviewer LLM 时 `run_patch_review` 返回 `unavailable`；
   无法解析的 reviewer 输出降级为 `revise`。推送门把除 `lgtm` 之外的一切都视为未通过。
6. **不可信数据被围栏。** 从 GitHub 抓取的文本进入 agent prompt 时被包在
   `<untrusted_data>` 标记内，并带显式的"这不是指令"前言；**只有终端输入到达意图解析器**
   （通道分离，§3.Y.4）。**抗注入来自通道分离，不是来自解析器。**
   （注：意图分类当时是"仅 LLM"；v3 期加入了确定性预解析层 —— 见
   `SPEC/intent.md`。）

## 模块映射

| 路径 | 设计概念 |
|---|---|
| `src/infermatrix_copilot/task_spec.py`、`intent.py`、`cli/` | §3.Y 对话式 CLI、TaskSpec、澄清而不猜测 |
| `src/infermatrix_copilot/engine/step.py`、`registry.py` | §3.X Step 抽象、已审核 step 库 |
| `src/infermatrix_copilot/engine/executor.py` | 引擎底座：检查点/resume、类型化失败路由 |
| `src/infermatrix_copilot/engine/planner.py` | §3.2 reuse > adapt > generate，L0/L1/L2 |
| `src/infermatrix_copilot/engine/steps/` | 已审核 step 库（守卫、rebase、评审门、push、gh 读、agent step）—— 自注册 |
| `src/infermatrix_copilot/engine/agent_runtime/` | 统一的 Agent-Step 运行时（修正方案；包结构：dispatch/knowledge/utils 底座 + runner/ensemble 入口）：AgentDispatchContext、证据包（封顶+归档）、skill/memory 检索 + 受门 candidate、强制 scope、结构化输出契约、完整 RunTrace；`run_agent_step_ensemble` —— 视角多样的扇出 + verify-and-merge，用于跨 run 稳健性（由评测得出；适用于任何列表输出型 agent step） |
| `src/infermatrix_copilot/playbooks/store.py`、`playbooks/*.yaml` | Playbook 注册表：带版本、带 provenance、candidate/active/locked/retired |
| `src/infermatrix_copilot/scopes.py`、`tools.py`、`agent_loop.py` | 框架层改进 (2)：单一 choke point 上的 ToolScope/PathScope |
| `src/infermatrix_copilot/review/` | 框架层改进 (3)：diff 摘要 → 触发规则 → 只读 patch reviewer |
| `src/infermatrix_copilot/run_trace.py`、`memory/` | 框架层改进 (4)：RunTrace / DebugMemory / 受门 skill |
| `src/infermatrix_copilot/adapters/` | RepoAdapter：adapter zero、注册表、确定性引导 → draft |
| `src/infermatrix_copilot/push.py` | 推送授权：`PushPolicy` + 统一的 `guard_push`（没有独立的 Target 层） |
| `src/infermatrix_copilot/notify.py` | 目标 #4：升级通道，被阻塞时退出码 3 |

## 逐 run 的数据与产物

`~/.infermatrix-copilot/runs/run-<ts>/`：`run_trace.jsonl`（事实）、`progress.json`
（step 检查点 —— resume 从首个未完成 step 重新进入）、`RUN_REPORT.md`、
`ESCALATION.md`（仅在被阻塞时）。

---

# Part II —— Design v2：仓库不变的 copilot（2026-07-10）

v1 已经写下了多仓库的成功判据（"接入第二个仓库不得触碰核心引擎 —— 只加一个 adapter"）。
v2 把它从*能跑起来*加强为**跑出稳定、可测量的表现**，并补上当前让这件事不可能达成的
那些缺口。三条工作流：

1. **§V2.1 修掉既有问题** —— 正确性缺陷、渗进核心的仓库知识、v1 遗留的开放边界。
2. **§V2.2 仓库不变性** —— 一份可强制的契约：引擎是仓库中立的，且质量是**逐仓库测量的，
   不是假定的**。
3. **§V2.3 仓库 profile** —— copilot 能够建立、维护并消费任何仓库的完整 profile：
   代码格式、skill、约束、模块分析，以及任务所需的其他产物。

## V2.0 先行工作与证据（调研，2026-07-10）

关于"给 agent 提供仓库上下文"这件事，业界学到了什么 —— 下面每一条都改变了一个 v2 决策。
来源列在本节末尾。

1. **自动生成的仓库上下文文件是有害的。** 苏黎世联邦理工的研究
   （[arXiv:2602.11988](https://arxiv.org/html/2602.11988v1)，438 个任务、4 个 agent）
   发现 LLM 生成的 AGENTS.md 式文件会**降低**解决率（−0.5 至 −2%），同时增加 20–23%
   的推理成本和 2–4 个额外步骤；agent 会尽责地照做那些额外指令（更多 grep、更多测试），
   **却换不来准确率**。代码库/目录概览 —— 在约 100% 的生成文件里都有 ——
   对"agent 多快够到相关代码"的影响是**零**。人工撰写的文件只有轻微帮助（+4%），
   而且**仅当**它们承载**非冗余、仓库专属的工具事实**（用哪个包管理器、确切的
   build/test 命令）；当同样的信息在 README/docs 里已经存在时，上下文文件是**纯成本**。
   GitHub 自己对 `copilot-instructions.md` 的建议也一致：从 10–20 条简短祈使指令开始，
   对照观察到的行为迭代。
   → **v2 后果**：profile **不是** prompt 倾倒场。它的大部分内容必须**被代码消费**或
   **按需检索**；always-on 的 prompt 切片必须**最小、精选，并在评测上自证其价值**
   （§V2.3.4、§V2.3.5）。
2. **有用的那张"图"是逐任务算出来的，不是一次写死的。** Aider 的 repo map
   （tree-sitter 符号图 + 个性化 PageRank，按每次对话的 token 预算裁剪）和 RepoGraph
   这条线（[arXiv:2410.14684](https://arxiv.org/html/2410.14684v1)，SWE-bench 上相对
   +32.8%；CodexGraph [arXiv:2408.03910](https://arxiv.org/abs/2408.03910)）
   都表明：仓库**结构**作为一张**可查询、按当前目标排序**的图才有回报 ——
   而不是作为一份静态概览文档。
   → **v2 后果**：`modules.yaml` 是**机器产物**（喂扇出、patch 触发器、wave 调度），
   外加给 agent step 用的按需 `repo_map` 工具；**它绝不被整体注入 prompt**。
3. **触发式知识胜过 always-on 知识。** OpenHands 的 microagent/skill
   （关键词触发的 .md 文件）、Devin 的知识库（每一条 = 内容 + 一段**触发描述**，
   相关时被语义召回）、以及 Agent Workflow Memory
   （[arXiv:2409.07429](https://arxiv.org/html/2409.07429v1)，从成功轨迹归纳出工作流，
   在 web-agent 基准上相对 +24.6–51.1% 且跨域稳健）收敛到同一个形状：
   **小的知识单元，各自携带自己的召回条件，只在被触发时注入**。
   我们的 skill store 已经是这个形状 —— v2 为它加上逐仓库命名空间，
   以及从成功 RunTrace 中归纳。
4. **逐仓库的表现方差是常态，不是例外。** SWE-bench 家族的分析显示，同一个模型在不同
   仓库上的解决率从 <10% 摆到 >50%，存在系统性的语言效应，且在私有/未见代码库上有
   显著下滑（例如 Opus 4.1 在 SWE-bench Pro 私有集上 22.7%→17.8%）。
   仓库属性 —— 架构复杂度、adapter/hook 体系、API 面清晰度 —— 可以预测难度。
   → **v2 后果**：不变性必须**逐仓库测量**（§V2.2.5）；一个只在 vllm-omni 上被评测过的
   agent，**在别处的表现是未知的**，而 profile 质量是那道差距上的一阶杠杆。
5. **"精选顶层架在证据之上"是正在收敛的记忆架构。** 2026 年的 agent 记忆文献与已上线
   系统（Zep/Graphiti、Mem0、Letta 的 sleep-time agent；**连续的 LLM 重写会腐蚀记忆**
   —— arXiv:2605.12978）收敛到：一个**不可变的证据库**之上架着一层小的、精选的、
   人类可读的 profile；**类型化 patch 操作是唯一写入面**；巩固是**有节奏的**
   （而不是每次交互都做）；溯源与稳定性分数**门控重写**。我们自己的个人 agent 正是这么
   实现的，且已在生产中运行（§V2.3.2 借用了它的骨架）。

来源：[ETH AGENTS.md 研究](https://arxiv.org/html/2602.11988v1) ·
[Aider repo map](https://aider.chat/docs/repomap.html) ·
[RepoGraph](https://arxiv.org/html/2410.14684v1) ·
[CodexGraph](https://arxiv.org/abs/2408.03910) ·
[OpenHands repo skills](https://docs.openhands.dev/overview/skills/repo) ·
[Devin Knowledge/DeepWiki](https://docs.devin.ai/work-with-devin/deepwiki) ·
[Agent Workflow Memory](https://arxiv.org/html/2409.07429v1) ·
[SWE-bench Pro](https://scale.com/blog/swe-bench-pro) ·
[Cline memory bank](https://docs.cline.bot/best-practices/memory-bank) ·
[Copilot custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)

## V2.1 既有问题与修复

### (a) 正确性缺陷（P0 —— 先于一切修掉）

| # | 问题 | 证据 | 修复 |
|---|---|---|---|
| 1 | **resume 丢失内存态。** step 之间通过直接写 `ctx.state` 交接结果（`pr.fetch_diff` → `diff_text`、`issue.fetch` → `issue_text`、`pr.gate_check` → `gate_report`、`pr.checkout_branch` → `push_policy`/分支引用、`agent.review_diff` → `review_text`），但 executor 的 resume 路径**只恢复 `outputs.state_updates`**。越过一个已完成 fetch 的 `--resume` 会在没有 `diff_text` 的情况下重入 `agent.review_diff` → 假 BLOCKED；在 push step 处 resume pr-rebase 会看到默认（拒绝一切）的 `PushPolicy` → 假 FORBIDDEN。 | `executor.py` 的 resume 分支 vs. `steps/pr/`/`steps/review/` 的 state 写入 | 契约：**任何被后续 step 消费的 state 键都必须经 `outputs.state_updates` 发布**（JSON-simple；`PushPolicy` 序列化）。由逐 playbook 的 resume 完整性测试强制：跑到第 N 步、杀掉进程、resume，断言在任何 N 上都不会出现"因缺 state 而 BLOCKED"。 |
| 2 | **`foreach` 扇出丢掉 `state_updates`。** `_merge` 按下标重新给条目输出打键，于是扇出条目发布的 `state_updates` 永远到不了 `state.update(...)`。 | `executor.py::_merge` | 显式跨条目合并 `state_updates`（同键最后写者胜是可接受的；冲突记 trace）。由同一个 resume 完整性测试覆盖。 |
| 3 | **`when:` 静默地只对 TaskSpec 求值。** 一个基于计算出的 state 键（例如 `has_conflicts`）的条件会**无错地判为 false**。 | `executor.py::_eval_when` | 对 `state` 求值并回退到 TaskSpec；未知键 → **规划期错误**，而不是静默跳过。 |
| 4 | **逐仓库知识被设计了但没接线。** `RepoAdapter.skills_dir` 和 `RepoAdapter.debug_memory_db` 存在，但 `agent_runtime` 读的是**全局**的 `settings.skills_dir` / `settings.memory_db` —— 每个仓库共用一个 skill store 和一个 debug memory。 | `adapters/base.py` vs `engine/agent_runtime/knowledge.py::_retrieve_skills/_retrieve_memories` | 知识库先经当前 adapter/profile 解析，全局共享池其次（§V2.2.6）。 |
| 5 | **高风险模块清单是硬编码在核心 settings 里的 vLLM-Omni 名字**，因此 patch-review 的 `high_risk_modules` 触发器在**任何其他仓库上都静默地永不触发**。 | `config.py::high_risk_modules` | 搬进 profile（`modules.yaml` 的风险分层，§V2.3）；该 setting 只作兜底。 |

### (b) 核心里的仓库知识泄漏（违反"知识在边缘"；阻碍不变性）

这些在 vllm-omni 上不是缺陷，但每一处都是**第二个仓库会被静默降级**的地方。
它们全部由**profile 注入**（§V2.3）解决 —— 核心只保留仓库中立的脚手架：

- `_REVIEW_SYSTEM` 和 `_REVIEW_LENSES` 在 `engine/steps/review/` 里硬编码了
  "vLLM-Omni" 和一份 Python/ML 仓库的评审 checklist（模块拆成包之后，
  prompt/checklist 数据现在住在 `engine/steps/review/prompts.py`）。
  → 拆成仓库中立的核心 prompt + 由 profile 提供的领域段落
  （`review.md`：领域 checklist、lens 扩展、严重度规范）。
- `_sweep_targets` 假定了 Python 的表层语法（`xs[0]`、`elif`、`tests/` 布局）。
  → 由 `profile.language` 选定的按语言抽取器，外加一个通用的 diff 启发式兜底。
- `TaskSpec.repo` / `Settings.default_repo` 默认是 `"vllm-omni"`；意图解析器**根本
  无法抽取仓库**（"review pr 12 in repo-b" 解析不了）。→ intent 获得仓库抽取能力；
  只配置了一个 profile 时，默认值来自它。
- playbook 声明 `repos: [vllm-omni]`，于是第二个仓库需要复制粘贴的 playbook，
  而它们**必然漂移**。→ 仓库中立的 playbook（§V2.2.3）。
- 默认 `gh` 是唯一 forge，Buildkite 处理零散且是桩。→ 由 profile 声明的 forge/CI
  adapter（§V2.2.4）。

### (c) v1 待收口的边界

- **Buildkite 日志下载**（是桩；PR-debug 只读 `gh pr checks`）→ 一个 `CIProvider`
  adapter 接口（拉取失败 job、下载日志、轮询构建），为 GitHub Actions 和 Buildkite
  各出一个实现，由 `profile.ci.provider` 选定。父 rebase-agent 已知的基线签名弱点
  （精确字符串比较把 flaky/已知失败误分类）**不得被继承**：adapter 里的签名匹配在比较前
  先做归一化（抹去时间戳/哈希/路径）。
- **指标反馈收集器**（按 METRICS_RESEARCH 路线图）：在线填充 useful/accepted/conflict
  的 gh 收集器、推送后的 CI 快照。
- **原生 rebase 的 prelude 环境导出**会修改 copilot 自己的进程环境 → 在子进程里用显式
  环境跑 prelude/各阶段，并保留被记 trace 的 `env_exported` 增量。
- **ensemble 覆盖面**：`run_agent_step_ensemble` 目前只接了评审。分流和 debug 假设类
  step 要等**它们自己的跨 run 方差被测量之后**才采用 lens ensemble
  （与评审战役同样的 replicate 均值纪律；**不要发布未经测量的"改进"**）。

## V2.2 仓库不变性

**定义。** 对 copilot 支持的每一种任务 kind，在一个**已建立 profile** 的新仓库上的
质量，都要落在参考仓库（vllm-omni）的**声明区间**内，且接入一个仓库需要
**零核心代码改动**。不变性是**契约加测量**，不是愿景 —— 基准文献（§V2.0.4）显示同一个
模型的解决率在不同仓库间从 <10% 摆到 >50%，所以**未经测量的跨仓库主张一文不值**。

1. **仓库中立的核心，且被强制。** `src/infermatrix_copilot/` 里**任何地方**都不得出现
   仓库专属字面量（仓库名、模块名、领域 prompt、绝对路径）—— 那类知识只住在
   `adapters/<repo>/`。由 `test_repo_neutral_core` 钉住：它扫描源码里已知的泄漏模式，
   遇到新的就失败。核心里的 prompt 可以陈述*怎么审查/调试/分流*；
   **只有 profile 才陈述*这个仓库是什么*。**
2. **单一注入路径。** 一切随仓库变化的东西，都经 DispatchContext 的 `profile` 段
   到达 step（§V2.3.4）：领域 prompt 段落、模块映射、风险分层、test/format 命令、
   CI/forge adapter、约定。**需要仓库知识却在 profile 里找不到的 step，必须显式降级
   （见第 4 条），绝不猜测。**
3. **仓库中立的 playbook。** playbook 声明 `repos: ["*"]` 加上一份 `requires:`
   的 profile 能力清单（例如 repo-rebase 需要 `ci.provider`、`upstream.fork_tracking`）。
   `PlaybookStore.find()` 匹配的是 **任务 kind + 能力满足**，而不是仓库名；
   存在仓库专属覆盖（精确 repo 匹配）时仍由它获胜。locked 的 `repo-rebase` playbook
   **按声明**仍然是 vllm-omni 专属的 —— 它 `requires` 那个只有 vllm-omni profile 提供的
   外部编排器能力；**零回归不受影响**。
4. **优雅的能力降级。** 能力缺失 → 一次**被声明**的降级，记为 `capability_gap`
   RunTrace 事件并在 run 报告里呈现：没有 CI provider → pr-debug 跑只读分诊；
   没有声明 upstream → repo_rebase 在**规划期**带理由拒绝；语言未知 → 通用 sweep 抽取器，
   并在评审输出里标注。**降级 ≠ 静默变差：每一个缺口都是可见的。**
5. **被测量的不变性。** 把评测 harness 扩展成跨仓库基准：逐仓库跑同样的 arm 和
   RQS3/RQS3e/CATQ 指标，**按 replicate 均值**计分（战役的惨痛教训：单次投掷是 ±0.1 的
   噪声）。逐任务 kind 报告一个**不变性指数** = min(仓库分) / mean(仓库分)；目标 ≥ 0.8。
   一个新仓库的 profile **只有在它的评测 run 落进区间之后**才被晋升（draft → active）
   —— **profile 的晋升门就是不变性门**。
6. **知识命名空间。** skill 与 debug memory **先按仓库解析**
   （`adapters/<repo>/skills/`、`adapters/<repo>/store/debug_memory.db` ——
   即 §(a)4 里那些已设计好的字段），再回落到共享的 general 池。
   写入**始终**落在当前仓库的命名空间；把一条仓库 skill 晋升到共享池是**策展决定**
   （它必须真的与仓库无关，比如"怎么二分一个 flaky 测试" vs. "HunyuanImage 的 SSIM 阈值"）。

## V2.3 仓库 profile

profile 把 adapter zero + Phase-0 引导，推广成 copilot 对一个仓库的**完整认识**。
下面的一切都受两条**由证据驱动**的设计规则统辖（§V2.0.1–2）：

- **规则 1 —— profile 不是 prompt。** profile 的大部分内容由**代码**消费（step 逻辑、
  adapter、触发器）或**按需检索**；always-on 的 prompt 切片是一份**精选的最小集**，
  只放非显然、非冗余的指令。**自动生成的概览被整体注入，实测比什么都不放更糟。**
- **规则 2 —— 没有溯源就没有 fact，没有稳定性就不许重写。** 每条 fact 都要写明它是
  怎么得出的、上次何时被确认；精选摘要**只由一个有节奏的巩固层**重写，
  **绝不连续重写**。这就是那套个人 agent 的 profile 架构 —— 它已在生产中运行，
  且它的失败模式（碎片化、证据倾倒、连续重写腐蚀）都已被摸清。

### V2.3.0 仓库知识的两个信任层

仓库知识按**谁可以写它、它承载多少信任**分成两层 —— 这是对**安全**要紧的那条轴，
与 §V2.3.4 的 机器 / briefing / 检索 这条**消费**轴正交：

- **Tier 1 —— manifest**（`manifest.yaml`）：*人工撰写、人工门禁*的配置，
  是那些**agent 去猜就不安全**的东西 —— 仓库/上游路径、推送策略（保护分支、`allowed`）、
  CI provider、能力。朴素声明式 YAML；高风险段（`repo`/`upstream`/`push`）**只能人工改**
  （`HIGH_RISK_SECTIONS`，在 `update_manifest` 里强制）。
  **必需**（没有它就无法安全地操作一个仓库），低频变动 —— 这是**安全门**（**D2**）。
- **Tier 2 —— profile**（`profile/`，外加 `skills/`、`store/`、`repo_map/`）：
  *agent 建立、证据门禁*的知识，是 agent **挣来**的 —— 逐 fact 溯源、
  类型化 patch op 作为唯一写入面、稳定性 + 陈旧度门（§V2.3.2）。
  **可选**的增强（缺失时检索回落到共享池），高频变动、自我纠正、可审计 ——
  这是**质量杠杆**（**D1**）。

manifest 是这个仓库的*宪法*；profile 是在它之下累积起来的知识。
两者是**刻意不合并**的：把 Tier 1 折进证据门禁的 Tier-2 写入路径，会让推送策略变成
**agent 可写**（一次安全回归）；而另一个选项 —— 在 profile 内部划一块"仅人类"区域 ——
不过是把同一条边界重画进一个文件里。两者的数据模型也不兼容
（`repo.path` 这样的 manifest fact 没有"证据"或"陈旧度"；而**没有证据的 profile fact
会被拒绝**）。容器 `adapters/<repo>/` 已经在磁盘上把它们统一了 ——
**一个仓库边缘，两个信任层**。agent *可以起草* Tier-1 的结构
（`profile.structure_scan` 为模块清单播种），但 Tier 1 的高风险段**永远需要人工激活**，
因此任何承载安全的东西都是 *agent 提议 / 人类确认*。

### V2.3.1 布局

```
adapters/<repo>/
  manifest.yaml            身份、仓库/上游路径、推送策略            （人工门禁）
  profile/
    profile.yaml         精选核心（小、人类可读）：逐 fact 的溯源字段 —— 见 §V2.3.2
    briefing.md          渲染出来的 always-on prompt 切片：10-30 条简短祈使指令
                         （工具命令、硬约束、已知陷阱）。有预算（<400 词），
                         与仓库文档非冗余 —— 需经验证，见 §V2.3.5
    format.yaml          formatter/linter + 确切命令，命名与注释约定（机器：验证命令）
    constraints.md       保护分支、评审/合并规范、必需检查、许可/DCO、
                         永不触碰路径（机器：推送守卫 + PathScope；另供 briefing 行）
    modules.yaml         模块映射（路径 -> 模块）、import 图 wave、
                         模块 -> 测试命令、归属、风险分层
                         （机器：扇出、触发器、调度；**绝不作为散文注入**）
    review.md            领域评审 checklist + lens 扩展 + 严重度规范（由 pr_review 检索）
    ci.yaml              provider、pipeline、日志访问、必需检查、
                         归一化后的 flaky 签名基线（机器）
    PROFILE_REPORT.md    渲染出来的溯源视图：每条 fact 是怎么得出的
                         （deterministic | agent | human）、证据、置信度
  skills/                逐仓库 skill，各带一段 TRIGGER 描述
                         （Devin 式：内容 + 什么时候召回它）
  store/debug_memory.db  逐仓库 debug memory
  repo_map/              供按需 repo_map 工具使用的缓存符号图
                         （Aider/RepoGraph 式，按查询排序、有 token 预算；漂移时重建）
```

`manifest.yaml` 保持它的 v1 角色和仅限人工的高风险段（`repo`/`upstream`/`push`）；
`profile/` 装那些**可被建立**的知识。

> **命名（2026-07-11 更名，原为 "plugin"）。** 旧名 "plugin" 是个误称 ——
> 这个包是**声明式的仓库知识**，不是可执行的扩展代码，而后者才是 "plugin" 在软件里
> 到处所暗示的东西。这份设计的头号性质是*仓库不变性*：一个通用引擎按仓库特化 ——
> 也就是 **adapter 模式** —— 所以这些概念现在是自解释的：
> - 容器 `adapters/<repo>/`（原 `plugins/<repo>/`）——
>   `RepoAdapter`/`AdapterRegistry`（原 `RepoPlugin`/`PluginRegistry`）
> - Tier-1 文件 `manifest.yaml`（原 `plugin.yaml`）—— 它在内部本来就是 `.manifest`
>   属性，而 "manifest" 诚实地命名了这个配置层
>
> 读作：**adapter**（容器）装着一份 **manifest**（Tier-1 配置）和一份 **profile**
> （Tier-2 知识）。`ADAPTERS_DIR` 环境变量（原 `PLUGINS_DIR`）指向 adapter 根目录。
> 这次更名是机械的（git-mv + 符号扫描，全程测试绿）；磁盘上的
> `adapters/<repo>/manifest.yaml` 取代了旧的 `plugins/<repo>/plugin.yaml`。

### V2.3.2 profile 记忆架构（借自个人 agent）

个人 agent（一个兄弟项目 —— `profile_store.py` + `RESEARCH_AGENT_MEMORY_2026.md`）
维护着一份人物 profile，其生命周期**恰好**就是仓库 profile 所需要的。
我们**整套采纳**它的骨架，翻译成仓库术语：

| 个人 agent 的机制 | 仓库 profile 的对应 |
|---|---|
| 一个小而精选的 `profile.yaml` 之下的不可变证据库（`events.db`） | RunTrace + Stage-1 证据归档是不可变层；`profile.yaml` 是精选层。**fact 概括证据，绝不取代证据** |
| **类型化 patch op 是唯一写入面**（`add_evidence`、`bump_last_seen`、`merge_*`、`mark_dormant`；畸形 op 被拒） | profile 变更是由 store 校验的类型化 op（`add_fact`、`add_evidence`、`bump_confirmed`、`merge_facts`、`mark_stale`、`update_command`）；**agent 绝不自由编辑 profile 文件** |
| **两个写入层**：每日追加式（不重写）vs. 每周巩固（**唯一**允许 `rewrite_entry` 的层）—— 连续的 LLM 重写**实测**会腐蚀记忆 | 逐 run 层：run 只能**追加**证据/candidate。巩固层（有节奏或评测后）：去重、合并、重写 `briefing.md` —— **散文只在这里被重新生成** |
| **对抗碎片化的 join key**：owner 可编辑的 `aliases.yaml`；每个 op 必须点名它的 initiative | **模块映射就是 join key**：每个 profile op 都要点名它所涉及的模块（或 `repo-wide`），于是知识**按模块收敛**而不是碎片化 |
| 逐条溯源：`evidence[]`、`first_seen`、`last_seen`、`confirmations: n` | 逐 fact 相同的字段，外加 `source: deterministic\|agent\|human` 和来源 commit |
| **稳定性门**：≥3 次确认的条目不得被重写成引用更少的证据 | 同一条规则：巩固重写**不得**从一条稳定 fact 上丢掉已引用的证据；被取代的正文进 `history[]`，**绝不删除** |
| **休眠衰减，绝不删除**（30/60 天窗口） | 超窗口未确认的 fact 翻成 `stale`（排除出注入/消费，**保留以备审计**）；刷新会重新确认或让它退役 |
| LLM 不能触碰的受保护段（`identity`、`preferences`） | `manifest.yaml` 的高风险段（已在 `update_manifest` 里强制）+ 标了 `source: human` 的人工撰写约束行 |
| **只读的 LLM judge**（每周）：报告矛盾/陈旧主张，**绝不自动修** | profile judge 拿 profile 对照最近 N 次 RunTrace 做审计（失败过的命令、搬走了的模块、从不触发的 checklist 项）—— findings 变成刷新提案 |
| 每份 profile 一个 git 仓库：每次保存一个提交，每周把 diff 发邮件，`git revert` 回滚 | `adapters/<repo>/` 是入库的；每次巩固是**一个被评审的提交**，diff 出现在 run 报告里 —— 回滚就是 `git revert` |

### V2.3.3 建立流水线（扩展 Phase-0 引导）

- **Stage 0 —— 确定性指纹**（已存在：`fingerprint_repo`）：语言构成、布局、CI 系统、
  remote、默认分支。扩展出 `modules.yaml` 的确定性部分（目录聚类、经静态分析得到的
  import 图 wave）以及 `repo_map/` 的构建。**无 LLM，不对目标仓库写入。**
- **Stage 1 —— profiling agent**（新）：只读的受治理 agent step，一个 profile 产物一个，
  全部经统一 agent 运行时：*structure*（在 Stage-0 图之上做模块语义 + 测试映射）、
  *format*（检测配置文件、推断未成文约定、产出确切的检查命令）、
  *constraints*（经 forge API 读 CONTRIBUTING/CODEOWNERS/PR 模板/分支保护）、
  *ci*（pipeline、日志访问）、*review*（从文档 + 近期人工评审 thread 提炼领域 checklist）。
  **每条产出的 fact 都必须引用它的证据 —— 未引用的 fact 在契约层被拒。**
- **Stage 1.5 —— 冗余过滤**（新，ETH 研究的教训）：一趟确定性处理，丢弃任何
  内容已在仓库自己的 README/docs/AGENTS.md 里写过的候选 briefing/checklist 行
  （agent 本来就会读那些），以及任何代码库概览式散文。**剩下的才是非显然的残余** ——
  工具命令、陷阱、不变量。如果存在 `AGENTS.md`/`CLAUDE.md`/
  `.github/copilot-instructions.md`，它会作为**人工撰写**的 briefing 输入被摄入
  （最高信任来源），而不是被重新推导。
- **Stage 2 —— 人工评审门**（已存在，已扩展）：profile 以 `status: draft` +
  `PROFILE_REPORT.md` 落盘；高风险段仅限人工。人工评审把 draft 翻成 candidate。
- **Stage 3 —— 实时校准**：最初 N 次 run 把低置信 fact 当作**假设**；
  修正（模块映射订正、真的能过的命令、flaky 基线条目）经策展门作为 candidate 提出。
  成功 run 的 RunTrace 喂给 **skill 归纳**（AWM 式）：反复出现的解决模式变成
  逐仓库的 skill candidate，带触发描述。通过评测区间（§V2.2.5 + §V2.3.5）即把
  candidate 晋升为 active。
- **Stage 4 —— 巩固与刷新**（个人 agent 的每周一趟）：有节奏的巩固按模块去重/合并 fact、
  在词预算内重新生成 `briefing.md`、施加休眠衰减；漂移检测器（模块路径消失、format
  命令失败、CI pipeline 改名、N 次与 profile 矛盾的 run、judge findings）触发对受影响
  Stage-1 agent 的**定向重跑**。**每个周期一个被评审的提交。**

### V2.3.4 消费：三条通道

ETH 的结论**强制**了这套纪律；每个产物都要声明自己的通道：

1. **机器消费（绝不作为散文注入）**：`modules.yaml` → 扇出、wave 调度、
   patch-review 的 `high_risk_modules`、检索查询；`format.yaml` → 在 patch 门之前
   运行的编辑后验证命令；`ci.yaml` → adapter 选择、必需检查清单、flaky 过滤；
   `constraints.md` 的机器行 → 推送守卫 + PathScope。
2. **always-on prompt 切片**：**只有** `briefing.md`（有词预算、精选、已冗余过滤）
   会进入该仓库的每一个 DispatchContext，外加与该 step 风险级别相关的那几行约束。
3. **触发式/按需**：逐仓库 skill 由触发匹配召回；`review.md` **只**被 pr_review step
   检索；`repo_map` 工具在 token 预算内回答按该 step 目标排序的结构查询 ——
   **agent 在需要时自己拉结构，而不是被灌一份概览。**

### V2.3.5 profile 的效力是被测量的，不是被假定的

同一份研究还显示，**即使是人工撰写**的上下文文件，在某些仓库上也可能是净负面。
所以 **profile 自己就是一条评测臂**：在每个已建立 profile 的仓库上，任务 kind 的评测
都跑 {无 profile} vs {有 profile}（一如既往，按 replicate 均值）。
一份 profile（或一次 briefing 修订）**只有在质量上非负、且不撑爆成本预算**时才被晋升
（CATQ 的 C 项已经为上下文文件所诱发的 +2–4 个额外步骤定了价）。
巩固层的 briefing 重写会**重跑这次消融**。
这就闭上了 AGENTS.md 的作者们跳过的那个环：**我们从不假定注入的上下文有帮助。**

### V2.3.6 治理

**没有新机器** —— profile 复用既有的那些门：profile 编辑就是知识编辑（本来就是 patch
review 的一个触发器）；agent **只能**提交类型化 op 的 candidate（`update_manifest`
本来就拒绝 agent 对高风险段的写入）；draft/candidate/active/retired 镜像 playbook 的
生命周期；每条被接受的 fact 都可经 `PROFILE_REPORT.md` 追溯；
**每次巩固都是一个被评审、可回滚的提交**。

## V2.4 里程碑与验收

- **P0 —— 正确性**：§V2.1(a) 的修复 + 逐 playbook 的 resume 完整性测试 +
  `test_repo_neutral_core`（初期以 xfail 列出已知泄漏，使这份清单**只能变短**）。
- **P1 —— profile 底座**：带类型化 patch op + 溯源字段的 profile store（§V2.3.2）、
  `profile/` schema + loader、Stage-0/1 建立 + Stage-1.5 冗余过滤 + PROFILE_REPORT、
  DispatchContext 的 `briefing` 注入、review/sweep/intent 按 profile 参数化
  （去除 §V2.1(b) 的泄漏）。
- **P2 —— 仓库中立的执行**：playbook 的 `requires:` 能力匹配、CI/forge adapter 接口
  （GitHub Actions + Buildkite）、能力缺口的降级路径、逐仓库知识命名空间接线、
  按需 `repo_map` 工具。
- **P3 —— 被测量的不变性**：跨仓库评测 harness（参考仓库 + 至少一个结构上不同的第二
  仓库）、不变性指数报告、**profile 消融臂**（§V2.3.5）、与评测区间绑定的晋升门；
  Stage-3 实时校准 + AWM 式 skill 归纳；有节奏的 Stage-4 巩固/judge/刷新循环。

**验收判据**

1. 第二个仓库被端到端接入（指纹 → profile → active），
   且**对 `src/infermatrix_copilot/` 零提交**。
2. 六种任务 kind 全部能在第二个仓库上执行 —— profile 提供了能力的地方就满能力运行，
   没提供的地方带**被记录的** `capability_gap` 降级；**没有静默的质量损失**。
3. 第二个仓库上的 pr-review RQS3（replicate 均值）落在 vllm-omni 参考的声明区间内；
   不变性指数 ≥ 0.8。
4. 每个 playbook 的 resume 完整性测试都绿（**没有由 resume 本身造成的 BLOCKED/FORBIDDEN**）。
5. locked 的 `repo-rebase` 夜跑行为保持**逐字节一致**（零回归约束原样贯穿 v2）。
6. profile 挣得它的位置：在每个已建立 profile 的仓库上，{有 profile} 臂在质量上
   相对 {无 profile} 非负且成本可接受（§V2.3.5），且每份 `briefing.md` 都在预算内、
   **零条与文档冗余的行**。

---

# Part III —— Design v3：两个前门与五个后端（2026-08）

v1 建成了执行主脊；v2 让它仓库不变。v3 回答的是**另一个问题** ——
**谁来跑模型，以及 copilot 是给谁用的** —— 它产出了当前代码库里占主导地位的两个结构：
第二种**入口**形状（Direct），和第二种**执行**形状（harness 后端）。

**两者都不是为重构而重构。** 每一个都补上了一个让产品对某一类真实用户不可用的缺口。

## V3.1 Direct 模式 —— 把 copilot 当作知识提供方

**缺口。** Strict 跑完整主脊：5–12 分钟、一个 API key、一份本地 checkout、
一个后台进程。而已经坐在 Claude Code、Codex 或 Cursor 里的用户，
**既有一个有能力的模型，又已经打开了仓库**。让他们再配置第二个模型来审查眼前的代码，
是一笔**没有回报的税**。

**决策。** 发布一种模式，让 MCP 服务端**完全不跑模型**。
`review(mode="direct")` **同步**返回知识路由和治理契约；阅读与判断由**宿主自己的模型**
完成。执行主脊（Part I §3.X）**完全不参与**。

**难的是治理，不是路由。** 服务端**约束不了**宿主的模型 —— 它根本不在那个环里。
所以"该怎么审"被编码成随返回值一起旅行的**结构化数据**（≤3 条带内嵌 `quick_map` 的
路由、一个硬性的 `execution_budget`、一份 checklist），而验收是一道**机械的完成门**
（`validate_direct_review`）。那道门**刻意只检查形状，不检查真伪**：恰好一条最终评论、
`subtraction_signal` 的自洽性、以及证明本次评审读的是固定提交的 `evidence_head_sha`。
**验证被引用的证据是否真实，超出了一个无状态服务端能做到的范围；
声称能做到，比不声称更糟。**

**对其余一切的后果。** 现在**一个仓库里住着两个产品**。playbook 和 step **只属于
Strict**；Direct 从不碰它们。这条区分一旦模糊，读者就会迷路 ——
这正是 [`../GUIDE.md`](../GUIDE.md) §1.1 要以它开篇的原因。

## V3.2 Provider 注册表 —— 接入点不可能是 `LLM.create()`

**缺口。** 每一次模型调用都要经过一个需要 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`
的原始 completions 客户端。**只有编码 agent 订阅**、没有裸 API key 的用户，
**根本跑不了 Strict**。

**塑造了整个设计的那条约束。** Claude Code、Codex CLI 和 cursor-agent 在订阅认证下
**不暴露 completions API**。它们是**自带工具循环的 agent harness**。
所以接缝不可能是 `LLM.create()`（无状态的 `system+messages+tools → tool_use` 往返）
—— 它必须上移一层，落在 **`run_session()`：委托一整个 agent step**。
**整个 `providers/` 包都是从这一个决策推出来的。**

**与维护者锁定的决策（2026-08-14）：**

1. **产品覆盖面，不是质量。** 保真度按 harness 尽力而为，并**逐 run 标注**。
   一个 harness 后端测量的是**循环 + 模型的组合**，因此**绝不**被并入生成器消融表 ——
   长期规则是：生成器臂骑我们自己的流水线，**只换模型**。
2. **显式选择，硬报错。** 由 `STRICT_BACKEND` 选定；未设置或未知的后端会**在前面**
   带着确切缺失项失败。**没有自动探测，没有静默回退** —— 与 `TierNotConfiguredError`
   同一套哲学。
3. **工具经桥回流，预防优先。** harness 会话经 MCP 收到 copilot 自己的 scoped 工具，
   每次调用仍然过 `tools.dispatch`。厂商内置工具在 harness 支持时被**关闭**
   （`builtin_tools_off`）；不支持时改用 OS 级只读沙箱（`codex`、`deepseek`）；
   **两者都做不到时**（`cursor-agent`），运行后审计作为**公开声明的侦测型**控制运行。
   纵深防御，且**控制类别写在 RUN_REPORT 里 —— 绝不留静默缺口**。
4. **统一注册表。** 既有的 API 路径被收编成同一张表里的 provider `api`：
   一条解析路径、一套 trace 词汇，外加一道**平价棘轮** —— 用 `api` 时行为**逐字节一致**。

**值得记住的那处不对称。** 凭据模型是**刻意不均匀**的：`api` 经 Settings 解析
key + 端点；harness provider 把订阅认证放在厂商 CLI 自己的 HOME 状态里，
**本代码库从不接触**。`deepseek` 打破了这个模式 —— 它是 harness 却**需要 API key**
—— 所以注册表用 `api_keyed` 标出它，而不是让调用方去假定"harness ⇒ 凭据在厂商那边"。

**为什么子进程环境是白名单。** 厂商 CLI 必须保住自己的认证，但**绝不能继承我们的**。
在这类机器上 `ANTHROPIC_BASE_URL` 指向一个网关；一旦被继承，
它会**悄悄把厂商 CLI 的流量改道到用户并未选择的地方**。
`sanitized_env()` 只保留 `PATH`/`HOME`/locale，其余全部丢弃。

## V3.3 双路径 `mode` —— 把成本作为一等的轴，且与权限正交

评审质量随模型强度上升，而 4-lens ensemble 要花约 4 倍。但**成本**和**爆炸半径**
绝不能混为一谈：v3 引入 `mode`（默认 `eco` / 仅在用户显式要求时 `performance`），
它选择 agent 的推理模型，并与 `tier` **保持正交**。

那条不变量值得直白写下来：**便宜的模型永远不会扩大一个任务被允许做的事。**
`tier` 仍然由 `kind` 推导（Part I 决策 3）；`mode` **碰不到它**。

## V3.4 v3 **没有**解决的问题

记录在此，好让后来者既不重新争论已经定论的东西，也不继承没有支撑的主张：

- **相对 agentic 基线的评审质量，并没有赢。** 已测量的状态是：precision 打平、
  recall 比 CC + Opus 5 低约 .05，成本约为其三分之一。
  见 [`../evaluation/README.md`](../evaluation/README.md)；
  "两项均值都严格超过基线"这个目标**没有达成**，
  而且用修正后的统计看，**它在战役的任何时点都从未达成过**。
- **harness 的成本优势是假定的，不是测量的。** harness 会话不向 span 记账暴露 token
  （每项都是 `tok_out=0`），所以 metrics 记来源为 `subscription`，**拒绝编造 USD**。
- **跨仓库不变性（§V2.2.5）仍未被测量。** v3 把测量预算花在了参考仓库的评审质量上。
  **不变性指数至今从未被计算过**，所以 Part II 里每一条跨仓库主张都是
  **设计意图，不是结果**。
