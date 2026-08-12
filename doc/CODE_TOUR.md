# 代码导览 —— InferMatrixCopilot(按数据流)

本文按**数据流**组织:跟着数据对象走——终端字符串 → `TaskSpec` → 共享
`state` 字典 → agent 的 prompt → 交付物与落盘,再看每次 run 读入/写出的
**知识平面**。每个文件在它所处的数据流位置就地讲解;`src/infermatrix_copilot/`
下全部 80 个 `.py` 文件都被覆盖,文末**附录**是 `文件 → 段落` 的查阅索引。
第一次通读建议按 §13 的阶段化阅读路线精读,再回来把本文当查阅手册用。
包根 `__init__.py` 只声明版本(`__version__`)。配套:`DESIGN.md`(为什么)、
`IMPLEMENTATION_STATUS.md`(做了什么)、`SPEC/`(规范契约)、
`eval/dataset/judgments/CAMPAIGN_FINAL.md`(评测结论)。

## 0. 数据流全景

两股正交的流动:**执行主脊**(一个任务,从左到右)与**知识平面**(持久
经验库,每次 run 读入/写出)。

```
 指令通道(仅终端)                                                       汇
 终端串 ─▶ intent ─▶ TaskSpec ─▶ planner ─▶ Resolution ─▶ executor ─▶ steps ─▶ report
            (预解析    (kind/pr/   (reuse>    (playbook/    (跑 step 图  (逐个     ├▶ RUN_REPORT.md
            +LLM       tier=f(kind)) adapt>    mode/tier)    + state 字典) 变换     ├▶ DIAGNOSTICS.md
            分类)                   generate)                              state)   ├▶ run_trace.jsonl
                                                                                    ├▶ metrics.json
 数据通道(GitHub/CI 文本,永远是 <untrusted_data>,永不成为指令)          └▶ ESCALATION.md
                       ▲ 读入                          ▼ 写出(受治理)
 知识平面: profile briefing/review.md · skills · debug memory · repo_map
           ────────────────────────────────────────────────────────────
           写出仅 candidate/typed-op:agent 提案,人类晋升(读宽写窄=安全模型)

 第二条流 · 离线评测(§9,独立叠加,不自动回灌)
 run_copilot_arm.py ─▶ CLI 跑数据集 ─▶ RUN_REPORT ─▶ judge_val.py 盲评 ─▶ 数值聚合
                       (走执行主脊)                  (第三方模型)      (judgments/)

 第三条流 · MCP 服务端(§12,宿主入口:Claude Code / Codex / Cursor,非交互)
 宿主 ─▶ thin_mcp_server ─┬▶ Direct(默认):server 零模型,同步返回知识路由+治理
                          │   契约,宿主自审 ─▶ validate_direct_review 完成门
                          │   (执行主脊完全不参与)
                          └▶ Strict:预约 run_id ─▶ 隔离子进程进入执行主脊
                              ─▶ get_status/get_result 轮询取结果
```

贯穿其上的两条不变量:**信任边界**(指令=终端;数据=围栏,见 §7)与
**安全闸**(`scopes`/`push` 门住每次工具调用与推送)。三条流共享同一套治理:
评测的知识写入仍走 candidate-then-human 门禁,MCP 的 kind 允许集直接引用
`READ_ONLY_KINDS`(细节分别见 §9、§12)。

## 1. 指令入口 —— 字符串 → `TaskSpec`

数据流起点。字符串从命令行或对话进来,先被分类成受治理的任务。

- **`cli/entry.py`**(196)——argparse + 单次/REPL 分派 + 内置命令路由:把
  argv/stdin 变成对 `Copilot` 的调用。`cli/__main__.py`(7)提供
  `python -m infermatrix_copilot.cli` 入口,`cli/__init__.py`(27)导出,
  `cli/utils.py`(33)是纯 helper(参数强制、metrics 行格式化)。
  **`cli/doctor.py`**(238)——`doctor` 预检诊断:逐项 ✓/✗,失败即给出**唯一**
  修复命令;只读、只打印密钥名不打印值、不做付费 LLM 调用,`--json` 供 CI。
- **`chat.py`**(440)——另一道前门:Claude-Code 式对话。用户输入任意文字,
  模型经 TOOLS 执行维护工作,但走**同一** TaskSpec/planner/确认路径,永不
  扩权;仓库读取被囚禁在配置的 repo 路径 + run 根,`.env*` 被拒。
  **`ui.py`**(194)是终端 chrome:`FancyUI`(rich:banner/spinner/流式尾/
  markdown)与 `PlainUI`(管道/测试/`--no-chat` 的降级),无一依赖 TTY。
- **`intent.py`**(379,**确定性优先**)——把一条终端命令变成 `TaskSpec`。
  预解析层先用纯代码解决 GitHub URL(校验**完整** owner/repo 身份,同名
  异主的仓库直接拒绝,绝不静默跑在本地 checkout 上)和无歧义的
  `<verb> pr/issue N` 命令,不花一次 LLM 调用;只有真正自由形式的输入才进
  LLM 分类器(一次修复重试,仍不行则澄清)。歧义/离题/注入 → 澄清提问,
  绝不猜测执行。**只有终端输入进入此函数**——拉取的 GitHub/CI 文本是数据
  不是指令(信任边界的第一道)。复合命令先切分,PR/issue 引用接续
  ("… then review it")。也在此设**双路径 `mode`**:默认 `eco`,仅当用户
  显式声明高性能模型才升 `performance`(确定性短语正则 + LLM `performance`
  标志,OR 取或;成本敏感决策绝不靠猜)。`resolve_repo_alias` 同时服务 §12
  Strict 入口的 URL 解析。由 `test_intent_taskspec.py` / `test_dual_path.py` /
  `test_phase_b.py` 固定。
