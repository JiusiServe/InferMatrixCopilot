# 代码导览 —— vllm-omni-copilot 阅读指南

一条贯穿代码库的导览路径(v1 引擎 + Design-v2 工作:仓库不变性与仓库
profile)。本文面向代码评审,因此按**执行顺序**展开、点明每个文件所强制的
不变量、并指向验证该行为的测试。配套文档:`DESIGN.md`(为什么这么做)、
`IMPLEMENTATION_STATUS.md`(做了什么)、`SPEC/`(规范契约:每层每个模块
必须/不得做什么,以及不可破坏的不变量)。

## 0. 全景:一个任务的端到端流程

以 `omni-copilot -p "review pr 4830"` 为例,跟着走一遍:

```
cli/entry.py:main      解析参数;单次 -p / chat / REPL
  intent.py            自然语言 -> TaskSpec   (先确定性解析,LLM 兜底)
  task_spec.py         TaskSpec: kind/pr/flags; TIER 由 KIND 推导
  cli/copilot.py:Copilot.resolve
    plugins/base.py    RepoPlugin.capabilities (repo.path, ci.provider, ...)
    engine/planner.py  reuse > adapt > generate  (+ 能力匹配)
      playbooks/store.py  注册表: candidate/active/locked; find()
  cli/copilot.py:run_task 回显计划; plan-review 门禁; [y/N] 确认
  engine/executor.py   执行 step: checkpoint/resume, foreach, when:, 重试
    engine/steps/*.py         step handler (经 @step 自注册)
      engine/agent_runtime/ 受治理的 agent 执行(核心,包)
        agent_loop.py        原始工具循环
        tools.py + scopes.py  唯一的、强制 scope 的分发器
  notify.py            被阻塞时: ESCALATION.md + 邮件 + exit 3
  metrics.py           每次运行的 CATQ metrics.json
```

建议的阅读顺序 = 下面各节,自上而下。

## 1. 任务层 —— 文字如何变成受治理的任务

- **`task_spec.py`**(约 70 行,建议通读)。最关键的一条不变量:`tier` 是
  **kind 的属性**——不存在任何 LLM 或用户可设置来扩大权限的字段。
  `read_only`/`confirm_required` 由 kind + flag 推导。v2 新增 `repo_profile`
  kind(L2,因写入知识而需确认门禁)。
- **`intent.py`**(**LLM-only**)。分类完全交给 LLM:把一条终端命令转成
  `TaskSpec`,**歧义/离题/注入 → 澄清提问**,绝不猜测执行(LLM 置信度
  <0.7 或返回 clarify 即澄清;无 LLM 或空命令也澄清)。已去掉确定性关键词
  解析器(`_KIND_HINTS`/`_parse_deterministic`)。仅保留 `parse_intents` 的
  **复合命令切分**与 PR/issue **引用接续**("… then review it")——那是分句,
  不是分类。只有终端输入进入此函数——拉取的 GitHub 文本永不进入(指令通道与
  数据通道分离,防 prompt 注入)。
  由 `test/test_intent_taskspec.py`(LLM 路径契约)、`test_phase_b.py`
  (切分+接续,用 fake 分类器)固定。

## 2. 规划 —— reuse > adapt > generate,现已加入能力匹配

- **`playbooks/store.py`**。`Playbook` 是数据(`playbooks/` 下的 yaml),
  `status` ∈ candidate/active/locked/retired。关键方法:
  - `find(kind, repo, capabilities)` —— 精确 repo 匹配的 playbook 优先;
    仓库无关的(`repos: []`)仅当 `requires ⊆ capabilities` 时匹配
    (v2 P2.1;`capabilities=None` = v1 行为)。candidate **永不**被召回——
    只能用 `--playbook <name>` 运行。
  - `missing_capabilities()` —— 能力缺口的升级材料。
- **`engine/planner.py`**(约 120 行,建议通读)。三档解析及其两条硬规则:
  locked playbook 拒绝改编;generate 路径**结构性**禁止 write/push step,
  只对只读 kind 存在。v2 新增能力缺口分支:改代码类 kind 若其仓库 profile
  无法满足某个已验证 playbook,抛出 "capability gap … run repo_profile",
  而非静默失败。
  由 `test_planner_playbooks.py`、`test_capabilities.py` 固定。
