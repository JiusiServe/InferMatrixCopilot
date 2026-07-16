# Code Taste

**硬规则:** 凡是要写业务代码、测试代码、示例代码、API 字段、CLI 参数、helper 函数，动手前先读本页。

这不是多跑一个 pass。人工 reviewer 抓的是代码气味：名字误导、逻辑住错层、helper 重复、测试放错、注释没解释策略、API 面膨胀、diff 像临时补丁。测试通过只能证明这条路径没坏，不能证明代码有品味。

## 写前先停一下

如果脑子里出现这些句子，先停：

- "先放这里吧"
- "这个名字差不多"
- "测试放这里也能跑"
- "复制一份最省事"
- "reviewer 应该能看懂"
- "这个参数以后可能有用"

## 8 条硬标准

1. **命名说机制。** 名字必须说清控制对象和机制，且匹配 helper 抽象层级。不要用 `force_ratio`、`align_size`、`compat` 这种需要口头解释的名字。
2. **逻辑住 owner。** 看数据和语义长期归谁，不看哪个文件方便改。Resolution/bucket 归 processor，AR token 限制归 sampler/model executor，HTTP 字段透传归 serving/protocol。
3. **新 helper 默认有罪。** 先 grep repo、upstream、AR/DiT 对侧实现和测试 fixture。写出 "mirrors X" 时，下一步是问为什么不复用 X。
4. **测试放行为 owner。** 测试文件要让 reviewer 一眼知道为什么在这里。只为了 import 方便而放到相邻 test，是错层。
5. **测试绑定当前 diff。** 每个新增测试必须对应 reviewer comment、当前 PR contract、明确 bug、或刚修复 diff 的最小 regression。答不出就删或移到 owner。
6. **注释解释策略。** 注释只解释 upstream 对齐、多分支选择、不变量、非显然边界；不要解释语法。
7. **diff 自带说服力。** 提交前按 [全量 diff 审查](reviewer-lens-gates.md#full-diff-review) 确认真实基线、当前 tracked 改动和属于本任务的 untracked 文件。文件列表、命名、注释、测试位置、helper 复用、silent fallback 都要经得起第一眼 review。
8. **条件分支要有正反对照。** 新增或修改选择、过滤、拦截或路由条件时，必须从同一个对外或生产入口至少测一个“应进入”和一个“不应进入”的例子，并断言用户或系统能观察到的结果。两个输入结构相同但语义不同时尤其容易漏测；只测负路径会让“把整个功能禁用”也误绿。

## 写完不等于完成

非琐碎开发任务在作者自测后，还必须进入 [开发交付的维护者审查闭环](../../agents/guides/agent-loop-workflow.md#开发交付的维护者审查闭环)。作者不能用“自审 0 finding”代替独立 reviewer；修复 finding 后也不能只验旧问题，必须重审当前完整 diff。

## 需要下钻的场景

- 新增 CLI/API/config/`extra_args`/`mm_processor_kwargs`/multimodal key/bridge 字段，或新增 optional fast-path 参数：读 [code_taste_api_surface](code-taste-api-surface.md)。
- 新 execution path 复用 request parsing、改 shared state/schema、处理 inline review、准备 push 前模拟人工 reviewer：读 [code_taste_review_flow](code-taste-review-flow.md)。
- 需要 sub-agent 或 push 前四项 reviewer-lens audit：读 [reviewer_lens_audit](reviewer-lens-audit.md)。

## 常见 owner 提示

- serving/chat shared path 只保留用户 payload 语义，不把单个模型的 multimodal key 规则推广为全局规则。
- consumer 不 hardcode producer 的 enum / token range / valid values。
- 如果要把数据搬出去才能算，通常逻辑放错层。把逻辑搬到数据 owner，而不是复制数据。
- 新建 dedicated owner test 文件比污染相邻 test 更好。

## 触发词

用户说这些话，下一次写代码前必须更认真读本页和下钻页：

- "代码品味"
- "人工 reviewer"
- "为什么会被发现那么多问题"
- "以后写代码必须看"
- "不要只是能跑"
- "像补丁"
