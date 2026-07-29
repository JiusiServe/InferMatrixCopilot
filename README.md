# InferMatrixCopilot

给 Codex 注入 vLLM-Omni 项目经验，让 PR 审查更符合维护者规则。
它不运行第二个模型，也不会自动发布评论。

这个项目同时服务两类人：

- 使用者：安装 MCP，让 Codex 在 review 时读取 vLLM-Omni 知识库。
- vLLM-Omni 维护者：把自己负责模块或模型的稳定经验写成规则，让人和 agent
  下次都能复用。

## 安装到 Codex

Windows：

```powershell
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot
.\install-codex.ps1
```

安装完成后重启 Codex，然后直接说：

```text
Use InferMatrixCopilot to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

macOS、Linux 和手工配置见
[`docs/codex/README.md`](docs/codex/README.md)。

## 它能做什么

| 能做 | 不能做 |
|---|---|
| 把知识库入口交给当前 Codex 模型 | 不运行第二个模型 |
| 让 Codex 按知识库地图选择相关规则 | 不替模型选择知识页面 |
| 辅助审查 vLLM-Omni PR 或本地改动 | 不自动发布 GitHub 评论 |
| 把知识维护入口交给 Codex，由 Codex 直接修改 Markdown | 不在 MCP 内部自动改写规则 |

默认是 **Direct 模式**：Codex 负责读取代码、理解改动和输出审查结果；
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

Codex 随后从这个入口读取文档地图，自行判断应使用哪些规则，再正常输出
带文件和行号的 review findings。MCP 不返回预制审查结果，也不一次性注入完整规则。

## 更新知识库

对 Codex 说：

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

Codex 按该入口已有的目录地图和落盘规范，自行选择 owner、修改 Markdown、
更新索引并执行文档中要求的校验。MCP 本身不猜 owner，也不写规则。

## 模块和模型 owner 怎样维护规则

不需要先理解整棵知识库，也不需要会写 MCP。已有模块或模型目录时，打开自己的
`rules.md`，把下面这段复制到末尾再改五处：

```markdown
### <沿用本页前缀的新 ID> — <一句话标题>

- 触发：<什么改动或现象需要这条规则>
- 必须：<实现或审核时必须做什么>
- 禁止：<最容易犯的错误>
- 验收：<什么测试或代码路径证明它满足>
```

然后更新文件顶部的 `updated` 和 `sources`，运行：

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

不知道应该改哪个文件，或者需要新增模块/模型时，直接照着完整样本改：

[`docs/knowledge-rule-samples.zh-CN.md`](docs/knowledge-rule-samples.zh-CN.md)

规则卡片、人工与 agent 分工、Codex 提示词和 PR 检查清单见：

[`docs/knowledge-maintainer.zh-CN.md`](docs/knowledge-maintainer.zh-CN.md)

不想直接改 Markdown 的 owner，可以
[提交中文规则建议](https://github.com/JiusiServe/InferMatrixCopilot/issues/new?template=knowledge-rule.yml)。
只需填写触发、必须、禁止、验收和来源，知识库维护者或 agent 再整理成 PR。

现有可复制文件模板位于
[`doc/knowledge-templates/`](doc/knowledge-templates/README.md)。知识树的权威贡献
规范仍是 [`knowledge/CONTRIBUTING.md`](knowledge/CONTRIBUTING.md)。

## Direct MCP 工具

- `review(target, repo?)`：返回审查知识入口。
- `update_knowledge(repo?)`：返回知识维护入口。
- `doc_search(query, repo?)`：按文本搜索知识库。
- `doc_read(path, repo?)`：读取指定知识页面。

Direct 模式不需要 API Key、endpoint 或额外模型配置。

## Strict 工作流模式

如果需要更强的流程约束，可以明确要求 Codex 使用 **Strict 工作流模式**。
InferMatrixCopilot 会维护持久化的
`evidence → gates → review → verify` 状态机，各阶段的分析仍由 Codex 当前模型完成。

## 其他模式

- Strict 模式的状态机用法见
  [`docs/codex/README.md`](docs/codex/README.md)。
- 自主工作流会运行自己的模型，是另一套产品入口，见
  [`docs/autonomous-workflow.md`](docs/autonomous-workflow.md)。
- 项目内部设计和实现说明见 [`doc/`](doc/)。
