# direct_routing.py —— 规范

<!-- verified-against: 2026-09-29 -->

`LOC ~880 · Direct 模式完整策略包与仓库中立的知识路由 · refactor-status: stable`

## 职责
Direct 模式的知识路由**机制**。模块中不出现任何被服务仓库的名字：每个仓库的
owner/model 路由表是知识数据 `knowledge/repos/<repo>/_routes.yaml`，仓库别名
来自 `adapters/<repo>/manifest.yaml` 的 `repo.full_name`/`repo.aliases`。
公开面由 `contract.py` 再导出。

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
- **每请求一个 `KnowledgeView`**：入口函数在开始时解析一次视图（未设置
  `KNOWLEDGE_ROOT` 时为打包知识；设置时为激活快照的真实目录并按清单校验），
  本请求内所有读取经同一视图。模块不再在导入期缓存知识根；`_KNOWLEDGE` 只保留
  为模块级 `__getattr__` 惰性别名。
- **路由选择按数据而非仓库名**：仓库有非空 `_routes.yaml` → title/body owner
  路由 + 模型路由 + scope fallback；否则有 adapter → changed-file 路由；否则
  `unsupported_exact_router`。`_routes.yaml` 引用的页面不存在时 fail-closed。
- `repo` 必填：空值抛 `ValueError`，不再默认某个仓库；形似路径的仓库名直接
  视为不支持。
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
- **未测公开函数候选（#164）**：`direct_review_plan(..., diff="")` 有 diff 时带
  `untested_public_api`（`status=ok` + 候选 + 评审规则），只基于 diff 自身的测试
  文件——provider 没有 PR head 的 checkout，树内测试搜索由 agent 按 checklist 完成；
  无 diff 为 `{"status": "no_diff"}`，adapter 关闭时为 `disabled`。
- 叶子模块：**绝不** import 任何 server 模块
  （`test_contract.py::test_direct_routing_does_not_import_a_server_module`）。

## 边界 —— 不属于这里
不执行、不调模型；只有机制，路由表在知识数据里。多 adapter 桥接经
`_normalize_repo`/`_adapter_for_repo` 走 `adapters/`。

## 依赖（允许）
stdlib + PyYAML + `.adapters`（AdapterError / AdapterRegistry / RepoAdapter）+
`.knowledge_view` + `.sdk._resources`。
位于 `contract.py` 和 `thin_mcp_server.py` 之下。

## 扩展点
新 owner 路由/模型规则 → 改对应仓库的 `_routes.yaml`（schema_version 1：
`owners[{owner, path, signals, scope_prefixes}]`、可选 `models{dir, page}`）；
新仓库 → 提供 adapter 与 `_routes.yaml`，不改 `src/`。

## 测试
`test_knowledge_view_routing.py`（150 个真实 vllm-omni PR 的黄金路由输出、
第二仓库经自身 `_routes.yaml` 路由、快照切换下一请求生效、快照篡改 fail-closed、
SDK 完成校验钉住计划时快照、模块源码不含仓库名）；`test_contract.py`（公开家、import 方向、中立性豁免）；
`test_thin_mcp_server.py` / `test_thin_mcp.py`（经新家继续锻炼全部
下划线函数：路由、预算、完成门）。

## 重构备注
原 `_DIRECT_OWNER_ROUTES`/`_REPO_ALIASES` 已外置（`known-debt` 清零），
`test_v2_p0.py` 与 `test_repo_vocabulary.py` 中本模块的泄漏上限随之移除。
