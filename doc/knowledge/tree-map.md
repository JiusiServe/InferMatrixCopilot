# Knowledge

这里存放可复用规则，不是需要整棵读取的文档站。

## 默认入口

| 任务 | 入口 | 什么时候停止 |
|---|---|---|
| PR review | Direct 根据 PR title/body 返回精确 owner/model `quick_map` | 路由返回后停止知识导航 |
| 通用方法 | [general](../../knowledge/general/_index.md) | 命中一个当前任务 guide 后停止 |
| 仓库规则和代码地图 | [repos](../../knowledge/repos/_index.md) | 命中主要 owner 后停止横向展开 |
| 写入或整理知识 | [CONTRIBUTING](CONTRIBUTING.md) | 选择最近 owner 后再写 |

vLLM-Omni 的直接入口是
[仓库地图](../../knowledge/repos/vllm-omni/_index.md)。已知 owner 时不要从根目录逐层点击：

- 配置：[`components/configuration/rules.md`](../../knowledge/repos/vllm-omni/components/configuration/rules.md)
- 在线服务：[`components/serving/rules.md`](../../knowledge/repos/vllm-omni/components/serving/rules.md)
- 模型执行：[`components/model-executor/rules.md`](../../knowledge/repos/vllm-omni/components/model-executor/rules.md)
- Diffusion：[`components/diffusion/rules.md`](../../knowledge/repos/vllm-omni/components/diffusion/rules.md)
- 调度：[`components/scheduler/rules.md`](../../knowledge/repos/vllm-omni/components/scheduler/rules.md)
- 模型专属：直接查看 [`models/`](../../knowledge/repos/vllm-omni/models/_index.md) 下对应目录

## 目录分层

```text
general/                         跨仓库方法
repos/<repo>/rules.md            仓库硬规则
repos/<repo>/components/<owner>/ 共享代码 owner
repos/<repo>/models/<model>/     模型 owner
repos/<repo>/<topic>/            CI、benchmark、Git 等工作主题
contributing/                    知识维护规范
```

下面这些不是默认知识入口：

- `incidents/`、`history/`、`results/`：历史证据，只在规则指向或问题高度相似时查；
- `skills/`、`.claude/`：运行扩展；
- `tools/`：校验和维护脚本；
- 启动脚本：本地辅助材料。

## 找不到时

先查目录名，再做一次有界搜索：

```powershell
Get-ChildItem repos/vllm-omni/models -Directory
rg -n "关键词" repos/vllm-omni/components repos/vllm-omni/models -g "*.md"
```

不要默认递归读取所有 `_index.md`、事故记录或同级 owner。

## 校验

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```
