---
title: "Agent loop / sub-agent workflow"
created: 2026-07-10
updated: 2026-07-23
type: guide
tags: [general, agents]
sources: []
---

# Agent loop / sub-agent workflow

**何时来翻**：用户明确要求 sub-agent / 并行 agent，或任务能拆成互不依赖的调查面。目标是降低等待和盲区，不是增加流程。

## 是否使用

适合使用：

- 多个代码路径、日志、artifact 或外部来源可以独立核对。
- 高风险 review 需要一个不继承主 agent 结论的只读视角。
- 长任务中有独立的验证、资料整理或兼容性调查可以并行完成。
- 非琐碎开发完成后，需要一个没参与实现的 reviewer 做交付前全量审查。

默认不用：

- 单文件小修、明确 reviewer follow-up、短解释或单条命令。
- scope 尚未收敛，拆分只会复制混乱。
- 多个 agent 会修改同一批文件，或子任务结果必须逐步依赖前一步。

上面的“默认不用”只限制实现阶段是否拆分工，不豁免非琐碎开发完成前的独立审查。明确 reviewer follow-up 可以由一个开发 agent 修，但修完仍要由没参与修复的视角复审当前完整改动。

不按文件数、步骤数或模型名称强制开 agent；由任务是否真的可独立决定。

## 最小委派合同

委派只需说明五件事：

1. 目标和范围。
2. 只读还是允许写入；允许写入时独占哪个目录或 worktree。
3. 需要返回的证据，例如文件行号、命令、日志或 artifact。
4. 哪些决定仍由主 agent 保留，例如扩大 scope、公开回复、commit 和 push。
5. 谁负责启动交付前独立审查。没有明确转交时，由发出委派的父 agent 负责，开发 sub-agent 不自行再拉 reviewer。

不要把未经验证的 root-cause 猜测写成子任务结论。可以限定对象，不能要求“证明 X 就是原因”。

主 agent 已用 live 证据确认开发 owner 时，委派合同直接附上 `根入口 + code taste + 仓库硬门禁 + owner 命中规则 → 第一批源码函数`。sub-agent 只读这些精确段落一次，然后从源码开始；不再读 discovery 索引、未命中的 planning/review guide 或同级 owner。只有实验目标本身是测量路由发现能力时才故意省略这份开发包，并在结果中把路由时间单独计算。

## 所有权与证据

- 只读 agent 可以共享 checkout；写入 agent 必须隔离目录、worktree 或明确文件所有权。
- 公共 PR body/comment、commit、push、merge 等外部动作只有一个 owner。
- 主 agent 必须复核关键引用；sub-agent 的 `OK` 不能替代测试、live diff、benchmark 或 artifact provenance。
- 子任务发现相邻问题时先作为 out-of-scope note 返回，不顺手扩大当前任务。

### 独立审查只由一个负责人安排

- 每个基线和当前完整 diff 只能有一个 agent 负责安排独立审查。开发任务由父 agent 委派时，默认由父 agent 负责；只有委派合同明确写明“开发者负责审查闭环”时，开发 sub-agent 才能启动 reviewer。根 agent 自己开发且没有上层调度者时，由根 agent 负责。
- 父 agent 负责审查时，开发 sub-agent 完成实现、最小验证和反证扫描后立即记录 `AUTHOR_COMPLETE`，返回 diff、测试、未验证边界和自发现问题，并标记“待父 agent 独立审查”。它不得读取完整 review guide、生成正式 review report、启动嵌套 reviewer，或等待 reviewer 后再改写 author 完成时间。
- 审查负责人只启动一次与风险匹配的审查：普通窄修改一个 reviewer，高风险任务才按下文拆成两个正交 reviewer。相同基线、相同 diff 已有一份合格独立审查且代码未改变时直接复用，不再以“更保险”为由重复全量审查。
- 只有新增了不同风险面并能说清专项合同，才增加专项 reviewer；例如安全审计和 GPU 实测不是同一职责。必须分别记录目的和耗时，不能把两个宽泛 review 伪装成正交审查。
- reviewer 提出问题并发生代码修改后，仍由同一个审查负责人安排复审当前完整 diff。所有 checker、review report 和最终 clean 判定也由审查负责人负责，不下沉给开发 worker 重复执行。

## 开发阶段耗时记录

非琐碎开发和框架效率实验使用实际时钟记录下面八个时间点：

