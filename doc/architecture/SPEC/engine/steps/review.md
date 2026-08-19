# engine/steps/review/ —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~900（6 个文件） · step 库（评审） · refactor-status: ok`

## 职责
条件式 patch 门 + PR 评审 agent step 及其仓库中立的 prompt 体系。
它曾是一个 341 行的模块；现在是一个把评测调优过的 prompt 数据、handler、
确定性 helper 三者分开的包。

## 包内布局（一个文件一个关注点）
- `__init__.py` —— import `steps` 以触发 `@step` 注册副作用；再导出公开契约（见下）。无逻辑。
- `prompts.py` —— 由评测得出的 prompt 数据：`_REVIEW_SYSTEM`、`_REVIEW_LENSES`、
  `_REVIEW_MERGE`。约 120 行文本，**移出控制流之外**。
- `utils.py` —— 确定性、无 LLM 的 helper：`_sweep_targets`、`_render_review_md`、
  `_SEVERITY_ORDER`。
- `steps.py` —— 两个 `@step` handler：`review.patch_gate`（validation/read）、
  `agent.review_diff`（agent/read）。
- `anchor.py` —— 基于代码片段的评论锚定（2026-08 新增）。
- `repo_tools.py` —— 只读的变更考古工具组（2026-08 新增）。

## 公开契约（可从 `engine.steps.review` import）
`_REVIEW_LENSES`、`_render_review_md`、`_sweep_targets` —— 由包的 `__init__` 再导出，
使拆分前的 import 路径保持不变。

## 不变量
- patch 门：廉价摘要**常开**，只有触发时才跑 LLM 评审；**fail-closed**（**C6**）；
  高风险模块来自 adapter，settings 只作兜底（**A5**）。
- 评审：领域 checklist 由 profile 的 `review.md` 扩展；`_sweep_targets` 以
  `repo.language` 为键，**诚实降级**；裁决自洽（任何 ≥minor 的评论 ⇒ REQUEST CHANGES）；
  确定性的按严重度排序的评论上限。
- prompt 是仓库中立的（**A5**）。
- **要引用，不要行号**（`anchor.py`）。模型给错行号的频率高到发布时必须降级该发现；
  修法是**换一个问题** —— 让模型引用它在说的代码，位置由程序自己算。校验器**仍然最后
  跑**，所以"绝不发布错锚点"的保证不变；变的是**只有行号错**的发现能保住自己的 inline
  位置，而不是被降级进正文。
- **裁决校准**：只有**已验证**的 blocker/major 才阻塞；minor 降级为 COMMENT，
  自述不确定的发现**永不阻塞**。
- **带着评论的升级会被抢救成一次成功的 REQUEST CHANGES** —— **找到缺陷本来就是一次成功
  的评审**。
- **考古工具是召回机器，不是便利设施**（`repo_tools.py`）。wave-2 取证测出：基线能做而
  我们的 pass 做不到的那些判官决定性动作，**全都是只读工具集当时恰好缺少的一条命令**
  （`git diff --stat base..HEAD` 证明被要求删除的东西压根没删；读 merge-base 版本的
  文件；`git show` / `git log -S`）。
- **覆盖率驱动的第二轮**由该 run 自己的覆盖空洞播种；**验证账本**会把这次 run 其实已经
  写下来的残余提升为发现 —— 取证发现，**漏掉的东西往往已经被赞许地记下来了，只是没被
  提出来**。
- **重复发现会合并到最丰富的那条陈述，而不是被丢弃**（`_dedupe_comments` + `_richness`，
  v20）。丢掉后出现的那条重复，会丢掉其中证据更好的那一份 —— 所以去重必须是**合并**，
  因为两份副本很少同样有据。
- 主体打分会把路径标识符坍缩成 basename（`_topic`），于是"用完整路径"和"用裸文件名"
  陈述的同一个发现会被识别为一条。
- **只有当一条评论确实同时具备主张和论证时，才发出 claim headline**
  （`_split_claim`，v21 及其修复）。只有一句话的评论会渲染成朴素的
  `file:line [sev] — text` 形状，而不是一个残缺标题；且 headline **永不截断**：
  第一版截到 160 字符，结果 49 条里有 34 条停在悬空的连接词上，
  **读起来比它所替代的那段还差**。那次提交里记下了一条长期教训 ——
  主张/论证的切分**无法从并非按此写就的散文里确定性地还原**，
  要可靠地拿到它，需要 reducer 直接产出一个 title 字段，
  **那是模型层的改动，不是渲染层的**。

## 边界 —— 不属于这里
不含 agent 运行时治理（那是 `agent_runtime`）；不写 adapter/profile。

## 依赖（允许）
`review/*`、`engine/step`、`.._common`、`..agent_runtime`、`profiles/languages`。

## 测试
`test_review_step.py`、`test_agent_ensemble.py`、
`test_profile_steps.py::test_review_guidance_from_profile`。

## 精简 —— **K2**（共享语言规则，已应用）
`_sweep_targets` 消费 `profiles/languages.py::sweep_re` —— 那是"按语言规则"三份旧副本
之一（另两份在 `profiles/establish`、`repo_map`），现已收敛到那个唯一来源。
未知语言时的诚实降级（只做文件级 sweep）**被保留**。
