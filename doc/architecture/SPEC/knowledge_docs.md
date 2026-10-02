# knowledge_docs.py —— 规范

<!-- verified-against: 2026-10-02 -->

`LOC ~280 · 供 Direct 与 Agent 共用的只读知识检索 · refactor-status: ok`

## 职责
对那棵精选 Markdown 知识库的跨平台、按仓库限定的**只读访问** ——
`doc_search`/`doc_read`/`doc_related` 的底座。

## 公开契约
`KnowledgeDocs`（search、read、related）、`KnowledgeDocsError`。

## 不变量（**C1**、**D1**）
- **限定在切片内**：general 切片加上**单个**仓库的切片。知识根之外的路径一律拒绝
  （`KnowledgeDocsError`）—— 这就是防路径逃逸的守卫。
- **只读。** 这里**根本没有写入面**；知识写入走别处的 candidate/类型化 op 路径。
- 读取是**分页**的（每页 24k），因此一个大页面不会把宿主对话撑爆。
- 检索是确定性的词重叠打分 —— **不调模型**。

## 边界 —— 不属于这里
不撰写知识、不提 candidate、不在代码里放仓库专属规则（那棵树是数据面）。

## 依赖（允许）
stdlib 与 `knowledge_service.lifecycle` 的页面/完整深读正文解析；不依赖模型、配置或 server。

## 测试
`test_knowledge_source.py`、`test_knowledge_retrieval.py`、`test_thin_mcp_server.py`。

## 有界审查背景

`related(changed_files, query=...)` 只选当前 repo 的 architecture/guide；规则页、索引与
结构化接口卡不进入背景。确定性优先级为固定来源路径、生产入口、源码 glob，再结合
功能 ID/标题和正文词命中；相同 feature 去重，完整深读优先于基础功能页。
最多返回两页、每页 3,000 字符、总计 6,000 字符；优先完整 facet，超长单 facet 仍提供
截断片段并标 `more_available`。返回来源 pin、命中路径、已有/缺失 facet，不验证 PR head。
`available_facets` 表示页内可用维度，`included_facets` 表示本次正文实际注入的维度；
`not_injected_facets` 是已有但因预算未注入的维度，调用方可用原有有界读取补读。
`facet_basis` 与 `included_facet_basis` 分别对应已有及已注入维度的认可依据。
旧证明默认 `supported`；`verified_absent` 通过确定性缺失证明准入并在 `verified_gaps`
保留缺口标签；没有认可区块的维度仍是 unknown。核验缺失不代表能力已实现、测试已运行
或测试通过，不得把这类背景升级为约束性规则或从覆盖分母删去。
深读正文哈希、证明形状或重复 facet 有问题时不提供该块；上游证据验证仍属于 init/audit。
所有读取前调用同一 `verify`，包括最终被排除的接口卡；激活快照校验失败直接阻断。
是否超过 `semantic_depth.per_facet_gt`、每个功能是否具有认可知识和原生审批绑定，
统一由 init/audit/publication 判定；读取器不重新认证上游、调用模型或宣称全缺口已补齐。
完整候选 checkout 的源码与审批审计、检索验收、独立审查和 CI 应先于授权合并；
自动背景可用不等于实际 PR 质量已经测量。

## 重构备注
**保持它不含模型**：这是 Direct MCP 路径与工具桥共用的**唯一**知识读取器，
在这里加一次模型调用，等于把第二个模型塞进了"server 不跑模型"这条保证里面。

## 2026-09-28 快照校验
可选 `verify(rel)` 回调在 `read`/`search` 读取每个文件前调用；MCP 传入 `KnowledgeView.path`，快照中缺失或被改动的文件使读取/搜索 fail-closed。

## 2026-09-28 退役规则不再提供
`read`/`search` 经 `visible_text` 去掉退役规则后再返回。
