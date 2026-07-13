# 代码导览 —— vllm-omni-copilot 阅读指南

一条贯穿代码库的导览路径。本文面向代码评审,按**执行顺序**展开、点明每个
文件所强制的不变量、并指向验证该行为的测试。三层沉积一体阅读:**v1 引擎**
(任务 → 规划 → 执行 → 受治理 agent)、**v2 profile**(仓库不变性与仓库知识
子系统)、以及 **2026-07 评测战役后**由 trace 取证驱动的一批机制修复(交付层、
裁决校准、PR-time checkout、prompt 缓存、自进化回路闭合)——后者不是独立
分支,而是嵌进了下面各自的执行位。配套文档:`DESIGN.md`(为什么)、
`IMPLEMENTATION_STATUS.md`(做了什么)、`SPEC/`(每层每模块的规范契约与
不可破坏的不变量)、`eval/dataset/judgments/CAMPAIGN_FINAL.md`(战役结论:
冻结测试集上 actionability/correctness/gap_hit 反超 Opus 基线,成本约 1/10)。

## 0. 全景:一个任务的端到端流程

以 `omni-copilot -p "review pr 4830"` 为例,跟着走一遍:

```
cli/entry.py:main      解析参数;单次 -p / chat / REPL
  intent.py            自然语言 -> TaskSpec   (LLM-only 分类)
  task_spec.py         TaskSpec: kind/pr/flags; TIER 由 KIND 推导
  cli/copilot.py:Copilot.resolve
    adapters/base.py    RepoAdapter.capabilities (repo.path, ci.provider, ...)
    engine/planner.py  reuse > adapt > generate  (+ 能力匹配)
      playbooks/store.py  注册表: candidate/active/locked; find()
  cli/copilot.py:run_task 回显计划; plan-review 门禁; [y/N] 确认
                          run 目录 = run-<ts>-<uuid6>(uuid 后缀:同秒并发过
                          去会互相覆写 task.json)
  engine/executor.py   执行 step: checkpoint/resume, foreach, when:, 重试
    engine/steps/*.py         step handler (经 @step 自注册)
      engine/agent_runtime/ 受治理的 agent 执行(核心,包)
        agent_loop.py        原始工具循环
        tools.py + scopes.py  唯一的、强制 scope 的分发器
  steps/report.py      RUN_REPORT.md(只含交付物)+ DIAGNOSTICS.md(诊断)
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
  解析器。仅保留 `parse_intents` 的**复合命令切分**与 PR/issue **引用接续**
  ("… then review it")——那是分句,不是分类。只有终端输入进入此函数——
  拉取的 GitHub 文本永不进入(指令通道与数据通道分离,防 prompt 注入)。
  由 `test_intent_taskspec.py`(LLM 路径契约)、`test_phase_b.py`(切分+接续,
  用 fake 分类器)固定。

## 2. 规划 —— reuse > adapt > generate,加入能力匹配

- **`playbooks/store.py`**。`Playbook` 是数据(`playbooks/` 下的 yaml),
  `status` ∈ candidate/active/locked/retired。关键方法:
  - `find(kind, repo, capabilities)` —— 精确 repo 匹配的 playbook 优先;
    仓库无关的(`repos: []`)仅当 `requires ⊆ capabilities` 时匹配
    (`capabilities=None` = v1 行为)。candidate **永不**被召回——只能用
    `--playbook <name>` 运行。
  - `missing_capabilities()` —— 能力缺口的升级材料。
- **`engine/planner.py`**(约 120 行,建议通读)。三档解析及其两条硬规则:
  locked playbook 拒绝改编;generate 路径**结构性**禁止 write/push step,
  只对只读 kind 存在。能力缺口分支:改代码类 kind 若其仓库 profile 无法满足
  某个已验证 playbook,抛出 "capability gap … run repo_profile",而非静默
  失败。由 `test_planner_playbooks.py`、`test_capabilities.py` 固定。
- **`adapters/base.py`**。`RepoAdapter` = 仓库知识所在的边缘:manifest
  (`manifest.yaml`)、`module_for_path`、`high_risk_modules`(`risk: high`
  标记)、`capabilities`(推导 + 显式)、以及按仓库隔离的
  `skills_dir`/`debug_memory_db`/`profile_dir`/`briefing()`。
  `update_manifest` 拒绝 agent 写入高风险段(`push`/`repo`/`upstream`)——
  这是人工专属的墙。Phase-0 引导:`fingerprint_repo`(确定性,无 LLM)+
  `draft_adapter`(停在 `status: draft`)。

## 3. 执行 —— 引擎底座

引擎按执行顺序分散在 §2–§5 讲(planner 在"规划",runtime 在"核心",
steps 在"库")。先给 `engine/` 目录一个整体清单:

```
engine/
  step.py          基础词汇: StepSpec / StepResult / StepContext /
                   FailureKind / Kind / Risk(仅类型,无行为)         → §3
  registry.py      StepRegistry: 名字 -> StepSpec 的注册表            → §3
  executor.py      执行底座: checkpoint/resume、foreach、when:、
                   类型化失败路由、state_updates 契约                 → §3
  planner.py       reuse > adapt > generate + 能力匹配                → §2
  agent_runtime/   受治理 agent 运行时 + 评审 ensemble(核心,包)      → §4
  steps/           vetted step 库,一个领域一个模块,自注册          → §5
