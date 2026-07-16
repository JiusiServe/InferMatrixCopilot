# 目录与归属

## 设计目标

这套目录先服务人类，再服务 agent。只看目录名和 `_index.md` 就应该能判断：

- 内容适用于所有仓库，还是只属于某个仓库、代码模块或模型；
- 正在做 review、CI、docs、benchmark、remote 还是其他工作；
- 应该从哪个入口继续，什么时候停止横向阅读。

只保留一套正式知识树。机器信息使用 ignored `local/`，不另建 private 知识树。

## 先判断放哪里

1. 换到完全无关的仓库后仍然正确吗？是就放 `framework/<主题>/`。
2. 依赖某个仓库的代码、命令或流程吗？放 `repos/<仓库>/<主题>/` 或仓库 `rules.md`。
3. 结论属于一块被多个模型/功能共用的源码吗？放 `repos/<仓库>/components/<模块>/`。
4. 只属于某个模型的实现、配置、checkpoint 或运行流程吗？放 `repos/<仓库>/models/<模型>/`。
5. 只是当前机器的地址、路径、cache、venv 或账号吗？放 ignored `local/`。

一个问题同时影响多个入口时，只在最近 owner 保留一份正文，其他位置只链接。

## 工作主题和代码 owner 是并列的

- `review`、`ci`、`docs`、`benchmark`、`remote`、`dev` 表示“正在做什么”。
- `components/frontend`、`components/backend`、`components/diffusion` 表示“事实属于哪块代码”。
- `models/hunyuan-image3` 表示“事实只属于哪个模型”。

不要套娃：

```text
# 错误
repos/acme/dev/frontend/incidents/
repos/vllm-omni/ci/models/hunyuan-image3/

# 正确
repos/acme/dev/
repos/acme/components/frontend/
repos/vllm-omni/ci/
repos/vllm-omni/models/hunyuan-image3/
```

## 最小目录图

```text
CLAUDE.md
README.md
CONTRIBUTING.md                    # 短入口
contributing/                      # 本仓库的知识树维护规范
  _index.md

framework/                         # 换仓库仍然成立
  <主题>/
    _index.md
    guides/                        # 有内容才创建
    incidents/                     # 复杂证据确有价值时才创建

repos/                             # 仓库专属知识
  _index.md
  <仓库>/
    _index.md
    rules.md                       # 有硬规则时才创建
    architecture.md                # 未拆模块时的系统总览，可选
    <工作主题>/
      _index.md
    components/
      _index.md
      <代码模块>/
        _index.md
        architecture.md
    models/
      _index.md
      <模型>/
        _index.md
        architecture.md

local/                             # Git 忽略，只放当前机器事实
tools/
skills/
```

不预建空目录。第一次有真实内容时，再同时创建目录和 `_index.md`。

## 每一层默认放什么

### `framework/<主题>/`

只放跨仓库通用方法。不出现某个仓库专有命令、模型结论或私人机器地址。

### `repos/<仓库>/<主题>/`

只写该仓库相对通用方法的差异，并链接通用页面。不复制整篇 `framework/` 正文。

### `components/<模块>/`

默认只有 `_index.md` 和 `architecture.md`。至少满足一项才建模块：独立源码目录、维护人或测试、运行流程、输入输出边界，或同一套知识影响多个模型/功能。

### `models/<模型>/`

默认只有 `_index.md` 和 `architecture.md`。checkpoint、尺寸和量化版本先作为同一模型入口的别名和差异；只有源码、配置语义或完整流程真正不同才建新模型目录。

### `local/`

`local/` 只放当前机器事实，不被正式 `_index.md` 链接，不能有被 Git 跟踪的文件。需要记录远端环境时可以创建 `local/remote.md`：

```markdown
# 当前远端环境

## <user@host:port>

- 登录别名：
- 计算节点或资源方式：
- 持久化工作目录：
- 容器和 Python/venv：
- 模型和依赖 cache：
- 最近验证日期：
- 备注：
```

可以记录凭据由哪个本机安全工具管理，不复制密码、token 或私钥正文。

## 查询时怎样避免又慢又乱

1. 确认真实仓库。
2. 根据任务选一个通用方法；根入口已直接指向 guide 时跳过主题索引。
3. canonical `repos/<slug>/` 已验证时先读仓库 `rules.md`；只有 upstream、URL、显示名或本地目录时，先用 `repos/_index.md` 映射。
4. 规则直接命中 owner 就停止导航；未命中才读仓库 `_index.md`、一个由任务目的选中的主题，再从 `components/_index.md` 或 `models/_index.md` 选主 owner。
5. 选定 owner 后停止横向展开；只有 live 调用链证明跨模块时才打开第二个 owner。
6. 历史错题只在规则明确提示、高度相似或用户明确调查历史时搜索。

已有完整日志和可读源码的窄 bug 优先按仓库规则完成诊断路由，`code taste` 在真正编辑前再读。

不知道最终归属时可以搜索，但不递归加载：

```powershell
rg "SSH timeout|shape mismatch" framework repos -g "*.md"
```