- **`plugins/base.py`**。`RepoPlugin` = 仓库知识所在的边缘:manifest
  (`plugin.yaml`)、`module_for_path`、`high_risk_modules`(`risk: high`
  标记)、`capabilities`(推导 + 显式)、以及按仓库隔离的
  `skills_dir`/`debug_memory_db`/`profile_dir`/`briefing()`。
  `update_manifest` 拒绝 agent 写入高风险段(`push`/`repo`/`upstream`)——
  这是人工专属的墙。Phase-0 引导:`fingerprint_repo`(确定性,无 LLM)+
  `draft_plugin`(停在 `status: draft`)。

## 3. 执行 —— 引擎底座

引擎按执行顺序分散在 §2–§5 讲(planner 在"规划",runtime 在"核心",
steps 在"库")。先给 `engine/` 目录一个整体清单,再逐个深入:

```
engine/
  step.py          基础词汇: StepSpec / StepResult / StepContext /
                   FailureKind / Kind / Risk(仅类型,无行为)         → §3
  registry.py      StepRegistry: 名字 -> StepSpec 的注册表
                   (名字解析成 handler 的唯一入口)                    → §3
  executor.py      执行底座: checkpoint/resume、foreach、when:、
                   类型化失败路由、state_updates 契约                 → §3
  planner.py       reuse > adapt > generate + 能力匹配                → §2
  agent_runtime/   受治理 agent 运行时 + 评审 ensemble(核心,包:
                   dispatch/knowledge/utils 底座 + runner/ensemble 入口)  → §4
  steps/           vetted step 库,一个领域一个模块,自注册          → §5
```

引擎之下、被它调用的原始能力在 `omni_copilot/` 顶层(不在 `engine/` 内):
`agent_loop.py`(工具循环)、`tools.py`(原子能力 + dispatch choke point)、
`scopes.py`(工具/路径权限)、`push.py`(推送授权)——见 §4。

- **`engine/step.py`**(约 60 行,建议通读)。核心词汇:`StepSpec`
  (name/kind/risk/handler/description——去掉了没人读的 tool_scope/
  patch_review_triggers)、`StepResult`(ok + 带类型的 `FailureKind`)、
  `StepContext`(handler 可触碰的一切)。六种失败类型走不同路由——这正是
  重点。`risk` 会被 planner 强制(C2),`kind` 只是描述(`agent` ⇒ 走受治理
  运行时,是约定)。
- **`engine/registry.py`**(约 30 行)。`StepRegistry` = 一个 `dict[str,
  StepSpec]`:`register` 存、`get` 取(未知名字大声报错)。它是"名字字符串
  → handler"的**唯一**解析点;由 `steps.register_builtin_steps` 填充。
- **`engine/executor.py`**(约 200 行,建议通读)。与任务无关的保证:
  每 step 的 checkpoint(`progress.json`)、`foreach` 扇出
  (asyncio.gather + `_merge`)、`when:` 条件、仅对 RETRYABLE 的有界重试、
  BLOCKED/ESCALATE/FORBIDDEN → notifier + 退出。
  **v2 P0 的状态契约就在这里**:step 通过 `outputs.state_updates` 发布每一个
  被后续 step 消费的状态键;resume 时恢复它们;`_merge` 会把扇出的 updates
  提升上来;`when:` 先读 TaskSpec 再读 state,遇未知键**大声阻塞**。若你只细看
  一处 v2 修复,就看这处——旧行为会静默破坏每一次 resume 运行。
  由 `test_engine.py`、`test_v2_p0.py`(resume 完整性测试)固定。

## 4. 受治理的 agent 运行时 —— 核心

