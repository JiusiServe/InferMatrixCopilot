## 1. 进陌生远端节点的正确流程

**错误示范（我犯过的）**：假设新节点路径结构和之前节点一样，直接 `cd /app/vllm-omni` 或 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`，全部踩空。

### 正确顺序

#### 1.1 先看节点上别人的容器怎么挂的

```bash
docker ps --format "{{.Names}} {{.Image}}"
docker inspect <someone_else_container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

**这比任何文档都权威**。别人容器挂什么，我就挂什么。

#### 1.2 节点有哪些持久存储

```bash
df -h | grep -E "home|scratch|lustre|nfs"
ls /home /scratch 2>/dev/null
```

Lustre 路径在不同节点可能：
- `/scratch/<YOUR_GROUP>/...`
- `/home/<YOUR_GROUP>/<user>/...`

**不要假设路径。先查文件系统。**

#### 1.3 节点上有哪些模型缓存

```bash
ls /home/models/hub 2>/dev/null     # Lustre 共享缓存
ls /scratch/<YOUR_GROUP>/huggingface/hub 2>/dev/null   # Lustre 用户缓存
find /home /scratch -maxdepth 4 -name "models--*" -type d 2>/dev/null | head
```

**模型缓存 160GB，能复用绝不重下**。

#### 1.4 节点上有没有现成的 vllm-omni clone 和 venv

```bash
OWNER_ROOT=/home/<user>   # 或用户明确点名的 /data/<user> / /scratch/<group>/<user>
test -d "$OWNER_ROOT" && find "$OWNER_ROOT" -maxdepth 4 -type d \( -name 'vllm-omni*' -o -name 'wt-*' -o -name '.venv' -o -name 'venv' -o -name 'vllm*' \) 2>/dev/null | sort
find "$OWNER_ROOT" -maxdepth 5 -path '*/bin/python' -type f 2>/dev/null | sort
ls /app/vllm-omni/.venv 2>/dev/null
which python   # 容器里可能是 /app/vllm-omni/.venv/bin/python
```

`local/remote.md`、历史错题和其他人的目录只能当候选线索，不能当“目标工作根不存在”的证据。用户明确说某个工作根或 vLLM 版本环境存在时，先用 live `find` / import gate 证明精确路径；环境目录可能按版本命名，不一定叫 `.venv`。没找到要汇报“我没有按正确根目录查到”，不能直接跳到其他用户目录。

候选 python 的最低 import gate：

```bash
"$PY" - <<'PY'
import sys
print("python", sys.executable)
try:
    import vllm
    print("vllm", vllm.__version__)
except Exception as e:
    print("vllm_import_error", repr(e))
try:
    import pytest
    print("pytest", pytest.__version__)
except Exception as e:
    print("pytest_import_error", repr(e))
PY
```

#### 1.5 容器权限问题

容器内是 root，但挂载的 Lustre 目录 owner 是 UID=2129 之类。会有两类问题：

- **Git 报 dubious ownership**：先验证仓库 owner 和绝对路径，只将当前已授权仓库加入 `safe.directory`；禁止使用通配符全局放行
- **某些 Lustre 子目录 root 没权限读**：没办法，需要容器加 `--user 2129:1033`（但 cuda-12.9 image 可能没建 user，风险高）

### 反面教训

- **不要**上来就跑业务命令。先 30 秒探环境
- **不要**假设节点路径结构。每个节点不一样
- **不要**依赖容器内的 `~/.cache`，写 Lustre 才持久
- **不要**因为看到别人的 repo/venv 可用，就跳过任务 owner root
- **不要**在他人 repo 下 `git fetch`、`git worktree add`、`pip install`、跑会写 cache 的测试，除非用户明确授权

## 2. 香港机器：直连 PyPI，不要清华源

### 规则

- **默认 PyPI 直连**：`pypi.org` 连得很快
- **不要用清华源**：`pypi.tuna.tsinghua.edu.cn` 在香港机器上**反而慢**（香港 → 北京 → 清华 → 香港，反向绕路）
- **不要用阿里云源**：同理

