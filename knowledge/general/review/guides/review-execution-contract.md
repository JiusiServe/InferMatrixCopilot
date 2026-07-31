---
title: "独立审查执行合同"
created: 2026-07-13
updated: 2026-07-30
type: guide
tags: [general, review]
sources: ["InferMatrixCopilot Issue #17", "InferMatrixCopilot Issue #24", "zuiho-kai/claude-workflow-starter@c217fc6"]
---

# 独立审查执行合同

**何时使用：** 开发完成后的独立 review、完整 diff review、准备交给项目 owner 前的最后审查。这里是默认 Direct 的单次审查入口；风险解释和专项 lens 只在首次审查留下具体高风险未知量时继续读取。

## 单次输入与简明检查单

主审查只采集一次 `{base_sha, head_sha, PR title/body, changed files, diff, mergeability, CI}`。先用 title/body 的声明目标选择精确 owner/model 规则组和第一批源码函数，再用 changed files 验证和补全范围；PR 描述只负责导航，不能作为 finding 证据。

同一份证据包持续追加已读文件、caller 搜索、测试结果和 findings，后续步骤必须复用，不能重新抓取或重复调查。第一次 Codex review 使用这份简明检查单：

- 快速门禁：snapshot、mergeability、CI、完整 diff；
- owner 路由：命中的 owner/model 规则组和第一批源码函数；
- 行为合同：public ingress → producer → final consumer、默认值、fallback、兼容；
- 验证合同：真实命中路径、相关测试、未验证边界；
- 设计减法：越界 scope、重复 abstraction、最小 owner 设计。

## 完成条件

审查分三轮，顺序不能交换：

1. **覆盖轮：** 冻结基线和完整 diff。先按[通用设计审查规则](../rules.md)检查同族实现和条件分支的结构触发；命中时记录 `REV-1a`/`REV-1b` 的覆盖结论。owner 定义审查触发组时，选择 `core` 加当前 diff 命中的组并完整枚举组内稳定 ID；没有触发组时才枚举该 owner 全部稳定 ID。随后填写当前可达公开入口和 changed-value producer→consumer 表。
2. **减法轮：** 先按用户目标和当前 RFC/mini spec slice 删除越界 behavior、文件和测试；再枚举保留的 production abstraction，写出最小 owner 设计和逐项减法账本。
3. **开放轮：** 再查 correctness、duplication、layering、edge cases、surface area 和命中的专项风险。

找到很多新问题不能代替覆盖轮或减法轮。任一轮发现 P0/P1/P2 都不能提前结束其他轮次。缺少所选规则行、可达入口、changed-value consumer、scope ledger、abstraction census、最小设计或证据时，结论只能是 `partial review`；不能说 `clean`、`ready` 或 `fully reviewed`。

规则覆盖表、入口矩阵和 producer→consumer trace 是 reviewer 的内部审计产物，不是默认
给用户看的 review。对外只交付已经证实、能落到具体代码位置的 actionable findings。

## 默认一次审查与条件专项

每次 PR review 只有一个主 Codex review，但必须在同一篇内部报告里覆盖两个维度：

- **Correctness：** 追公开入口、producer→consumer、行为、兼容、默认值和测试。
- **Design/subtraction：** 先删越界 scope，再查模块 owner、最小数据流、最小修改、既有复用和可删/并/内联/迁移的层。

不能把两个维度拆成两篇通用审查。只有主审查遇到新颖、证据矛盾或仍未覆盖的高风险合同，才允许追加一个有边界的专项问题；专项只读取共享证据包和完成该问题所需的新增源码，不重跑完整 diff，也不独立输出 verdict 或评论。

用户未指定深审时，端到端默认 10 分钟。到时停止新工具调用并返回现有结论；不能为完整 CI、全量测试、历史 thread 或额外专项无限等待。

## 解释压力反查

减法轮必须用最终 head 做一次不依赖历史的人话解释：只说输入、每个 source × scope 的唯一 owner 产物和最终 consumer。若必须靠修复时间线说明结构，检查：

- 两个字段组、helper 或中间对象没有不同 consumer，最终只是立即合并、转发或拆后再合；
- 同一 owner 产物跨层不断换名，尤其把已校验 projection 又叫回 raw request 或 kwargs；
- normalizer 已产出最终值，下游仍重读原始输入、补 default、重做 alias 或 precedence；
- 当前 RFC slice 明确不拥有的职责，production diff 却修改了其真实 consumer。

命中后写出“当前结构 → 最小结构 → 具体删除或迁移项”。只有 representation、lifecycle 或 failure policy 不同才允许额外层；“兼容复杂”“测试很多”不是证明。

