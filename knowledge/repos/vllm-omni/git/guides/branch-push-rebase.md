# PR Workflow · Branch / Push / Rebase

## 机制入口

本页分两层读：

- **通用机制**：开工前确认 git root / worktree、目标 PR head branch、DCO trailer、push remote、rebase 后语义复审。
- **私有操作细节**：Taffy fork、`github-taffy` remote、历史 PR 事故和具体 sign-off identity 只在处理当前私有仓 PR 时复用；同步到公开版时只保留“使用 PR owner 指定身份和 remote，不自造 branch”。

执行顺序固定：

1. 先确认这是新 PR、已有 PR follow-up，还是 rebase / cherry-pick 后更新 PR。
2. 已有 PR 必须查真实 head branch，不用本地自造 branch 名推 fork。
3. 写代码前确认是否在 `wt-*` worktree；主仓只做干净基准。
4. commit 用 DCO sign-off；push 用 PR head owner 对应的可写 remote / SSH identity。
5. rebase 或自动合并后，把冲突文件和 shared path 当 fresh diff 重审。

## 0. 框架代码开工前：主仓保持 main，只作干净基准源

vllm-omni 框架的负责代码仓库在本机：

```powershell
$repo = "D:\vllm-omni\vllm-omni"
```

代码包入口是：

```text
D:\vllm-omni\vllm-omni\vllm_omni
```

**Hard stop guard before any file write:**

在 `D:\vllm-omni\vllm-omni` 相关任务里，任何 `apply_patch` / 文件写入 / 格式化命令前先跑：

```powershell
$root = git rev-parse --show-toplevel
Split-Path $root -Leaf
git status --short --branch
```

如果输出的 git root 目录名不是 `wt-*`，禁止写文件。先新建 worktree，再把 cwd 切到 worktree。只读命令（`rg` / `Get-Content` / `git show`）可以在主仓跑；一旦要改文件，必须通过这个 guard。

**How to apply:**
- 主仓分支保持 `main`，不要在主仓切工作分支、不要在主仓写业务改动。
- 开始框架代码工作前，在主仓同步 `origin/main`：
  ```powershell
  git -C $repo switch main
  git -C $repo fetch origin main
  git -C $repo pull --ff-only origin main
  ```
- 如果主仓只是基准镜像、需要强制回到远端 main，也允许硬对齐（命令是 `--hard`，不是 `-head`）：
  ```powershell
  git -C $repo switch main
  git -C $repo fetch origin main
  git -C $repo reset --hard origin/main
  ```
- 然后从 `origin/main` 或本地 `main` 开独立 worktree，命名 `wt-<purpose>`：
  ```powershell
  $wt = "D:\vllm-omni\wt-<purpose>"
  git -C $repo worktree add -b codex/<purpose> $wt origin/main
  ```
- 后续所有编辑、测试、commit 都在 worktree 内做；主仓只负责保持 `main` 和作为 worktree 源。
- 如果已经在主仓误写，立刻停手：记录 `git status --short`，用 `git diff -- <touched files>` 保存/迁移改动到新 worktree，然后只撤回自己刚造成的主仓改动；不要继续在主仓“顺手修完”。

## 1. PR 分支改完自动 push，不要等用户说

When working on an existing PR/worktree branch, do not wait for the user to say "push" after finishing a code change.

**Why:** 用户原话："自动push 不要我说"。