- **`task_spec.py`**(91)——数据对象 `TaskSpec`:kind/pr/issue/flags。最硬的
  不变量:**`tier` 由 `kind` 推导**,不存在任何文字或 LLM 可设的扩权字段;
  `read_only`/`confirm_required` 由 kind + flag 推导。另有**双路径 `mode`**
  (`eco` 默认 / `performance`):由 intent 设定、整条 run 共享,选 agent 推理
  模型(见 §4),与 `tier` 正交——便宜模型永不放大任务权限。`READ_ONLY_KINDS`
  也是 §12 MCP 策略的唯一允许集来源。

## 2. 解析 —— `TaskSpec` + 能力 → 计划(Resolution)

TaskSpec 遇上仓库能力,解析成一条可执行流水线。

- **`cli/copilot.py`**(501)——`Copilot` 编排核,把整条流串起来:
  resolve → plan → plan-review 门 → executor,外加复合命令队列、resume、
  `/status /logs /playbooks` 内置。run 目录名 `run-<ts>-<uuid6>`(uuid 后缀:
  同秒并发过去会互相覆写 `task.json`)。
- **`engine/planner.py`**(137)——reuse > adapt > generate + 能力匹配。两条硬
  规则:locked playbook 拒改编;generate 路径**结构性**禁止 write/push step,
  只对只读 kind 存在。能力缺口 → 抛 "capability gap … run repo_profile" 而非
  静默失败。由 `test_planner_playbooks.py` / `test_capabilities.py` 固定。
- **`playbooks/store.py`**(195)——`Playbook` 是数据(`playbooks/` 下 yaml),
  `find(kind, repo, capabilities)`:精确 repo 优先,仓库无关的仅当
  `requires ⊆ capabilities` 才匹配;candidate **永不**被召回。`__init__.py`(5)
  导出。
- **`adapters/base.py`**(368)——能力的来源。`RepoAdapter`:声明式
  manifest.yaml、`module_for_path`、`high_risk_modules`、`capabilities`
  (推导 + 显式)、按仓库隔离的 skills/memory/profile 目录、`briefing()`。
  高风险段(`push`/`repo`/`upstream`)是 human-only——agent 侧的
  `update_manifest` 在此层被拒;未知仓库得到确定性 `fingerprint_repo` +
  DRAFT `draft_adapter`,停下等人审(Phase-0 引导)。`adapters/__init__.py`
  (16)再导出公开面。

## 3. 执行底座 —— 共享 `state` 字典与 `state_updates` 契约

计划落到执行器,step 之间**只通过一个共享 `state` 字典**交接——这是全库
最要紧的数据流细节。

- **`engine/executor.py`**(267)——任务无关的保证:每 step checkpoint
  (`progress.json`)、`foreach` 扇出(asyncio.gather + `_merge`)、`when:`
  条件、仅对 RETRYABLE 的有界重试、BLOCKED/ESCALATE/FORBIDDEN → notifier +
  退出。**状态契约在这里**:step 通过 `outputs.state_updates` 发布每一个被
  后续 step 消费的键(`diff_text`/`repo_path`/`checkout_note`/`PushPolicy`/
  `review_text`…);resume 时恢复它们;`_merge` 提升扇出的 updates;`when:`
  先读 TaskSpec 再读 state,遇未知键**大声阻塞**。旧行为会静默破坏每次
  resume。由 `test_engine.py` / `test_v2_p0.py` 固定。
- **`engine/step.py`**(79)——流经执行器的类型词汇:`StepSpec`
  (name/kind/risk/handler)、`StepResult`(ok + 类型化 `FailureKind`,失败是
  **值**不是异常)、`StepContext`(handler 能触碰的一切:settings/state/
  params/run_dir/trace/llm)。六种失败类型走不同路由。`engine/registry.py`
  (39)是"名字→handler"的唯一解析点;`engine/steps/__init__.py`(34)导入
  即触发 `@step` 自注册、`register_builtin_steps` 刷进 registry;
  `engine/__init__.py`(8)导出。
- **`config.py`**(418)——`Settings`(pydantic,从 `.env`/环境,永不提交),
  被塞进每个 `StepContext`:LLM 端点、仓库路径、引擎预算
  (`ensemble_lens_max_iters`/`evidence_caps`/`llm_max_tokens`/
  `ensemble_stagger_seconds`/`ensemble_zero_yield_retry`…)、MoA 成员与预算
  (§4)、推送安全、profile 开关。改行为先改这里。

## 4. Agent step 内部 —— `state` → prompt → 结构化输出

高价值 step(`agent.review_diff`/`agent.draft_issue_answer`/
`agent.debug_group`)全都汇入**`run_agent_step`**,这是数据流里信息密度最高
的一段变换。`engine/agent_runtime/` 是一个包(`__init__.py`(29)原样
re-export,公开导入面不变)。

- **`engine/agent_runtime/runner.py`**(202)——每个 `kind=="agent"` step 的
  唯一入口:组装 dispatch context、注入知识、跑工具循环、按契约收敛输出、
  成功后 `touch` 命中的 skills(用量先验)。**双路径分流点**:按 run 的 tier
  (`spec.mode`→`settings.model_for`)选 agent 推理模型传给 `run_agent`——
  intent 之后才分流,上游(规划/证据/知识)全共享。