```text
任务开始：
owner 锁定：
首次有效代码、测试或目标文档落盘：
首次目标测试：
开发完成（`AUTHOR_COMPLETE`，reviewer 启动前）：
独立 review 开始：
独立 review 完成：
最终完成：
```

报告时分别计算路由、编码、验证、review 等待、review 执行和 review 修复时间，不只给一个总耗时。纯开发时间固定截止 `AUTHOR_COMPLETE`；reviewer 排队、spawn、读取和审查不得混入开发分母，review 后没有代码变化时也不能重写这个时间点。没有可靠时间戳的阶段写 `unknown`，不能根据文件数量或聊天体感补时间。TODO、注释、纯格式、占位测试和空骨架不记为首次有效落盘。owner 已锁定且 live source 可读时，开发 agent 不为“更完整地了解仓库”继续横向读文档；五分钟首次落盘门禁和允许扩展的阻塞条件见根 `CLAUDE.md`。

## 框架规则迭代怎么验收

因为一次 AI 漏检而修改本框架时，发布前至少重跑同一个冻结任务和一个不同类型的 control；不能只证明新增规则会背出已知答案。实验开始前固定基线、任务输入、允许知识和评分表，并分别报告：首次有效落盘、开发时间、review 时间、真实问题召回、错误 P1、默认路径回归和端到端时间。

最低目标是首次有效落盘不超过五分钟、窄 bug 开发时间不比同模型裸基线慢超过 15%、错误 P1 为零，并且 control 不劣化。没有裸基线时只报告绝对时间，不编造提升比例。提高检查项数量或报告长度不算正确率提升；只有更早发现真实问题且不新增错误 blocker 才算优化有效。

## 开发交付的维护者审查闭环

适用于非琐碎的业务代码、测试、公开接口、配置、CLI 或模型适配。目标不是让 reviewer 说句“看起来可以”，而是在交给真实 maintainer 前消掉会阻止合并的问题。

窄 bug 先完成一个十五分钟内的生产纵向切片：前三分钟锁 owner、复现和官方入口，随后约七分钟修改真实 owner 路径，再留三分钟跑最小目标测试和默认或相邻 control，最后两分钟做反证扫描。先证明生产影响面，再扩测试；同一种语义在多个模块重复时只选代表 consumer 测试，不按模块数量堆矩阵。十五分钟是首个可验证切片的上限，不是复杂任务的总预算；只有真实运行或对齐证据仍有残余差异，才进入对应的 compatibility、precision、runtime 或 remote 组继续调查。

开发 agent 在交给独立 reviewer 前，窄 bug 留两分钟、高风险任务最多四分钟做一次**反证扫描**。这不是再读一轮规则或 review guide，只沿当前 diff 和已经打开的 live source 找会推翻“可以交付”的证据：

1. **公开入口：** 列出受影响行为的真实 dispatcher，确认每条入口都在 decode、load、网络或 GPU 等昂贵操作前执行同一 owner 合同；不能用一个 helper 被另一条入口调用来代替。
2. **精确 consumer 反查：** diff 改变共享字段的类型、默认值、sentinel 或“是否提供”语义时，只取 diff 中真实改变的字段名，在生产代码内做最多两次、总计不超过九十秒的精确引用搜索；只检查赋默认值、truthiness、fallback、alias 和已注册 consumer。命中其他模块不触发文档或规则扩读，确认需要修改时才打开源码。局部实现或搜索没有新 consumer 时立即停止，不能扩大成全仓库审计。
3. **数量和形状：** 把最小、最大、超界以及一个异构/ragged 样例走到第一处 `stack`、`concat`、索引或 batch reshape；只测 helper 的数量判断不算完成。
4. **阶段状态：** 涉及多阶段或 online/offline 时，逐阶段核对 seed、sampling、system/task 和中间产物没有在 dispatcher 或 adapter 处丢失。
5. **不受影响路径：** 修改 shared serving、协议或通用 adapter 时，至少跟一条其他 owner 或 legacy fallback 从入口走到旧 consumer，证明新列表、默认值和错误处理没有改变它。

精确 consumer 反查必须在扩充测试矩阵前完成。扫描发现问题就先修再自测；时间到点仍有关键链路未知时，把具体未知量标为 `implementation draft` 交给 reviewer，不能用更多搜索、stub、lint、compile 或“另一条入口正常”冒充完成。反证扫描结果不喂给盲审 reviewer；reviewer 仍从任务合同、owner 规则和完整 diff 独立判断。

