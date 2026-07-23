---
title: "Reviewer-lens audit"
created: 2026-07-10
updated: 2026-07-23
type: guide
tags: [general, review]
sources: []
---

# Reviewer-lens audit

**Why:** PR #3626 证明普通 "code check" 护不住 review：sub-agent 说 OK，但 reviewer 仍抓到重复算法、错层、非连续 token id 和冗余 surface。Reviewer-lens 的目的不是让 sub-agent 拍板，而是把 reviewer 会看的维度显式化。

需要立即执行独立审查时先用短入口 [独立审查执行合同](review-execution-contract.md)。本页解释审查方法，不能替代执行合同要求的覆盖报告和机器检查。

派生自 [review_delegation_framing](../../agents/guides/review-delegation-framing.md)：那条管怎么 spawn，这条管必须审什么。

## 先分类再审

不要先找 bug。先判断这个改动改变了哪类工程系统性质，再决定要跑哪些 lens。最少输出这些字段：

```text
Review risk tags:
- public API / user-facing contract:
- module semantic contract:
- cross-module producer-consumer contract:
- async / concurrency / scheduling:
- resource lifetime / cleanup:
- data format / serialization / IPC:
- performance claim / benchmark evidence:
- error handling / cancellation / timeout:
- feature flag / config / default behavior:
- backward compatibility:
- test or validation evidence:
Selected lenses:
```

## 先审已知不变量，再开放找问题

先确认主要 owner；只有 live producer-consumer trace 证明 diff 跨越其他 owner 边界时，才沿调用链增加 owner。owner 定义审查触发组时，只建立 `core` 加当前 diff 命中组的稳定 ID 清单；没有组时才全页枚举。组内每个 ID 都输出 `PASS / FAIL / MISSING_EVIDENCE / NOT_APPLICABLE` 和证据，未触发组不靠几十行 `NOT_APPLICABLE` 制造完整感。

旧规则没有稳定子 ID 时，以每个项目符号或普通段落作为 source unit，原文引用后逐项列出其中识别到的规范性要求，尾签标成 `legacy-unstructured`。这种页面可以完成审查，但不能声称精确 clause coverage；实质修改该规则时应先按贡献规范补 ID。不能运行时靠关键词解析自然语言总数。

没有 owner `rules.md` 时明确写 `OWNER RULES: none`，继续执行 contract 和开放审查；不能自行读取 incidents/history 来猜规则。尾签中每个 owner 的已审条数必须等于所选触发组去重后的规则数；未定义组时才等于整页稳定 ID 总数。

这一步和开放式 finding 是两轮：第一轮防止已经沉淀的错误复发，第二轮再找规则之外的新问题。找到很多新 P1 不能抵消已知不变量漏审。

```text
OWNER RULE AUDIT:
- <owner path> <rule id or quoted legacy unit>: PASS | FAIL | MISSING_EVIDENCE | NOT_APPLICABLE — <evidence>
```

命中 async / concurrency / scheduler / thread / process / IPC / shared memory / socket / file / cache / GPU-CPU transfer / pinned memory / lock / resource lifetime / performance claim 时，基础四项不够。必须加 systems/runtime owner；有性能、质量、可靠性、精度 claim 时还要加 evidence/benchmark auditor。没写 risk tags 和 selected lenses，只能叫 partial review。

## 先别这样问

这些 prompt 默认无效：

- "帮我 code check 一下"
- "看有没有问题"
- "review 一下这个 PR / commit / 改动"
- "static review 看下"
- "扫一遍" / "审一下"
- "确认一下没问题"

**原因:** 子 agent 只回答 prompt 框定的问题。没给 audit 维度，它没有判断 "出问题" 的标尺。

## 必跑四项

每次 push 前、spawn review sub-agent 前、准备把 PR 交给 reviewer 前，至少审这四项：

1. **Duplication:** 新函数 / class / 算法 / 常量是否已有 in-repo 或 upstream 实现。
2. **Layering:** 逻辑是否住在拥有数据和语义的 owner 模块。
3. **Edge cases:** range、边界、默认值、状态矩阵、real checkpoint edge 是否被覆盖。
4. **Surface area:** 新 public knob / API field / extra_args / schema / streaming protocol 是否真的必要，contract 是否完整。

新增或修改选择、过滤、拦截或路由条件时，Edge cases 必须从同一个对外或生产入口包含至少一个“应进入”和一个“不应进入”的对照，并检查两边可观察的结果。两个输入结构相同但语义不同时尤其要查；如果整个功能被禁用仍能让测试通过，就是实质性 finding。