- **`engine/agent_runtime/dispatch.py`**(96)——`AgentDispatchContext` +
  基础输出 schema。`render()` **静态在前、动态在后**,为 prompt-cache 前缀
  复用(供应商按逐字节相同前缀缓存):输出契约 / permissions / briefing /
  skills 领头(跨同类 run 重复),per-run 的 REPO/TASK/step/evidence 收尾。
  证据 `<untrusted_data>` 围栏、逐项截断(见下)。
- **`engine/agent_runtime/utils.py`**(119)——无状态 helper:`_build_evidence`
  (`evidence_item_chars` 默认 24k;`evidence_caps` 给 pr_diff 120k / issue_text
  30k;大而共享的证据进共享前缀一次、并把全文归档到 run 目录)、
  `_coerce_output`(契约 + 一轮修复;**非空最终文本被抢救**成
  `needs_review`+`_raw_text` 而非丢弃)、`_to_step_result`(状态→FailureKind)。
- **`engine/agent_runtime/knowledge.py`**(264)——知识**流入**这里(通向 §6):
  `_ScopedKnowledge`(仓库优先的 skill/memory 检索 + `touch()` 用量先验 +
  candidate 提案)、`_repo_map_tool`(按需拉结构,绝不散文注入)、memory 检索。
- **`engine/agent_runtime/ensemble.py`**(387)——评审质量的机器:多 lens 扇出
  (共享同一缓存前缀)→ 精确去重 → 逐编号 keep/drop/dup 裁决、确定性组装
  (未提及即保留)。**零产出 lens 单独重问一次**(`ensemble_zero_yield_retry`),
  而非整个多 lens 重跑;lens 错峰启动(`ensemble_stagger_seconds`);reducer
  的 merge guidance 有"自述不确定即降级"硬规则,`ensemble_merge_evidence_chars`
  60k 使其能看到 diff。
- **`engine/agent_runtime/moa.py`**(230)——Mixture-of-Agents(W6):lens/
  draft 提案可跑在异构 `LLM_MIXTURE` 成员上,verify-and-merge reducer 仍用本
  run 的 tier 模型。硬保证在代码不在 prompt:每个成员请求先原子 `reserve()`
  保守上界成本、结算时替换为实际用量,已结算花费永不超 `moa_max_usd`(预约
  失败 → 降级 tier 模型或跳过成员,绝无不封顶请求);per-request deadline 取
  成员超时与整体剩余的最小值;成员身份是 `model@host`,密钥只经 env 变量名
  引用,永不落日志/trace。由 `test_moa.py` 固定。
- **`agent_loop.py`**(126)——原始工具循环:每次调用过 `tools.dispatch`;预算
  耗尽强制最终答复;"FINAL ROUND" 收尾提示**必须排在 tool_result 之后**
  (否则违反 tool_use→tool_result 邻接契约,整个请求 400)。
- **`tools.py`**(228)+ **`scopes.py`**(119)——原子能力与权限(它们也是安全
  闸,见 §7)。一条规则:**每一次**工具调用过 `tools.dispatch`,检查
  `ToolScope`/`PathScope` 并记 trace,三种结果:允许 / 拒绝 / 越界但记录。
  `read_file` 是**窗口化**的(48k + `offset` 分页):整文件读会吹爆会话历史、
  倍增未缓存 token、把对话推出可靠缓存长度。
- **`llm.py`**(452)——Anthropic/OpenAI 兼容端点的中立封装(各自支持可选
  Base URL):回复归一化成 `Reply`/`Block`,agent loop / intent / reviewer
  与测试 fake 永不直接触 SDK 类型;捕获 `cache_read_input_tokens` 供计费/
  缓存分析。**`tracing.py`**(652)——可移植 span 树记录器(OTel 形状:
  trace_id/span_id/parent/attributes,零外部依赖):span 关闭即追加一行
  jsonl,被杀的 run 保留一切已完成的 span;sync 与 asyncio 双安全,父子嵌套
  经 `contextvars` 按 task 复制,并行 agent 得到独立正确的树;`create()`
  包在 `span("llm")` 里记 TTFT/token/并发。
- 固定:`test_scopes_tools.py`、`test_agent_loop.py`
  (`test_final_round_nudge_follows_tool_results` 钉消息形状)、
  `test_agent_runtime.py`(dispatch 参数化 +
  `test_unparseable_after_repair_is_salvaged_as_escalation` 钉抢救)、
  `test_agent_ensemble.py`(裁决校准 / 零产出重问)。

## 5. Step 库 —— 逐个把 `state` 往前推的变换

每个 step 一个 handler,在 `engine/steps/` 就地 `@step` 自注册。按数据流分
支叙述(取 → 评审/回答/debug → 报告 → 委托 → profile)。

- **`engine/steps/_common.py`**(260)——共享地基:`@step`/`register_step`
  装饰器 + helper(`gh`/`git`/`repo_path`/`gh_read_tools`/`post_step`)+
  **`record_debug_memory`**(成功修复写回 debug memory,闭环写入,写失败被
  trace 吞掉)。**`engine/steps/workspace.py`**(51)——`workspace.guard_clean`
  (拒脏树)、`analysis.diff_summary`。