- **`engine/agent_runtime/`**(建议通读;全库信息密度最高的部分,现已拆成
  一个**包**:`dispatch.py`(AgentDispatchContext + 基础 schema)、
  `knowledge.py`(skill/memory/repo_map 检索)、`utils.py`(无状态 helper)
  三者构成底座,`runner.py`(`run_agent_step`)与 `ensemble.py`
  (`run_agent_step_ensemble`)是两个入口;`__init__.py` 原样 re-export,
  公开导入面不变)。`runner.py::run_agent_step` 是每个 `kind == "agent"`
  step 的唯一入口:
  1. `AgentDispatchContext` —— 结构化输入,一次性渲染:task/step/repo/
     briefing/evidence/permissions/skills/memories/输出契约。证据被
     `<untrusted_data>` 围栏包裹并**逐项截断**,全文归档到运行目录
     (`_build_evidence`)。
  2. 知识:`_ScopedKnowledge`(v2 P0)—— 先查该仓库自己的 skills + debug
     memory,再查共享池;agent 的提案落在该仓库命名空间,且仅为 candidate。
  3. `_repo_map_tool`(v2 P2.2)—— 按目标排序的结构查询,按需拉取;绝不作为
     散文注入。
  4. 输出契约(基础 schema + 每 step 扩展)、一轮修复、状态 → FailureKind
     的类型映射;预算耗尽时强制给出最终答案,而非丢弃整个调查。
  其下的 `run_agent_step_ensemble` 是评审质量的机器:视角多样的 lens 扇出、
  精确去重 → 共识、逐编号候选项的 keep/drop/dup 裁决并确定性组装
  (未提及即保留,逐项 fail-open)、共识门控的快速路径。行内注释引用了逼出
  每个选择的 eval 结果——请读它们,那是那场优化战役的制度记忆。
- **`agent_loop.py`** + **`tools.py`** + **`scopes.py`**(都短,三者一起读)。
  一条规则:**每一次**工具调用都经过 `tools.dispatch`,它检查
  `ToolScope`/`PathScope` 并记录 trace。三种结果:允许 / 拒绝 /
  执行但记录(在可写墙内、但超出范围的写入)。agent step 永远看不到其 scope
  不允许的工具。由 `test_scopes_tools.py`、`test_agent_loop.py` 固定。

## 5. Step 库 —— `engine/steps/`(自注册)

Step 位于 `engine/steps/` 包,一个领域一个模块,每个 step 在其定义处
**自注册**——一个 `@step(name, kind, risk, desc)` 装饰器(工厂生成的 handler
则用 `register_step(StepSpec(...))`)把名字、元数据和 handler 绑在一起。
不再有中央的 `add(StepSpec(...))` 块:导入该包即运行装饰器,
`steps/__init__.register_builtin_steps` 再把收集到的 spec 刷进 `StepRegistry`。
要定位一个 step,grep 它的名字字符串:
`grep -rn '"pr.fetch_diff"' src/omni_copilot/engine/steps/`。

- **`steps/_common.py`** —— 共享地基:`@step`/`register_step` 装饰器 + 收集表,
  以及每个 step 文件都用的 helper(`gh`、`repo_path`、`git`、`task_spec`、
  `gh_read_tools`、`post_step`)。一个归宿,取代了旧的 step 文件之间的
  late-import 链。
- **`steps/workspace.py`** —— `workspace.guard_clean`、`analysis.diff_summary`。
- **`steps/rebase_ext.py`** —— `rebase.run_external`:锁定夜跑的受监控子进程
  委托(state.json → 进度事件、陈旧状态守卫、失败分类 → 升级材料)。
- **`steps/review/`**(现为一个**包**:`prompts.py`(评审 prompt/清单数据)、
  `utils.py`(sweep/render helper)、`steps.py`(两个 `@step` handler);
  `__init__.py` re-export 并注册 step)—— `review.patch_gate`(条件式 Patch
  Review:廉价的
  diffsummary 总是跑,仅当 `review/triggers.py` 规则命中才跑 LLM 评审;
  高风险模块来自 *plugin*,settings 只是兜底)与 `agent.review_diff` 及评审
  prompt 系统(`_REVIEW_SYSTEM`、`_REVIEW_LENSES`、`_sweep_targets`)——
  核心仓库无关;领域清单从 profile 的 `review.md` 扩展而来;sweep 提取器以
  `repo.language` 为键,未知语言时诚实降级。
- **`steps/pr/`**(现为一个**包**:`fetch.py`(只读 fetch/gate step)、
  `rebase.py`(PR rebase + module verify)、`debug.py`(PR debug 各 step)、
  `publish.py`(`ci.push` + `pr.post_review`)、`utils.py`(纯 `extract_signature`);
  `__init__.py` re-export 并注册 step)—— `ci.push`(很薄:所有安全都在
  `push.py::guard_push`)、只读的 fetch/gate step、PR rebase
  (fork 感知的 checkout → 推导 PushPolicy → rebase → 冲突 agent 或
  abort+升级)、以及 PR debug(拉取失败 check → **CI 日志富化** →
  归一化签名分组 → 逐组 debug agent → 增量 push)。