## 减法轮交付合同

减法轮先做 scope subtraction，再做 architecture subtraction，并在内部审计中交付：

1. **Scope ledger：** 每个新增 behavior、production 文件和测试组映射到当前目标或 RFC slice；无法映射就 `DELETE / DEFER`。
2. **当前 census：** 枚举保留范围内新增或扩张的 helper、class、field group、allowlist、owner projection、跨层 artifact 和末端补偿。
3. **最小设计：** 在保持 scope 外 base 行为不变时，写出最少 owner artifact、transformation 和 consumer。
4. **逐项账本：** 对 census 每项标记 `KEEP / INLINE / MERGE / MOVE / DELETE` 并给代码锚点；改名、换文件、删临时变量不算减法。
5. **净结果：** 分别报告 scope 删除项，以及 abstraction、owner、重复 projection、末端补偿和 production branch 的净减少。

correctness bug 不算减法。减法 `PASS` 必须给可执行的删/并/内联方案，或用完整 ledger 证明授权 scope 和 census 已经最小。

## 用户可见输出

默认输出必须像正常 GitHub code review，而不是合规报告：

1. 每个 pinned head 只发布一篇合并后的 review comment；专项结果回到主审查，不能各发一篇。渐进状态留在宿主对话或状态流，除非用户明确要求，不发布“初稿评论 + 最终评论”。
2. 每个 finding 绑定精确 `path:line` 或 diff hunk。
3. 正文依次说清具体触发输入/调用路径、当前行为、为什么有风险、最小修复方向。
4. 不显示规则 ID、覆盖表、入口矩阵、`PASS`、`MISSING_EVIDENCE` 或 `Disposition`；
   这些只在用户明确要求完整审计产物时附上。
5. 单独给出一到三项具体 scope/architecture 减法；没有可删项时简短说明最小设计证据。
6. 没有 actionable finding 时只简短说明没有发现问题，并指出真正影响结论的验证缺口。

规则用于帮助 reviewer 找到问题和防止漏检，不能成为用户自己翻译的输出格式。

Direct MCP 提供完成检查工具时，最终评论前必须提交以下二选一结构：

- `subtraction`: 每项包含具体代码锚点、`DELETE / DEFER / INLINE / MERGE / MOVE`
  动作和风险；
- `minimality_proof`: 包含 scope ledger 结论、abstraction census 结论，以及
  为什么没有安全删除项。

两者都缺失时只能返回 `partial_review`，复用现有证据补一次有界减法检查后重新
验证。检查不要求每个 PR 硬凑删除项，也不允许因此产生第二篇评论。

### Source-consumer decision matrix

同一用户语义如果有多个输入来源、dispatcher、stage 类型或兼容入口，覆盖轮还必须先写完**来源 × consumer scope 决策矩阵**，再读具体实现。每个 source/scope 单元格只能标成：路由到哪个 consumer、与哪些来源重复时拒绝、明确不适用，或非用户 default；不能留给字典合并顺序和分支先后隐式决定。至少验证每个合法单来源、每组同 scope 重复、一个跨 scope 共存 control，以及每条 production dispatcher 的等价结果。矩阵缺失时，即使当前测试和开放轮没有 finding，也只能报 `partial review`。

PR 声称“严格校验”“拒绝未知字段”“统一 normalization”或其他全入口行为时，公开入口不能只按 changed hunk 或当前 production caller 枚举。必须搜索同一合同的所有可调用 constructor、factory、classmethod、兼容 helper 和旧入口，包括本次未修改、已退出当前主调用链但仍可被仓库测试或外部调用者直接使用的入口；对每个入口运行同一个最小负向样例并记录结果。任一入口仍静默接受、过滤或覆盖该样例时，整体合同未闭环；如果宽松行为确属兼容要求，必须有明确文档、专门回归测试和不把它算作严格入口的 scope 声明。只证明两条 production 路径严格，不能据此宣称整个配置或 API surface 已严格化。

## Reviewer 只读输入

- 用户需求和允许修改的范围；
- 固定的 target/base SHA；
- 当前完整 diff，以及属于任务的未跟踪文件；
- [通用设计审查规则](../rules.md)及当前 diff 命中的结构触发；
- live 调用链证明的 owner `rules.md`；
- 每个 owner 的规则组选择及触发理由；有触发组时必须包含 `core`，选择错误由主 agent 复核，checker 只验证组内覆盖完整；
- 编码前已存在的 mini spec 或合同矩阵；不存在时记 `MISSING_EVIDENCE`，不能事后代写；
- 必要的仓库源码、测试和官方实现。

