# AFD Copilot 使用指南

本文面向第一次配置、复用 AFD 维护 Agent 的同事，覆盖安装、功能、一次维护和失败恢复。适用实现：Copilot 的 `codex/afd-rebase-v1` 分支，包含 `dfddec86` 及后续提交；不要假定其他分支或已发布安装包包含这些功能。

目标是每天或每隔几天**手动启动一次**，把 vLLM 上游变化和 AFD 官方 main 的变化逐步消化到团队维护分支，减少发版时积累的适配工作。不要求严格追上 main HEAD，也没有内置定时任务。

## 1. 第一次使用：如何配置

### 1.1 先确定在哪里执行

| 入口 | 适合做什么 | 是否自动记录维护基线 |
| --- | --- | --- |
| 在 Codex App 中使用 Copilot 知识/Review 能力，或让 Codex 直接改代码 | Review、问题修复、单功能适配试验 | 不会因为对话完成就自动推进 workflow 基线 |
| 独立 CLI：`repo-rebase-v3 / local_rebase` | 同步 AFD main、选择 vLLM wheel、模块适配、测试、发布维护分支 | 成功发布后记录，下次继承 |

**本文的版本维护命令使用第二个入口。** 它通过配置并登录的 Codex CLI 启动独立 Agent 会话，不续用 App 聊天上下文。仅安装 Direct MCP，不等于已配置好维护执行器。

本指南采用**手动确认启动**：当前显式 playbook 的外层计划审查仍走 API reviewer；只配置 Codex 登录时，该 reviewer 会显示 unavailable，由操作者看过计划后确认。模块内的适配/计划审查再使用 Codex。不要给下面的新运行命令加 `--yes`，否则缺少外层 reviewer 会直接阻塞。无需为了日常手动使用而额外配置 API key。

完整 `local_rebase` 会安装目标 vLLM runtime、检查原生扩展和类接口。执行机器须支持目标 wheel；当前 GPU 路径通常是匹配 CUDA 环境的 Linux x86_64。macOS 可控制任务、Review 或做 CPU 单点试验，不能在本机完成 Linux CUDA wheel 的完整验收。

**当前 workflow 没有 SSH 测试转发功能。** Copilot、AFD checkout、vLLM checkout 和目标虚拟环境须在执行机器可访问的文件系统中。从本地 Codex 协调服务器时，需另行提交服务器任务，不能仅把远程目录填成 SSH 地址。共享服务器上的安装、构建和测试遵守该服务器调度规则，不在登录节点做重工作。

### 1.2 安装工具和 Copilot

需要 Git、uv、Python 3.11+、Codex CLI，以及对目标 fork 的 Git 推送权限。下面用 Python 3.12；实际目标 Python 仍须匹配所选 wheel。

```bash
mkdir -p "$HOME/work/afd-maintenance"
cd "$HOME/work/afd-maintenance"
git clone --branch codex/afd-rebase-v1 \
  https://github.com/JiusiServe/InferMatrixCopilot.git copilot
cd copilot
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[mcp,dev]'
```