- **PR 评审支流**(diff → review_text):
  - **`engine/steps/pr/fetch.py`**(328)——`pr.fetch_diff` 产出 `diff_text`,
    并含 **PR-time checkout**(`_pr_time_checkout`:把评审树 pin 到 PR head——
    head sha 取最后 commit 的 oid;`git fetch origin pull/N/head` 对开放/已合并
    PR 都有效;detached worktree 复用于 `~/.infermatrix-copilot/worktrees/`),经
    `state_updates` 发布 `repo_path`/`checkout_note`,于是所有 lens 工具都在
    PR 时点的树上工作;失败降级回 live checkout 并带响亮注记 + `capability_gap`
    trace。`pr.gate_check` 产出 draft/merge-state/failing-checks 报告。
    `diff_text`/`gate_report` 均可经 state 注入,网络之下的路径离线可测;
    `gh` 不可用一律降级 BLOCKED,绝不崩溃。`pr/__init__.py`(17)re-export +
    注册。
  - **`engine/steps/review/steps.py`**(224)——`review.patch_gate` +
    `agent.review_diff`;带 comments 却报 escalate 时**抢救为成功的
    REQUEST CHANGES**(找到缺陷本就是成功评审)。
    **`review/planner.py`**(307,顶层 review/ 包)——审查深度自适应:4-lens
    ensemble 是重大改动的召回下限,但成本约 4×;确定性规则先裁明确案例
    (小而低风险 → light 单遍;大或高风险路径 → full 全 ensemble),只有灰区
    花一次小 LLM 调用,且该调用**只能选 standard 或 full**——`light` 永不
    来自模型输出,PR 内容说服不了 planner 降级。深度不变量就地强制:
    light ⇒ 无 lens,standard ⇒ 2–3 lens,full ⇒ 全部。playbook 的
    `review_depth` 参数可显式 pin。
    **`review/prompts.py`**(155)——`_REVIEW_SYSTEM`/`_REVIEW_LENSES`/
    `_REVIEW_MERGE`/清单数据(枚举-再剪、`[validated]` 记录、reducer 降级规则
    在此)。**`review/utils.py`**(193)——`_render_review_md`:**裁决校准**
    (仅已验证 blocker/major 阻塞,minor→COMMENT,自述 uncertain 永不阻塞)+
    `[validated]`/`[upstream-verify]`/`[sweep]` 渲染成 "Validated" 段;
    `_sweep_targets`。`review/__init__.py`(17)re-export + 注册。

- **议题支流**(issue_text → draft_answer):
  - **`engine/steps/issue.py`**(338)——`issue.fetch`、`agent.draft_issue_answer`
    (contract 含 **disposition 槽** close/keep-open/duplicate-of-#N + reopen;
    缺 gh 验证的合并声明加 epistemics caveat;实质草稿即便 escalate 也带 caveat
    交付;用 `max_agent_iters` 给 grep 重的 triage 留白)、`agent.triage_issues`、
    门禁 `issue.post_answer`。

- **PR debug / rebase 支流**(CI 日志 → 签名 → 修复 → push):
  - **`engine/steps/pr/debug.py`**(184)——失败 check 收集(CI 日志富化)→
    签名分组 → `agent.debug_group`(成功后 `record_debug_memory`)→ 增量 push。
    **`pr/utils.py`**(23)——纯 `extract_signature`(从 CI 日志抽根因签名)。
  - **`engine/steps/pr/rebase.py`**(252)——PR head fork-aware checkout →
    推导 PushPolicy → rebase → 冲突 agent 或 abort+升级(冲突 agent 成功后
    `record_debug_memory`);`agent.verify_module` 仅建议。
  - **`engine/steps/pr/publish.py`**(327)——向外写的两个 choke point
    (risk=push):`ci.push` 过 `guard_push`;`pr.post_review` 双闸
    (explicit post + ALLOW_POST),把每条 finding 的位置对照已取回的 diff
    校验后,以**单条 GitHub review + inline threads** 的结构化形式提交。
    这两个是安全闸的出口,详见 §7。

- **报告汇**:**`engine/steps/report.py`**(73)——`report.final_summary` 把
  `state` 汇成 `RUN_REPORT.md`(每个 deliverable 恰好一次 + checkout 注记 +
  待裁决 skill candidate 队列)与 `DIAGNOSTICS.md`(逐 step 诊断,评审曾被三重
  渲染并混入 blockers/confidence 噪声,现隔离)。

- **委托/夜跑支流**(数据流出到父流水线):
  **`engine/steps/rebase_ext.py`**(115)——`rebase.run_external`:锁定夜跑的
  受监控子进程委托。**`engine/steps/rebase_native.py`**(443)——原生分解候选
  (wrap 父包函数、不重写;`repo-rebase-native` playbook,candidate)。
  **`rebase/monitor.py`**(163)——只读消费父 orchestrator 的 `state.json`
  (phase/module/test 进度)→ copilot 进度事件 + 失败分类 + 升级材料,绝不写
  父文件;`rebase/__init__.py`(13)导出。

- **profile 建立支流**(通向 §6):**`engine/steps/profile.py`**(441)——
  `profile.fingerprint` → `structure_scan` → `ingest_docs` → `agent.profile_repo`
  (fact 必须引证据否则被拒)+ Stage-4 一组(`detect_drift`/`decay_stale`/
  `agent.profile_consolidate`/`profile.judge`)。由 `test_profile_steps.py` /
  `test_p3_machinery.py` 固定。

## 6. 知识平面 —— 每次 run 的读入 / 写出

与执行主脊正交:持久经验库在 dispatch 时被读入(§4 的 `knowledge.py`),在
step 成功后被写出。**读宽写窄**——agent 只能提案,人类晋升,是安全模型的核心。

