# InferMatrixCopilot 开发者入口

这份文档给维护 InferMatrixCopilot 本身的人。普通安装和使用请看
[README](README.md)。

## 先看文档地图

不要递归读取整棵 `knowledge/`。先按任务选一个入口，命中具体 owner 后停止导航。

| 正在做什么 | 通用入口 | vLLM-Omni 补充 |
|---|---|---|
| Code review | [review contract](knowledge/general/review/guides/review-execution-contract.md) | [review](knowledge/repos/vllm-omni/review/_index.md) |
| 写代码或改接口 | [code taste](knowledge/general/review/guides/code-taste.md) | 先从下面的 owner 表定位组件 |
| CI 和测试 | [general/ci](knowledge/general/ci/_index.md) | [vLLM-Omni CI](knowledge/repos/vllm-omni/ci/_index.md) |
| 文档和 RFC | [general/docs](knowledge/general/docs/_index.md) | [vLLM-Omni docs](knowledge/repos/vllm-omni/docs/_index.md) |
| 调试 | [general/debug](knowledge/general/debug/_index.md) | [vLLM-Omni debug](knowledge/repos/vllm-omni/debug/_index.md) |
| Git、PR、rebase | [general/git](knowledge/general/git/_index.md) | [Git](knowledge/repos/vllm-omni/git/_index.md) / [rebase](knowledge/repos/vllm-omni/rebase/_index.md) |
| Benchmark | [general/benchmark](knowledge/general/benchmark/_index.md) | [vLLM-Omni benchmark](knowledge/repos/vllm-omni/benchmark/_index.md) |
| 远端验证 | [general/remote](knowledge/general/remote/_index.md) | [vLLM-Omni remote](knowledge/repos/vllm-omni/remote/_index.md) |
| 新增或整理知识 | [knowledge/CONTRIBUTING](knowledge/CONTRIBUTING.md) | 先确定最近的 owner |

vLLM-Omni 的代码 owner：

| 改动内容 | Owner 规则 |
|---|---|
| PipelineConfig、YAML、registry、default、deploy | [configuration](knowledge/repos/vllm-omni/components/configuration/rules.md) |
| HTTP/OpenAI request、response、endpoint、engine lifecycle | [serving](knowledge/repos/vllm-omni/components/serving/rules.md) |
| checkpoint、tokenizer、processor、stage handoff | [model executor](knowledge/repos/vllm-omni/components/model-executor/rules.md) |
| diffusion pipeline、denoise、VAE、DiT、图像生成 | [diffusion](knowledge/repos/vllm-omni/components/diffusion/rules.md) |
| connector、collective、跨 stage 通信 | [distributed](knowledge/repos/vllm-omni/components/distributed/_index.md) |
| queue、token budget、prefix cache、调度 | [scheduler](knowledge/repos/vllm-omni/components/scheduler/rules.md) |
| 明确的模型或 registry key | [models](knowledge/repos/vllm-omni/models/_index.md) |

完整知识入口仍在 [knowledge/README](knowledge/README.md)。只有 owner 不明确时才看
[组件职责表](knowledge/repos/vllm-omni/components/_index.md)；不要默认打开事故记录、
history、results 或所有 `_index.md`。

## 代码地图

```text
plugins/、skills/、integrations/  Agent 安装入口和 /imreview、/imupdate
src/infermatrix_copilot/
  thin_mcp_server.py             默认 MCP：Direct 路由和 Strict 入口
  mcp_server.py                  Strict 后台任务、状态和结果
  config.py、llm.py              配置及 Anthropic/OpenAI 后端
  intent.py、task_spec.py        用户意图和任务协议
  engine/                        playbook 执行器及步骤
  adapters/                      仓库适配层
playbooks/                       Strict/Autonomous 工作流定义
adapters/                        发布包中的仓库配置
knowledge/                       通用、仓库、组件和模型知识
doc/architecture/SPEC/                        与 src 文件对应的约束和职责
test/                            离线测试
```

整体架构先看 [CODE_TOUR](doc/architecture/CODE_TOUR.md)，修改具体源码前再看
[file-level SPEC](doc/architecture/SPEC/README.md) 中对应文件。

## 常见改动从哪里开始

| 要改什么 | 主要位置 | 最少验证 |
|---|---|---|
| Direct 返回内容或路由 | `thin_mcp_server.py`、Direct Skill | `test_thin_mcp_server.py`、`test_imreview_output_contract.py` |
| Strict 启动、轮询、发布门禁 | `mcp_server.py`、`mcp_policy.py` | `test_mcp.py` |
| 模型、Key、Base URL | `config.py`、`llm.py` | `test_llm_providers.py`、`test_tier_split.py` |
| 工作流步骤 | `playbooks/*.yaml`、`engine/steps/` | 对应 step 测试和 playbook 加载测试 |
| 新仓库支持 | `adapters/<repo>/`、`knowledge/repos/<repo>/` | adapter 测试和知识检查 |
| 更新 vLLM-Omni 知识 | `/imupdate` 维护流程 | [release maintenance](doc/contributing/release-maintenance.md) |
| 安装或发布包 | `scripts/install_mcp.py`、`pyproject.toml` | installer 测试和 wheel 内容检查 |

## 本地开发

```powershell
python -m pip install -e ".[dev,mcp]" ruff build
$env:PYTHONPATH = "src"
python -m pytest
python -m ruff check .
git diff --check
```

知识文件有改动时额外运行：

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

发布包有改动时：

```powershell
python -m build --wheel
```

确认 wheel 中包含 `knowledge/`、`_runtime/playbooks/`、`_runtime/adapters/` 和
`_runtime/skills/`，不能只验证源码 checkout。

## CI

`.github/workflows/test.yml` 在每次 push 与 PR 上跑上面这些检查：整套 pytest、
`--help` / `doctor` 冒烟、把 wheel 装进干净 venv 验证四棵数据树确实随包发布
（`test_packaged_runtime.py` 只断言 pyproject 的**文本**，证明不了这件事），
以及两个知识树 linter。

**它目前只是信号，不是合并门禁。** 要让它真正挡住合并，需要在
Settings → Branches（或 repository ruleset）里把 `suite` 这个 job 设为
required status check —— 这是仓库设置，任何一次提交都做不到。<!-- TODO(maintainer) -->


## 三条边界

- Direct 使用宿主 Agent 的模型，不在 MCP 内再次调用模型。
- Strict 使用 InferMatrixCopilot 配置的模型和本地仓库 checkout。
- `knowledge/` 是数据面；仓库、组件或模型规则不要硬编码进通用执行引擎。

运行产物默认在 `~/.infermatrix-copilot/runs/`。密钥、机器路径和本地 checkout
配置只放 `~/.infermatrix-copilot/.env`，不要提交。

## 进一步阅读

- [指南](doc/GUIDE.md) —— 操作者使用 + 维护者开发，外加 playbook / step / tool
  清单和性能对比（`CODE_TOUR` 的结构视角对照版）
- [设计](doc/architecture/DESIGN.md)
- [知识来源和同步边界](doc/architecture/KNOWLEDGE.md)
- [扩展知识库](doc/contributing/EXTENDING-KNOWLEDGE.md)
- [MCP 安装与接口](doc/guide/mcp.md)
- [Autonomous workflow](doc/guide/autonomous-workflow.md)
- [评测](eval/README.md)
