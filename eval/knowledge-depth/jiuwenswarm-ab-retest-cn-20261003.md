# JiuwenSwarm GLM‑5.3 协议修复与复测

状态：`completed_with_failures`；复测有效评审 62/72，已独立评分 62 份。

本轮有效完成率提高：76.39% → 86.11%。主样本精确率为A 65.56%、B 65.48%，B−A -0.08个百分点（共同可计算7个PR）；成对原生耗时B−A +32.71秒（19对重复、7个PR）。这些描述性结果未证明知识库带来精确率或速度收益。已确认问题召回率A 100.00%、B 100.00%，仅针对2个PR的预冻结有限问题清单。

原作者资料与知识库的内容、覆盖及固定版本比较见[原中文报告](jiuwenswarm-original-docs-comparison-cn-20261003.md)及其[紧凑数据](jiuwenswarm-original-docs-comparison-cn-20261003.json)。原报告及其中的旧A/B结果保留不变，本报告交付协议修复后的新批次结果。

完成率指交付可评分结果的比例；全部调用结束不等于全部有效。失败继续计入原分母，旧结果保持原判定。

| 样本 | 资料 | 修复前有效/计划 | 复测有效/计划 | 完成率变化 |
| --- | --- | ---: | ---: | --- |
| 主样本 | 原作者资料 | 21/24 | 22/24 | 87.50% → 91.67% |
| 主样本 | 当前知识库 | 15/24 | 19/24 | 62.50% → 79.17% |
| 全部样本 | 原作者资料 | 30/36 | 31/36 | 83.33% → 86.11% |
| 全部样本 | 当前知识库 | 25/36 | 31/36 | 69.44% → 86.11% |

## 交付时效性核查

核查时间：2026-10-03T14:12:30.142246+08:00；固定源码基线：`f0a69728c96b5961d993449f1a901cbd2f4dac5b`；交付时 develop：`f0a69728c96b5961d993449f1a901cbd2f4dac5b`（提交日期 2026-09-30T09:01:50Z）。相对固定基线新增提交 0，基线独有提交 0；变更生产文件 0，受影响功能：无。

文件统计范围：same fixed 2199-file inventory; new files are listed separately in changed_paths。依据为归档表中的 `upstream_freshness` 哈希绑定记录；这只是一次分支观测，不代表持续实时更新，也未更新本轮冻结语料。

## 修复范围与解释边界

旧17次无效评审中，14次涉及评估接口冲突或普通目录写法，2次为模型JSON语法错误，1次未完整读取大PR提示。共享评审提示允许省略锚点和使用 duplicate，却与旧验证器冲突。所有旧失败均保留；本次新建批次，不事后补算为成功。

本轮源代码、作者资料、知识库、12个PR、三次重复和两个模型通道保持固定，修改评估协议、提示一致性、MCP结果渲染和UTF‑8预算。随机生成、共享排期、服务限流、上下文呈现及提示变化都会影响结果，不能把修复前后的变化全部归因于知识库，也不能据此证明知识库加速。

旧 harness SHA：`9c25817901900d706afc0594c1b10dff0f69110344a56a0914d047dc50e6a091`；新 harness SHA：`6311449672ae9a058d2bd991d339e8c3281425f71e838790ebb26efd2defb8ec`。具体变更：tool and output protocol only; content, native model and budgets stay frozen

路径逃逸、跨组文档、未完整输入、错误模型身份和未经授权工具仍属于失败；目录尾斜线与根目录 shorthand 只在受控目录检索中规范化。没有补写证据、模型切换或内容失败后重新采样。

原始基线保留既有完成率与评分，但其字面原生24,000字符预算未获认证：FastMCP字符串返回可能额外渲染Structured content，同一结果重复呈现；原生适配器也可能截断。旧bridge载荷满足预算不等于旧native ToolResult满足预算，不能把旧试验称为已通过新的渲染审计。

当前有效评审逐次要求哈希绑定的原生日志结果无适配器截断、无重复结构内容，字符及UTF‑8字节均不超过24,000，并核对源码/计算请求ID累计不超过60，包含MCP执行前被拒绝的请求。证据止于native日志ToolResult；最终provider请求体未归档，不冒称已核验其完整序列化或实际模型接收字节。