**读入通道**(注入 dispatch context):profile briefing + `review.md` 清单、
top-k skills、top-3 debug memory、按需 repo_map。三条注入面各有**硬上限**,
超出静默丢弃:`review.md` 4,000 字符、每个 SKILL.md body 1,500、briefing
350 词(按最常确认在前,溢出先淘汰新 fact)。

- **`profiles/store.py`**(324)——精选层:带溯源 fact
  (source/evidence/first_seen/last_confirmed/confirmations)、类型化 patch op
  作为**唯一**写入面、两 tier(`RUN_OPS` 仅追加;`CONSOLIDATE_OPS` 可
  rewrite/merge/stale)、稳定性门禁、`render_briefing()`(词预算)。由
  `test_profile_store.py` 固定。**`profiles/establish.py`**(102)——Stage 0–1.5
  helper:6 词 shingle 冗余过滤(ETH 规则)、指令抽取、模块扫描。
  **`profiles/consolidate.py`**(52)——Stage-4:调度化门控巩固(唯一可
  rewrite/merge)+ 确定性衰减 + 漂移检测。**`profiles/repo_map.py`**(150)——
  按语言正则符号索引,按 HEAD 缓存,查询排序 + 字符预算(结构由 agent 主动拉)。
  **`profiles/languages.py`**(54)——按语言的叶子数据(源文件后缀/符号/索引
  访问),未知语言返回空、消费者诚实降级;三处旧副本的共同归宿。
  `profiles/__init__.py`(6)导出。
- **`memory/debug_memory.py`**(125)——SQLite+FTS5 失败/修复库:写入契约(必须
  root_cause + verification,由 `_common.record_debug_memory` 实际写);检索
  返回摘要,取全文是第二次调用。**`memory/skills.py`**(181)——SKILL.md 库:
  propose→candidate→人工 promote;`find` 用 module/词重叠/`run_count` 排序;
  `touch` 累计 `run_count`/`last_used_at`。`memory/__init__.py`(6)导出。由
  `test_memory.py`(含 skill touch / debug memory 写入)固定。

## 7. 贯穿数据流的闸 —— 信任边界与安全

不是流程的一段,而是横切每一步的约束。

- **信任边界**:指令通道=终端输入(只在 §1 的 `intent.py` 入口);数据通道=
  拉取的 diff/issue/CI 文本,一律 `<untrusted_data>` 围栏,永不成为指令。
- **`scopes.py` / `tools.py`**(见 §4):每次工具调用的门。越界写执行但记录,
  agent 永远看不到 scope 不允许的工具。
- **`push.py`**(55)——`guard_push`:唯一推送 choke point,PushPolicy × 受保护
  分支双闸,force 仅 with-lease,默认 dry-run。§5 的 `pr/publish.py` 是它的
  唯一出口。由 `test_push_and_steps.py` 固定。
- **条件式 Patch Review**(推送前的闸,顶层 `review/` 包,勿与 §5 的
  `engine/steps/review/` 混淆):**`review/diff_summary.py`**(75)廉价确定性
  摘要常开 → **`review/triggers.py`**(57)7 条规则(越界/高风险模块/大 diff/
  无测试/…)仅高风险才升级 → **`review/reviewer.py`**(100)只读裁决,
  fail-closed(无 LLM → `unavailable`,推送门须当作不通过)。`review/__init__.py`
  (9)导出。(同包的 `planner.py` 属评审深度,见 §5。)

## 8. 汇 —— 落盘、遥测、升级、CI 摄入

数据流的终点与旁路记录。

- **`run_trace.py`**(51)——仅追加 jsonl 事实记录(`agent_dispatch`/
  `agent_output`/`tool_refused`/`capability_gap`/`pr_time_checkout`/
  `debug_memory_recorded`/`lens_zero_yield_retry`/`profile_*`…);默认不进
  prompt,供 diff summary / 触发器 / 升级 / 审计消费。(`tracing.py` 的计时
  span 见 §4。)
- **`metrics.py`**(493)——CATQ 家族(`eval/METRICS_RESEARCH.md`):
  CATQ = Q·S/C。Q 只对**实际已知**的分量加权(权重重归一并标 `partial`;
  judged 分量由评测管线/反馈收集器填充,本模块绝不编造判分),S 由类型化
  incident 几何衰减,C 是 USD+墙钟的对数成本指数;写 `metrics.json`,失败
  绝不搞垮 run。
- **`notify.py`**(132)——升级通道:`ESCALATION.md` + RunTrace 事件 + 邮件
  (Resend→SMTP)+ `BLOCKED_EXIT`;"通知而非猜测"。
- **CI 日志摄入**(pr-debug 支流的**源**,数据流上是入口而非汇,但代码在
  `ci/`):**`ci/normalize.py`**(35)分组前抹去时间戳/哈希/行号(刻意不继承
  父 monitor 的精确比较缺陷);**`ci/providers.py`**(134)`provider_for`:
  `BuildkiteLogs` / `GithubActionsLogs`,缺 provider/token → `capability_gap`
  + 降级。`ci/__init__.py`(6)导出。由 `test_ci_and_repo_map.py` 固定。

## 9. 第二条数据流 —— 离线评测(`eval/dataset/`)

