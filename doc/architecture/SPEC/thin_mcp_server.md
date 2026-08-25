# thin_mcp_server.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~1286 · 默认 MCP：Direct 路由 + Strict 入口 · refactor-status: oversized`

## 职责
安装器**实际注册**的那个 MCP 门面：以**零模型**提供 Direct 模式的知识路由，
并在被要求时桥接到 Strict。

## 功能
七个工具：`review`（按 `mode` 分流）、`validate_direct_review`、
`get_review_status` / `get_review_result`（转发给 `CopilotMCP`）、
`update_knowledge`、`doc_search`、`doc_read`。

## 公开契约
上述七个工具；`build_mcp(...)`；`main()`。

## 不变量（**C1**、**C2**、**D1**）
- **Direct 在这个 server 里不跑任何模型。** 它返回知识路由和一份治理契约；阅读由
  **宿主自己的模型**完成。执行主脊完全不参与。
- **治理靠数据，因为 server 管不住宿主。** "该怎么审"被编码成随返回值一起下发的结构化
  字段：≤3 条路由（内嵌 `quick_map`，3.5k 封顶）、一个硬性的 `execution_budget`、
  一份 checklist，以及 `mandatory_review_guides` —— 跨 owner 的强制评审程序
  （`_DIRECT_MANDATORY_REVIEW_GUIDES`），**失败即关闭**：路径解析不了就报错，
  而不是悄悄发一份少了它的契约。它们也计入 `execution_budget` 的
  `knowledge_file_reads`，所以下发一份读不完的预算是不可能的。
- **`validate_direct_review` 检查的是结构，不是证据真伪**：恰好一条最终评论、
  `subtraction_signal` 的自洽性（`none` 不得附带证据；`triggered` 需要减法项或最小性
  证明）、以及证明本次评审读的是固定提交的 `evidence_head_sha`。
  **它不能也没有**去验证被引用的证据是否真实 —— 声称它能，比不声称更糟。
- **路由绝不静默替换。** `title`/`body` 选 owner；`changed_files` 通常只做范围校验。
  它们只在**最后手段**下选路（当存活路由无一命中它们推导出的 owner 时），且该情况是
  **显式的**：`status="scope_fallback"`、`selected_by="title_body+changed_files"`，
  且每条这样的路由都会说明理由。
- **仓库守卫先跑。** 不支持的仓库在任何路由推导**之前**就返回
  `unsupported_exact_router` —— 否则一个没有描述的、来自陌生仓库的 PR，会被喂上
  本仓库的 owner 知识。
- `_knowledge_path` 阻止逃出知识根；`_guard` 把异常转成 `{"error": ...}` 值返回，
  而不是协议层错误。**唯一的例外是 `_contributing_entry`**：贡献入口随文档搬到了
  `doc/knowledge/`，已经不在知识根内，所以它按设计不走 `_knowledge_path`，而是
  在源码树和 wheel 旁的两个候选路径里定位，都找不到才抛。它是一个写死的常量路径，
  不接受调用方输入 —— 逃逸防护针对的是后者。
- **Strict 绝不启动注定失败的 run**：Strict 分支先查 `strict_readiness`，
  改为返回缺失项。
- `update_knowledge` 只返回知识贡献入口 —— 它**不是** `imupdate` 的发版审计器。
- **每个工具都声明 `ToolAnnotations`，且提示必须真实。** 审批门控的宿主（codex 对
  无注解工具逐次弹批准框，headless 下自动取消，见 #86）靠这些提示放行只读面：
  `review` 是唯一保留状态变更（预留 Strict run）与触网（Strict 子进程）的工具，
  其余六个全部 `readOnlyHint=true`。把一个会写的工具标成只读，比不标更糟。
  （要求 `mcp>=1.8`，注解类型自该版本起可用。）

## 边界 —— 不属于这里
Direct 路径里不调模型；不含 Strict 后台机器（`mcp_server.py`）；不定义策略
（`mcp_policy.py`）。

## 依赖（允许）
stdlib + `mcp` extra + `.adapters` + `.config` + `.intent.resolve_repo_alias` +
`.knowledge_docs` + `.mcp_policy` + `.mcp_server`。

## 测试
`test_thin_mcp_server.py`、`test_thin_mcp.py`、`test_imreview_output_contract.py`。

## 重构备注
约 1286 行，是包里**最大**的模块，且自上次核对以来又长了约 480 行；Direct 路由
helper（`_direct_*`，现有 6 个）是一个内聚单元，如果再次增长，那就是显而易见的
拆分点。**拆分时务必保住"server 不跑模型"这条
性质 —— 它就是 Direct 模式的产品承诺。**
