# Workflow Starter

这是一套可以直接用 Markdown 手工维护的项目知识框架。它把跨仓库通用方法、仓库专有规则、代码模块、模型和可选历史案例放在一棵目录树中，避免每次任务把无关内容全部加载。

## 开始使用

```bash
git clone https://github.com/zuiho-kai/claude-workflow-starter.git
cd claude-workflow-starter
```

如果还需要项目代码，可以把目标仓库克隆到旁边或按自己的 worktree 规则管理。知识仓库用 `repos/<仓库>/` 表示经验归属，不要求把项目代码塞进这个目录。

## 在其他仓库接入

推荐把框架入口放到目标仓库根目录，这样 agent 会自动发现 `AGENTS.md`，人类也能从 README 进入。如果只把本项目放在目标仓库旁边，目标仓库自己的 `AGENTS.md` 必须显式要求读取这个知识仓库；否则两边不会自动关联。

最短接入流程：

1. 把 `AGENTS.md`、`CLAUDE.md`、`README.md`、`CONTRIBUTING.md`、`contributing/`、`framework/` 和 `tools/check_knowledge_tree.py` 复制或合并到目标仓库根目录。已有同名规则时先合并，不要直接覆盖。
2. 在目标仓库的 `.gitignore` 中加入 `local/`；机器地址、账号、cache 和 venv 只写 `local/`。
3. 新建 `repos/_index.md` 和 `repos/<你的仓库>/_index.md`。如果 fork 了本仓，删除与你无关的 `repos/vllm-omni/`、`repos/jianghan-roleplay-data-pipeline/`，并同步 `repos/_index.md`。
4. 只有该仓库确实有每次开工都必须执行的专属门禁时，才新建 `repos/<你的仓库>/rules.md`，并从仓库 `_index.md` 链接它。
5. 按实际需要增加主题、`components/<模块>/`、`models/<模型>/` 和规则；只有复杂历史证据需要长期保留时才增加 `incidents/`，不要预建空目录。
6. 运行 `python tools/check_knowledge_tree.py`，确认索引、链接和目录结构完整。

根 `AGENTS.md` 和 `CLAUDE.md` 必须保持仓库中性。模型、GPU、工作目录、Git 身份、专用 remote 和 PR 格式等规则只能放到对应 `repos/<仓库>/` 或 ignored `local/`，不能重新堆回根入口。

## 从哪里查

- [通用经验](framework/_index.md)：review、CI、docs、Git、debug、benchmark、环境、远端、agent 和规划。
- [仓库经验](repos/_index.md)：从仓库列表进入当前实际保留的仓库、代码模块和模型；第三方接入后以自己的列表为准。
- [贡献与目录维护](CONTRIBUTING.md)：短入口会按任务带你进入归属、页面、复盘、拆分或校验规范，不要求整套通读。

### 按任务找入口

| 你正在做什么 | 先看通用入口 | 识别仓库后必须检查 |
|---|---|---|
| code review 和 reviewer follow-up | [review](framework/review/_index.md) | `repos/<仓库>/review/` |
| 测试和 CI | [ci](framework/ci/_index.md) | `repos/<仓库>/ci/` |
| 文档、RFC 和公开说明 | [docs](framework/docs/_index.md) | `repos/<仓库>/docs/` |
| Git、commit、rebase 和 PR | [git](framework/git/_index.md) | `repos/<仓库>/git/` |
| 调试和根因收敛 | [debug](framework/debug/_index.md) | `repos/<仓库>/debug/` |
| benchmark 和性能证据 | [benchmark](framework/benchmark/_index.md) | `repos/<仓库>/benchmark/` |
| Windows、WSL 和本地环境 | [environment](framework/environment/_index.md) | 通常不需要仓库补充 |
| SSH、容器、GPU 和远端任务 | [remote](framework/remote/_index.md) | `repos/<仓库>/remote/` |
| 多 agent 分工 | [agents](framework/agents/_index.md) | 通常不需要仓库补充 |
| 需求拆分和执行计划 | [planning](framework/planning/_index.md) | 仓库入口中的业务主题 |

实际顺序以 `CLAUDE.md` 的场景触发器为准：直接命中具体 guide 时跳过通用主题索引。只有 canonical `repos/<slug>/` 未经验证时才用 [仓库列表](repos/_index.md) 把 upstream、URL、显示名或本地目录映射到 slug；不凭名字猜目录。随后先读当前仓库 `rules.md`，规则精确命中 owner 就停止导航；未命中才读仓库 `_index.md`、一个由任务目的选中的仓库主题，再从 `components/_index.md` 或 `models/_index.md` 选择主要 owner。读完 owner 已有规则后停止横向展开，只有 live 调用链证明跨模块时才打开第二个目录。

已有完整日志和可读源码的窄 bug 例外：先按仓库规则完成诊断路由和首次根因，真正编辑前再读 code taste。