不要给 reviewer 作者自评、怀疑根因、历史 reviewer 答案或 incidents。规则直接指向 owner 后停止读其他文档，但**停止读文档不等于停止追源码**：必须继续覆盖所有能到达同一 consumer 的公开入口和跨 owner 调用边界。

## Owner 怎样声明审查组

小 owner 可以不分组，继续全量审计。规则较多时，在 `rules.md` 放一张人能直接编辑的表；一旦使用分组，必须有 `core`，每个稳定 ID 至少属于一个组，组名只用小写字母、数字和连字符。开发路由规则可以放 `author-routing`，不要塞进每次代码 review 的 `core`。

```markdown
| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次代码审查 | `ABC-1a`, `ABC-1b` |
| `public-topology` | CLI、API、资源获取或 topology 改动 | `ABC-2a`, `ABC-2b` |
```

第三方新增 owner 时只需手工增加同样的表和稳定 ID；checker 会验证组名、`core`、未分组 ID、未知 ID 和报告里的组内覆盖，但不会替人判断触发条件是否写得合理。

## 内部审计 Markdown

reviewer 或审查负责人把下面内容保存为内部 Markdown，供 checker 检查覆盖完整性。除非
用户明确要求完整审计，不要把它原样粘贴到 GitHub review 或聊天回复。

```markdown
# Review report

## Review scope
- Base SHA: <sha>
- Diff: <base -> working tree or head>
- Owners: <rules paths or none>
- Rule groups: <rules path> = core,prompt-token[,other-triggered-group]；owner 没有组时写 `full`
- In-scope untracked files: <files or none>

## Owner rule audit
| Rule ID | Status | Evidence | Disposition |
|---|---|---|---|
| ABC-1a | PASS / FAIL / MISSING_EVIDENCE / NOT_APPLICABLE | file:function + test/run evidence | `-` / `FINDING:F1` / `DRAFT:blocked evidence` |
| LEGACY:path/to/rules.md#1 | PASS / FAIL / MISSING_EVIDENCE / NOT_APPLICABLE | quoted source unit + file/function/test evidence | `-` / `FINDING:F1` / `DRAFT:blocked evidence` |

## Public ingress matrix
| Ingress | Actual dispatcher | Contract check | First expensive operation | Owner adapter/consumer | Production-path test/evidence |
|---|---|---|---|---|---|
| <offline/API/chat/internal entry> | `<real function reached from the public entry>` | <validation/normalization and location> | `<decode/load/GPU/VAE call>` | `<actual adapter or bypass>` | <evidence> |

## Producer-consumer trace
| Value or contract | Producer | Transformations | Final consumer | Stop/failure owner | Evidence |
|---|---|---|---|---|---|
| <field/behavior> | <source> | <every handoff> | <actual reader> | <boundary> | <evidence> |

## Subtraction audit
### Scope ledger
| Behavior / production file / test group | Authorized goal or current RFC slice | KEEP / DELETE / DEFER | Evidence |
|---|---|---|---|
| <item> | <merge condition or none> | <decision> | <contract anchor> |

### Abstraction census and minimal design
- Current census: <every helper/class/field group/projection/artifact/compensation flow>
- Minimal owner design: <least owner artifacts, transformations and consumers>

### Item ledger
| Current abstraction | KEEP / INLINE / MERGE / MOVE / DELETE | Code anchor | Survival proof or removal |
|---|---|---|---|
| <item> | <decision> | <path:symbol> | <reason> |

### Net result
- Scope subtraction: <behaviors/files/tests removed or zero with proof>
- Architecture subtraction: <net abstraction/owner/projection/compensation/branch counts>

## Source-consumer decision matrix
| Source | Consumer scope / dispatcher | Decision | Conflicts with | Production-path evidence |
|---|---|---|---|---|
| <root/nested/alias/per-stage/default source> | <specific stage or consumer> | ROUTE / REJECT_DUP / NOT_APPLICABLE / DEFAULT | <specific sources or concrete reason no conflict exists> | <test/run evidence> |

只有能够证明当前 diff 不存在多来源、多 dispatcher、多 stage 或兼容入口时，本节才可使用 N/A；仍须保留表头，并在唯一数据行的每个单元格写具体理由，第一格以 `N/A-with-evidence:` 开头。一个 source 有多个 consumer scope 时分行写，不能在一个单元格里用“视情况”概括。

## Open findings
- `P0 F1` / `P1 F2` / `P2 F3` or `none`. Blocking finding uses one machine-readable line:
  `- P1 F1 — DIFF:<changed hunk>; PATH:<reachable runtime path>; CONTRACT:<pre-existing source>; FAILURE:<user-visible break>; COUNTEREVIDENCE:<canonical alternative checked>; FIX:<smallest safe fix>`
- 没有完成这六项证明的架构怀疑写 `NOTE N1`，不计入 P0/P1/P2，也不能映射成 owner `FAIL`。

## Completion
OWNER RULE GROUPS: <rules path>: core,prompt-token[,other-triggered-group]；owner 没有组时不写
OWNER RULE COVERAGE: <rules path>: X/Y stable IDs inventoried — A pass / B fail / C missing evidence / D not applicable
SUBTRACTION VERDICT: PASS / FAIL / PARTIAL — <scope and architecture result>
CORRECTNESS VERDICT: PASS / FAIL / PARTIAL — <findings or clean evidence>
AUDITS RUN: coverage,ingress,producer-consumer,source-consumer,duplication,layering,edge-cases,surface-area — N findings (Pa P0, Pb P1, Pc P2)
```

