# 独立审查执行合同

**何时使用：** 开发完成后的独立 review、完整 diff review、准备交给项目 owner 前的最后审查。这里是可直接执行的短入口；风险解释和专项 lens 只在本页要求时继续读取。

## 完成条件

审查分两轮，顺序不能交换：

1. **覆盖轮：** 冻结基线和完整 diff，枚举 owner 的全部稳定规则 ID，填写公开入口和 producer→consumer 表。
2. **开放轮：** 再查 duplication、layering、edge cases、surface area 和命中的专项风险。

找到很多新问题不能代替覆盖轮。缺少规则行、入口行、consumer 或证据时，结论只能是 `partial review`；不能说 `clean`、`ready` 或 `fully reviewed`。

## Reviewer 只读输入

- 用户需求和允许修改的范围；
- 固定的 target/base SHA；
- 当前完整 diff，以及属于任务的未跟踪文件；
- live 调用链证明的 owner `rules.md`；
- 编码前已存在的 mini spec 或合同矩阵；不存在时记 `MISSING_EVIDENCE`，不能事后代写；
- 必要的仓库源码、测试和官方实现。

不要给 reviewer 作者自评、怀疑根因、历史 reviewer 答案或 incidents。规则直接指向 owner 后停止读其他文档，但**停止读文档不等于停止追源码**：必须继续覆盖所有能到达同一 consumer 的公开入口和跨 owner 调用边界。

## 必须交付的 Markdown

```markdown
# Review report

## Review scope
- Base SHA: <sha>
- Diff: <base -> working tree or head>
- Owners: <rules paths or none>
- In-scope untracked files: <files or none>

## Owner rule audit
| Rule ID | Status | Evidence |
|---|---|---|
| ABC-1a | PASS / FAIL / MISSING_EVIDENCE / NOT_APPLICABLE | file:function + test/run evidence |
| LEGACY:path/to/rules.md#1 | PASS / FAIL / MISSING_EVIDENCE / NOT_APPLICABLE | quoted source unit + file/function/test evidence |

## Public ingress matrix
| Ingress | Validation/normalization | Before expensive work? | Production-path test/evidence |
|---|---|---|---|
| <offline/API/chat/internal entry> | <owner and behavior> | yes/no/N/A-with-evidence | <evidence> |

## Producer-consumer trace
| Value or contract | Producer | Transformations | Final consumer | Stop/failure owner | Evidence |
|---|---|---|---|---|---|
| <field/behavior> | <source> | <every handoff> | <actual reader> | <boundary> | <evidence> |

## Open findings
- P0/P1/P2 or `none`; each finding states the failure, why this diff owns it, and the smallest fix.

## Completion
OWNER RULE COVERAGE: <rules path>: X/Y stable IDs inventoried — A pass / B fail / C missing evidence / D not applicable
AUDITS RUN: coverage,ingress,producer-consumer,duplication,layering,edge-cases,surface-area — N findings (Pa P0, Pb P1, Pc P2)
```

每个稳定 ID owner 各写一行 `OWNER RULE COVERAGE`。旧规则页没有稳定 ID 时传 `--legacy-rules`，按文件顺序给每个项目符号、普通段落和 Markdown 表格数据行写一行连续编号的 `LEGACY:<rules path>#N`，尾签写 `OWNER RULE COVERAGE: <rules path>: X source units inventoried — A pass / B fail / C missing evidence / D not applicable — legacy-unstructured, no exact clause-coverage claim`。脚本只核对这些机械源单元是否齐全，不声称能把一个自然语言段落自动拆成精确子句。完全没有 `rules.md` 时在规则表写 `OWNER RULES: none`，尾签写 `OWNER RULE COVERAGE: none: 0/0 stable IDs inventoried — 0 pass / 0 fail / 0 missing evidence / 0 not applicable`。其他表仍要完成；不适用的入口或行为必须保留一行 `N/A-with-evidence`，不能删除整张表。

## 机器检查

把 reviewer 输出保存为 Markdown 后运行：

```powershell
python tools/check_review_report.py --report <review.md> --rules <stable-owner-rules.md> --legacy-rules <legacy-owner-rules.md>
```

多个 owner 重复传 `--rules`。脚本检查必需章节、规则 ID 是否逐条且只出现一次、两张矩阵是否有真实非占位行以及完成尾签；它不判断证据真假，也不把 `FAIL` 或 `MISSING_EVIDENCE` 自动改成通过。最终交付前增加 `--require-clean`，同时拒绝 owner 规则中的 `FAIL` / `MISSING_EVIDENCE` 和完成尾签中非零的开放 finding 数。

脚本失败时，主 agent 只把缺失项退回原 reviewer 补齐，不重新 framing，也不接受“已经找到足够多问题”。结构通过后，主 agent仍要抽查关键文件/函数证据。

## 何时继续读取详细指南

- 需要完整可粘贴 prompt 或专项 owner 角色：[reviewer lens prompt](reviewer-lens-prompt.md)
- 涉及 async、资源生命周期、性能证据或 rebase：[reviewer lens gates](reviewer-lens-gates.md)
- 需要理解四类开放审查方法：[reviewer lens audit](reviewer-lens-audit.md)
- public API、跨阶段字段或协议矩阵：[reviewer lens contracts](reviewer-lens-contracts.md)