**How to apply:**
- After implementing a requested PR branch change and passing reasonable local checks, commit or amend as appropriate and push automatically.
- If the branch history was amended, use `git push --force-with-lease`, not a blind force push.
- **动手前先跑 design-time 双 owner review**（[reviewer_lens_gates](../../../../framework/review/guides/reviewer-lens-gates.md)）——非平凡业务改动在形成方案前开两个 sub-agent：module owner 评估模块 contract / edge cases / 测试矩阵，omni project owner 评估 repo 归属 / API surface / PR evidence。不要等写完再 “code check”；事后发现 P0/P1 说明方案 gate 放晚了。
- **Push 前必跑 ruff，且必须在最后一次 edit 后跑** —— `ruff check <changed files>` + `ruff format --check --diff <changed py files>`，两条都要过。CI 用的就是 ruff/pre-commit，跑了 e2e 还栽在 lint/format 上太蠢。2026-05-15 PR `fix/hunyuan-image3-image-size` 上 CI 用 ruff format 把多行 `if` 拍成单行；2026-05-21 PR #3766 又因为最后一次 patch 后只跑了 `ruff check`/pytest/py_compile、漏跑 `ruff format --check`，pre-commit 红了一次。Anaconda Scripts/ruff 已在 PATH，直接 `ruff check ...` + `ruff format --check --diff ...` 几秒过；如果 amend 前又改了任何 Python 文件，重新跑这两条，不能沿用旧结果。
- **Push 前必跑 reviewer-lens 4-audit**（[reviewer_lens_audit](../../../../framework/review/guides/reviewer-lens-audit.md)，prompt 见 [reviewer_lens_prompt](../../../../framework/review/guides/reviewer-lens-prompt.md)）——duplication / layering / edge cases / surface area，自己跑或开 sub-agent 都要用模板里那段 prompt，**禁用** "code check 一下" 类 framing。子 agent 答 "no issues found" 不能直接当通过，CLAUDE.md B33 兜底。PR #3626 没跑这步被 reviewer 4 条评论打回。
- Keep using DCO sign-off for commits.
- **Sign-off identity 机制**：DCO trailer 必须匹配当前 PR / fork 的提交身份；不要从联系人、CLAUDE 说明或远端登录用户脑补邮箱。
- **本私有仓 Taffy PR 细节** (2026-05-15 起): `Signed-off-by: TaffyOfficial <2324465096@qq.com>`. 节点上 `git config user.{name,email}` 应该已经是这对——`git commit -s` 自动带上。**任何手写 trailer / PR 描述 / 给用户的引用文本里都用这个邮箱**，不要把 claudeMd 里的 `wu15922848573@outlook.com` 当 DCO 用（那是 user contact，不是 commit identity）。如果哪天发现 commit 实际 sign-off 用了别的邮箱（例如新节点 git config 没设），就 `git -c user.email=2324465096@qq.com -c user.name=TaffyOfficial commit --amend -s` 改回，再 force-with-lease 推。
- If the user specified an SSH key or remote for the branch, keep using that key/remote for subsequent pushes.
- Only stop before pushing if there is an unresolved test failure, a conflict, missing credentials, or a genuinely risky ambiguity.

### 1.1 Reviewer follow-up 小修复快速通道

**事故**：2026-06-05 PR #4041 只需要修一个 masked `piecewise_attn` span-count P2 和一个 protocol type P3。我已经让 sub-agent 复核 finding 成立，代码改动也只有 3 个文件，但 push 前又机械套完整 PR 流程：二次 reviewer-lens audit、按整个 `origin/main...HEAD` 跑 scope gate、写全 PR ledger、等待 sub-agent，最后才发现远端 head 已经包含修复，`push` 只是 no-op。一个几分钟 follow-up 被拖成半小时。

**规则**：已明确的 reviewer follow-up 小修复走快速通道，不套完整 PR 出货流程。

**触发条件**（全部满足）：
- reviewer finding 已明确，或已被本轮 sub-agent/人工复核确认；
- 本次修复 ≤3 个文件，且只处理已确认 finding；
- 不新增 public API / CLI / extra args / multimodal key；
- 不跨新 model owner，不做重构，不扩大 PR 行为面。

**固定流程**：
1. `gh pr view` / `git fetch <fork> <head-branch>` 先确认 PR 远端 head；如果远端已经包含修复，直接 no-op push 并汇报。
2. 最小 edit + 最小 regression / repro；本地依赖缺失时只记录 blocker，不继续找多层替代证明。
3. 跑 touched Python 文件的 `ruff check` + `ruff format --check --diff`。
4. `git commit -s`，按 PR head owner 的指定 SSH remote push。

