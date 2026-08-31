# sdk/ —— 规范

<!-- verified-against: 2026-08-31 -->

`Python SDK v1 · 跨仓库唯一 typed 边界 · refactor-status: ok`

## 职责

给 ReviewBot 等嵌入式宿主提供一个版本化、可序列化、wheel-safe 的公开 API：
`infermatrix_copilot.sdk.v1`。宿主不得再 import `mcp_server`、`config`、
`thin_mcp_server` 或其私有 helper。

## 公开契约

- `get_capabilities()` / `DirectClient.capabilities()` 返回 typed
  `Capabilities`：distribution/SDK/Direct/Strict/Knowledge 版本、resource revision、支持仓库、
  expected-head/structured-result/post-false/file-lock/idempotency 能力与 worker 上限。
- Direct：`DirectReviewRequest` → `DirectClient.plan()` → `DirectReviewPlan`；
  `read_document(document_id, offset, max_bytes)`；
  `DirectCompletionRequest` → `validate()` → `DirectCompletionDecision`。
- Strict：`StrictRuntime(settings_overrides=...)`，以及
  `capabilities` / `readiness` / `reserve_review`（`start_review` 别名）/
  `get_status` / `get_result` / `close`。
- Knowledge：宿主把不可信输入投影成 `KnowledgeEvidenceEvent` / `KnowledgeEvidenceBatch`，
  再依次调用 `KnowledgeCurator.build_prompt()`、自己的 model adapter、
  `validate_proposals()` 与 `apply()`。返回值为 typed
  `KnowledgeProposalValidation` / `KnowledgeApplyResult`；validator 失败以
  `KnowledgeValidatorError.result` 携带完整、可序列化的失败结果。
- 所有公开 dataclass 皆 frozen，并有 lossless `to_dict()`。

## 不变量

- **公开 import 无副作用**：单纯 import `sdk.v1` 不加载 `config`、legacy
  `contract`、`direct_routing` 或任一 server；Direct provider 实现在调用
  `plan`/`validate` 时才加载，Strict server 在构造 `StrictRuntime` 时才加载。
- **只跨 document ID，不跨 provider filesystem path**：知识入口、route、guide、
  map 与 fallback 均为相对 knowledge-root 的 ID；`read_document` 拒绝 absolute、
  traversal 与 bundle 外路径。Strict result 丢弃私有 `report_path`，保留 report
  内容、分页游标和结构化 result。
- **资源由 artifact 定义**：`sdk._resources` 用 `importlib.resources.files` 找
  wheel 内 `knowledge` 与 `_runtime/adapters`，用 marker 校验；editable checkout
  才回退仓库根。resource revision 跳过 `__pycache__`/bytecode，保证 clean wheel
  与源码内容寻址不被解释器副产物污染。
- **Direct completion fail closed**：context ID 不只是长得像 hash；它必须由同一
  `DirectClient.plan` 签发、expected head 必须一致、资源 revision 不能漂移。
  签发缓存为有界 LRU（默认 256），被淘汰/未知 context 都拒绝完成。
- **Strict created 语义真实**：SDK 从 core 的 `(run_id, created)` 读取；命中
  idempotency key 的重试返回 `created=False` 且绝不再次入队。review depth 只经
  policy allowlisted `params` 传入。
- **知识规则由 provider 唯一定义**：catalog 只暴露当前仓库 owner 与 general 的
  `rules.md` document ID；prompt 把事件放进唯一 `<untrusted_data>` fence，proposal
  shape、rule ID、heading、source citation、目标页和重复 ID 都由 SDK 机械校验。
  `proposal_id` 同时绑定 batch、输入下标、repository、section、sources 与目标页
  SHA，宿主不能在 model call 后静默改写已接纳 proposal。
- **知识 apply 是 append-only transaction**：只追加完整 rule section 并更新唯一
  `updated:` frontmatter；写前复核 page SHA。固定且按序执行
  `knowledge/tools/check_knowledge_tree.py`、`knowledge/tools/check_wiki_lint.py`；
  validator 缺失则写前 fail closed，执行失败/超时则逐 byte rollback 全部目标页。
  同一 work checkout 的 writer 以 process 内 mutex 与位于系统临时目录的
  `flock` 串行化；等待后的 SHA 复核让第二个 stale writer 失败，不会覆盖首个结果。
- **知识 orchestration 留在宿主**：SDK 不 clone、调用 model、管理 ledger、commit、
  push、开 PR 或 schedule。ReviewBot 必须向 `KnowledgeCurator` 传 dedicated work
  checkout，并继续拥有重试、artifact 与 fork publication；SDK 也绝不写 packaged
  knowledge tree。
- SDK、Direct、Strict、Knowledge API 版本常量均为 `1.0.0`，distribution 为
  `0.2.0`；`Capabilities.knowledge_api_version` 与
  `supports_knowledge_curation` 组成 ReviewBot 的 paired-release 握手，避免只按
  wheel 名称误接缺失知识 API 的 artifact。后者只有完整 apply 所需的 process file
  lock 在当前平台可用时才为 true，否则 fail closed；旧 `contract.py` 仅做
  dict/helper 兼容投影，不拥有第二套版本事实。

## 依赖方向

`sdk.v1.models` 为纯 stdlib 模型；`direct` import-time 只依赖模型与资源解析，
函数调用时才向下进入 `direct_routing`；`strict` 构造时才向下进入
`Settings`/`CopilotMCP`。`knowledge` 只依赖 stdlib、公开模型和显式 work checkout，
并以 subprocess 运行上述两个固定 validator。任何 server 都不得被 SDK package
initializer 反向 import，provider domain 也不得反向依赖 ReviewBot。

## 测试

`test/test_sdk_v1.py` 钉住公开 import 边界、两 adapter wheel 路由、无绝对知识
路径、有界 context 绑定、feedback/disposition 透传、Strict serializer/path
边界和真实 runtime capabilities smoke；CI 另在 clean venv 中安装 wheel 再执行
公开 API smoke。`test/test_sdk_knowledge_v1.py` 钉住 repo-scoped catalog、prompt
fence、strict proposal shape/ID/source/page 校验、typed index accounting、append-only
写入、固定 validator 顺序、missing-validator fail-closed、multi-page byte rollback、
tamper/stale detection 与两个 curator 的 writer serialization；测试只创建临时
knowledge checkout，不改仓库真实 `knowledge/`。
