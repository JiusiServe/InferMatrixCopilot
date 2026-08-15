# 安装 InferMatrixCopilot

InferMatrixCopilot 的核心发布物保持一份：

- `plugins/infermatrix-copilot/.mcp.json`：标准 stdio MCP 描述；
- `plugins/infermatrix-copilot/skills/`：开放 Agent Skills；
- Claude、Codex、Cursor 的市场文件只负责把同一个插件展示出来，不包含各自的安装逻辑。

## 私有仓库过渡安装

```text
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

# Windows cmd、PowerShell 或双击
install.cmd
install.cmd --repo-path D:\path\to\vllm-omni

# macOS / Linux
./install-mcp.sh
./install-mcp.sh --repo-path /path/to/vllm-omni
```

两个入口共用 `scripts/install_mcp.py`，但用户不需要安装或直接运行 Python：
入口会自动安装 `uv`，再由 `uv` 提供隔离运行环境。安装器会：

- 自动识别 Codex、Claude Code、Cursor 和 ZCode，检测到几个就安装几个；
- 保留 Cursor / ZCode 已有配置并先备份；
- 没识别到已知 Agent 时生成 `infermatrix-copilot.mcp.json`，不会直接失败。
- 创建 `~/.infermatrix-copilot/.env` 作为 Strict 的稳定配置入口；安装时传入
  `--repo-path` 会写入本地 vLLM-Omni checkout。模型密钥不会自动复制，使用
  Strict 前在该文件填写 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`。两者分别支持
  可选的 `ANTHROPIC_BASE_URL` 和 `OPENAI_BASE_URL`；只填一种 Key 时自动选择，
  两种都填时用 `LLM_PROVIDER` 指定。

## 公共市场上线后

在 Agent 的插件市场搜索 `infermatrix-copilot` 并点击安装，然后直接运行：

```text
# Codex
$imreview <PR URL>
$imupdate <local path, repository name, alias, or URL>

# Claude Code / Cursor / ZCode
/imreview <PR URL>
/imupdate <local path, repository name, alias, or URL>
```

市场只安装同一份 MCP 与 Skill；不会把逐 Agent 逻辑带回核心包。

## 其他 MCP Agent

安装器生成的 `infermatrix-copilot.mcp.json` 与
[`plugins/infermatrix-copilot/.mcp.json`](../plugins/infermatrix-copilot/.mcp.json)
内容相同，可直接导入支持 stdio MCP 的客户端。开放 Skill 位于：

```text
plugins/infermatrix-copilot/skills/imreview/SKILL.md
plugins/infermatrix-copilot/skills/imupdate/SKILL.md
```

核心 MCP 配置：

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

这里用 `uvx` 自动拉取并缓存隔离运行环境。宿主如果能消费 MCP Registry，则应优先
使用 Registry 条目；项目不为每个新 Agent 增加安装分支。

## 使用

```text
# Codex
$imreview https://github.com/vllm-project/vllm-omni/pull/5172
$imupdate D:\path\to\vllm-omni
$imupdate vllmomni
```

默认 Direct 模式只提供知识库，由 Agent 当前模型完成审查；不会自动评论或推送代码。
