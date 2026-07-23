---
title: "独立审查执行合同"
created: 2026-07-13
updated: 2026-07-23
type: guide
tags: [general, review]
sources: []
---

# 独立审查执行合同

**何时使用：** 开发完成后的独立 review、完整 diff review、准备交给项目 owner 前的最后审查。这里是可直接执行的短入口；风险解释和专项 lens 只在本页要求时继续读取。

## 完成条件

审查分两轮，顺序不能交换：

1. **覆盖轮：** 冻结基线和完整 diff。owner 定义审查触发组时，选择 `core` 加当前 diff 命中的组并完整枚举组内稳定 ID；没有触发组时才枚举该 owner 全部稳定 ID。随后填写当前可达公开入口和 changed-value producer→consumer 表。
2. **开放轮：** 再查 duplication、layering、edge cases、surface area 和命中的专项风险。

找到很多新问题不能代替覆盖轮。不能为了省事漏掉命中组，也不能为了“更全面”把未触发组全部展开成噪声。缺少所选规则行、可达入口、changed-value consumer 或证据时，结论只能是 `partial review`；不能说 `clean`、`ready` 或 `fully reviewed`。

PR 声称“严格校验”“拒绝未知字段”“统一 normalization”或其他全入口行为时，公开入口不能只按 changed hunk 或当前 production caller 枚举。必须搜索同一合同的所有可调用 constructor、factory、classmethod、兼容 helper 和旧入口，包括本次未修改、已退出当前主调用链但仍可被仓库测试或外部调用者直接使用的入口；对每个入口运行同一个最小负向样例并记录结果。任一入口仍静默接受、过滤或覆盖该样例时，整体合同未闭环；如果宽松行为确属兼容要求，必须有明确文档、专门回归测试和不把它算作严格入口的 scope 声明。只证明两条 production 路径严格，不能据此宣称整个配置或 API surface 已严格化。

## Reviewer 只读输入

- 用户需求和允许修改的范围；
- 固定的 target/base SHA；
- 当前完整 diff，以及属于任务的未跟踪文件；
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

## 必须交付的 Markdown

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

## Open findings
- `P0 F1` / `P1 F2` / `P2 F3` or `none`. Blocking finding uses one machine-readable line:
  `- P1 F1 — DIFF:<changed hunk>; PATH:<reachable runtime path>; CONTRACT:<pre-existing source>; FAILURE:<user-visible break>; COUNTEREVIDENCE:<canonical alternative checked>; FIX:<smallest safe fix>`
- 没有完成这六项证明的架构怀疑写 `NOTE N1`，不计入 P0/P1/P2，也不能映射成 owner `FAIL`。

## Completion
OWNER RULE GROUPS: <rules path>: core,prompt-token[,other-triggered-group]；owner 没有组时不写
OWNER RULE COVERAGE: <rules path>: X/Y stable IDs inventoried — A pass / B fail / C missing evidence / D not applicable
AUDITS RUN: coverage,ingress,producer-consumer,duplication,layering,edge-cases,surface-area — N findings (Pa P0, Pb P1, Pc P2)
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