路由时先只读索引和命中的规则，写出用户入口、主要 owner 和准备核对的源码边界；具体 guide 在 owner 确定后按需读取，一次不要预加载多篇方法正文。

不知道归属时，可以先全文搜索：

```powershell
rg "SSH timeout|shape mismatch" framework repos -g "*.md"
```

## 目录怎样理解

```text
framework/<主题>/                         # 换仓库仍然成立
repos/<仓库>/<主题>/                      # 某仓库专有流程
repos/<仓库>/components/<代码模块>/       # 前端、后端、diffusion 等共享代码
repos/<仓库>/models/<模型>/               # 模型专有实现和配置
<最近目录>/incidents/                     # 可选的复杂历史证据，不是默认规则入口
local/                                    # 当前机器信息，Git 忽略
```

每个正式目录都有 `_index.md`，说明什么时候查、什么不放这里，以及每个页面的入口。普通维护者不需要编辑 YAML 或修改检查脚本。

## 新增普通经验

1. 判断内容属于通用主题、仓库、代码模块还是模型。
2. 在最接近的目录中新建 Markdown。
3. 在同目录 `_index.md` 增加一行“遇到什么 → 查看哪里”。
4. 运行：

   ```powershell
   python tools/check_knowledge_tree.py
   ```

具体的 `_index.md` 写法和目录示例见 [页面写法](contributing/page-rules.md)。也可以直接参考现有同类目录。

## 复盘和沉淀

复盘的默认产物是最近 owner 的 `rules.md`。先回答为什么发生、为什么以前没发现、怎样提前阻止、怎样验收，再把可重复执行的结论写成规则。只有复现链、日志证据或历史背景很复杂，规则无法承载且以后仍可能重新取证时，才额外新增错题。

确实需要错题时，按根因放在最近的 `incidents/`：

- 通用 SSH、WSL、PowerShell 或 Git 错误 → `framework/<主题>/incidents/`
- 仓库 CI、benchmark、review 或 remote 错误 → `repos/<仓库>/<主题>/incidents/`
- 多模型共享代码错误 → `repos/<仓库>/components/<模块>/incidents/`
- 模型专有错误 → `repos/<仓库>/models/<模型>/incidents/`

按已经验证的根因归属，不按用户最先看到现象的位置归属。例如前端看到 API 404，不等于根因一定在 frontend。根因未明时默认继续调查；只有用户要求保留过程记录时，才暂放仓库对应工作主题并标记“待归类”。

文件名使用 `YYYY-MM-DD-short-name.md`，正文按 [错题页面格式](contributing/incidents.md#正文模板) 编写。一件事故只保留一篇完整正文，并链接已经提炼的规则；正常任务仍从规则开始，不要求先找到事故文件。

## 内容多了怎样拆

- 单文件达到 300 个非空行或 16 KiB：检查是否已经混入多个主题。
- 单文件达到 500 个非空行或 32 KiB：必须拆分，或在 `_index.md` 写明暂不拆的原因和复核日期。
- 一个目录直接放到第 8 个普通页面：按 `guides/`、`incidents/` 或明确业务主题分类。
- 一个分类目录超过 20 篇当前有效页面：继续按稳定问题主题分类。

检查工具只报告可以机械判断的问题，不会生成目录、静默决定语义归属或在后台移动文件。

## 当前机器信息

真实服务器地址、账号、token、私钥、cache 和 venv 路径只放 Git 忽略的 `local/`。需要时直接创建 `local/remote.md`，按机器或完整 `user@host:port` 分段记录；该文件不能被 Git 跟踪。

正式知识页面不得包含私人 host、凭据或用户绝对路径。去除敏感信息后仍有复用价值的教训，再写入 `framework/` 或 `repos/`。

## 自动检查

```powershell
python tools/check_knowledge_tree.py
```

它会检查：

- 每个目录是否有 `_index.md`；
- 页面和子目录是否登记到最近索引；
- 相对链接是否存在；
- 错题的文件名、编号、归属、状态和入口是否完整；
- 文件和目录是否超过拆分限制；
- `local/` 是否意外进入 Git。

脚本不会判断两篇文章是否语义重复，也不会替人决定问题属于哪个代码模块或模型。

## 主要入口

| 内容 | 路径 |
|---|---|
| 开工硬规则 | `CLAUDE.md` |
| 通用经验 | `framework/` |
| 仓库、代码模块、模型和错题 | `repos/` |
| 当前机器信息 | `local/`（Git ignored） |
| 贡献与目录维护 | `CONTRIBUTING.md` |
| 贡献专题规范 | `contributing/` |
| 索引检查 | `tools/check_knowledge_tree.py` |

框架目标只有一个：让人和 agent 都能沿清晰入口找到需要的最少内容，并且让新经验在下一次任务中真正可查。
