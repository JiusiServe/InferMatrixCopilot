# InferMatrixCopilot

让 Codex、Claude Code、Cursor 按 **vLLM-Omni 的项目规则**审查代码。

InferMatrixCopilot 是一个本地 MCP 知识插件。它把维护者沉淀的模型、组件和工程规则
提供给你正在使用的 Coding Agent，帮助 Agent 少做泛泛的代码检查，多关注真正影响
vLLM-Omni 的兼容性、正确性和性能问题。

默认模式下：

- 继续使用 Agent 当前选择的模型，不运行第二个模型；
- 不需要额外的 API Key；
- 不会自动发 GitHub 评论，也不会推送代码。

## 快速开始

要求：Windows、Python 3.11+，以及已经安装好的 Codex、Claude Code 或 Cursor。

```text
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

# Windows PowerShell
.\install-mcp.ps1 claude

# macOS / Linux
./install-mcp.sh claude
```

把 `claude` 换成 `codex` 或 `cursor` 即可安装到其他 Agent。脚本会安装 MCP
和 `/imreview` 命令。重启 Agent 后，把 PR 地址交给它：

```text
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
```

不带地址时，`/imreview` 会审查当前 PR 或本地工作区。

Windows 使用 `.ps1`，macOS 和 Linux 使用 `.sh`；两个入口共用同一套安装逻辑。
旧的 `install-codex.ps1`、`install-claude.ps1` 和 `install-cursor.ps1`
继续保留。Windows 请在 PowerShell 中运行，不要在 `cmd.exe` 中直接执行 `.ps1`。

macOS、Linux、手工配置和其他 MCP Agent 的接入方法见
[`doc/MCP.md`](doc/MCP.md)。

## 它是怎么工作的

```text
你发起 /imreview
  → Agent 读取 PR 或本地改动
  → InferMatrixCopilot 返回知识库入口
  → Agent 按改动选择相关模型、组件和通用规则
  → Agent 输出带文件和行号的审查结论
```

代码理解和推理由 Agent 当前模型完成。InferMatrixCopilot 只负责提供知识地图和维护者
规则，不返回一份预先生成的审查结果，也不会把整套知识库一次性塞进上下文。

| 它负责什么 | 它不负责什么 |
|---|---|
| 提供 vLLM-Omni 知识库入口 | 运行或替换 Agent 的模型 |
| 帮助 Agent 找到相关 owner 规则 | 替 Agent 理解代码和下结论 |
| 支持审查远程 PR 和本地改动 | 自动发布评论或推送代码 |
| 提供知识维护入口 | 在 MCP 内部自动改写规则 |

## 确认安装成功

在 Agent 中查看 MCP 列表，确认 `infermatrix_copilot` 已连接。Codex 可以运行：

```powershell
codex mcp list
```

如果审查时没有调用 InferMatrixCopilot，直接说明：

```text
Use InferMatrixCopilot to review this PR.
```

## 维护项目知识

如果你是 vLLM-Omni 的模块或模型维护者，不需要先理解整棵知识树。选择最接近的示例，
复制现有规则，再补齐触发条件、要求、禁止项、验收方法和来源：

- [给已有组件增加规则](docs/samples/add-component-rule.zh-CN.md)
- [给已有模型增加规则](docs/samples/add-model-rule.zh-CN.md)
- [为新模型创建 owner 目录](docs/samples/add-new-model-owner.zh-CN.md)

每条规则都要能追溯到 PR、源码或设计文档。提交前运行：

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

完整流程见
[`docs/knowledge-maintainer.zh-CN.md`](docs/knowledge-maintainer.zh-CN.md)；
不想直接改 Markdown，也可以
[提交中文规则建议](https://github.com/JiusiServe/InferMatrixCopilot/issues/new?template=knowledge-rule.yml)。
Agent 按该入口已有的目录地图和落盘规范，自行选择 owner、修改 Markdown、
更新索引并执行文档中要求的校验。MCP 本身不猜 owner，也不写规则。

## 默认 MCP 工具

- `review(target, repo?, mode?, post?)`：Direct 只返回审查知识入口；显式指定
  `mode="strict"` 时运行旧 Eco 审查工作流。
- `get_review_result(run_id)`：轮询 Strict 结果。
- `get_review_status(run_id)`：查看 Strict 的原工作流进度。
- `update_knowledge(repo?)`：`repo` 仅为兼容旧调用保留，返回知识维护入口。
- `doc_search(query, repo?)`：按文本搜索知识库。
- `doc_read(path, repo?)`：读取指定知识页面。

## 工作模式

| 模式 | 适合场景 | 说明 |
|---|---|---|
| Direct（默认） | 日常 PR 和本地审查 | Agent 自己完成推理，MCP 只提供知识入口 |
| Strict | 需要旧版完整审查工作流 | Strict 只是旧 Eco 的新名称，继续使用原 playbook、模型和运行状态 |
| Autonomous | 需要独立执行器 | 使用单独配置的模型和工作流 |

Strict 不会自动发布评论。只有调用时明确传入 `post=true`，并且服务端配置
`ALLOW_POST=1`，原工作流的发布步骤才会执行。

Strict 模式需要用户明确提出。具体用法见
[`docs/codex/README.md`](docs/codex/README.md)；Autonomous 模式见
[`docs/autonomous-workflow.md`](docs/autonomous-workflow.md)。

## 文档

- [安装和 MCP 配置](doc/MCP.md)
- [知识库贡献规范](knowledge/CONTRIBUTING.md)
- [项目设计与实现](doc/)
- [评测说明](eval/README.md)