叠在上面所有之上的一条独立数据流,**不自动回灌**:`run_copilot_arm.py` 驱动
CLI 跑数据集 → RUN_REPORT → `judge_val.py`(盲评,第三方模型)→ 数值聚合。
数据集 `vllm_omni_dataset.yaml`(40 项,SIP-Bench 式 train/val/test 分区)、
逐阶段报告在 `judgments/`(`T3_FORENSICS.md` → `T4_REPORT.md` →
`CAMPAIGN_FINAL.md`)。任何知识写入仍走 candidate-then-human 门禁。

## 10. 护栏测试 —— 你不能破坏的行为

| 测试 | 它固定的不变量 | 数据流段 |
|---|---|---|
| `test_v2_p0.py::test_repo_neutral_core` | `src/` 仓库字面量被泄漏清单封顶 | §6 |
| `test_v2_p0.py::test_resume_restores_state_handoffs` | state_updates 契约 | §3 |
| `test_capabilities.py` | 能力匹配;locked rebase 不泄漏 | §2 |
| `test_profile_store.py::test_stability_gate_and_history` | stable fact 永不丢证据 | §6 |
| `test_profile_steps.py::test_profile_agent_applies_gated_facts` | 无证据 fact 被拒 | §5/§6 |
| `test_p3_machinery.py::test_judge_reports_but_never_mutates` | judge 只读 | §5 |
| `test_agent_runtime.py`(参数化 dispatch) | `kind=="agent"` ⇒ 统一运行时治理 | §4 |
| `test_agent_runtime.py::test_unparseable_after_repair_is_salvaged_as_escalation` | 非空失败答复被抢救 | §4 |
| `test_agent_loop.py::test_final_round_nudge_follows_tool_results` | 收尾提示排在 tool_result 后 | §4 |
| `test_agent_ensemble.py::test_render_verdict_calibration` | 仅已验证 blocker/major 阻塞 | §5 |
| `test_agent_ensemble.py::test_zero_yield_lens_gets_one_retry` | 零产出 lens 单独重问 | §4 |
| `test_moa.py` | MoA 预算台账封顶;密钥永不落 trace | §4 |
| `test_review_step.py::test_review_salvaged_when_agent_escalates_with_comments` | 带 comments 的 escalate 抢救 | §5 |
| `test_pr_steps.py::test_fetch_diff_pins_pr_time_checkout` | 评审树 pin 到 PR head | §5 |
| `test_memory.py::test_skill_touch_increments_usage` | 用量先验累计 / debug memory 写入 | §6 |
| `test_push_and_steps.py` | guard_push 语义 | §7 |
| `test_thin_mcp_server.py` / `test_imreview_output_contract.py` | Direct 路由/预算/完成门契约 | §12 |
| `test_mcp.py` | 篡改防御、单写者对账、分页、只读工具集 | §12 |

## 11. 如何运行 · 从哪里开始改

```bash
pip install -e . && pytest                      # 45 个测试文件、430+ 离线用例
infermatrix-copilot doctor                      # 预检:逐项 ✓/✗ + 唯一修复命令
infermatrix-copilot -p "review pr 4830" --plan-only    # 只看计划不执行
infermatrix-copilot -p "profile the repo" --yes        # 建立 profile(draft)
infermatrix-copilot --playbook profile-consolidate --yes   # Stage-4 维护
PROFILE_BRIEFING_ENABLED=0 ...                  # {无 profile} 的 eval 对照臂
infermatrix-copilot --resume                           # 从首个未完成 step 重入
```

产物:`~/.infermatrix-copilot/runs/run-<ts>-<uuid6>/`(`RUN_REPORT.md`、
`DIAGNOSTICS.md`、`run_trace.jsonl`、`progress.json`、`metrics.json`、
`ensemble_agent.review_diff.json`、`ESCALATION.md`)+ PR 评审的
`~/.infermatrix-copilot/worktrees/<repo>-pr<n>/`。Profile:`adapters/<repo>/profile/`。

- **新 step** → 在 `engine/steps/*.py` 加 handler,`@step(name,kind,risk,desc)`
  装饰,通过 `state_updates` 发布被消费的键,加护栏测试。无需改中央注册。
- **新任务 kind** → `task_spec.py`(kind+tier)→ playbook yaml → intent hint →
  chat enum。planner/executor 不动。
- **新仓库知识(数据面)** → 类型化 op 写 profile fact 或一个 skill;三条注入面
  都有上限,改完先量字符数。绝不在 `src/` 写仓库字符串——
  `test_repo_neutral_core` 会抓到你。
- **改交付/评审行为前先看 trace 取证**:评测教训是裁判扣分约九成来自机械
  交付问题而非分析能力;先读 `eval/dataset/judgments/T3_FORENSICS.md`。

## 12. 第三条数据流 —— MCP 服务端(Claude Code / Codex / Cursor → 只读工具)

叠在核心之上、面向宿主的一条独立入口。宿主非交互(无 `[y/N]`),所以"宿主
不能放大权限"必须是**结构性**保证,且不能依赖磁盘上 `request.json` 未被同用户
进程篡改。

两种入口形状共存于**同一个**默认 MCP(`thin_mcp_server.py`,安装器注册的就是
它):**Direct**(默认)——server 零模型、零状态,一次同步调用把知识路由和治理
契约返回给宿主,由宿主自己的模型完成阅读与判断,执行主脊(§1–§5)完全不参与;
**Strict**——桥入下面 `mcp_server.py` 的预约+轮询机制,进入完整执行主脊。

Direct 的数据流:

```
宿主 /imreview(先冻结 PR 快照,在对话报 head SHA / CI / mergeability)
  → review(target, mode="direct", title, body, changed_files)
      title/body 选 owner(词边界信号匹配;model 路由长名优先)
      changed_files 常规下仅做 scope 校验;当存活路由无一命中其推导出的
      owner 时,由它选路(status=scope_fallback,显式声明,不静默)
  → ≤3 条知识路由(quick_map 只截规则页 "## …Direct" 节,3.5k 封顶)
    + execution_budget(docs_only/code 两档,硬顶) + checklist + progress_update
  → 宿主并行读源码、跑验证(知识只用 quick_map,不开全文;
      唯一例外:quick_map_status≠ok 的路由(unavailable 无图 / truncated 只有半张)须打开,预算逐条放行)
  → validate_direct_review(subtraction 完成门:机械结构检查——
      none 不得附带证据 / triggered 需减法项或 minimality_proof;恰好 1 条最终评论)
  → 单条合并评审结论(仅当前对话;发布仍需显式 post + ALLOW_POST)
```

- **`thin_mcp_server.py`**(806)——默认 MCP 门面,七个工具:`review`(按 `mode`
  分流)、`validate_direct_review`、`get_review_status`/`get_review_result`
  (转发 `CopilotMCP`)、`update_knowledge`(只返回 CONTRIBUTING 入口,不是
  imupdate 的审计器)、`doc_search`/`doc_read`。Direct 的"治理"全靠返回的数据
  契约——server 管不住宿主模型,于是把"该怎么审"编码成结构化字段随返回值
  下发,再用完成门机械验收(它检查结构,不验证证据真伪)。`_guard` 把异常转成
  `{"error": …}` 值返回,`_knowledge_path` 防路径逃逸出知识根;Strict 分支先
  `strict_readiness` 查缺项,绝不启动注定失败的 run。由
  `test_thin_mcp_server.py` / `test_imreview_output_contract.py` 固定。
- **`knowledge_docs.py`**(122)——`doc_search`/`doc_read` 的底座:限定 general
  切片 + 单个仓库切片的只读检索(词重叠计分)与分页读取(24k/页),越界路径
  一律拒绝。
- **`mcp_policy.py`**(141,enforce_mcp_policy)——安全闸,在**边界**(server)与
  **子进程**(权威)各跑一次:kind 必须 ∈ `READ_ONLY_KINDS`
  (pr_review/issue_answer/issue_filter),`post` 硬置 False,repo 必须在
  allowlist,pr/issue 为正,未知 params 剥除。允许集直接引用 `task_spec.py` 的
  `READ_ONLY_KINDS`,永不与代码漂移。
- **`mcp_server.py`**(392,FastMCP,stdio)——Strict 的后台机器:start/poll
  工具对(评审 5–12 分钟会撑爆同步调用超时):`start_review`/
  `start_issue_answer`/`start_issue_triage` 预约即返回 `run_id`;`get_result`
  (分页 `next_offset`+`report_path`,封顶 `mcp_report_max_bytes`)/
  `get_status`(`run_status`+`progress`)轮询。单 worker 线程串行,每个 run
  一个**隔离子进程**(`python -m infermatrix_copilot --execute-reserved <id>`):
  子进程 stdout 落 `console.log`,server stdout 只走 JSON-RPC;进程级全局
  tracer / `last_run_dir` 因此天然按 run 隔离。它自身的 `build_mcp()` 暴露
  V1 工具面,是 `docs/autonomous-workflow.md` 的独立执行器入口,默认不注册。
- **`run_status.py`**(247)——`run_status.json` 的耐久单写者记录。`reserve_run`
  (server,子进程存在前)写 `queued`;子进程一启动先写自己的 pid
  (`mark_child_started`)再 `planning→running→terminal`,是运行期唯一写者;
  父进程只在 `.wait()` 后(子已死)对账;跨进程对账仅在确认写者已死后、持
  `flock` 写并保留 owner 字段。按属主对账(`owner_server_id`/
  `owner_server_pid`/`child_pid`):只有属主 server 被确认死亡才把非终态 run
  标 `interrupted`——多 server(Claude+Codex 各起一个)下不会互抢对方 live 的
  `queued` run。lazy(每次 get_*)+ 父进程 wait 后 + 启动扫描,三处对账,无
  run 永久非终态。
- **`__main__.py`**(12)——`python -m infermatrix_copilot` 入口,供 server 以
  当前解释器拉起 `--execute-reserved` 子进程。CLI 主路径(`run_task`)不变:
  仍在建 run 目录**前**过门,弃用计划不落目录;预约(先建目录后规划)是 MCP
  专属形状。
- 打包:`plugins/infermatrix-copilot/`(共享 MCP + Skill + 薄市场清单)、根
  `.claude-plugin/marketplace.json`、`.cursor-plugin/marketplace.json`、
  `.agents/plugins/marketplace.json`、`docs/codex/config.toml`、
  `docs/cursor/mcp.json`;安装说明见 `doc/MCP.md`。`mcp` 依赖在 `[mcp]` extra
  后,独立 CLI 安装保持零依赖。由 `test_mcp.py` 固定(篡改防御、单写者对账、
  分页、只读工具集)。

## 13. 建议阅读路线 —— 分阶段精读(新人向)

正文按数据流组织,适合定位查阅;第一次通读按下面的顺序走。真正需要精读的
核心不到 20 个文件,其余按需查阅。每阶段读完,用"重点与自测"检验理解、
跑对应护栏测试(§10)再进下一阶段。

