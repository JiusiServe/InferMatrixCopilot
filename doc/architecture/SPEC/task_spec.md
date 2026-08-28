# task_spec.py —— 规范

<!-- verified-against: 2026-08-28 -->

`LOC ~104 · 任务层，纯数据 · refactor-status: ok`

## 职责
定义 `TaskSpec`（意图解析的结构化产物），并从任务 kind **推导**出它的权限 **tier**。

## 功能
持有 kind/repo/pr/issue/flags；计算 `tier`、`read_only`、`confirm_required`，
以及给人看的 `describe()`。

## 公开契约
`TaskSpec(kind, repo, pr?, issue?, report_only, post, params,
expected_head_sha?, repo_path?)`；property `tier`、`read_only`、
`confirm_required`；`describe()`。常量：`TaskKind`（7 种 kind）、
`READ_ONLY_KINDS`、`KIND_TIER`、`FULL_SHA_RE`（40 位十六进制全长 SHA 的
唯一真相正则，`mcp_policy.py` 复用它校验）。

## 不变量
- **C1**：**不存在可设置的 tier 字段**；`tier = KIND_TIER[kind]` —— 文本无法把它扩大。
- 只读 kind 的 `read_only` = `not post`，其余为 `report_only`；
  `confirm_required = not read_only`。
- **快照绑定字段只收窄，绝不扩权**（C1 完整无损）：`expected_head_sha`
  （field_validator 强制 `FULL_SHA_RE`；设置后 run 只准评审这个 head，
  否则以 stale 停下）与 `repo_path`（预约时冻结、由
  `mcp_policy.authorize_repo_path` 授权的 canonical checkout；空 = 按环境
  解析，即所有 CLI run）都是惰性数据 —— 它们缩小 run 接受的输入，
  从不改变 run 被允许做的事。

## 边界 —— 不属于这里
不解析、不做 I/O、不执行、不含仓库知识。纯数据 + 推导。

## 依赖（允许）
仅 `pydantic`。

## 扩展点
新 kind → 加进 `TaskKind` + `KIND_TIER`（只读的话再加 `READ_ONLY_KINDS`）。

## 测试
`test_intent_taskspec.py`。

## 重构备注
干净、极简 —— "单一职责"的范例。**不要**在这里加行为；保持它是"数据 + 推导"模块。
它是 C1 的唯一真相来源，所以任何**别处**出现的权限逻辑都是坏味道。
