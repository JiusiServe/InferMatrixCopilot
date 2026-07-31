# 安装 InferMatrixCopilot

InferMatrixCopilot 只维护一个发布物：

- `plugins/infermatrix-copilot/.mcp.json`：标准 stdio MCP 描述；
- `plugins/infermatrix-copilot/skills/imreview/SKILL.md`：开放 Agent Skills；
- Claude、Codex、Cursor 的市场文件只负责把同一个插件展示出来，不包含各自的安装逻辑。

## 推荐：插件市场

在 Agent 的插件市场搜索并安装 `infermatrix-copilot`。插件会一起安装 MCP 和
`imreview` Skill，不要求用户直接运行 Python、PowerShell 或 shell 脚本。

当前仓库也可作为市场源：

```text
# Claude Code
claude plugin marketplace add JiusiServe/InferMatrixCopilot
claude plugin install infermatrix-copilot@infermatrix-copilot-marketplace

# Codex
codex plugin marketplace add JiusiServe/InferMatrixCopilot
# 然后在 /plugins 中安装 infermatrix-copilot
```

Cursor 的公开市场条目审核通过后，在 Agent 中运行：

```text
/add-plugin infermatrix-copilot
```

## 其他 Agent

Skill 使用开放格式，可由通用 Skills CLI 安装；该 CLI 负责识别 Codex、Cursor、
Claude、Trae 等客户端：

```text
npx skills add JiusiServe/InferMatrixCopilot --skill imreview
```

MCP 客户端导入
[`plugins/infermatrix-copilot/.mcp.json`](../plugins/infermatrix-copilot/.mcp.json)
即可。核心配置只有一份：

```json
{
  "mcpServers": {
    "infermatrix-copilot": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "infermatrix-copilot[mcp] @ git+https://github.com/JiusiServe/InferMatrixCopilot.git@main",
        "infermatrix-copilot-mcp"
      ]
    }
  }
}
```

这里用 `uvx` 自动拉取隔离运行环境，用户不需要直接操作 Python。宿主如果能消费
MCP Registry，则应优先使用 Registry 条目；项目不为每个新 Agent 增加安装分支。

## 使用

```text
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
```

默认 Direct 模式只提供知识库，由 Agent 当前模型完成审查；不会自动评论或推送代码。