每个稳定 ID owner 各写一行 `OWNER RULE COVERAGE`。owner 的 `rules.md` 包含“审查组”表时，`Completion` 必须写一行 `OWNER RULE GROUPS`，至少选择 `core`；覆盖分母是所选组去重后的稳定 ID 数，不是整页总数。未定义组的 owner 保持全量覆盖。`PASS` / `NOT_APPLICABLE` 的 Disposition 写 `-`；`FAIL` 必须写 `FINDING:F<number>` 并指向已完成六项证明的正式 finding；`MISSING_EVIDENCE` 必须写 finding，或用 `DRAFT:<具体且可核对的依赖、测试或 artifact 阻塞>` 说明为什么只能作为 implementation draft。多个规则可以指向同一个 finding，不能从失败行里随意挑几个上报；每个 finding 也必须反向被规则行引用，只有紧跟 F ID 的 `OWNER_RULE:NONE` 新问题例外。

旧规则页没有稳定 ID 时传 `--legacy-rules`，按文件顺序给每个项目符号、普通段落和 Markdown 表格数据行写一行连续编号的 `LEGACY:<rules path>#N`，尾签写 `OWNER RULE COVERAGE: <rules path>: X source units inventoried — A pass / B fail / C missing evidence / D not applicable — legacy-unstructured, no exact clause-coverage claim`。脚本只核对这些机械源单元是否齐全，不声称能把一个自然语言段落自动拆成精确子句。完全没有 `rules.md` 时在规则表写 `OWNER RULES: none`，尾签写 `OWNER RULE COVERAGE: none: 0/0 stable IDs inventoried — 0 pass / 0 fail / 0 missing evidence / 0 not applicable`。其他表仍要完成；只列当前 diff 可达入口和 changed values。完全不适用时使用 `N/A-with-evidence: <至少二十字具体原因>`，每个单元格都给出具体解释，不能用 `-`、`none`、`unknown` 填充。正常入口的 dispatcher、第一处昂贵操作和 owner consumer 用反引号写真实代码路径。

## 机器检查

把 reviewer 输出保存为 Markdown 后运行：

```powershell
python tools/check_review_report.py --report <review.md> --rules <stable-owner-rules.md> --legacy-rules <legacy-owner-rules.md>
```

多个 owner 重复传 `--rules`。脚本检查规则组选取、组内 ID 完整性、必需章节、失败行到六项 finding 证明的映射、具体 draft 阻塞、入口 dispatcher→昂贵操作→owner consumer，以及完成尾签；它不判断触发组是否选对或证据真假，主 agent仍需抽查。最终交付前增加 `--require-clean`，同时拒绝所选 owner 规则中的 `FAIL` / `MISSING_EVIDENCE` 和非零开放 finding。

脚本失败时，主 agent 只把缺失项退回原 reviewer 补齐，不重新 framing，也不接受“已经找到足够多问题”。结构通过后，主 agent仍要抽查关键文件/函数证据。

## 何时继续读取详细指南

- 需要完整可粘贴 prompt 或专项 owner 角色：[reviewer lens prompt](reviewer-lens-prompt.md)
- 涉及 async、资源生命周期、性能证据或 rebase：[reviewer lens gates](reviewer-lens-gates.md)
- 需要理解四类开放审查方法：[reviewer lens audit](reviewer-lens-audit.md)
- public API、跨阶段字段或协议矩阵：[reviewer lens contracts](reviewer-lens-contracts.md)