中止的v3批次与预检作为单独外部证明保存，不纳入本轮72个正式槽位、评分分母或速度统计。

## 本次失败归因

| 阶段 | 组别 | 原生状态/失败原因 | 次数 |
| --- | --- | --- | ---: |
| 修复前 | A | status:valid | 30 |
| 修复前 | A | status:invalid_run | 6 |
| 修复前 | A | unknown_bridge_protocol | 1 |
| 修复前 | A | output_schema_or_contract_rejected | 5 |
| 修复前 | B | status:invalid_run | 11 |
| 修复前 | B | status:valid | 25 |
| 修复前 | B | incomplete_prompt | 1 |
| 修复前 | B | output_schema_or_contract_rejected | 7 |
| 修复前 | B | directory_trailing_slash_protocol_rejection | 3 |
| 复测 | A | status:invalid_run | 5 |
| 复测 | A | status:valid | 31 |
| 复测 | A | unknown_bridge_protocol | 5 |
| 复测 | B | status:valid | 31 |
| 复测 | B | status:invalid_run | 5 |
| 复测 | B | unknown_bridge_protocol | 4 |
| 复测 | B | output_schema_or_contract_rejected | 1 |

原始诊断保留不变。以下槽位的状态与事件哈希证明：模型尝试通过源码工具读取文档，被独立文档预算边界拒绝。原始诊断中的unknown_bridge_protocol是未匹配错误字符串的兜底标签，不据此声称存在共享协议故障。

| PR | 组别 | 重复 | 复核原因 |
| --- | --- | ---: | --- |
| #7639 | A | 1 | 尝试读取文档，被预算边界拒绝 |
| #7639 | A | 2 | 尝试读取文档，被预算边界拒绝 |
| #7639 | A | 3 | 尝试读取文档，被预算边界拒绝 |
| #7641 | B | 3 | 尝试读取文档，被预算边界拒绝 |
| #7650 | A | 1 | 尝试读取文档，被预算边界拒绝 |
| #7650 | A | 3 | 尝试读取文档，被预算边界拒绝 |
| #7650 | B | 1 | 尝试读取文档，被预算边界拒绝 |
| #7650 | B | 2 | 尝试读取文档，被预算边界拒绝 |
| #7650 | B | 3 | 尝试读取文档，被预算边界拒绝 |

同一无效评审可能有多项拒绝原因，原因计数不直接相加当作失败调用数；源码或协议信息不足的原因保持unknown。旧失败逐槽位人工归因与原始诊断分别保存在JSON。

## 本次准确率与速度

以下精确率只统计有效、已评分输出，并按两组均有可计算结果的同一PR取均值。unknown不计误报，非缺陷建议另计。召回只针对预先冻结的自动独立审计有限问题清单，新发现不回填分母；无确认问题的PR不可计算召回。

| 分组 | 指标 | A 原作者资料 | B 当前知识库 | 同时可计算PR数 |
| --- | --- | ---: | ---: | ---: |
| 主样本 | 缺陷评论精确率 | 65.56% | 65.48% | 7 |
| 主样本 | 已确认问题召回 | 100.00% | 100.00% | 2 |
| 主样本 | 建议有效性 | 100.00% | 100.00% | 6 |
| 全部 | 缺陷评论精确率 | 73.94% | 70.61% | 10 |
| 全部 | 已确认问题召回 | 87.50% | 79.17% | 4 |
| 全部 | 建议有效性 | 100.00% | 95.99% | 9 |
| 旧分叉探索 | 缺陷评论精确率 | 93.52% | 82.59% | 3 |
| 旧分叉探索 | 已确认问题召回 | 75.00% | 58.33% | 2 |
| 旧分叉探索 | 建议有效性 | 100.00% | 87.96% | 3 |

以下按各组有效且已评分的评审累计评论，unknown比例为unknown/(TP+FP+unknown)，非缺陷建议不进入该分母。每次评审内部按根因去重，三次重复仍是三个观测；这些计数不是不同缺陷总数，也不限定为两组同时可计算的PR。

