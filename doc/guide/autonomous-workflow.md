# 独立执行器（Autonomous workflow）

本页介绍可选的 autonomous CLI 与 workflow MCP。它与仓库 README 描述的**默认 Direct
MCP 是两回事**。

autonomous 工作流**跑自己的模型**，支持更长的仓库维护 playbook —— 评审、issue 处理、
CI 调试、rebase。因此它需要模型凭据和仓库配置。

自动化宿主还可以通过 `CopilotMCP.start_quality_review` 启动专用的
`pr-quality` 工作流：它只评估 PR 是否已准备好进入维护者评审，不复用完整
`pr-review` 的 findings 数量作质量分数。调用方钉住 head、轮询
`get_quality_result`，并且仍由调用方独占所有对外发布。

## 安装

```bash
bash install.sh
```

编辑 `.env`，填好必需的模型凭据和 `REPO_PATHS`，然后运行：

```bash
./infermatrix-copilot doctor
```

## 使用

```bash
./infermatrix-copilot
./infermatrix-copilot -p "review pr 4830" --yes
./infermatrix-copilot -p "answer issue 4842, do not post"
./infermatrix-copilot -p "rebase pr 4830, then review it"
./infermatrix-copilot --resume
```

autonomous 的 MCP 命令是：

```text
infermatrix-copilot-workflow-mcp
```

**默认的 Codex 安装器不会注册它。**

## 安全

- push 需要策略允许，未显式开启前一律 dry-run。
- 保护分支永不被直接推送。
- 发布需要明确意图加上配置开关。
- 被阻塞的 run 写出升级产物，而不是猜测继续。

实现细节：

- [`../../QUICKSTART.md`](../../QUICKSTART.md)
- [`../architecture/DESIGN.md`](../architecture/DESIGN.md)
- [`../archive/IMPLEMENTATION_STATUS.md`](../archive/IMPLEMENTATION_STATUS.md)