| 阶段 | 精读文件 | 详解 | 重点与自测 |
|---|---|---|---|
| 1 数据对象 | `task_spec.py` · `engine/step.py` · `config.py` | §1/§3 | `tier` 为何是 property 而非字段?`StepResult.failure` 为何是值而非异常?(答案在阶段 2 的 executor) |
| 2 执行主脊 | `cli/copilot.py` → `intent.py` → `playbooks/store.py`(对照仓库根 `playbooks/pr-review.yaml`)→ `engine/planner.py` → `engine/executor.py` → `engine/registry.py` | §1/§2/§3 | state_updates 契约与 resume 如何恢复;generate 路径为何**结构上**不可能含 write/push step。验证:`test_v2_p0.py`、`test_planner_playbooks.py`;动手:`--plan-only` |
| 3 agent 运行时 | `agent_runtime/runner.py` · `dispatch.py` · `agent_loop.py` · `tools.py`+`scopes.py` · `ensemble.py` · `moa.py` · `utils.py`+`knowledge.py`;略读 `llm.py`、`tracing.py` | §4 | prompt 静态前缀为何在前?"FINAL ROUND" 为何必须排在 tool_result 后?零产出 lens 为何单独重问而非整组重跑?验证:`test_agent_loop.py`、`test_agent_runtime.py`、`test_agent_ensemble.py` |
| 4 step 库 | 先 `engine/steps/_common.py`,再按支流选读(评审/issue/CI debug/rebase/publish/profile/report) | §5 | `pr/publish.py` 是全库唯一 risk=push 出口,必读;评审支流看 `_pr_time_checkout` 与 escalate 抢救 |
| 5 知识平面 | `profiles/store.py`(主菜)· `memory/skills.py` · `memory/debug_memory.py` · `adapters/base.py`;其余 `profiles/*` 略读 | §6/§2 | 三条注入面硬上限(350 词 / 1,500 / 4,000 字符);写入面为何只有类型化 patch op?candidate 为何必须人工晋升? |
| 6 安全闸 | `push.py` · 顶层 `review/` 三件套 | §7 | fail-closed:reviewer 无 LLM 返回 `unavailable` 时,推送门如何表现? |
| 7 MCP 面 | `mcp_policy.py` → `thin_mcp_server.py` → `mcp_server.py`+`run_status.py`;略读 `chat.py`、`ui.py` | §12 | policy 为何在边界与子进程各跑一次?多 server 并存为何不互抢对方的 `queued` run? |
| 8 汇与旁路 | `run_trace.py` · `metrics.py` · `notify.py` · `ci/` | §8 | 快速过;记住 run_trace 默认不进 prompt |

三个高效读法:

- **配对读护栏测试**:每读完一个模块,按 §10 对照表跑对应测试并读断言——
  它们是"可执行的文档"。
- **跑一次真实 run 对照产物**:按 §11 的命令先 `--plan-only` 看计划,再跑
  完整 run,把 `~/.infermatrix-copilot/runs/` 下的产物与 §3/§8 的代码对上。
- **改代码前先查 `SPEC/`**:那里写的是对应文件"什么不能破坏"。

## 附录:文件 → 段落(完整索引)

顶层 `infermatrix_copilot/`:`__init__.py`=包根 · `intent.py`§1 · `task_spec.py`§1 ·
`chat.py`§1 · `ui.py`§1 · `config.py`§3 · `agent_loop.py`§4 · `tools.py`§4/§7 ·
`scopes.py`§4/§7 · `llm.py`§4 · `tracing.py`§4 · `push.py`§7 · `run_trace.py`§8 ·
`metrics.py`§8 · `notify.py`§8 · `mcp_policy.py`§12 · `mcp_server.py`§12 ·
`thin_mcp_server.py`§12 · `knowledge_docs.py`§12 · `run_status.py`§12 ·
`__main__.py`§12。
`cli/`:`entry.py`(亦 §12)·`__main__.py`·`__init__.py`·`utils.py`·`doctor.py`§1;`copilot.py`§2(亦 §12)。
`adapters/`:`base.py`·`__init__.py`§2。
`playbooks/`:`store.py`·`__init__.py`§2。
`engine/`:`__init__.py`·`executor.py`·`step.py`·`registry.py`§3;`planner.py`§2。
`engine/agent_runtime/`:`__init__.py`·`runner.py`·`dispatch.py`·`utils.py`·
`knowledge.py`·`ensemble.py`·`moa.py`§4。
`engine/steps/`:`__init__.py`§3;`_common.py`·`workspace.py`·`issue.py`·
`report.py`·`rebase_ext.py`·`rebase_native.py`·`profile.py`§5。
`engine/steps/pr/`:`__init__.py`·`fetch.py`·`debug.py`·`utils.py`·`rebase.py`·
`publish.py`§5(`publish.py` 亦 §7)。
`engine/steps/review/`:`__init__.py`·`steps.py`·`prompts.py`·`utils.py`§5。
`memory/`:`__init__.py`·`debug_memory.py`·`skills.py`§6。
`profiles/`:`__init__.py`·`store.py`·`establish.py`·`consolidate.py`·
`repo_map.py`·`languages.py`§6。
`ci/`:`__init__.py`·`normalize.py`·`providers.py`§8。
`rebase/`:`__init__.py`·`monitor.py`§5。
`review/`(顶层 Patch Review):`__init__.py`·`diff_summary.py`·`triggers.py`·
`reviewer.py`§7;`planner.py`§5(审查深度)。