| 分组 | 评论统计 | A | B |
| --- | --- | ---: | ---: |
| 主样本 | 缺陷判断中的未知比例 | 18.18% | 15.38% |
| 主样本 | 有效缺陷评论 | 22 | 21 |
| 主样本 | 误报 | 14 | 12 |
| 主样本 | 未知缺陷判断 | 8 | 6 |
| 主样本 | 非缺陷建议 | 38 | 27 |
| 主样本 | 有效建议 | 38 | 26 |
| 主样本 | 无效建议 | 0 | 0 |
| 主样本 | 有效性未知的建议 | 0 | 1 |
| 主样本 | 新发现有效缺陷，不回填召回基准 | 16 | 15 |
| 全部 | 缺陷判断中的未知比例 | 15.07% | 16.28% |
| 全部 | 有效缺陷评论 | 46 | 54 |
| 全部 | 误报 | 16 | 18 |
| 全部 | 未知缺陷判断 | 11 | 14 |
| 全部 | 非缺陷建议 | 55 | 47 |
| 全部 | 有效建议 | 54 | 44 |
| 全部 | 无效建议 | 0 | 2 |
| 全部 | 有效性未知的建议 | 1 | 1 |
| 全部 | 新发现有效缺陷，不回填召回基准 | 未知 | 未知 |
| 旧分叉探索 | 缺陷判断中的未知比例 | 10.34% | 17.02% |
| 旧分叉探索 | 有效缺陷评论 | 24 | 33 |
| 旧分叉探索 | 误报 | 2 | 6 |
| 旧分叉探索 | 未知缺陷判断 | 3 | 8 |
| 旧分叉探索 | 非缺陷建议 | 17 | 20 |
| 旧分叉探索 | 有效建议 | 16 | 18 |
| 旧分叉探索 | 无效建议 | 0 | 2 |
| 旧分叉探索 | 有效性未知的建议 | 1 | 0 |
| 旧分叉探索 | 新发现有效缺陷，不回填召回基准 | 未知 | 未知 |

| 主样本速度（秒） | A | B |
| --- | ---: | ---: |
| 原生评审 p50 | 525.42 | 545.71 |
| 原生评审 p90_linear | 610.76 | 664.12 |
| worker内排队 p50 | 145.14 | 258.35 |
| worker内排队 p90_linear | 575.84 | 1129.21 |
| worker入口至结束 p50 | 717.83 | 927.27 |
| worker入口至结束 p90_linear | 1146.29 | 1704.75 |

同一PR与重复序号均有效的成对原生时间：A 505.64秒、B 538.35秒，B−A 32.71秒；19组成对重复、7个PR。属于描述性耗时，不能证明因果加速。

排队与端到端从worker入口计时；线程池入队前等待未完整记录，完整任务提交到退出耗时保持未知。429请求级重试与原生CLI重试分开，请求延迟参数不冒称实际退避耗时。P50/P90仅有效输出，对不同完成集合的比较受选择偏差影响。

## 逐PR完成情况

| PR | A 修复前→复测 | B 修复前→复测 | 复测A精确率 | 复测B精确率 |
| --- | --- | --- | ---: | ---: |
| #7639 | 1/3 → 0/3 | 2/3 → 3/3 | 不可计算 | 100.00% |
| #7641 | 3/3 → 3/3 | 3/3 → 2/3 | 100.00% | 100.00% |
| #7642 | 3/3 → 3/3 | 2/3 → 2/3 | 77.78% | 75.00% |
| #7645 | 3/3 → 3/3 | 3/3 → 3/3 | 20.00% | 55.56% |
| #7647 | 2/3 → 3/3 | 1/3 → 3/3 | 61.11% | 77.78% |
| #7649 | 2/3 → 3/3 | 1/3 → 3/3 | 100.00% | 100.00% |
| #7650 | 2/3 → 1/3 | 1/3 → 0/3 | 不可计算 | 不可计算 |
| #7651 | 3/3 → 3/3 | 2/3 → 3/3 | 0.00% | 0.00% |
| #7654 | 3/3 → 3/3 | 3/3 → 3/3 | 100.00% | 88.89% |
| #7655 | 2/3 → 3/3 | 2/3 → 3/3 | 100.00% | 75.56% |
| #7656 | 3/3 → 3/3 | 3/3 → 3/3 | 80.56% | 83.33% |
| #7675 | 3/3 → 3/3 | 2/3 → 3/3 | 100.00% | 50.00% |