**禁止**：
- 同一 finding 已有 sub-agent/人工复核后，再开 reviewer-lens audit 阻塞 push。
- 对已有 PR 的小 follow-up 强行跑全 PR scope gate / 写全 PR ledger；只有本次 follow-up 扩大文件范围或触碰新 owner 才跑。
- 用户明确说 `push` 时先补流程材料。先 push/确认 no-op push，再复盘流程问题。

### 1.2 远端没 GitHub 写权限时，用本机已有 fork remote 推

**症状**：远端 worktree 的 `origin` 是 HTTPS fork：
```text
origin https://github.com/TaffyOfficial/vllm-omni.git
```
直接 `git push` 报：
```text
fatal: could not read Username for 'https://github.com': No such device or address
```
改用 SSH URL 后又报：
```text
ERROR: Permission to TaffyOfficial/vllm-omni.git denied to deploy key
```

**根因**：远端机器的 GitHub SSH key 是 deploy/read key，能 `ls-remote`，不能 push；远端也没有 `gh` 登录态或 credential helper。之前能 SSH 到远端不等于远端能 SSH push GitHub。

**解法**：本机 repo 已配置 `github-taffy` 的可写 remotes（例如 `fork git@github-taffy:TaffyOfficial/vllm-omni.git`）。不要让远端凭据问题阻塞，改走本机干净 worktree：
```powershell
$repo = "D:\vllm-omni\vllm-omni"
$wt = "D:\vllm-omni\wt-push-i2t-smoke"
git -C $repo worktree add -B <branch> $wt origin/main
```
从远端导出目标 commit patch，必须用 `git format-patch` + `scp` 原样拷，不要用 PowerShell `Set-Content` 写 mbox：
```bash
ssh ... 'cd <REMOTE_WORK_ROOT>/wt-i2t-test-fix && git format-patch -1 --stdout HEAD > /tmp/fix.patch'
scp ... root@host:/tmp/fix.patch D:\vllm-omni\fix.patch
git -C D:\vllm-omni\wt-push-i2t-smoke am D:\vllm-omni\fix.patch
git -C D:\vllm-omni\wt-push-i2t-smoke push -u fork <branch> --force-with-lease
```

**为什么不能用 `Set-Content`**：PowerShell 可能加 BOM / 改编码，`git am` 会报 `Patch format detection failed`。`scp` 保留原始 mbox 字节。

**怎么避免**：
1. push 前先跑：
   ```bash
   git remote -v
   ssh -T git@github.com
   gh auth status
   ```
   明确是 GitHub 写凭据还是只读 deploy key。
2. 远端没写权限时，不要反复换 URL；切到本机已有可写 remote。
3. 在本机原 repo 有未跟踪文件时，用独立 worktree 推，避免误带用户改动。
4. `git am` 生成的新 commit hash 可能不同，但作者、message、DCO 和 diff 保持一致；PR 关注 diff 和 trailer。

## 2. "push 到 X 更新 PR Y" 必须查 head branch 名，不要自造分支

要更新一个**已存在的 PR**（不论自己的还是别人的），必须先查 PR head 对应 fork 上的实际 branch 名再 push；自造的本地 branch 名 push 到 fork = 在 fork 上新建 branch，**不会**更新原 PR。

**Why**：2026-05-04 用户让 "push到taff"（语境：更新 PR 2986，作者 TaffyOfficial）。我用本地自造 branch 名 `feat/hunyuanimage3-i2t-ar-prefix-ci` push 到 `fork` remote，结果在 TaffyOfficial fork 新建了一个无人认领的 branch，PR 2986 完全没更新。

**How to apply**：
- 用户说"push 到 X fork 更新 PR Y" / "push到taff" / 类似语境 = 操作目标是更新 PR Y，不是新建 branch
- 执行前查 PR head branch 名：
  ```bash
  git fetch <remote> pull/<PR>/head:pr-<PR>          # 拿到 PR head commit
  PR_COMMIT=$(git rev-parse pr-<PR>)
  git ls-remote <fork-remote> | grep "$PR_COMMIT"     # 找 fork 上指向同 commit 的 refs/heads/<name>
  ```
