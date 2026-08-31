# direct_routing.py —— 规范

<!-- verified-against: 2026-08-29 -->

`LOC ~917 · Direct 模式完整策略包与知识路由 · refactor-status: known-debt`

## 职责
Direct 模式的知识路由：owner/model 路由表和选路机制。从
`thin_mcp_server.py` **逐字迁出**（下游曾经 `importlib` 拿它的私有名），
公开面由 `contract.py` 再导出。它显式携带仓库专属知识 —— 这正是
`contract.py` 必须保持中立而这里不必的原因；把表外置到
`adapters/<repo>/` 是**未被这次搬迁改变的既有欠账**。

## 公开契约
经 `contract.py` 再导出的五个名字：`direct_review_plan`（完整、一次性的
Direct policy bundle）、`direct_knowledge_routes`、
`direct_execution_budget`、`direct_completion_result`、
`direct_mandatory_review_guides`。其余全部下划线私有 —— 仅供
`thin_mcp_server` 既有调用点/测试使用（它继续直接 import 下划线名）。

## 不变量
- **repo 守卫最先跑**：不支持的仓库在任何路由计算之前被拒 —— 修的是一个
  真实历史 bug（守卫曾排在空 intent 提前返回之后，向不支持的仓库泄漏
  owner 知识）。
- **quick map fail-closed**：`_direct_quick_map` 返回内嵌代码地图与状态
  `{ok, truncated, unavailable}`，`truncated` 不是装饰 —— 把残图当全图
  与缺图同罪、且更难察觉；`_direct_route` 据此置
  `read_required = status != "ok"`（"自己去打开"是真回退，"什么都不给
  又不许看"不是）。
- adapter-backed changed-file 路由同样拆开 `(quick_map, status)`，绝不把 tuple
  当成文本跨边界，也绝不把 unavailable 误报成无需读取。
- knowledge/adapters 根由 `sdk._resources` 的 `importlib.resources` 解析，editable
  source 与安装 wheel 走同一标记校验；仓库路径只留在本模块内部的旧版 dict，
  `sdk.v1.DirectClient` 对外转换为 document ID。
- **changed files 校验选择、绝不静默替换选择**：title/body 选 owner，
  diff 只报告支持或矛盾；scope-fallback 是最后手段且永远显式
  （`status="scope_fallback"`）。
- `_direct_execution_budget` 是**硬顶**预算字典（`hard_ceiling=True`、
  一次有界扩展）；docs-only PR 走更便宜的 profile。
- `_direct_completion_result` 是**机械结构门**，不校验证据真假：
  单条最终评论、`subtraction_signal ∈ {none, triggered}`、
  `evidence_head_sha` 7–40 位十六进制、`existing_feedback_status` 枚举、
  `finding_dispositions` 的 anchor/disposition/existing_thread/
  head_recheck 约束。
- 叶子模块：**绝不** import 任何 server 模块
  （`test_contract.py::test_direct_routing_does_not_import_a_server_module`）。

## 边界 —— 不属于这里
不执行、不调模型；只有路由表 + 机制。多 adapter 桥接经
`_normalize_repo`/`_adapter_for_repo` 走 `adapters/`。

## 依赖（允许）
stdlib + `.adapters`（AdapterError / AdapterRegistry / RepoAdapter）+
`.sdk._resources`。
位于 `contract.py` 和 `thin_mcp_server.py` 之下。

## 扩展点
新 owner 路由/模型规则 → 表数据；跨仓库通用化 → 外置进
`adapters/<repo>/routing`（既有欠账的正解，不是在这里再长表）。

## 测试
`test_contract.py`（公开家、import 方向、中立性豁免）；
`test_thin_mcp_server.py` / `test_thin_mcp.py`（经新家继续锻炼全部
下划线函数：路由、预算、完成门）。

## 重构备注
768 行里约 500 行是表数据。`known-debt` 指的就是表：机制是稳定的，
表的归宿在 adapter 数据面（见结构重组计划 Stage 8 的 routing.yaml 方案）。
