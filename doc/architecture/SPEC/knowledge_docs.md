# knowledge_docs.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~122 · 供 MCP 面使用的只读知识检索 · refactor-status: ok`

## 职责
对那棵精选 Markdown 知识库的跨平台、按仓库限定的**只读访问** ——
`doc_search`/`doc_read` 的底座。

## 公开契约
`KnowledgeDocs`（search、read）、`KnowledgeDocsError`。

## 不变量（**C1**、**D1**）
- **限定在切片内**：general 切片加上**单个**仓库的切片。知识根之外的路径一律拒绝
  （`KnowledgeDocsError`）—— 这就是防路径逃逸的守卫。
- **只读。** 这里**根本没有写入面**；知识写入走别处的 candidate/类型化 op 路径。
- 读取是**分页**的（每页 24k），因此一个大页面不会把宿主对话撑爆。
- 检索是确定性的词重叠打分 —— **不调模型**。

## 边界 —— 不属于这里
不撰写知识、不提 candidate、不在代码里放仓库专属规则（那棵树是数据面）。

## 依赖（允许）
仅 stdlib。

## 测试
`test_knowledge_source.py`、`test_thin_mcp_server.py`。

## 重构备注
**保持它不含模型**：这是 Direct MCP 路径与工具桥共用的**唯一**知识读取器，
在这里加一次模型调用，等于把第二个模型塞进了"server 不跑模型"这条保证里面。