## 输入、用量与可追溯性

逻辑检索与bridge下发知识累计预算6000字符、初始两页；注入内容与补读均归档，库存总量不代表模型收到的上下文。旧native渲染中的额外重复另行披露，6000逻辑字符不冒称旧provider只收到了6000字符。每次最多60次源码/计算工具调用，单次结果24000字符，原生超时1800秒，并发13。

所有有效调用的GLM服务实际模型均核查为GLM‑5.3；失败调用保留记录中的身份或未知状态。独立评分请求Codex gpt-6-sol/medium；原生记录未报告served model时保持未知。用量为服务记录的累计步骤tokens，不等于新增计费tokens；实际费用未知。

#7639、#7654、#7655、#7656仅为旧分叉探索样本，不能视为无时间泄漏的前瞻评审；#7656预冻结真值仍未知。主样本8个PR均为小型后端修复，不能推广到全项目、大型功能或前端。没有执行JiuwenSwarm运行时测试。

完整输入、流、工具调用、注入文档、评分和配置保存在Git外归档，公开JSON只保存紧凑统计与哈希。复跑入口：`python -m eval.jiuwenswarm_ab_retest_report --previous-study OLD --study NEW --output-dir OUT`。

| 复测用量与输入 | A | B |
| --- | ---: | ---: |
| 累计输入tokens | 41609757 | 32426949 |
| 累计输出tokens | 1184921 | 1192638 |
| 发生429的评审 | 12 | 15 |
| 429通知 | 37 | 38 |
| 实际累计知识字符P50 | 5375.50 | 5483.00 |
| 实际源码/计算请求最大值 | 51 | 43 |
| 提示未完成而被拒绝的请求 | 0 | 0 |

旧协议的内部计数器未累加提示读完前被拒绝的源码/计算请求；当前协议先计数后执行门禁。交付审计分别重计bridge请求与native独立请求ID（含错误和拒绝），跨传输尝试累计；有效评审超限或证据未知时阻止认可与报告发布。超限、证据未知的失败调用仍保留在失败分母，不删除也不记为有效。

| 原生渲染审计 | 修复前A | 修复前B | 复测A | 复测B |
| --- | ---: | ---: | ---: | ---: |
| 获本次原生规则认证的评审 | 0 | 0 | 36 | 36 |
| 源码/计算请求ID最大值 | 35 | 36 | 51 | 43 |
| 结果字符最大值 | 50000 | 50000 | 24000 | 24000 |
| 结果UTF‑8字节最大值 | 50000 | 50000 | 24000 | 24000 |
| 适配器截断结果 | 35 | 37 | 0 | 0 |
| 额外结构内容重复结果 | 942 | 933 | 0 | 0 |

独立评分实际served model未报告的调用数：12；费用保持未知。

