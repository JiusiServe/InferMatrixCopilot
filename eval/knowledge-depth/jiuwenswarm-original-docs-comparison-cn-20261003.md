# JiuwenSwarm 原项目文档与当前知识库对比报告

生成时间：2026-10-03T04:23:27.746695+08:00（北京时间）。源码知识基线：`f0a69728c96b5961d993449f1a901cbd2f4dac5b`；当前知识内容为 PR #290 已合并版本。

实际知识 checkout 为 `58279d334cd827adb631891a760bb14efe376420`；PR #290 合并提交为 `2ce6068a065712d0c71da2067844506ed8dbf3d9`。checkout、文档逐文件哈希和评估运行版本分别归档。

当前知识库在功能组织、源码关联和可审计性方面更完整；原资料保留了作者的设计意图、被拒绝方案、完整使用手册和维护风险，两者都能为评审提供有价值的上下文。
当前认可 **552/553（99.82%）**；原作者正文在本次有界映射中提供 **361/553（65.28%）** 项说明。两项统计的依据不同，不能将其差额直接解释为新增正确知识。

实测状态：**completed_with_failures**；72 个计划评审中已有 72 个终态结果、55 个有效评审、55 个完成独立评分。

全体有效完成率：A 30/36、B 25/36。判断质量以已评分有效评审为条件，须同时考虑失败和未交付；本轮不会修正失败回复后重新评分。

主样本有效完成率 A 87.50%、B 62.50%。已评分有效评审中：缺陷评论精确率 A 69.12%、B 76.76%，B−A 为 +7.64 个百分点（共同适用 6 PR）；已确认问题召回率 A 100.00%、B 100.00%，B−A 为 +0.00 个百分点（共同适用 2 PR）。成对原生耗时均值 A 426.33 秒、B 416.77 秒（15 对重复，8 PR）。有效评审的原生耗时 P50 为 A 460.81 秒、B 421.98 秒，两组有效样本可能不同。耗时包含限流和工具等待，本轮不能认定整体评审收益或因果加速。结果来自 8 个所选 PR，不能推广为全项目准确率。

## 内容与覆盖

| 指标 | 原项目作者资料 | 当前知识库 | 统计含义 |
| --- | ---: | ---: | --- |
| Markdown 库存 | 488 | 744 | 文档数不是知识数；包含不同语言及不同粒度 |
| 功能与原文档关联 | 79/79，55 篇不同文档 | 沿用这些原文档并结合源码 | 文件存在或目录关联，不证明正文充分说明 |
| 七维正文映射/认可 | 支持 361、冲突 18、未知 174 | 认可 552、未知 1 | 原正文映射与当前认可流程分别展示 |
| 解释性正文明确引用生产文件 | 49/2199（2.23%） | 364/2199（16.55%） | 相同保守解析规则的引用下界；排除扫描清单与机器卡片 |
| 生产文件结构覆盖 | 无同口径审计，无法比较 | 2043/2199（92.91%） | 结构卡片覆盖，不是整个文件的行为验证 |
| 深度知识的生产文件证据 | 无同口径审计，无法比较 | 205 个文件 | 已使用的源码证明文件，不是结构覆盖分母 |

| 维度 | 原正文支持 | 原正文冲突 | 原正文未知 | 当前认可 |
| --- | ---: | ---: | ---: | ---: |
| 执行流程 | 65/79 | 4 | 10 | 79/79 |
| API 契约 | 53/79 | 2 | 24 | 79/79 |
| 配置与默认行为 | 49/79 | 9 | 21 | 79/79 |
| 依赖与关联功能 | 68/79 | 1 | 10 | 79/79 |
| 失败与降级行为 | 53/79 | 2 | 24 | 79/79 |
| 设计取舍 | 40/79 | 0 | 39 | 78/79 |
| 验证与测试入口 | 33/79 | 0 | 46 | 79/79 |