### 容器里 pip 配置可能是遗留

`pip config list` 如果显示 `global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'`，那是镜像拉自国内集群的老配置遗留，**在香港节点上应当无视或覆盖**：

```bash
# 好：直连 pypi
uv pip install --index-strategy unsafe-best-match <pkg>
pip install --index-url https://pypi.org/simple <pkg>

# 坏：绕路清华
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple <pkg>
pip install <pkg>  # 如果 pip.conf 是清华
```

### 数据点

- 装 `mmengine`：清华源挂起 60+ 秒不动 → Ctrl-C；默认 pypi **3.82 秒** 装完
- 装 `open_clip_torch + clip-benchmark`（5 个包）：默认 pypi ~20 秒

### 踩坑教训：装包慢先怀疑源，不要怀疑包

**症状**：`uv pip install X` 卡 60 秒无输出，我以为是 uv 在解依赖
**真相**：是 pypi.tuna 清华源在香港连接慢；切 pypi.org 3.82 秒完成
**教训**：命令行装包不动，第一反应**换源**（pypi.org），不要去 Ctrl-C 然后换工具（pip vs uv）——**工具不是问题，源才是问题**

### 推论

- HF 下载同理，`hf download` 默认直连 `huggingface.co`，在香港直连最快，不要设镜像
- `apt install` 同理，默认 `archive.ubuntu.com` 或 docker image 预设的源通常 OK

## 3. 别人的 editable install：worktree + PYTHONPATH 前置

远端 `/rebase/.venv/bin/python` 这种共享 venv 里 vllm_omni 经常是别人活跃 checkout 的 editable install（典型在 `/mnt/scratch/wt-pr<n>/`），上面可能有别人 mid-edit 的脏文件，**不能直接 patch**。

更严格的边界：他人 repo/venv 默认只能只读侦察版本、依赖和 editable 指向；不要把新 worktree 挂到对方 repo 的 `.git/worktrees`，也不要用对方 venv 做安装或测试缓存写入。真正验证用 owner root 下已确认的 repo/venv，或本轮专用 clone + 自有 venv/cache。

### 套路

1. **建自己的干净 clone/worktree**：从任务 owner 的远端和自己有写权限的目录创建；他人的 editable install 只用于识别版本和依赖，不在其中 fetch、建 worktree 或修改文件
2. **SCP 自己的改动文件**：改了哪几个就 scp 哪几个进新 worktree 的相同相对路径（不要整目录 sync，否则把对方未 push 的状态也带过去）
3. **PYTHONPATH 前置**跑：
   ```bash
   PYTHONPATH=/mnt/scratch/wt-<my-feature>:$PYTHONPATH python -m pytest <test_path> -v
   ```
   Python 找包按 sys.path 顺序，前置自己的目录 → 我的 `vllm_omni/...` 模块文件先被找到，editable install 里的同名模块被屏蔽
4. **验证生效**：`python -c "import vllm_omni.X; print(vllm_omni.X.__file__)"` 必须打印自己 worktree 路径，不是 `/mnt/scratch/wt-pr<n>/...`

### 适用范围

- 测试 Python 端纯逻辑改动（prompt 构造、schema、validator、DSL）
- 改动只涉及少数 .py 文件（≲10 个），SCP 还能控制
- **不适用**：动 C++ extension / kernel / 编译产物——editable install 的 .so 是另一份、PYTHONPATH 不解决 ABI
- **不适用**：改动牵动 setup.py / pyproject.toml / `__init__.py` 重导出顺序——可能需要重装

### 反例（不要做）

- 直接 `vim /mnt/scratch/wt-pr<n>/vllm_omni/...` 改对方 working tree
- `pip install -e .` 自己的 worktree 覆盖对方的 editable
- rsync 整个本地 worktree 上去——会把本地未 commit 的脏文件、pyc 缓存、IDE 配置全推过去