| 归档 | 逻辑路径 | SHA256 |
| --- | --- | --- |
| previous/campaign.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/campaign.json` | `aad5a545be0696ab3d95332ef11606e66ef92801347ceae007b2eba412de79cb` |
| previous/identity.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/identity.json` | `69de794892c0874e6d2e1a9f44ef02028f36509371722195693df1358e0f365d` |
| previous/collection.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/collection.json` | `fff76dd31e13966b8b22d79b94ddbf3035985f1ddad72ff0437f05cdc82c3c9f` |
| previous/reviews-manifest.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/reviews-manifest.json` | `e0a19ade80825ed332f1bbdfb386c9777f25d83b015e3b6e67d9080d829070c2` |
| previous/truth-prerequisite.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/truth-prerequisite.json` | `eb8b64b97d8fe3d2c4eeb52bf6ef94c084443e65749e0928e3a72e8434d30602` |
| previous/private-codex/truth-manifest.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/truth-manifest.json` | `f342ba63168aa96292e1614e97ce92f564fb874f07c1f503a5d79c67c870f6d6` |
| previous/private-codex/results.json | `.kb-jiuwenswarm-docs-ab-20261003/evaluation-v2/private-codex/results.json` | `6eeb2e5d029624bec80922faa4d0747ce64955119ca00cb81ca9917afea6db83` |
| current/campaign.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/campaign.json` | `8187cd31ce1e8dccffa4a3cb08d222df0348d806287ffaf6862baa802244f0f7` |
| current/identity.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/identity.json` | `b67b554d07241b8ae488fffb05043115fe7cb0112dab734128f69baf81219f8a` |
| current/collection.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/collection.json` | `03df05f6f9595ca4cbb26a3952ff7b6608d374873e62b221f8ad4916e30ab0b2` |
| current/reviews-manifest.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/reviews-manifest.json` | `41d1d63240abff54bf132065d1168a9cab19c00a2e18fff10d7a2404c3e316e1` |
| current/truth-prerequisite.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/truth-prerequisite.json` | `e820daed948b6e4be37a2781411575136ca9a45bd5f1844857828092fe9e6c1c` |
| current/private-codex/truth-manifest.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/private-codex/truth-manifest.json` | `cef79a9fd89a105c6720c3a2cd39e9b10a07d78143f784d9d5d320e4860df83b` |
| current/private-codex/results.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/private-codex/results.json` | `140ee74492bb20547b62a12f62a88ef47ab2d3d63bd1d3280a0ecbe1e983781d` |
| current/retest-provenance.json | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/retest-provenance.json` | `251ab4edf5226de34c18d2513d52c99f60ffcc920ec84888f1f68afba3ca88db` |
| raw_trace_index | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/raw-trace-index.json` | `1953f356160c39bf7528443d1a312b0f81d7d3948063db613aeb38951dcb176e` |
| validation | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/final-validation.json` | `5aa503a338f589f4b6d2005355d41ed0d51466b449da2445a12f3791bb3584db` |
| upstream_freshness | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/upstream-freshness.json` | `d010a9b977343e519e2fdb737983c2108a7a3a231247805a765cf3b4714a3cdf` |
| original_comparison_md | `repository/eval/knowledge-depth/jiuwenswarm-original-docs-comparison-cn-20261003.md` | `c06b8963f3471820c91339e35370cbb34360fd6f1f8de63044e9beead4d8c553` |
| original_comparison_json | `repository/eval/knowledge-depth/jiuwenswarm-original-docs-comparison-cn-20261003.json` | `ece1b57980e808a6c339e2af75e74c30b66ec72e188fb94c3a7611b63a351cdc` |
| native_preflight | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/preflight-native-final-audit.json` | `82e3b6975c07bef1974b44371fe306993ec38551493716841da2146a21d1970d` |
| runtime_snapshot | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/private-codex/runtime-snapshot.json` | `999af51e6333e5d75f09d06924884592615370cd99b5dfde4ce6bafd313be598` |
| runtime_environment | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/runtime-final/environment.json` | `0fdcc8c2c1de8d023a347292239230ed0aa681c20aa20e8712e1c9aafac1d924` |
| independent_terminal_native_audit | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/independent-terminal-native-guard-audit.json` | `b52c1dde5084a6572586917ee98000455e88bb5a89af6214b3d13ffd4656084b` |
| scoring_execution | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/private-codex/scoring-execution-attestation.json` | `6ce6e6902e7736ce3456f8a8edd7d1da16036fb9be6fae1719d4ee6146572854` |
| scoring_cli_capture | `.kb-jiuwenswarm-docs-ab-retest-v4-20261003/evaluation-v2/private-codex/scoring-cli-capture.json` | `7016bc55d8075e0f94631ae8c619afddd2296e5a5670818cd14598b958b518ad` |
| excluded_v3_abort | `external-artifact/protocol-abort-final-audit.json` | `9dc1aaf185e9c3baf536350a88864a20c4fc09fb84dd719b092d147ca612cd50` |