- **`steps/issue.py`** —— `issue.fetch`、起草回答与 triage 的 agent step、
  以及带门禁的 `issue.post_answer`。
- **`steps/report.py`** —— `report.final_summary`。
- **`steps/profile.py`** —— profile 建立 + Stage-4 维护 step(见 §6)。
- **`steps/rebase_native.py`** —— 夜跑的原生分解候选版(导入父包自己的 phase
  wrapper;命令式注册)。仅在处理晋升路径时阅读。
- **`push.py`**(约 46 行,建议通读)。`guard_push` 是唯一的推送
  choke point:PushPolicy 且受保护分支双重把关;force 仅 with-lease,且
  **绝不**对受保护分支。它是一个纯安全原语(scopes.py 的姊妹),不属于任何
  "Target 层"——设计里的 Target 职责由 `TaskSpec` + `Playbook` 承担。

## 6. 仓库 profile(v2)—— 知识子系统

按此顺序阅读:

1. **`profiles/store.py`** —— 精选层。带溯源的 fact
   (`source`/`evidence`/`first_seen`/`last_confirmed`/`confirmations`)、
   类型化 patch op 作为**唯一**写入面、两个 tier(`RUN_OPS` 仅追加;
   `CONSOLIDATE_OPS` 可 rewrite/merge/stale)、稳定性门禁(stable fact 永不
   丢失已引用证据;被取代的文本进 `history`)、merge 存根、以及三条消费通道
   —— `render_briefing()` **仅**输出 briefing 通道的 fact 且受硬性词数预算。
   这个文件是 personal-agent 架构的移植;docstring 说明了哪条规则守护哪种
   失效模式。由 `test_profile_store.py` 固定。
2. **`profiles/establish.py`** —— Stage 0–1.5 的 helper:6 词 shingle 的
   **冗余过滤器**(ETH 研究的规则:与文档重复的 briefing 行是纯成本)、从
   AGENTS.md 类文件抽取指令、确定性的模块扫描。
3. **`engine/steps/profile.py`** —— 流水线的各 step:
   `profile.fingerprint` → `profile.structure_scan` → `profile.ingest_docs`
   → `agent.profile_repo`(fact 必须引用证据,否则被 store 拒绝;概览是
   被禁止的输出),外加 Stage-4 一组:`profile.detect_drift` /
   `profile.decay_stale` / `agent.profile_consolidate`(LLM 提出 op,由 store
   的门禁裁决)/ `profile.judge`(只读审计;结构上无法变更)。
   Playbook:`repo-profile`(active,仓库无关)与 `profile-consolidate`
   (candidate = 仅计划/显式运行)。
   由 `test_profile_steps.py`、`test_p3_machinery.py` 固定。
4. **`profiles/repo_map.py`** —— 按语言的正则符号索引,按 HEAD 落盘缓存,
   按查询排序、受字符预算约束地渲染。设计立场:结构由 agent **主动拉取**
   (通道 3),绝不作为概览推送。
5. **`profiles/consolidate.py`** —— 衰减 + 漂移(确定性,仅报告)。

## 7. CI 适配器(v2)—— `ci/`

- **`ci/normalize.py`**(30 行,建议通读):分组前把签名中的时间戳/哈希/
  地址/临时路径/行号/时长抹去;小的字面数字保留。这是对父 monitor
  精确字符串比较缺陷的**刻意不继承**。
- **`ci/providers.py`**:`provider_for(plugin, settings)` 按 profile 的
  `ci.provider` 选择——`BuildkiteLogs`(REST,逐 check 尽力而为)或
  `GithubActionsLogs`(`gh run view --log-failed`,按 run 缓存)。缺 provider
  /token → `(None, reason)` → 该 step 记录 `capability_gap` 事件,pr-debug
  降级为按名字分组。由 `test_ci_and_repo_map.py` 固定。

## 8. 安全、记忆、界面 —— 其余部分

