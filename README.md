# InferMatrixCopilot

给 Codex、Claude Code、Cursor 等 coding agent 注入 vLLM-Omni 项目经验，
让 PR 审查更符合维护者规则。
它不运行第二个模型，也不会自动发布评论。

## 一键安装

```powershell
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

# 只运行与你的 Agent 对应的一条
.\install-codex.ps1    # Codex
.\install-claude.ps1   # Claude Code
.\install-cursor.ps1   # Cursor
```

脚本会自动安装 MCP 和 `imreview` skill。重启 Agent 后：

```text
/imreview <PR URL>
```

不传 URL 时默认审查当前 PR 或工作区，始终使用 Direct 模式。其他 MCP 宿主和
手工配置见 [`doc/MCP.md`](doc/MCP.md)。

## 它能做什么

| 能做 | 不能做 |
|---|---|
| 把知识库入口交给当前 Agent 模型 | 不运行第二个模型 |
| 让 Agent 按知识库地图选择相关规则 | 不替模型选择知识页面 |
| 辅助审查 vLLM-Omni PR 或本地改动 | 不自动发布 GitHub 评论 |
| 把知识维护入口交给 Agent，由 Agent 直接修改 Markdown | 不在 MCP 内部自动改写规则 |

默认是 **Direct 模式**：当前 Agent 负责读取代码、理解改动和输出审查结果；
InferMatrixCopilot 只提供知识库入口。

## 怎样确认它真的被用了

先用 `/mcp` 或下面的命令确认 `infermatrix_copilot` 已连接：

```powershell
codex mcp list
```

Direct `review` 的 MCP 返回很短：

```json
{
  "knowledge_entry": "C:\\...\\InferMatrixCopilot\\knowledge\\AGENTS.md"
}
```

Agent 随后从这个入口读取文档地图，自行判断应使用哪些规则，再正常输出
带文件和行号的 review findings。MCP 不返回预制审查结果，也不一次性注入完整规则。

## 更新知识库

对当前 Agent 说：

```text
Use InferMatrixCopilot to update the knowledge base with the reusable rule
from this review.
```

`update_knowledge` 只返回：

```json
{
  "knowledge_entry": "C:\\...\\InferMatrixCopilot\\knowledge\\CONTRIBUTING.md"
}
```

Agent 按该入口已有的目录地图和落盘规范，自行选择 owner、修改 Markdown、
更新索引并执行文档中要求的校验。MCP 本身不猜 owner，也不写规则。

## Direct MCP 工具

- `review(target, repo?)`：返回审查知识入口。
- `update_knowledge(repo?)`：返回知识维护入口。
- `doc_search(query, repo?)`：按文本搜索知识库。
- `doc_read(path, repo?)`：读取指定知识页面。

Direct 模式不需要 API Key、endpoint 或额外模型配置。

## Strict workflow mode

For stronger process adherence, ask the host agent to use **strict workflow mode**.
InferMatrixCopilot then owns a persistent `evidence → gates → review → verify`
state machine while the host agent's current model performs each reasoning step.

## 其他模式

- Strict 模式的状态机用法见
  [`docs/codex/README.md`](docs/codex/README.md)。
- 自主工作流会运行自己的模型，是另一套产品入口，见
  [`docs/autonomous-workflow.md`](docs/autonomous-workflow.md)。
- 项目内部设计和实现说明见 [`doc/`](doc/)。