Codex CLI 未安装时，按 [OpenAI 官方 CLI 安装说明](https://learn.chatgpt.com/docs/codex/cli) 安装。账号登录流程见 [官方认证说明](https://learn.chatgpt.com/docs/auth)。在**实际执行机器、实际执行用户**下确认：

```bash
codex --version
codex login
codex login status
```

已登录可跳过 `codex login`。本指南选择 Codex 登录后端，不需要为它另配 Anthropic API key。Git 认证是另一回事：使用团队已有的 SSH key 或 HTTPS credential helper，不把 token 写入文档或 adapter。

### 1.3 准备两个 checkout 和维护分支

使用独立 AFD checkout，不与正在开发或运行服务的目录混用。以下路径可替换；`YOUR_TEAM` 和示例身份必须改为自己的值。

```bash
cd "$HOME/work/afd-maintenance"
git clone https://github.com/vllm-project/afd-plugin.git afd-plugin
git -C afd-plugin remote rename origin upstream
git -C afd-plugin remote add fork git@github.com:YOUR_TEAM/afd-plugin.git
git clone https://github.com/vllm-project/vllm.git vllm
```

| 仓库 | remote | 用途 |
| --- | --- | --- |
| AFD checkout | `upstream` → `vllm-project/afd-plugin` | 获取官方 AFD main |
| AFD checkout | `fork` → 团队可写仓库 | 继承、发布维护分支 |
| vLLM checkout | `origin` → `vllm-project/vllm` | 获取 vLLM main 和版本历史 |

长期使用一个维护分支，例如 `codex/afd-maintenance`，不要每轮新建空分支。

- **fork 已有维护分支**：执行器会 fetch 并继承它；初次可先 checkout，确认包含团队已有补丁。
- **首次创建分支**：从团队确认的 AFD 基线创建，必须包含要保留的修改。不要直接从官方 main 重开，丢掉尚未上游的适配。

已有远端分支的例子：

```bash
git -C afd-plugin fetch fork codex/afd-maintenance
git -C afd-plugin switch --track -c codex/afd-maintenance fork/codex/afd-maintenance
```

新分支则使用 `git switch -c codex/afd-maintenance <已确认的AFD基线ref>`。这里填 **AFD ref**；第 3 节的 `last_rebase_commit` 填 **vLLM SHA**，不能混用。

### 1.4 配置自己的 adapter

仓库自带 AFD adapter 中的 fork、分支和签名属于原维护者。**不要照搬后直接 push。** 在 Copilot 根目录复制本地配置：

```bash
cd "$HOME/work/afd-maintenance/copilot"
mkdir -p local/afd/adapters
cp -R adapters/afd_plugin local/afd/adapters/
printf '\n/local/afd/\n' >> .git/info/exclude
```

编辑 `local/afd/adapters/afd_plugin/manifest.yaml` 的 `push` 段，保留其他模块和测试配置：

```yaml
push:
  default_remote: fork
  remote_url: git@github.com:YOUR_TEAM/afd-plugin.git
  rebase_branch: codex/afd-maintenance
  rebase_branch_allowed: true
  protected_branches: [main, master]
  allowed: true
  signoff: {name: Your Name, email: you@example.com}
```

`remote_url` 与 AFD checkout 的 `fork` 保持一致，`rebase_branch` 是要维护的分支。配置允许 push 后，每次执行仍需显式 `ALLOW_PUSH=true`。Git 本地提交身份也设置为自己的：

```bash
git -C ../afd-plugin config user.name 'Your Name'
git -C ../afd-plugin config user.email 'you@example.com'
```

保留下面的跟踪配置；不要同时添加固定 `target_ref` 或传 `force_upstream_commit`：

```yaml
upstream:
  kind: fork_tracking
  repo_path: ${VLLM_UPSTREAM_REPO}
  remote: origin
  target_branch: main
  tracking: latest_wheel
```

本地 adapter 是快照。以后更新 Copilot 时，对照更新模块映射、wheel 和测试规则，保留自己的 push/身份配置。

### 1.5 配置运行环境

将下面内容保存为 Copilot 的 `local/afd/env.sh`，路径改为**执行机器上的绝对路径**。上一步将 `local/afd/` 加入当前 checkout 的 Git 排除列表，不提交凭据或机器配置。

```bash
export COPILOT_REPO="$HOME/work/afd-maintenance/copilot"
export ADAPTERS_DIR="$COPILOT_REPO/local/afd/adapters"
export AFD_PLUGIN_REPO="$HOME/work/afd-maintenance/afd-plugin"
export VLLM_UPSTREAM_REPO="$HOME/work/afd-maintenance/vllm"
export AFD_PLUGIN_VENV="$HOME/work/afd-maintenance/afd-runtime"
export VLLM_WHEEL_VARIANT=cu130
export VLLM_WHEEL_ARCH=x86_64
export STRICT_BACKEND=codex
export ALLOW_PUSH=false
export RUN_ROOT="$HOME/work/afd-maintenance/runs"
```

`cu130 / x86_64` 是例子，需匹配目标软件栈和架构。AFD 目标环境独立于 Copilot 的 `.venv`，也不能复用正在服务的环境：维护会替换其中的 vLLM。

`STRICT_BACKEND_MODEL` 默认留空，沿用所用 Codex CLI 的模型配置。PATH 上的 Codex 不能启动时，可设 `STRICT_BACKEND_CLI=/absolute/path/to/codex`，并对这个**同一可执行文件**检查版本和登录状态，不必改全局安装。

加载配置，安装 AFD 自身与开发工具：

```bash
cd "$HOME/work/afd-maintenance/copilot"
source local/afd/env.sh
uv venv --python 3.12 "$AFD_PLUGIN_VENV"
cd "$AFD_PLUGIN_REPO"
AFD_BUILD_ASCEND_OPS=0 uv pip install --python "$AFD_PLUGIN_VENV/bin/python" \
  --group dev -e .
cd "$COPILOT_REPO"
```

不要手工安装旧 `[vllm]` extra 覆盖目标。workflow 会选择源码提交、使用预编译 wheel 安装 vLLM，并让 Agent 更新依赖和 `uv.lock`。安装有网络和磁盘开销；不跑模型不代表完整维护是纯离线轻任务。

### 1.6 首次检查

下面检查分别发现环境/认证缺项、仓库连错和未提交改动；发现问题先修正，再启动维护。

```bash
"$COPILOT_REPO/.venv/bin/infermatrix-copilot" doctor
git -C "$AFD_PLUGIN_REPO" remote -v
git -C "$VLLM_UPSTREAM_REPO" remote -v
git -C "$AFD_PLUGIN_REPO" status --short --branch
```

`doctor` 不等于 wheel/原生扩展/GPU 验收，也不保证可 push。只处理本次 AFD/Codex 路径所需缺项，不必为无关 provider 配密钥。若已有 `REPO_PATHS` 或其他 `.env`，确认没有将 `afd-plugin` 指到另一 checkout。

只想在 Codex App 中 Review、设计或修 issue：另按 [Codex 宿主接入说明](hosts/codex.md) 安装 Direct MCP/skills。这是可选入口，不是下面 CLI 的前置要求。

## 2. 目前有哪些功能

| 功能 | 当前支持与边界 |
| --- | --- |
| 仓库识别与知识路由 | 根据范围加载 AFD 架构、组件和 Review 知识；历史知识不替代目标源码 |
| Review、设计、issue 修复 | 可复用 `imreview`、`imdesign`、`imcifix` 等宿主流程；评论/PR 发布需另行授权 |
| 跟进 vLLM main | 选择 main 第一父链上有目标架构 wheel 的近期提交；本轮固定 SHA |
| 跟进 AFD main | merge 官方 main 到维护分支，保留已发布适配；文本冲突与语义适配分别处理 |
| 模块适配与 Debug | 7 个模块、计划审查、Codex 工具执行、有限重试和失败报告 |
| 依赖与原生扩展检查 | 目标源码/runtime 身份、原生扩展导入、版本、commit 专属 wheel 索引和 uv lock |
| 默认本地测试 | CPU 单测＋必需 runtime 类路径/方法签名检查；必需测试 skip 不算通过 |
| pre-commit 与发布 | 修改后重验，绑定已验证内容再提交；受控 push，不覆盖分叉远端或 protected branch |
| 跨次维护和恢复 | 已发布提交记录 `AFD-Upstream-Commit`，下一次继承；失败可 resume |
| GPU/NPU 模型验收 | **未接入默认维护流程**；仓库已有 E2E 需另行提交服务器任务执行 |
| 远程 CI 修复循环 | AFD **未接通**；`github_actions` provider 声明不代表已有闭环 |
| release 审计/验收 | 滚动维护提供准备工作，不替代精确 release 和硬件验收，也不等于具备 Omni 全部 release audit |

目前已验证真实 Codex/MCP 单功能适配，以及本地 Git 两轮基线/发布机制；尚未完成真实 AFD 全范围维护＋GPU 验收。Copilot 自身 CI 绿色不代表 AFD GPU 功能通过。

## 3. 如何进行一次版本维护

### 3.1 首次运行：确认 vLLM 基线

需要对应的两项事实：维护分支已有的 **AFD 代码**，以及它此前已适配的 **vLLM commit**。`last_rebase_commit` 告诉执行器从哪里开始分析上游差异。

从团队记录或已验证标签解析完整 SHA，把下面 `vX.Y.Z` 替换为实际基线标签：

```bash
source "$HOME/work/afd-maintenance/copilot/local/afd/env.sh"
export BASELINE_REF=vX.Y.Z
export BASELINE_VLLM_SHA="$(git -C "$VLLM_UPSTREAM_REPO" rev-parse "$BASELINE_REF^{commit}")"
```

不要填 AFD SHA，也不要仅凭包版本号认定已有适配完成。没有可信基线时先与维护者确认，不能随意填最新 SHA 跳过未做工作。此前的单功能试验分支不能作为整版维护成功基线。

### 3.2 先预览，控制本轮范围

当前 CLI 的显式 playbook 入口使用 `--task-param repo=afd-plugin` 指定仓库；不要替换成 `--repo afd-plugin`，后者在此入口不会覆盖默认仓库。输出的 `task` 必须明确是 `afd-plugin`，否则不要继续。

只看 playbook，不执行适配：

```bash
"$COPILOT_REPO/.venv/bin/infermatrix-copilot" \
  --playbook repo-rebase-v3 --task-param repo=afd-plugin --plan-only \
  --task-param rebase_mode=local_rebase
```

查看实际 vLLM 差异对应的模块和 wheel 候选：

```bash
"$COPILOT_REPO/.venv/bin/infermatrix-copilot" \
  --playbook repo-rebase-v3 --task-param repo=afd-plugin \
  --task-param rebase_mode=report_only \
  --task-param last_rebase_commit="$BASELINE_VLLM_SHA"
```

`report_only` 会 fetch 上游、写报告并在临时 scratch 中选目标；不安装 runtime、不改 AFD 源码、不发布。**当前预览要显式传基线**，不像正式维护自动继承已发布记录。关注 `commits_assignment.md` 和 `path_drift_check.md`。

预览或正式运行显示 `Run locked playbook ... [y/N]` 时，确认仓库、模式和配置无误后输入 `y`。显示 `no reviewer LLM` 是上述外层审查缺项，不等于 Codex 登录失败；若是明确的 `block` 结论则先处理原因。

这不是完整 AFD-main 合并预演。已有维护分支时，可单独看官方变化：

```bash
git -C "$AFD_PLUGIN_REPO" fetch upstream main
git -C "$AFD_PLUGIN_REPO" log --oneline codex/afd-maintenance..upstream/main
```

**`local_rebase` 会处理命中的所有模块，没有已实现的“只适配一个特性”开关。** 预览发现改动很大时，不直接启动完整维护。可先让 Codex 在独立试验分支做一个明确接口的适配和针对性测试，但不推进整版维护基线。

### 3.3 首次正式维护

确认配置、基线和范围后执行：

```bash
cd "$COPILOT_REPO"
ALLOW_PUSH=true "$COPILOT_REPO/.venv/bin/infermatrix-copilot" \
  --playbook repo-rebase-v3 --task-param repo=afd-plugin \
  --task-param rebase_mode=local_rebase \
  --task-param last_rebase_commit="$BASELINE_VLLM_SHA"
```

流程依次执行：

1. 固定 AFD main 与维护分支输入，继承成果，merge AFD main。
2. 固定 vLLM main 快照，选择不早于已发布基线的 wheel-ready commit。
3. 安装并核对目标 runtime，按 vLLM 与 AFD-main 改动分配模块。
4. 审查计划、适配 AFD、更新依赖与锁文件，运行测试和有限轮 Debug。
5. pre-commit、必要重验和发布检查通过后，提交并 push 指定维护分支。

这里 rebase 是工作流名称，不是简单执行 `git rebase`。AFD main 用 merge 同步；vLLM 是外部依赖，需要适配 AFD 对其接口/行为的使用。没有 Git conflict 仍可能需要改代码。

没有更新的可用 wheel 时，可保持 vLLM 基线，仍处理 AFD main 的变化。每轮最多探测 200 个新增第一父链提交；超出且无 wheel 时停止，不无限回退。

首次想先检查本地产物，可改用 `ALLOW_PUSH=false`。这**不是 dry-run**：仍会改代码、安装依赖、测试和创建本地提交，只在远程发布前停止，不推进已发布基线。

### 3.4 第二次及以后

首次成功发布后，继续使用相同维护分支，**不再传** `last_rebase_commit`：

```bash
source "$HOME/work/afd-maintenance/copilot/local/afd/env.sh"
cd "$COPILOT_REPO"
ALLOW_PUSH=true "$COPILOT_REPO/.venv/bin/infermatrix-copilot" \
  --playbook repo-rebase-v3 --task-param repo=afd-plugin \
  --task-param rebase_mode=local_rebase
```

执行器从 fetch 后的远端维护历史读取 `AFD-Upstream-Commit`。换同事或机器也可继承，前提是 fork、分支和环境配置一致。失败/未授权的 push 不算成功，不手工伪造 trailer。新目标无需代码变化时，可创建一个空的验证记录提交；同一目标重复执行不会不断生成该记录。

同一维护分支一次由一个操作者执行；任务期间不要让其他工具修改 checkout 或替换目标环境。

### 3.5 查看结果、恢复失败

命令输出 run 目录；上文存入 `RUN_ROOT`，未设置时默认为 `~/.infermatrix-copilot/runs/`。

| 文件 | 用途 |
| --- | --- |
| `RUN_REPORT.md`、存在时的 `FINAL_SUMMARY.md` | 状态、停止原因和结论 |
| `substate.json` | 固定输入、上游目标、模块、测试、发布状态 |
| `plans/`、工具轨迹 | Agent 计划、审查与实际操作 |
| `tests/`、JUnit、`wheel_install.log`、`wheel_import_check.log` | 测试、失败/skip、安装与导入证据 |
| `push_wal/` | 发布尝试与恢复记录 |

区分**适配完成、默认测试通过、远端发布成功**；不能只看 Agent 的 success 文本。必需 runtime 未运行、失败或 skip，不能跳过门禁宣布成功。

修复报告中的登录、网络、依赖或冲突等问题后，继续同一轮：

```bash
ALLOW_PUSH=true "$COPILOT_REPO/.venv/bin/infermatrix-copilot" --resume
```

`--resume` 恢复当前 `RUN_ROOT` 最近的保存任务，沿用原 AFD/vLLM 输入，不重新追最新 main。先确认最近任务正是要恢复的维护任务；不要混用他人的 run 目录。获取更新输入用第 3.4 节的新运行命令。

失败的维护保留 scratch 和 editable-runtime 产物供恢复；成功后清理 scratch。目标虚拟环境是维护基础设施，不直接当部署环境。远端分叉需人工协调，执行器不 force push 覆盖同事提交。

## 4. GPU 验收、发版与排查

**GPU 验收不必先接 CI。** 本地 Codex/操作者可向服务器调度器提交限定范围的验证任务，运行已有 E2E 并收集结果；当前需要另行执行，尚非 AFD `local_rebase` 自动步骤。资源申请和清理遵守目标服务器规则，本文不固化个人机器地址或账号。

日常 CPU/runtime 通过不代表 eager、Graph、DBO、通信、模型正确性或 NPU 通过。vLLM release 时仍需固定精确 release、检查剩余变化并做团队要求的硬件验收，不能仅凭 main nightly 结果宣称支持 release。

| 现象 | 怎么处理 |
| --- | --- |
| App 可用，CLI 启动/模型失败 | 检查执行机器上的 CLI、登录和模型；需要时设 `STRICT_BACKEND_CLI` |
| `no reviewer LLM ... --yes ... blocked` | 使用本文的交互命令，去掉 `--yes`，核对计划后人工确认；不是修改模块审查门禁 |
| 仓库找不到或目录错误 | 核对 `ADAPTERS_DIR`、路径变量、已有 `REPO_PATHS` 和加载的 env |
| wheel 有包但安装失败 | 候选存在不等于可安装；核对 Python、平台、CUDA 和日志，不扩大为源码编译任务 |
| 缺首次 baseline | 填此前已适配的 vLLM 完整 SHA，不填 AFD SHA |
| 显式 baseline 与远端不一致 | 后续正式运行去掉旧参数，确认远端记录正确 |
| 测试 skip、pre-commit 失败、提交内容变化 | 按报告修正；内容变更后重验，不绕过发布门禁 |
| push 权限不足或分叉 | 核对自己的 fork/认证，协调分叉后恢复 |
| push 维护分支未触发 AFD CI | 核对实际 workflow；当前候选 CPU CI 面向 main/master 的 push/PR，维护分支 push 不等于自动跑 CI |

实现依据：[AFD adapter](../../adapters/afd_plugin/manifest.yaml)、[维护 playbook](../../playbooks/repo-rebase-v3.yaml)、[执行步骤](../../src/infermatrix_copilot/engine/steps/rebase_v3.py)、[上游跟踪](../../src/infermatrix_copilot/rebase_engine/upstream_tracking.py)。