- **`review/`**:`diff_summary.py`(廉价的常开 fact)→ `triggers.py`(7 条
  规则)→ `reviewer.py`(只读裁决;除 `lgtm` 外一律视为不通过——fail-closed)。
- **`run_trace.py`**(40 行):仅追加的 jsonl;本库中每一条治理主张归根结底
  都意味着"有一个 trace 事件为它作证"。值得留意的事件:
  `agent_dispatch`/`agent_output`、`tool_refused`、`out_of_scope_edit`、
  `capability_gap`(v2)、`profile_*`(v2)。
- **`memory/`**:`debug_memory.py`(FTS 写入契约:必须有 root_cause +
  verification)与 `skills.py`(propose → candidate → 人工晋升)。
- **`notify.py`**:ESCALATION.md + 邮件 + `BLOCKED_EXIT=3` —— 把"通知而非
  猜测"写成代码。
- **`metrics.py`**:每次运行 CATQ = Q·S/C;绝不允许它破坏一次运行。
- **`cli/`**(现为一个**包**:`copilot.py` 编排类 + `entry.py` 参数/REPL +
  `utils.py` 纯函数)然后 **`chat.py`**:两者都汇入同一个
  `run_task`/`run_playbook`——chat 只是前端,不是第二条执行路径(它的工具
  无法扩大权限;仓库读取被囚禁,`.env*` 被拒)。`ui.py` 只负责呈现。

## 9. 护栏测试 —— 你不能破坏的行为

| 测试 | 它固定的不变量 |
|---|---|
| `test_v2_p0.py::test_repo_neutral_core` | `src/` 中的仓库字面量被已知泄漏清单封顶(只能减少) |
| `test_v2_p0.py::test_resume_restores_state_handoffs` / `test_push_policy_survives_resume` | state_updates 契约 |
| `test_capabilities.py` | 仓库无关 playbook 按能力匹配;locked rebase 绝不泄漏到其他仓库 |
| `test_profile_store.py::test_stability_gate_and_history` | stable fact 永不丢证据;history 永不删除 |
| `test_profile_steps.py::test_profile_agent_applies_gated_facts` | 无证据 fact 被拒;与文档重复的 briefing 被丢弃 |
| `test_p3_machinery.py::test_judge_reports_but_never_mutates` | judge 是只读的 |
| `test_agent_runtime.py`(参数化 dispatch 测试) | `kind == "agent"` ⇒ 受统一运行时治理,无临时 LLM 调用 |
| `test_push_and_steps.py` | guard_push 语义 |

## 10. 如何运行

```bash
pip install -e . && pytest                      # 211 个离线测试
omni-copilot -p "review pr 4830" --plan-only    # 只看计划不执行
omni-copilot -p "profile the repo" --yes        # 建立 profile(draft)
omni-copilot --playbook profile-consolidate --yes   # Stage-4 维护
PROFILE_BRIEFING_ENABLED=0 ...                  # {无 profile} 的 eval 对照臂
omni-copilot --resume                           # 从上次运行的首个未完成 step 重入
```

每次运行的产物:`~/.omni-copilot/runs/run-<ts>/`(`run_trace.jsonl`、
`progress.json`、`RUN_REPORT.md`、`metrics.json`、被阻塞时的
`ESCALATION.md`)。Profile:`plugins/<repo>/profile/`(`profile.yaml`、
`PROFILE_REPORT.md`、`JUDGE_REPORT.md`、`ops_log.jsonl`)。

## 11. 从哪里开始改

- 新仓库 → `omni-copilot -p "profile the repo"`,审查草稿 plugin +
  PROFILE_REPORT,翻转 `status`,完成——零核心改动是契约。
- 新 step → 在合适的 `engine/steps/*.py` 里加一个 handler,用
  `@step(name, kind, risk, desc)` 装饰(risk 要诚实),通过 `state_updates`
  发布被消费的状态,加一个护栏测试。无需改任何中央注册。
- 新任务 kind → `task_spec.py`(kind + tier)→ playbook yaml → intent
  hint → chat enum。planner 和 executor 无需改动。
- 新仓库知识 → 通过类型化 op 写一条 profile fact(或一个 skill),绝不在
  `src/` 里写字符串——`test_repo_neutral_core` 会抓到你。