P2 表示低严重度但仍需修复的实质问题。纯样式、不影响行为、可维护性和证据的建议单独标为 `nit`，不计入 P2。

直接粘贴用的 sub-agent prompt 在 [reviewer_lens_prompt](reviewer-lens-prompt.md)。

## 什么时候升级

下列场景不能只跑基础四项：

- 新模型 / 新 pipeline / 新 backend：语义 owner 查官方 parity，integration owner 查 topology、默认入口和 unaffected control，见 [reviewer_lens_gates](reviewer-lens-gates.md)。
- 新 public API、`extra_args`、`mm_processor_kwargs`、multimodal bridge：先写 contract matrix，见 [reviewer_lens_contracts](reviewer-lens-contracts.md)。
- streaming / SSE / WebSocket / OpenAI-compatible schema：按 public protocol surface 审，见 [reviewer_lens_contracts](reviewer-lens-contracts.md)。
- async / concurrency / scheduler / IPC / resource lifetime / GPU-CPU transfer / performance claim：加跑 systems/runtime owner 和 evidence/benchmark auditor，见 [reviewer_lens_gates](reviewer-lens-gates.md)。
- full diff review、rebase、inline review 处理、fix 后复审：见 [reviewer_lens_gates](reviewer-lens-gates.md)。
- 另一个 Codex / bot / reviewer 能在我写出的 diff 里集中发现多个问题：按 authoring-time self-review failure 处理，写代码过程中跑 authoring-time delta audit，见 [reviewer_lens_gates](reviewer-lens-gates.md)。

## 输出格式

每条 finding 必须先说人话：

1. 会发生什么坏事。
2. 为什么这是当前 PR 要管的事。
3. 最小收口是什么。

禁止只写 `contract` / `ABI` / `surface area` / `state matrix`。这些词只能当括号里的精确标签，前面必须有具体行为例子。

结尾必须写：

```text
OWNER RULE GROUPS: <grouped path>: core,<triggered groups>
OWNER RULE COVERAGE:
- <path or none>: X/Y selected stable IDs inventoried — A pass / B fail / C missing evidence / D not applicable
- <legacy path>: X source units inventoried — A pass / B fail / C missing evidence / D not applicable — legacy-unstructured, no exact clause-coverage claim
AUDITS RUN: coverage,ingress,producer-consumer,duplication,layering,edge-cases,surface-area — N findings (Pa P0, Pb P1, Pc P2)
```

缺这个尾签，就当 audit 没跑完。

## 适用方式

**自审:** push 前逐条写 review note，不要心算 "应该没问题"。

**Sub-agent review:** 用 [reviewer_lens_prompt](reviewer-lens-prompt.md) 的完整模板，不要把自己的怀疑原因塞进去。

**并行 multi-framing:** 高风险 PR 拆成两个同时运行且职责正交的只读 reviewer，不串行增加墙钟时间：

- 语义 reviewer：官方入口、token、stop、sampling、精度和模型语义。
- 集成 reviewer：默认 CLI、真实 topology、资源可用性、public ingress、online/offline 和 unaffected control。

两者使用相同基线、diff、owner 和任务合同，不能互看结果，也不能重复做一遍宽泛 producer-consumer 扫描。finding 标出命中的 owner rule；没有现成规则时标 `OWNER_RULE:NONE`。主 agent 自己 union 结果，重判 finding 影响的规则行，不再 spawn “汇总 agent”。

## 反模式

- "sub-agent 说 OK 我就 push 了"。
- 只 grep 仓库或 upstream 其中一边。
- 把 audit 当可选 thoroughness。
- commit message 写了 trade-off，但没写边界条件。
- 修完 finding 后不复审新增 diff。

## 历史案例

精简案例索引见 [reviewer_lens_cases](reviewer-lens-cases.md)。

## 链接

- [reviewer_lens_prompt](reviewer-lens-prompt.md)
- [reviewer_lens_gates](reviewer-lens-gates.md)
- [reviewer_lens_contracts](reviewer-lens-contracts.md)
- [reviewer_lens_cases](reviewer-lens-cases.md)
- [review_delegation_framing](../../agents/guides/review-delegation-framing.md)
- [upstream_first_for_algorithm](upstream-first-for-algorithm.md)
- [codex_review_lessons](codex-review-lessons.md)