```

引擎之下、被它调用的原始能力在 `omni_copilot/` 顶层(不在 `engine/` 内):
`agent_loop.py`(工具循环)、`tools.py`(原子能力 + dispatch choke point)、
`scopes.py`(工具/路径权限)、`push.py`(推送授权)——见 §4。

- **`engine/step.py`**(约 60 行,建议通读)。核心词汇:`StepSpec`
  (name/kind/risk/handler/description)、`StepResult`(ok + 带类型的
  `FailureKind`)、`StepContext`(handler 可触碰的一切)。六种失败类型走不同
  路由——这正是重点。`risk` 会被 planner 强制(C2),`kind` 只是描述
  (`agent` ⇒ 走受治理运行时,是约定)。
- **`engine/registry.py`**(约 30 行)。`StepRegistry` = 一个 `dict[str,
  StepSpec]`:`register` 存、`get` 取(未知名字大声报错)。它是"名字字符串
  → handler"的**唯一**解析点;由 `steps.register_builtin_steps` 填充。
- **`engine/executor.py`**(约 200 行,建议通读)。与任务无关的保证:
  每 step 的 checkpoint(`progress.json`)、`foreach` 扇出(asyncio.gather +
  `_merge`)、`when:` 条件、仅对 RETRYABLE 的有界重试、
  BLOCKED/ESCALATE/FORBIDDEN → notifier + 退出。**状态契约就在这里**:step
  通过 `outputs.state_updates` 发布每一个被后续 step 消费的状态键;resume
  时恢复它们;`_merge` 会把扇出的 updates 提升上来;`when:` 先读 TaskSpec
  再读 state,遇未知键**大声阻塞**。旧行为会静默破坏每一次 resume 运行。
  由 `test_engine.py`、`test_v2_p0.py`(resume 完整性)固定。

## 4. 受治理的 agent 运行时 —— 核心

`engine/agent_runtime/`(建议通读;全库信息密度最高的部分,是一个**包**:
`dispatch.py`(AgentDispatchContext + 基础 schema)、`knowledge.py`
(skill/memory/repo_map 检索 + `_ScopedKnowledge`)、`utils.py`(无状态 helper)
三者构成底座,`runner.py`(`run_agent_step`)与 `ensemble.py`
(`run_agent_step_ensemble`)是两个入口)。`runner.py::run_agent_step` 是每个
`kind == "agent"` step 的唯一入口:

1. **`AgentDispatchContext`** —— 结构化输入。`render()` 的段序是
   **静态在前、动态在后**,为的是 prompt-cache 前缀复用(供应商按逐字节相同
   前缀缓存):输出契约 / permissions / briefing / 检索到的 skills 领头
   (它们跨同类 step 的 run 重复),per-run 的 REPO/TASK/step/evidence 收尾,
   末尾再补一句静态的契约提醒。证据被 `<untrusted_data>` 围栏包裹并**逐项
   截断**(`evidence_item_chars` 默认 24k;`evidence_caps` 给 `pr_diff` 120k /
   `issue_text` 30k——大而共享的证据进共享前缀一次,而不是每个 lens 各自
   当私有工具结果重读),全文归档到运行目录(`_build_evidence`)。system
   prompt 保持**全静态**;step guidance 与 lens focus 挂到 user prompt 尾部,
   否则同一 ensemble 的四个 lens 无法共享前缀。
2. **知识**:`_ScopedKnowledge` —— 先查该仓库自己的 skills + debug memory,
   再查共享池;agent 的提案落在该仓库命名空间,且仅为 candidate。step 成功后
   `touch()` 命中的 skills,把 `run_count`/`last_used_at` 累计上去——检索
   tie-break 的用量先验。
3. **`_repo_map_tool`** —— 按目标排序的结构查询,按需拉取;绝不作为散文注入。
4. **输出契约**(基础 schema + 每 step 扩展)、一轮修复、状态 → FailureKind
   的类型映射。预算耗尽或合同两次解析失败时**不丢弃调查**:`_coerce_output`
   把非空的最终文本包装成 `needs_review` + `_raw_text`(带 escalate),让有
   文本交付物的 step 能带 caveat 交付而非空手而归。

`run_agent_step_ensemble` 是评审质量的机器:视角多样的 lens 扇出、精确去重
→ 共识、逐编号候选项的 keep/drop/dup 裁决并确定性组装(未提及即保留,逐项
fail-open)。要点:**零产出 lens 单独重问一次**(`ensemble_zero_yield_retry`),
而不是把整个 8-lens 重跑;lens 错峰启动(`ensemble_stagger_seconds`,让首个
lens 先把共享前缀写进缓存);reducer 的 merge guidance 有"自述不确定即降级"
的硬规则,且 `ensemble_merge_evidence_chars`(60k)使 reducer 能看到 diff
(看不到 diff 就无从验证)。行内注释引用了逼出每个选择的 eval 结果——请读它们,
那是那场优化战役的制度记忆。

**`agent_loop.py`** + **`tools.py`** + **`scopes.py`**(都短,三者一起读)。
一条规则:**每一次**工具调用都经过 `tools.dispatch`,它检查 `ToolScope`/
`PathScope` 并记录 trace。三种结果:允许 / 拒绝 / 执行但记录(在可写墙内、但
超出范围的写入)。agent step 永远看不到其 scope 不允许的工具。两处与缓存/
预算相关的细节:预算耗尽的最终调用**保留同一 tools 列表**(tools 序列化在
system 之前,换成 `[]` 会把整个前缀打穿);倒数第二轮注入 "FINAL ROUND"
提示时**必须放在 tool_result 块之后**——放前面违反 tool_use→tool_result
邻接契约,会把整个请求 400 掉。`read_file` 是**窗口化**的(每次 48k 字符 +
`offset` 分页):不设界的整文件读会把会话历史吹爆,既倍增未缓存 token,又把
对话推出供应商可靠缓存的长度范围。由 `test_scopes_tools.py`、
`test_agent_loop.py`(含 `test_final_round_nudge_follows_tool_results` 钉住
消息形状)、`test_agent_runtime.py`(`test_unparseable_after_repair_is_
salvaged_as_escalation` 钉住抢救)固定。

## 5. Step 库 —— `engine/steps/`(自注册)

Step 位于 `engine/steps/` 包,一个领域一个模块,每个 step 在其定义处
**自注册**——`@step(name, kind, risk, desc)` 装饰器(工厂生成的 handler 用
`register_step(StepSpec(...))`)把名字、元数据和 handler 绑在一起。导入该包
即运行装饰器,`steps/__init__.register_builtin_steps` 再把收集到的 spec 刷进
`StepRegistry`。要定位一个 step,grep 它的名字字符串:
`grep -rn '"pr.fetch_diff"' src/omni_copilot/engine/steps/`。

- **`steps/_common.py`** —— 共享地基:`@step`/`register_step` 装饰器 + 收集表,
  以及每个 step 文件都用的 helper(`gh`、`repo_path`、`git`、`task_spec`、
  `gh_read_tools`、`post_step`),外加 `record_debug_memory()`——成功解决的
  失败/修复经 root_cause+verification 契约写进仓库范围的 debug memory,写失败
  被 trace 并吞掉(闭环绝不能反过来搞垮修复本身)。
- **`steps/workspace.py`** —— `workspace.guard_clean`、`analysis.diff_summary`。
- **`steps/rebase_ext.py`** —— `rebase.run_external`:锁定夜跑的受监控子进程
  委托(state.json → 进度事件、陈旧状态守卫、失败分类 → 升级材料)。
- **`steps/review/`**(包:`prompts.py` 评审 prompt/清单数据、`utils.py`
  sweep/render helper、`steps.py` 两个 `@step` handler)。`review.patch_gate`
  (条件式 Patch Review:廉价 diffsummary 常开,仅当 `review/triggers.py`
  规则命中才跑 LLM 评审;高风险模块来自 *adapter*,settings 只是兜底)与
  `agent.review_diff`。评审核心仓库无关;领域清单从 profile 的 `review.md`
  扩展;sweep 提取器以 `repo.language` 为键,未知语言诚实降级。两处战役后的
  行为:(a) 若 agent 携带 comments 却报 escalate,`steps.py` 会把它**抢救为
  成功的 REQUEST CHANGES**(找到缺陷本就是一次成功评审,不是失败 step);
  (b) `utils.py::_render_review_md` 的**裁决校准**——仅"已验证的
  blocker/major"阻塞,自述 uncertain 的 comment 永不阻塞,minor→COMMENT,
  无 comment→APPROVE;`[validated]`/`[upstream-verify]`/`[sweep]` findings
  渲染成 "Validated" 段(人类会 approve 的 PR 上,GT"关切"多为验证性推理,
  只出 comment 会结构性压低 recall)。由 `test_review_step.py`、
  `test_agent_ensemble.py::test_render_verdict_calibration` /
  `test_zero_yield_lens_gets_one_retry` 固定。
- **`steps/pr/`**(包:`fetch.py`、`rebase.py`、`debug.py`、`publish.py`、
  `utils.py`)。
  - **`fetch.py`** —— `pr.fetch_diff`(只读 diff)、`pr.gate_check`
    (draft/merge-state/failing-checks,确定性)。这里含**PR-time checkout
    机制**:`_pr_time_checkout` 把评审树 pin 到 PR head(head sha 取最后一个
    commit 的 oid——`headRefOid` 并非每个 gh 版本都暴露;`git fetch origin
    pull/N/head` 对开放和已合并 PR 都有效;detached worktree 复用于
    `~/.omni-copilot/worktrees/<repo>-pr<n>`),`repo_path`/`checkout_note`
    经 `state_updates` 发布,于是所有 lens 工具都在 PR 时点的树上工作。任一
    失败路径降级回 live checkout,并带响亮注记 + `capability_gap` trace:
    "在 post-merge main 上,clean grep 证明不了 PR 时点的状态"。这修的是
    "潜在缺陷"评测类(#4810 漏改的 `get_cache_scale` caller,后来的
    issue #4891)——在 post-merge main 上评审会把 PR 漏掉的正是那些点藏起来;
    checklist 文本三个评测阶段都没做到,机制一上来就把 gap_hit 从 0.00 提到
    与 frontier 基线打平。由 `test_pr_steps.py::test_worktree_at_* /
    test_fetch_diff_pins_pr_time_checkout` 固定。
  - `ci.push`(很薄:所有安全都在 `push.py::guard_push`)、PR rebase
    (fork 感知 checkout → 推导 PushPolicy → rebase → 冲突 agent 或
    abort+升级;冲突 agent 成功后 `record_debug_memory`)、PR debug(拉取失败
    check → CI 日志富化 → 归一化签名分组 → 逐组 `agent.debug_group` → 增量
    push;debug agent 成功后 `record_debug_memory`)。
- **`steps/issue.py`** —— `issue.fetch`、`agent.draft_issue_answer`、
  `agent.triage_issues`、带门禁的 `issue.post_answer`。战役后:草稿契约多了
  **disposition 槽**(close/keep-open/duplicate-of-#N + reopen 条件),渲染时
  在缺 gh 验证的合并声明上加 epistemics caveat;实质草稿即便 escalate 也带
  caveat 交付而非丢弃;议题 agent 用 `max_agent_iters`(评审预算对 grep 重的
  triage 留白为零,曾把 issue 卡死在预算耗尽)。
- **`steps/report.py`** —— `report.final_summary`:`RUN_REPORT.md` 每个
  deliverable(review_text/draft_answer/triage_table)**恰好渲染一次** +
  checkout 注记 + 待裁决的 skill candidate 队列;逐 step 诊断隔离进
  `DIAGNOSTICS.md`(评审曾被三重渲染并混入 blockers/confidence 噪声,裁判
  打的正是那份被污染的产物)。
- **`steps/profile.py`** —— profile 建立 + Stage-4 维护 step(见 §6)。
- **`steps/rebase_native.py`** —— 夜跑的原生分解候选版。仅在晋升路径时读。
- **`push.py`**(约 46 行,建议通读)。`guard_push` 是唯一的推送 choke point:
  PushPolicy 且受保护分支双重把关;force 仅 with-lease,**绝不**对受保护
  分支。它是一个纯安全原语(scopes.py 的姊妹)。

## 6. 仓库 profile(v2)—— 知识子系统

按此顺序阅读:

1. **`profiles/store.py`** —— 精选层。带溯源的 fact
   (`source`/`evidence`/`first_seen`/`last_confirmed`/`confirmations`)、
   类型化 patch op 作为**唯一**写入面、两个 tier(`RUN_OPS` 仅追加;
   `CONSOLIDATE_OPS` 可 rewrite/merge/stale)、稳定性门禁(stable fact 永不
   丢失已引用证据;被取代的文本进 `history`)、merge 存根、以及三条消费通道
   —— `render_briefing()` **仅**输出 briefing 通道的 fact 且受硬性词数预算。
   由 `test_profile_store.py` 固定。
2. **`profiles/establish.py`** —— Stage 0–1.5 的 helper:6 词 shingle 的
   **冗余过滤器**(与文档重复的 briefing 行是纯成本)、从 AGENTS.md 类文件
   抽取指令、确定性的模块扫描。
3. **`engine/steps/profile.py`** —— 流水线各 step:`profile.fingerprint` →
   `profile.structure_scan` → `profile.ingest_docs` → `agent.profile_repo`
   (fact 必须引用证据,否则被 store 拒绝;概览是被禁止的输出),外加 Stage-4
   一组:`profile.detect_drift` / `profile.decay_stale` /
   `agent.profile_consolidate`(LLM 提出 op,由 store 门禁裁决)/
   `profile.judge`(只读审计,结构上无法变更)。Playbook:`repo-profile`
   (active,仓库无关)与 `profile-consolidate`(candidate)。由
   `test_profile_steps.py`、`test_p3_machinery.py` 固定。
4. **`profiles/repo_map.py`** —— 按语言的正则符号索引,按 HEAD 落盘缓存,
   按查询排序、受字符预算约束地渲染。结构由 agent **主动拉取**,绝不推送。
5. **`profiles/consolidate.py`** —— 衰减 + 漂移(确定性,仅报告)。

> 一条被评测验证的立场:知识**注入面有硬上限**——`review.md` 4,000 字符、
> 每个 SKILL.md body 1,500 字符、briefing 350 词,超出部分在注入时静默丢弃
> (briefing 按最常确认在前,溢出先淘汰新 fact)。可扩展的细节放进按需检索的
> topic skill 或 `constraints.md`,不要把 `review.md` 撑大。

## 7. CI 适配器(v2)—— `ci/`

- **`ci/normalize.py`**(30 行,建议通读):分组前把签名中的时间戳/哈希/
  地址/临时路径/行号/时长抹去;小的字面数字保留。这是对父 monitor 精确
  字符串比较缺陷的**刻意不继承**。
- **`ci/providers.py`**:`provider_for(adapter, settings)` 按 profile 的
  `ci.provider` 选择——`BuildkiteLogs`(REST,逐 check 尽力而为)或
  `GithubActionsLogs`(`gh run view --log-failed`,按 run 缓存)。缺 provider
  /token → `(None, reason)` → 该 step 记录 `capability_gap`,pr-debug 降级
  为按名字分组。由 `test_ci_and_repo_map.py` 固定。

## 8. 安全、记忆、界面 —— 其余部分

- **`review/`**:`diff_summary.py`(廉价的常开 fact)→ `triggers.py`(7 条
  规则)→ `reviewer.py`(只读裁决;除 `lgtm` 外一律视为不通过——fail-closed)。
- **`run_trace.py`**(40 行):仅追加的 jsonl;本库中每一条治理主张归根结底
  都意味着"有一个 trace 事件为它作证"。值得留意的事件:
  `agent_dispatch`/`agent_output`、`tool_refused`、`out_of_scope_edit`、
  `capability_gap`、`pr_time_checkout`、`debug_memory_recorded`、
  `lens_zero_yield_retry`、`profile_*`。
- **`memory/`**:`debug_memory.py`(FTS 写入契约:必须有 root_cause +
  verification;由 `_common.record_debug_memory` 在 debug/冲突 agent 成功后
  实际写入)与 `skills.py`(propose → candidate → 人工晋升;`touch()` 累计
  `run_count`/`last_used_at`)。由 `test_memory.py`(含 `test_skill_touch_*` /
  `test_debug_memory_recorded_*`)固定。
- **`notify.py`**:ESCALATION.md + 邮件 + `BLOCKED_EXIT=3` —— 把"通知而非
  猜测"写成代码。
- **`metrics.py`**:每次运行 CATQ = Q·S/C;绝不允许它破坏一次运行。
- **`cli/`**(包:`copilot.py` 编排类 + `entry.py` 参数/REPL + `utils.py`
  纯函数)与 **`chat.py`**:两者都汇入同一个 `run_task`/`run_playbook`——
  chat 只是前端,不是第二条执行路径(工具无法扩大权限;仓库读取被囚禁,
  `.env*` 被拒)。`ui.py` 只负责呈现。run 目录名带 uuid 后缀,并发不覆写。

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
| `test_agent_runtime.py::test_unparseable_after_repair_is_salvaged_as_escalation` | 非空的失败最终答复被抢救,不丢弃 |
| `test_agent_loop.py::test_final_round_nudge_follows_tool_results` | 收尾提示排在 tool_result 之后(API 邻接契约) |
| `test_agent_ensemble.py::test_render_verdict_calibration` | 仅已验证 blocker/major 阻塞;minor→COMMENT;Validated 段渲染 |
| `test_agent_ensemble.py::test_zero_yield_lens_gets_one_retry` | 零产出 lens 单独重问,不整轮重跑 |
| `test_review_step.py::test_review_salvaged_when_agent_escalates_with_comments` | 带 comments 的 escalate 抢救为 REQUEST CHANGES |
| `test_pr_steps.py::test_fetch_diff_pins_pr_time_checkout` | 评审树 pin 到 PR head;失败降级带注记 |
| `test_memory.py::test_skill_touch_increments_usage` / `test_debug_memory_recorded_from_step_helper` | 用量先验累计;debug memory 写入契约 |
| `test_push_and_steps.py` | guard_push 语义 |

## 10. 如何运行

```bash
pip install -e . && pytest                      # 226 个离线测试
omni-copilot -p "review pr 4830" --plan-only    # 只看计划不执行
omni-copilot -p "profile the repo" --yes        # 建立 profile(draft)
omni-copilot --playbook profile-consolidate --yes   # Stage-4 维护
PROFILE_BRIEFING_ENABLED=0 ...                  # {无 profile} 的 eval 对照臂
omni-copilot --resume                           # 从上次运行的首个未完成 step 重入
```

每次运行的产物:`~/.omni-copilot/runs/run-<ts>-<uuid6>/`(`RUN_REPORT.md`、
`DIAGNOSTICS.md`、`run_trace.jsonl`、`progress.json`、`metrics.json`、
`ensemble_agent.review_diff.json`、被阻塞时的 `ESCALATION.md`)。PR 评审
额外用到 `~/.omni-copilot/worktrees/<repo>-pr<n>/`(PR 时点树)。Profile:
`adapters/<repo>/profile/`(`profile.yaml`、`PROFILE_REPORT.md`、
`JUDGE_REPORT.md`、`ops_log.jsonl`)。

评测台账在 `eval/dataset/`:`vllm_omni_dataset.yaml`(40 项数据集,SIP-Bench
式 train/val/test 分区)、`run_copilot_arm.py` + `judge_val.py`(盲评)、
`judgments/`(逐阶段报告 + 取证:`T3_FORENSICS.md` → `T4_REPORT.md` →
`CAMPAIGN_FINAL.md`)。

## 11. 从哪里开始改

- **新仓库** → `omni-copilot -p "profile the repo"`,审查草稿 adapter +
  PROFILE_REPORT,翻转 `status`,完成——零核心改动是契约。
- **新 step** → 在合适的 `engine/steps/*.py` 里加一个 handler,用
  `@step(name, kind, risk, desc)` 装饰(risk 要诚实),通过 `state_updates`
  发布被消费的状态,加一个护栏测试。无需改任何中央注册。
- **新任务 kind** → `task_spec.py`(kind + tier)→ playbook yaml → intent
  hint → chat enum。planner 和 executor 无需改动。
- **新仓库知识(数据面,不改 `src/`)** → 通过类型化 op 写一条 profile fact
  或一个 skill;`review.md`/skills/briefing 都有注入上限,改完先量字符数。
  绝不在 `src/` 里写仓库字符串——`test_repo_neutral_core` 会抓到你。
- **改交付/评审行为前先看 trace 取证**:评测战役的教训是裁判扣分约九成来自
  机械交付问题(截断、误标 verdict、丢弃草稿),而非分析能力;先读
  `eval/dataset/judgments/T3_FORENSICS.md` 的排名缺陷清单,再决定动哪里。

## 附录 A:完整文件清单(`src/omni_copilot/` 逐个)

导览正文是**阅读路径**;本附录是**完整索引**——每个 `.py` 文件一行,标注
角色与它在正文中的位置(§)。行数为量级参考。

### 顶层 `omni_copilot/`
- `__init__.py`(3) — 包根,版本/公共导出。
- `task_spec.py`(81) — `TaskSpec`:kind/pr/issue/flags;**tier 由 kind 推导**,
  文字无法扩权。→ §1
- `intent.py`(120) — 自然语言 → TaskSpec,**LLM-only**;歧义/离题/注入即澄清;
  只有终端输入进入,GitHub 文本永不进入。→ §1
- `config.py`(137) — `Settings`(pydantic,从 `.env`/环境加载):LLM 端点、
  仓库路径、引擎预算(`ensemble_lens_max_iters`/`evidence_caps`/
  `llm_max_tokens`…)、推送安全、profile 开关。改行为先改这里。
- `llm.py`(142) — Anthropic SDK 薄封装(兼容 DeepSeek `/anthropic`);把回复
  归一化成 `Reply`/`Block`,捕获 `cache_read_input_tokens` 供计费/缓存分析。→ §4
- `agent_loop.py`(126) — 原始工具循环:每次调用过 `tools.dispatch`;预算耗尽
  强制最终答复;FINAL-ROUND 提示排在 tool_result 之后(API 邻接契约)。→ §4
- `tools.py`(195) — 原子能力 + **唯一** scope-enforcing choke point;越界写
  执行但记录;`read_file` 窗口化(48k+offset)。→ §4
- `scopes.py`(115) — `ToolScope`/`PathScope`:允许 / 拒绝 / 越界但记录。→ §4
- `push.py`(55) — `guard_push`:唯一推送 choke point,PushPolicy × 受保护分支
  双闸,force 仅 with-lease。→ §5
- `run_trace.py`(51) — 仅追加 jsonl 事实记录;默认不进 prompt;供 diff summary/
  触发器/升级/审计消费。→ §8
- `tracing.py`(340) — 可移植的 OTel 形状 span 记录器(零外部依赖):
  trace_id/span_id/parent + 计时,span 关闭即写一行 jsonl;跨 sync/asyncio,
  用 `contextvars` 传递父子嵌套;`llm.py` 的 `create()` 包在 `span("llm")` 里
  记 TTFT/token/并发。三个 agent 仓库共用的可移植 tracing。
- `metrics.py`(356) — CATQ = Q·S/C:Q 只对已知分量加权(绝不编造判分),
  S 由类型化 incident 几何衰减,C 是 USD+墙钟的对数成本指数;写
  `metrics.json`,失败绝不搞垮 run。→ §8
- `notify.py`(132) — 升级通道:ESCALATION.md + RunTrace 事件 + 邮件(Resend→
  SMTP)+ `BLOCKED_EXIT`;"通知而非猜测"。→ §8
- `chat.py`(411) — Claude-Code 式对话前端;执行走**同一** TaskSpec/planner/
  确认路径,永不扩权;仓库读取被囚禁,`.env*` 被拒。→ §8
- `ui.py`(194) — 终端 chrome:`FancyUI`(rich:banner/spinner/流式尾/markdown)
  与 `PlainUI`(管道/测试/`--no-chat` 的降级),无一依赖 TTY。→ §8

### `cli/` — 命令行(包)
- `__init__.py`(27) / `__main__.py`(7) — 包导出;`python -m omni_copilot.cli` 入口。
- `copilot.py`(327) — `Copilot` 编排核:resolve → plan → plan-review 门 →
  executor,复合命令队列、resume、`/status /logs /playbooks` 内置;run 目录
  `run-<ts>-<uuid6>`。→ §0/§5
- `entry.py`(113) — argparse + 单次/REPL 分派 + 内置命令路由(把 argv/stdin
  变成对 `Copilot` 的调用)。
- `utils.py`(32) — 纯 CLI helper:参数强制、metrics 行格式化。

### `adapters/` — 仓库结构知识(包)
- `__init__.py`(16) — 再导出 `RepoAdapter`/`AdapterRegistry`/loaders/writers/
  Phase-0 引导/`HIGH_RISK_SECTIONS`。
- `base.py`(250) — `RepoAdapter`:manifest、`module_for_path`、
  `high_risk_modules`、`capabilities`、按仓库隔离的 skills/memory/profile 目录;
  `update_manifest` 拒写高风险段;`fingerprint_repo`/`draft_adapter`。→ §2

### `engine/` — 引擎底座
- `__init__.py`(8) — 包导出。
- `step.py`(79) — `StepSpec`/`StepResult`/`StepContext`/`FailureKind`(仅类型)。→ §3
- `registry.py`(39) — `StepRegistry`:名字→handler 的唯一解析点。→ §3
- `executor.py`(233) — 任务无关保证:checkpoint/resume、foreach、when:、
  类型化失败路由、**state_updates 契约**。→ §3
- `planner.py`(137) — reuse > adapt > generate + 能力匹配;locked 拒改编,
  generate 只读。→ §2

### `engine/agent_runtime/` — 受治理 agent 运行时(核心,包)
- `__init__.py`(29) — 原样 re-export,公开导入面不变。
- `dispatch.py`(94) — `AgentDispatchContext` + 基础输出 schema;`render()`
  **静态在前动态在后**(prompt-cache 前缀复用);证据 `<untrusted_data>` 围栏。→ §4
- `knowledge.py`(201) — `_ScopedKnowledge`(仓库优先的 skill/memory 检索 +
  `touch()` 用量先验 + candidate 提案)、`_repo_map_tool`、memory 检索。→ §4
- `runner.py`(145) — `run_agent_step`:每个 `kind=="agent"` step 的唯一入口。→ §4
- `ensemble.py`(306) — `run_agent_step_ensemble`:多 lens 扇出 → 去重 → 逐编号
  裁决;零产出重问;reducer 不确定即降级。→ §4
- `utils.py`(119) — 无状态 helper:`_build_evidence`(caps+归档)、
  `_coerce_output`(合同修复 + **非空最终文本抢救**)、`_to_step_result`。→ §4

### `engine/steps/` — vetted step 库(自注册,包)
- `__init__.py`(34) — 导入即注册;`register_builtin_steps` 刷进 registry。→ §5
- `_common.py`(230) — `@step`/`register_step` 装饰器 + helper(`gh`/`git`/
  `repo_path`/`gh_read_tools`/`post_step`)+ `record_debug_memory`(闭环写入)。→ §5
- `workspace.py`(50) — `workspace.guard_clean`(拒脏树)、`analysis.diff_summary`。
- `report.py`(73) — `report.final_summary`:RUN_REPORT.md 每 deliverable 一次 +
  candidate 队列;诊断入 DIAGNOSTICS.md。→ §5
- `issue.py`(179) — `issue.fetch`、`agent.draft_issue_answer`(disposition 槽 +
  epistemics caveat + 草稿抢救)、`agent.triage_issues`、门禁 `issue.post_answer`。→ §5
- `profile.py`(441) — profile 建立 Stage 0–1.5 + Stage-4 维护 step。→ §6
- `rebase_ext.py`(115) — `rebase.run_external`:锁定夜跑的受监控子进程委托。→ §5
- `rebase_native.py`(442) — 夜跑原生分解候选(wrap 父包函数,不重写);
  `repo-rebase-native` playbook(candidate)。晋升路径时读。

### `engine/steps/pr/` — PR 领域 step(包)
- `__init__.py`(17) — re-export + 注册。
- `fetch.py`(169) — `pr.fetch_diff`(含 **PR-time checkout** `_pr_time_checkout`)、
  `pr.gate_check`。→ §5
- `rebase.py`(252) — PR head fork-aware checkout → PushPolicy → rebase → 冲突
  agent 或 abort+升级;`agent.verify_module`(仅建议)。→ §5
- `debug.py`(184) — 失败 check 收集(CI 日志富化)→ 签名分组 → `agent.debug_group`
  (成功后 `record_debug_memory`)→ 增量 push。→ §5
- `publish.py`(56) — 向外写(risk=push):`ci.push`(过 `guard_push`)、门禁
  `pr.post_review`(explicit post + ALLOW_POST)。→ §5
- `utils.py`(23) — 纯 `extract_signature`:从 CI 日志抽根因签名。

### `engine/steps/review/` — 评审 step(包)
- `__init__.py`(17) — re-export + 注册。
- `prompts.py`(145) — `_REVIEW_SYSTEM`/`_REVIEW_LENSES`/`_REVIEW_MERGE`/清单
  数据;枚举-再剪、`[validated]` 记录、reducer 不确定降级规则都在这里。→ §5
- `steps.py`(149) — `review.patch_gate` + `agent.review_diff`;带 comments 的
  escalate 抢救为 REQUEST CHANGES。→ §5
- `utils.py`(122) — `_render_review_md`(**裁决校准** + Validated 段)、
  `_SEVERITY_ORDER`、`_sweep_targets`。→ §5

### `memory/` — 经验库(包)
- `__init__.py`(6) — 再导出 `DebugMemory`/`SkillStore`。
- `debug_memory.py`(125) — SQLite+FTS5 失败/修复库;写入契约(必须 root_cause +
  verification);检索返回摘要,取全文是第二次调用。→ §8
- `skills.py`(181) — SKILL.md 库:propose→candidate→人工 promote;`find` 用
  module/词重叠/`run_count` 排序;`touch` 累计用量。→ §5/§8

### `playbooks/` — playbook 注册表(包)
- `__init__.py`(5) — 导出。
- `store.py`(195) — `Playbook`(yaml 数据)+ `find`(kind→精确 repo→能力匹配的
  仓库无关);candidate 永不召回。→ §2

### `profiles/` — 仓库知识子系统(包)
- `__init__.py`(6) — 导出。
- `store.py`(323) — 精选层:带溯源 fact、类型化 op 唯一写入面、两 tier、稳定性
  门禁、`render_briefing()`(词预算)。→ §6
- `establish.py`(102) — Stage 0–1.5 helper:6 词 shingle 冗余过滤(ETH 规则)、
  指令抽取、模块扫描。→ §6
- `consolidate.py`(52) — Stage-4:调度化门控巩固(唯一可 rewrite/merge)+
  确定性衰减 + 漂移检测。→ §6
- `repo_map.py`(149) — 按语言正则符号索引,按 HEAD 缓存,查询排序 + 字符预算;
  结构由 agent 主动拉取。→ §6
- `languages.py`(54) — 按语言的叶子数据(源文件后缀/符号/索引访问);未知语言
  返回空,消费者诚实降级。三处旧副本的共同归宿。

### `ci/` — CI 日志适配器(包)
- `__init__.py`(6) — 导出。
- `normalize.py`(35) — 分组前抹去时间戳/哈希/行号(刻意不继承父 monitor 的
  精确比较缺陷)。→ §7
- `providers.py`(134) — `provider_for`:`BuildkiteLogs` / `GithubActionsLogs`;
  缺 provider/token → `capability_gap` + 降级。→ §7

### `rebase/` — 父流水线可观测性(包)
- `__init__.py`(13) — 导出。
- `monitor.py`(163) — 只读消费父 orchestrator 的 `state.json`(phase/module/test
  进度)→ copilot 进度事件 + 失败分类 + 升级材料;绝不写父文件。→ §5

### `review/` — 条件式 Patch Review(包)
- `__init__.py`(9) — 导出。
- `diff_summary.py`(74) — 廉价确定性 diff 摘要(Patch Review 常开首段)。→ §8
- `triggers.py`(57) — 7 条触发规则(越界/高风险模块/大 diff/无测试/…):仅高风险
  才跑 LLM 评审。→ §8
- `reviewer.py`(100) — 只读 Patch Review agent;fail-closed(无 LLM →
  `unavailable`,推送门须当作不通过)。→ §8