- 把当前 commit push 到 `<fork-remote> <commit>:refs/heads/<那个 name>`，**不要**用本地 branch 名直接 push
- fast-forward push 到别人 PR head 是 OK 的（保留作者 commit + 我的增量）；force-push 才需要确认

## 2.1 Rebase 后不能只验证能编译，必须做语义复审

**触发条件**：
- PR rebase 到最新 `origin/main`。
- cherry-pick / conflict resolution / force-with-lease 更新 PR head。
- rebase 后 reviewer 又在刚改过的行上问 “why revert previous change?” / “will this affect model X?”。

**不要做**：
- 不要只跑 `ruff` / `compileall` / `git diff --check` 就 push。
- 不要把 “Git 自动合并没有冲突” 当成语义正确。
- 不要用 HunyuanImage3 的局部正确性解释 shared serving path 上的跨模型行为。

**必须做的 gate**：
1. 记录 rebase 前后 head：
   ```powershell
   git rev-parse HEAD
   git ls-remote git@github-taffy:TaffyOfficial/vllm-omni.git refs/heads/<pr-branch>
   ```
2. rebase 后列 commit / 文件范围：
   ```powershell
   $i=1; git log --oneline origin/main..HEAD | ForEach-Object { "{0,2} {1}" -f $i, $_; $i++ }
   git diff --stat origin/main..HEAD
   git diff --name-only origin/main..HEAD
   ```
3. 对冲突文件和自动合并文件跑 fresh semantic diff：
   ```powershell
   git diff origin/main..HEAD -- <file>
   git show origin/main:<file> | Select-String -Pattern "<anchor>" -Context 5,20
   ```
4. 读当前 non-outdated reviewer threads，不只看本地 diff：
   ```powershell
   gh pr view <PR> --repo vllm-project/vllm-omni --json headRefOid
   ```
   需要 thread state 时用 GitHub reviewThreads / `gh api graphql`，区分 outdated 和 current。
5. 对 shared serving / multimodal path 改动，必须 grep 所有消费者：
   ```powershell
   rg -n '"img2img"|"image"|"images"|multi_modal_data|mm_processor_kwargs' `
     vllm_omni/model_executor vllm_omni/diffusion vllm_omni/entrypoints tests
   ```
   然后写一句结论：每个受影响模型是保留、转换、兼容，还是不适用。

**两个 high-risk pattern**：

- **Algorithm 参数被半保留**：HunyuanImage3 explicit size 不是单个 `target_h/w`。`resolve_stop_token_ids(..., image_size="WxH")` 决定 AR 何时 stop；`target_h/w` 决定如果需要 ratio token 时强制哪个 ratio。rebase 时丢任一个都算回退。
- **Multimodal key 被全局化**：`multi_modal_data["image"]` 对 HunyuanImage3 DiT bridge 是正确 consumer，但 Bagel 依赖 `multi_modal_data["img2img"]` 走 `Img2ImgProcessorItems`。共享 chat path 不能为了一个模型改全局 key；模型专属转换要放在模型 owner 或专用 builder。

**验收标准**：
- 当前 PR head、PR body Test Result head、远端 branch head 一致。
- conflict / auto-merged 文件的 semantic diff 已看过，不只是静态检查。
- 当前 non-outdated review threads 没有继续指向“为什么 revert / 会不会影响其他模型”的开放风险。
- shared path 改动有跨模型 grep 证据或测试。

**事故来源**：2026-06-04 PR #3626 rebase 后，`end2end.py` 丢了主干已有的 `image_size` stop-token contract，只保留 `target_h/w`；`serving_chat.py` 把 shared chat img2img payload 从 `{"img2img": img}` 改成 `{"image": img}`，影响 Bagel parser。之前几轮 audit 没发现，是因为 framing 只看 HunyuanImage3 infer-align / explicit-size 语义，rebase 后没有把冲突和 auto-merged 文件当 fresh diff 重审。