1. 开发 agent 完成实现、目标测试和自审，记录 `AUTHOR_COMPLETE`，但此时只能说“待独立审查”。父 agent 默认负责安排审查；开发 sub-agent 返回交接后停止，不自行嵌套 reviewer。
2. 审查负责人换一个没参与设计和编码的 reviewer。它只读用户要求、本轮确认的仓库规则、基线、当前完整 diff，以及绑定当前基线和 changed surfaces 的 canonical mini spec/编码前 contract matrix；后者是允许核对的设计合同，不等于允许继承作者的根因假设、自审结论或“重点帮我看 X”。记录不存在时 reviewer 明确报 `MISSING_EVIDENCE`，不能在 review 阶段代写。先提供主要 owner 的 `rules.md`；只有 live producer-consumer trace 跨越其他 owner 时才沿调用链补充每个实际 owner 的规则，incidents/history 不作为盲审默认输入。
   高风险任务才同时启动两个只读 reviewer，且职责必须正交：语义 reviewer 负责官方入口、token、stop、sampling、精度和模型语义；集成 reviewer 负责默认 CLI、真实 topology、public ingress、资源可用性、online/offline 和 unaffected control。两者墙钟时间取最大值而不是相加，输入的基线、diff、owner 和任务合同相同，不能互看结果，也不能都做一遍宽泛 producer→consumer 扫描。普通窄修改只用一个 reviewer。
3. reviewer 按 [独立审查执行合同](../../review/guides/review-execution-contract.md) 分两轮审：owner 定义触发组时先选择 `core` 加当前 diff 命中的组并完整枚举组内稳定 ID；没有组时才全量枚举该 owner。逐条判定 `PASS / FAIL / MISSING_EVIDENCE / NOT_APPLICABLE`，填写当前可达入口和 changed-value producer→consumer 表，再按 [全量 diff 审查](../../review/guides/reviewer-lens-gates.md#full-diff-review) 查 duplication、layering、edge cases 和 surface area。新的 blocking finding 必须完成 `DIFF / PATH / CONTRACT / FAILURE / COUNTEREVIDENCE / FIX` 六项证明；证据不足的架构怀疑写调查 note，不能用来制造 `FAIL`。
4. 语气可以像强硬的项目 owner：直接、不放水、不接受假证据；但只评代码和证据，不攻击人。
5. 原开发者在原实现工作区修复 P0/P1/P2；写入 agent 继续遵守已约定的隔离目录、worktree 或文件所有权边界。P2 表示低严重度但仍需修复的实质问题；纯样式 nit 单列且不阻止完成，不能把维护问题降级成 nit。
6. 修复后由 reviewer 重新审查当前完整 diff，既检查旧 finding 是否真正关闭，也查修复引入的新问题。只关闭旧问题不等于全量复审。
7. 审查负责人把 reviewer 输出保存为 Markdown，并按执行合同运行 `python tools/check_review_report.py --report <review.md> --rules <stable-owner-rules.md> --legacy-rules <legacy-owner-rules.md>`；checker 验证所选触发组及组内覆盖，审查负责人仍要核对组是否选对、finding 六项证据是否真实。最终交付再加 `--require-clean`。只有结构通过、所选规则 `0 FAIL / 0 MISSING_EVIDENCE` 且开放审查 `0 P0 / 0 P1 / 0 P2` 才能完成。正式测试被依赖、模型、硬件或环境阻塞且没有等价证据时，才标记 `implementation draft`；不能用 lint、compile、mock 冒充行为证据。

审查 prompt 的通用维度见 [reviewer lens prompt](../../review/guides/reviewer-lens-prompt.md)，如何避免把作者偏见传给 reviewer 见 [review delegation](review-delegation-framing.md)。

当前环境没有独立 agent 能力时，仍要按同一维度做一次新鲜全 diff 自审，并明确报告“未经独立 reviewer”；不能声称已经通过独立维护者审查。

## 停止条件

出现以下任一情况就收回主线程判断：

- 证据互相冲突。
- 子任务开始依赖未验证的前置结论。
- 多个 agent 触碰同一写入面。
- 连续尝试没有产生新证据。
- 继续推进需要用户授权或会扩大任务范围。

长跑、远端 GPU、benchmark 的预算和 watchdog 仍由对应场景 runbook 管理，不在这里重复定义。