当前 552 项包括严格认可 207 项和轻量认可 345 项，均为 supported，verified_absent 为零。唯一未知是 `im-feishu / 设计取舍`，不能据此声称飞书功能或测试不存在。
79 个功能均有深度说明，78 个功能七维齐全。一个维度认可表示至少有一段可用解释；代表流程或单个 API 契约不能证明该功能的所有分支、接口或文件均已解释。
原文档映射每个功能一次独立 Codex 调用；只计入实际解释该功能的原作者行段。候选段落有预算，未知包含未检索到、内容不足、引用不合法和读取失败，不能解释为项目没有相关知识。
原作者库存 488 篇包含 313 篇维护资料、143 篇主 docs 和 32 篇嵌套开发指南。本次去重识别 144 张符号卡片，集中在 4 个生产文件，其中作者元数据标为 agent_audited 61、unaudited 80、audit_expired 3；这些是作者历史标签，未审计正文仍可能有价值，也不能作为当前实现的认可证明。
维护资料的 [README 历史库存](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/README.md#L19) 与 [build-plan 账本](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/project/build-plan.md#L30) 使用 1,275 文件、15,584 符号的旧范围；扫描库存和符号卡片数量不等于本报告的生产文件解释覆盖。
每功能映射最多提供 24,000 字符作者正文和 16,000 字符源码候选，仅 15/79 个功能的候选正文全部送入，因此原资料的解释数是有界审计结果。初次整体格式校验只有 19/79 通过；随后对既有 79 份答复确定性重放，允许原文空行连接，不增加模型调用或声明。仍不合法的 7 个维度保持未知。
这次原资料映射的完整 CLI 流未全部保存；精确输入、原始答复、哈希及已报告用量保留。后续 PR A/B 则保存完整原生流和工具记录，两者不混算。
原正文与固定实现的一致性另计：89 项得到所提供源码支持，12 项冲突，其余 452 项无法确认。无法确认不等于过时。正文映射的 18 项 conflict 包括作者资料内部矛盾，并非 18 个已证明的实现缺陷。
源码一致性只核查实际提供的候选实现段落；候选来自当前知识的生产源码证明路径，不包含完整测试源码。89/12/452 不能视为原资料全库新鲜度测量，也不能与当前 552 项认可直接作正确率比较。

## 双方内容的价值与时效性

原资料的 [AgentServer 预热会话 ADR](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/decisions/ADR-0001-agentserver-owned-prewarmed-sessions.md) 记录决策、后果和被拒绝方案，适合判断 PR 是否违背作者意图。原维护资料还集中保留 AgentServer 风险、审计状态与健康维度；这些内容不能被一个七维计数替代。
当前知识库按 owner 和功能整理代表流程、API 义务、配置默认值、失败分支及源码引用，便于评审定位入口。轻量认可允许明确标注的推断；这与原作者明确陈述的设计理由分别呈现。

| 内容 | 原作者资料的具体价值 | 当前知识的具体价值及评审用途 |
| --- | --- | --- |
| 架构 | [Runtime Session 参考链](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/project/flows/runtime-session-reference-chain.md) 解释迁移边界 | 按 owner 组织入口与下游，附固定源码和认可记录，便于回查实现 |
| 流程 | [Skill 自演进指南](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Skill%E8%87%AA%E6%BC%94%E8%BF%9B.md#L92) 解释用户发起与审批过程 | [Skill 深读](https://github.com/JiusiServe/InferMatrixCopilot/blob/58279d334cd827adb631891a760bb14efe376420/knowledge/repos/jiuwenswarm/components/agent-server-runtime/feature-depth-skill-evolution.md) 补充 no_evolution_no_records 分支的返回映射 |
| API | 同一指南给出 `/evolve <skill_name> [user_intent]` 及提案义务 | [Cron 深读](https://github.com/JiusiServe/InferMatrixCopilot/blob/58279d334cd827adb631891a760bb14efe376420/knowledge/repos/jiuwenswarm/components/cron-scheduling/feature-depth-cron.md) 明确 update_job 空 id 与任务不存在时的异常契约 |
| 配置 | [配置信息](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%85%8D%E7%BD%AE%E4%BF%A1%E6%81%AF.md) 提供用户配置操作 | Cron 深读说明默认 file、仅显式 etcd 生效及空 endpoints 不回落 file，帮助识别错误默认假设 |
| 依赖 | [A2A 指南](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/A2A.md#L24) 解释入站链路、SDK 和服务边界 | Cron 深读定位 mod_revision 条件写与 EtcdError 包装，帮助检查并发更新 |
| 失败行为 | 使用与维护文档保留故障提示及恢复指南 | Cron 的 CAS 单次重试、Skill 超时读取失败的 fallback，都有具体实现引用 |
| 设计取舍 | 预热会话 ADR 有作者明确意图和被否决方案 | Cron 默认后端与 Skill watcher 代价明确标注为设计推断，不代替作者意图 |
| 验证入口 | 测试、SDK 和客户端资料有完整操作指南 | Cron 表达式与文件锁断言、Skill helper 断言定位精确，并明确不是本次测试执行结果 |

原资料也存在局部不同步：较早的 [架构说明](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/project/architecture.md) 与较新的 [Runtime 会话参考链](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/project/flows/runtime-session-reference-chain.md) 对 AgentServer 迁移状态的表述不同。文档日期、源码版本和实际声明需逐项检查，不能用一次最后提交时间判定全部内容新鲜。
具体默认值冲突：[企业微信指南](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%9B%BD%E5%86%85%E9%A2%91%E9%81%93.md#L564) 写 `send_thinking_message` 默认 false，但固定版本的 [WecomConfig](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wecom/wecom_connect.py#L55) 定义为 True。评审若只沿用文档默认值，会误判新增配置或调用行为。
原维护资料标为 partial；历史 ledger 的符号审计分母和统计日期与本报告不同。历史的 trusted/expired 数字不作为当前源码上的正确率。

| 时效性证据 | 原作者资料 | 当前知识库 |
| --- | --- | --- |
| 文档/记录日期 | README 为 2026-08-01，manifest 为 2026-09-08，部分流程为 2026-09-11；不代表所有正文同日复核 | 本轮深度补齐于 2026-10-02，报告于 2026-10-03 复核 |
| 声明版本 | 旧扫描记录仍声明 7 月版本 10afedf2，部分正文无可确认实现版本 | 生效深度区块绑定完整 f0a69728 SHA、引用哈希及严格/轻量认可记录 |
| 与源码一致性 | 有界核查 89 支持、12 冲突、452 未知 | 552 项通过已有固定版本审计；未来 PR 仍须重新验证受影响声明 |

本报告固定知识在 f0a69728；它不能自动保证对后来 PR 头部仍然有效。评审必须回到冻结 PR 源码验证。
交付核查的 develop 为 `f0a69728c96b5961d993449f1a901cbd2f4dac5b`，核查时间 2026-10-03T04:18:42.485781+08:00；相对知识基线的新增提交数为 0、基线独有提交数为 0，变更生产文件数为 0。受影响功能：无。

develop 变更生产文件数仅按固定 2199 文件库存统计；新增文件另见配套 JSON 的 changed_paths。一次观测无提交差距不代表持续实时更新。
验证维度有内容不等于运行时测试覆盖：当前分类包括 27 个运行时测试入口、1 个源码文本断言、14 个辅助函数测试、9 个文档手工验证入口和 28 个历史未分类区块。本轮 PR 评审是只读实验，没有执行 JiuwenSwarm 上游测试，也没有把作者历史测试通过的声明当成本轮通过。

## GLM‑5.3 PR 评审实测

A 组只检索原作者资料；B 组只检索当前 JiuwenSwarm 知识库。两组使用相同冻结源码、提示词、检索算法、两页初始检索和 6000 字符累计知识预算。后续搜索和读取扣除余量。并发 13，共享排期；每评审最多 60 次源码调用，每次结果最多 24,000 字符，原生超时 30 分钟。
模型配置冻结为 Zcode 订阅 GLM‑5.3、请求 reasoning=max；有效 reasoning 档位未由服务报告时保持未知。逐调用核查 served model 和订阅 provider，身份不符属于失败，不切换模型。
独立评分请求 Codex gpt-6-sol/medium；原生记录未报告实际 served model，该字段保持未知。GLM 的实际 served model 与订阅 provider 已逐调用验证，两个通道的身份信息分别归档。
12 PR × 两组 × 三重复，共 72 个评审。GitHub 的目标分支 SHA 与 PR 实际 diff 基线分开记录；diff 使用真实 merge-base→head，不将目标分支的历史变化当作 PR 修改。
8 个直接基于 f0a69728 的 PR 为主样本；#7639、#7654、#7655、#7656 从较旧提交分叉，且头部提交早于知识基线，只作探索性对照。其知识可能描述较新的目标分支实现，不能混同为无时间泄漏的前瞻准确率。
主样本均为 2–4 文件的后端修复，涉及 cron、MCP、权限、hooks、gateway、agent-mode、runtime 和输出截断。52 文件的大型研究工作台（含前端改动）在旧分叉 #7639；主样本不足以代表大型功能或前端评审。
独立 Codex 在正式 GLM 评审前冻结确认问题；随后对匿名、随机顺序的评论核验。只有新增或加重且有源码证据的缺陷计 TP；证实不成立计 FP；证据不足计 unknown。风格、文档和其他建议另计有效性。召回仅指对自动独立审计已确认问题的召回，无法覆盖全部真实缺陷。

盲评输入移除 A/B 标签、重复序号和文档来源路径，评分入口不能访问来源映射；措辞或内容风格仍可能提供来源线索，不能保证绝对无法辨识。

| 冻结样本 | PR 内容 | 变更文件数 | 分组 |
| --- | --- | ---: | --- |
| #7639 | feat: add auditable research workbench and native offline paper workflow | 52 | 旧分叉探索 |
| #7641 | fix(cron): reject nonexistent local times for one-shot reminders | 2 | 主样本 |
| #7642 | fix(mcp): confine credential files to storage directory | 2 | 主样本 |
| #7645 | fix(security): enforce session ownership checks in control endpoints (#4987) | 4 | 主样本 |
| #7647 | fix(hooks): run user-configured hooks for sub-agent tool calls (#4999) | 3 | 主样本 |
| #7649 | fix(gateway): clear cancelled flag on rid reuse to prevent response drop (#4940) | 2 | 主样本 |
| #7650 | fix(agent-mode): register code_agent subagent when enabled in config (#4892) | 2 | 主样本 |
| #7651 | fix(runtime): ignore invalid stored session mode tags at read time (#4903) | 2 | 主样本 |
| #7654 | feat(swarm): opt-in scientific verification rail for research outputs (#4982) | 6 | 旧分叉探索 |
| #7655 | feat(memory): MemoryIndexManager.search_claims — deterministic ledger retrieval (#4983) | 2 | 旧分叉探索 |
| #7656 | feat(swarm): reviewer-feedback evolution journal — append-only attribution audit (#4984) | 3 | 旧分叉探索 |
| #7675 | fix(rails): report a model response cut short at the output-token cap | 2 | 主样本 |

源码基准审计成功 11/12，未知 PR 为 [7656]。#7656 的原答复缺少现有源码的基线证据，未重抽样；它的确认问题数和召回率保持未知。主样本只在 #7647、#7649 确认各一个问题，主样本召回率最多有 2 个适用 PR，应谨慎解读。

### 主样本：8 PR / 48 次

| 指标（先 PR 内有效重复均值，再按 PR 平均） | A 原资料 | B 当前知识 |
| --- | ---: | ---: |
| 缺陷评论精确率 | 64.34%（适用 8 PR） | 76.76%（适用 6 PR） |
| 已确认问题召回率 | 100.00%（适用 2 PR） | 100.00%（适用 2 PR） |
| 非缺陷建议有效率 | 97.92%（适用 8 PR） | 100.00%（适用 8 PR） |
| 已完成独立评分 / 有效评审 | 21/21 | 15/15 |
| 缺陷判断中的未知比例 | 15.69% | 10.71% |
| 有效缺陷评论 | 23 | 15 |
| 误报 | 20 | 10 |
| 未知缺陷判断 | 8 | 3 |
| 非缺陷建议 | 34 | 31 |
| 有效且可操作的建议 | 33 | 31 |
| 有效性未知的建议 | 0 | 0 |
| 新发现有效缺陷（不回填召回基准） | 19 | 13 |
| 原生耗时 | P50 460.81 秒 / P90 499.57 秒，n=21 | P50 421.98 秒 / P90 487.16 秒，n=15 |
| worker 内排期等待 | P50 267.96 秒 / P90 982.28 秒，n=21 | P50 153.75 秒 / P90 891.41 秒，n=15 |
| 端到端耗时 | P50 796.59 秒 / P90 1395.67 秒，n=21 | P50 591.00 秒 / P90 1335.40 秒，n=15 |
| 有效评审 / 计划评审 | 21/24 | 15/24 |

两组各自适用 PR 可能不同，以上条件宏平均不直接作因果差异。共同适用的 PR 对照如下：

| 共同适用 PR 的指标 | A | B | B−A | PR 数 |
| --- | ---: | ---: | ---: | ---: |
| 缺陷评论精确率 | 69.12% | 76.76% | +7.64 个百分点 | 6 |
| 已确认问题召回率 | 100.00% | 100.00% | +0.00 个百分点 | 2 |
| 建议有效率 | 97.92% | 100.00% | +2.08 个百分点 | 8 |

| 同一 PR/重复均有效的耗时（先 PR 内均值，再 PR 均值） | A | B | B−A | PR / 成对重复数 |
| --- | ---: | ---: | ---: | ---: |
| 原生评审 | 426.33 秒 | 416.77 秒 | -9.56 秒 | 8 / 15 |
| worker 内等待 | 464.91 秒 | 287.21 秒 | -177.70 秒 | 8 / 15 |
| 端到端 | 898.78 秒 | 712.46 秒 | -186.32 秒 | 8 / 15 |

耗时成对比较仍只覆盖双方均成功的试次；限流、工具等待与运行次序会影响观察差，不是纯知识处理速度或因果加速估计。

### 旧分叉探索：4 PR / 24 次

| 指标（先 PR 内有效重复均值，再按 PR 平均） | A 原资料 | B 当前知识 |
| --- | ---: | ---: |
| 缺陷评论精确率 | 100.00%（适用 4 PR） | 90.62%（适用 4 PR） |
| 已确认问题召回率 | 50.00%（适用 3 PR） | 44.44%（适用 3 PR） |
| 非缺陷建议有效率 | 100.00%（适用 4 PR） | 100.00%（适用 4 PR） |
| 已完成独立评分 / 有效评审 | 9/9 | 10/10 |
| 缺陷判断中的未知比例 | 20.69% | 0.00% |
| 有效缺陷评论 | 23 | 34 |
| 误报 | 0 | 3 |
| 未知缺陷判断 | 6 | 0 |
| 非缺陷建议 | 17 | 18 |
| 有效且可操作的建议 | 17 | 17 |
| 有效性未知的建议 | 0 | 1 |
| 新发现有效缺陷（不回填召回基准） | 未知 | 未知 |
| 原生耗时 | P50 485.33 秒 / P90 552.38 秒，n=9 | P50 472.01 秒 / P90 562.42 秒，n=10 |
| worker 内排期等待 | P50 300.93 秒 / P90 498.40 秒，n=9 | P50 239.10 秒 / P90 603.11 秒，n=10 |
| 端到端耗时 | P50 752.29 秒 / P90 1017.68 秒，n=9 | P50 718.10 秒 / P90 1067.05 秒，n=10 |
| 有效评审 / 计划评审 | 9/12 | 10/12 |

两组各自适用 PR 可能不同，以上条件宏平均不直接作因果差异。共同适用的 PR 对照如下：

| 共同适用 PR 的指标 | A | B | B−A | PR 数 |
| --- | ---: | ---: | ---: | ---: |
| 缺陷评论精确率 | 100.00% | 90.62% | -9.38 个百分点 | 4 |
| 已确认问题召回率 | 50.00% | 44.44% | -5.56 个百分点 | 3 |
| 建议有效率 | 100.00% | 100.00% | +0.00 个百分点 | 4 |

| 同一 PR/重复均有效的耗时（先 PR 内均值，再 PR 均值） | A | B | B−A | PR / 成对重复数 |
| --- | ---: | ---: | ---: | ---: |
| 原生评审 | 461.64 秒 | 441.57 秒 | -20.07 秒 | 3 / 8 |
| worker 内等待 | 319.94 秒 | 388.53 秒 | 68.59 秒 | 3 / 8 |
| 端到端 | 786.88 秒 | 836.28 秒 | 49.40 秒 | 3 / 8 |

耗时成对比较仍只覆盖双方均成功的试次；限流、工具等待与运行次序会影响观察差，不是纯知识处理速度或因果加速估计。

评论数按每次评审的根因去重，三次重复仍是三个观测，不称作不同缺陷总数。未知比例为 unknown/(TP+FP+unknown)，非缺陷建议不进入该分母。精确率排除未知，须结合未知比例和完成率阅读。

### 失败归因

| 冻结运行的失败原因 | A | B |
| --- | ---: | ---: |
| `directory_trailing_slash_protocol_rejection` | 0 | 3 |
| `incomplete_prompt` | 0 | 1 |
| `output_schema_or_contract_rejected` | 5 | 7 |
| `unknown_bridge_protocol` | 1 | 0 |

原因标签可在同一失败评审中并存，不能将这一表直接相加当作失败总数。失败评审不进入缺陷评论准确率，仍计入完成率。

### 速度、完成率与实际注入

| 指标 | A 原资料 | B 当前知识 |
| --- | ---: | ---: |
| 原生评审耗时 | P50 467.29 秒 / P90 530.45 秒，n=30 | P50 437.15 秒 / P90 544.17 秒，n=25 |
| worker 内排期等待 | P50 284.45 秒 / P90 954.74 秒，n=30 | P50 222.33 秒 / P90 838.20 秒，n=25 |
| 初始知识检索耗时 | P50 2.96 秒 / P90 10.59 秒，n=30 | P50 3.92 秒 / P90 12.60 秒，n=25 |
| 每评审端到端耗时 | P50 774.44 秒 / P90 1348.73 秒，n=30 | P50 649.03 秒 / P90 1239.18 秒，n=25 |
| 有效评审数 / 36 | 30 | 25 |
| 终态失败数 | 6 | 11 |
| 实际原生调用次数（含传输重试） | 36 | 36 |
| 已报告输入 token 小计 | 47854615（未报告 0 次） | 43253107（未报告 0 次） |
| 已报告输出 token 小计 | 996997（未报告 0 次） | 949660（未报告 0 次） |
| 已报告 cache 读取 token 小计 | 未知（未报告 36 次） | 未知（未报告 36 次） |
| 初始实际注入字符均值 | 5018.83 | 5036.08 |
| 累计实际知识字符均值 | 5018.83 | 5036.08 |
| 后续补读/搜索字符均值 | 0.00 | 0.00 |
| 观测到 429 的评审数 | 8 | 3 |
| 去重后的 429 通知 | 26 | 7 |
| 原生 CLI 内部退避记录 | 26 | 7 |
| 源码/计算工具累计调用 P50（含失败评审） | 22.00 | 22.00 |

当前知识组初始每次完整注入的功能×维度区块均值为 6.25，片段区块均值为 0.00；所选页面可用区块均值为 12.25（跨页面累计，同一维度可涉及多个功能）。只按实际正文匹配计算完整注入，库存 552 项并非全部进入模型。原作者页没有 kb:depth 标记，不能把其标记数为零解释为没有知识。
速度表列出有效评审；失败、超时和额外尝试保留在完成率及配套 JSON 中，不删除较慢或失败样本。排期等待从 worker 开始计算，不包含尚未获得 worker 的排队；表中端到端也从 worker 进入评审函数计到终态。逐任务的提交到退出总耗时及完整池内排队未记录，保持未知。P90 使用线性插值。知识库存、初始实际注入及后续工具读取分别记录。
6000 字符按知识正文和后续搜索片段累计；导航元数据、PR diff、源码工具输出及协议提示词另记输入 token。原生耗时是 CLI 执行时间，包含工具读写和服务内部退避，不等同于纯推理时间。
订阅服务的 HTTP429 可触发 Zcode 内部请求退避，观测 maxAttempts 为 11；这是原生请求重试，与最多一次外层 CLI 传输重试分开。共享排期初始间隔 15 秒、限流冷却 90 秒，可放缓到 60 秒。请求的退避延迟不是测得的等待时间，排队延迟不能归因于检索质量。
实际 CLI 并发峰值为 9，完整区间数为 72；缺失区间时仅为下界。全批次从首次原生启动到最后退出的时间为 4821.85 秒，不含准备与独立评分。
冻结协议的失败归因另列在 JSON 中：目录尾斜杠兼容问题、未读完整输入、输出格式、真实边界拒绝和无法判断分别记录。`source_grep(path="tests/")` 曾被误判为违规，该次属于工具格式失败，不计缺陷误报；未重新抽样或事后改写原生结果。
收益判断以成对 PR 结果为准，不预设当前知识组一定更准或更快。只取短样本或只比较提取速度不能支持 PR 评审加速结论。

### 逐 PR 结果

| PR | 类型 | 确认缺陷数 | A 精确率 / 确认召回 | B 精确率 / 确认召回 | A/B 已评分重复 |
| --- | --- | ---: | --- | --- | --- |
| [#7639](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7639) | 旧分叉探索 | 3 | 100.00% / 0.00% | 100.00% / 0.00% | 1/2 |
| [#7641](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7641) | 主样本 | 0 | 100.00% / 不可计算 | 100.00% / 不可计算 | 3/3 |
| [#7642](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7642) | 主样本 | 0 | 66.67% / 不可计算 | 83.33% / 不可计算 | 3/2 |
| [#7645](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7645) | 主样本 | 0 | 21.67% / 不可计算 | 35.56% / 不可计算 | 3/3 |
| [#7647](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7647) | 主样本 | 1 | 70.83% / 100.00% | 66.67% / 100.00% | 2/1 |
| [#7649](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7649) | 主样本 | 1 | 100.00% / 100.00% | 100.00% / 100.00% | 2/1 |
| [#7650](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7650) | 主样本 | 0 | 100.00% / 不可计算 | 不可计算 / 不可计算 | 2/1 |
| [#7651](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7651) | 主样本 | 0 | 0.00% / 不可计算 | 不可计算 / 不可计算 | 3/2 |
| [#7654](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7654) | 旧分叉探索 | 2 | 100.00% / 50.00% | 100.00% / 33.33% | 3/3 |
| [#7655](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7655) | 旧分叉探索 | 1 | 100.00% / 100.00% | 62.50% / 100.00% | 2/2 |
| [#7656](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7656) | 旧分叉探索 | 未知 | 100.00% / 不可计算 | 100.00% / 不可计算 | 3/3 |
| [#7675](https://github.com/openJiuwen-ai/jiuwenswarm/pull/7675) | 主样本 | 0 | 55.56% / 不可计算 | 75.00% / 不可计算 | 3/2 |

没有确认缺陷时，召回为不可计算；不将其视为 100%，也不据此认定 PR 无缺陷。新确认发现单列，不回填本轮基准。

## 提取耗时、验收与复查

此前补齐 63 项的知识提取记录含 63 次 GLM 调用、63 次 Codex 调用。GLM 原生提取 P50 为 66.45 秒、P90 为 91.71 秒；这些是知识提取耗时，不是上面的 PR 评审速度。
实际账单金额未知。订阅验证通过不代表没有费用；缺失 token、cache 或费用字段不按零计算。
首次附件式 Codex 审计因主机 max_user_namespaces=0 无法读取输入，12 次基础设施失败均完整保存，未计作零缺陷。正式版本改为封闭只读 MCP 输入，保留订阅 Codex 和原沙箱设置；旧运行及修复前运行版本保留用于复查。
完整输入、流式输出、工具事件、实际注入、配置、模型身份、失败及评分记录存于 Git 外归档 `.kb-jiuwenswarm-docs-ab-20261003/`。下表路径相对于归档根；机器绝对路径只保留在原始记录中。Git 中仅保存紧凑结果、报告和运行工具，原始大文件没有重复提交。

| 复查输入 | 逻辑路径 | SHA256 |
| --- | --- | --- |
| inventory | `.kb-jiuwenswarm-docs-ab-20261003/mapping/inventory.json` | `b9a59c454d5aea9157ebe18e58b32db54c8a7645992abfe16586d16a111cc155` |
| author_mapping | `.kb-jiuwenswarm-docs-ab-20261003/mapping/author-mapping.json` | `8c7adc0dbcdf990616c6a7254fb27c52b920339f974ea2f070bc0bd643d8a232` |
| campaign | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/campaign.json` | `aad5a545be0696ab3d95332ef11606e66ef92801347ceae007b2eba412de79cb` |
| collection | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/collection.json` | `fff76dd31e13966b8b22d79b94ddbf3035985f1ddad72ff0437f05cdc82c3c9f` |
| truth | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/truth-manifest.json` | `f342ba63168aa96292e1614e97ce92f564fb874f07c1f503a5d79c67c870f6d6` |
| scores | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/results.json` | `6eeb2e5d029624bec80922faa4d0747ce64955119ca00cb81ca9917afea6db83` |
| extraction_timing | `.kb-jiuwenswarm-docs-ab-20261003/extraction-timing.json` | `88b73bd23f35790bf41c0d55ea4122e59231414f21b8b3819c1888ad343d997f` |
| freshness | `.kb-jiuwenswarm-docs-ab-20261003/upstream-freshness.json` | `2f78d8b80584e705751e2e4f2c250a78ff92c6dd102540ef0099ceab31830f96` |
| validation | `.kb-jiuwenswarm-docs-ab-20261003/final-validation.json` | `f56f891fcd6e5aa7e6fcd3575c0c12cca63ca2d4cf1fca82e3d48432d03aa72f` |
| knowledge_acceptance | `repository/eval/knowledge-depth/jiuwenswarm-repair63-final-20261002.json` | `a6f0114ddf362e49839804042d0cd38639bd53f5a031dacbe4b444b887a65fbf` |
| runtime_identity | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/identity.json` | `69de794892c0874e6d2e1a9f44ef02028f36509371722195693df1358e0f365d` |
| codex_runtime | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/runtime-snapshot.json` | `afc7854eab677a46d58e78262c94d34d0587b786d2a3f397c8df526c939e95e8` |
| codex_score_runtime | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/score-runtime-snapshot.json` | `a14b48e2bc57bf171b6dd0aa5dbecd147eb8340da3bd96e1368335820a052d74` |
| codex_preflight | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/preflight.json` | `e58ba1e063d1ec75e50b7d8cdc03a312b4eccc9c54c15b21289cbf0cfa90598c` |
| reviews_manifest | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/reviews-manifest.json` | `e0a19ade80825ed332f1bbdfb386c9777f25d83b015e3b6e67d9080d829070c2` |
| native_diagnostics | `.kb-jiuwenswarm-docs-ab-20261003/report-derived/native-diagnostics.json` | `bbab74042b1d8188f8b46bd6df8fcbe298a401ff8e94de4d5c63179c6d281d7a` |
| raw_trace_index | `.kb-jiuwenswarm-docs-ab-20261003/raw-trace-index.json` | `d397dba74d0ae0af47a32513dbaa55dc154822f0df8d2e07c69c5888b412f49e` |
| baseline_pr | `.kb-jiuwenswarm-docs-ab-20261003/baseline-pr290.json` | `936c2edaa4e088d70892711389d9fa85ec4e2c7c4a8d1301c2230c86dae1d96f` |
| A 组文档快照 | 见 inventory | `f228db8ed02d00a8a5be13edf3f8a785810cebdbd35e19a65c068476e3c313e5` |
| B 组文档快照 | 见 inventory | `f98af18e075181bdd60c1342b03bedc83ee9577ab4201d60ac8ddf78b3a16ab5` |

本地验证：local_checks_passed；全量 pytest 3033 通过、17 跳过；知识目录 0 错误、44 提醒。CLI、doctor JSON、文档链接、引用、SPEC 和独立安装包检查的日志哈希保留在配套 JSON。GitHub CI：passed for finalized evaluation code commit d00449677 (2 suite checks); report-only delivery commit checked separately。

## 改善建议

1. 下一版封闭工具允许安全的目录尾斜杠写法，并先做路径规范化和边界校验；本轮失败保留，不能事后替换结果。
2. 将长提示词读取改为顺序游标协议，增加完整输入确认和输出 schema 检查，减少跳读与格式失败；内容不合格仍不重新采样。
3. 检索按 PR 涉及的功能与维度选段，优先注入 API、失败分支及测试义务；保留作者 ADR 的决策与被拒绝方案，避免把库存覆盖率当作已注入覆盖率。
4. 用共享排期对订阅限流做适应，分别观察排队、原生耗时与有效完成率；不能将包含 429 的耗时差全部归因于知识质量。
5. 增加真实 PR 及维护者人工确认的问题基准，尤其补充有确认缺陷的前瞻样本。本轮主样本召回仅涉及 2 个 PR，不足以推断全项目召回率。

当前结论只适用于所选 PR、固定 GLM 配置和相同检索预算；不能把知识认可率当作缺陷识别准确率。
