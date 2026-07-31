# 在 Codex、Claude Code、Cursor 中使用 InferMatrixCopilot

InferMatrixCopilot 是本地 stdio MCP 服务。Agent 仍使用自己当前的模型完成
代码阅读和审查；MCP 只返回知识库入口，不需要 API Key 或第二个模型。

## 推荐：一键安装

```text
python install-mcp.py codex
python install-mcp.py claude
python install-mcp.py cursor
```

每次只运行与你的 Agent 对应的一条。脚本会同时安装 MCP 和 `imreview`：

```text
/imreview <PR URL>
```

同一个 `install-mcp.py` 支持 Windows、macOS 和 Linux。macOS/Linux 如果没有
`python` 命令，使用 `python3`；Windows 也可以使用 `py -3.11`。旧的 `.ps1`
入口继续保留，但不要在 `cmd.exe` 中直接运行 `.ps1`。

## 手工配置

Windows：

```powershell
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot
py -3 -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "mcp>=1.2,<2" "PyYAML>=6.0"
```

macOS / Linux：

```bash
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot
python3 -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
python3 -m venv .venv
./.venv/bin/python -m pip install "mcp>=1.2,<2" "PyYAML>=6.0"
```

## Codex

所有平台：

```text
python install-mcp.py codex
```

手工配置见 [`docs/codex/README.md`](../docs/codex/README.md)。

## Claude Code

在仓库根目录运行：

```text
python install-mcp.py claude
```

下面是等价的手工配置。

Windows PowerShell：

```powershell
$Root = (Resolve-Path .).Path
claude mcp add --env "PYTHONPATH=$Root\src" --transport stdio --scope user `
  infermatrix_copilot -- "$Root\.venv\Scripts\python.exe" `
  -m infermatrix_copilot.thin_mcp_server
claude mcp list
```

macOS / Linux：

```bash
ROOT="$PWD"
claude mcp add --env "PYTHONPATH=$ROOT/src" --transport stdio --scope user \
  infermatrix_copilot -- "$ROOT/.venv/bin/python" \
  -m infermatrix_copilot.thin_mcp_server
claude mcp list
```

## Cursor

所有平台：

```text
python install-mcp.py cursor
```

手工配置时，把 [`docs/cursor/mcp.json`](../docs/cursor/mcp.json) 复制到项目的
`.cursor/mcp.json` 或用户目录的 `~/.cursor/mcp.json`，然后把示例中的
`D:\\path\\to\\InferMatrixCopilot` 替换为真实绝对路径。

## 其他 MCP Agent

只要宿主支持本地 stdio MCP，就使用与 Cursor 相同的三个字段：

```json
{
  "command": "D:\\path\\to\\InferMatrixCopilot\\.venv\\Scripts\\python.exe",
  "args": ["-m", "infermatrix_copilot.thin_mcp_server"],
  "env": {
    "PYTHONPATH": "D:\\path\\to\\InferMatrixCopilot\\src"
  }
}
```

macOS / Linux 把 `command` 换成 `<repo>/.venv/bin/python`，把
`PYTHONPATH` 换成 `<repo>/src`。

## 使用方法

连接后，对任意 Agent 使用同一句话：

```text
Use InferMatrixCopilot to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

默认 Direct 模式下，`review` 返回 `knowledge/AGENTS.md`，Agent 按其中的地图
读取相关规则。需要维护知识库时调用 `update_knowledge`；只有用户明确要求时才
使用 Strict workflow mode。

Direct MCP 不运行模型、不发 GitHub 评论、不推送代码。
