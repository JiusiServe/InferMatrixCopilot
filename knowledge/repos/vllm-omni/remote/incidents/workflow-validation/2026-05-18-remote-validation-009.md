# 2026-05-18 — gh CLI token keyring 失效，PR 描述更新需手贴

- 编号：`inc-2026-05-18-remote-validation-009`
- 归属：`repos/vllm-omni/remote`
- 状态：已验证
- 搜索词：gh CLI token keyring 失效，PR 描述更新需手贴
- 影响范围：repos/vllm-omni/remote

**症状**：`gh pr edit 3626 --body-file ...` 报 `Failed to log in to github.com account zuiho-kai (keyring) - The token in keyring is invalid`。

**根因**：Windows 上 gh 的 keyring 存的 token 过期或被替换。本会话内无法刷新。

**解法**：把 PR 描述写成 markdown 文件（如 `.scratch_pr_body.md`），让用户在 GitHub Web 端 Edit → 粘贴。

**怎么避免**：
1. 会话内 `gh auth status` 一次失败 → 标记本会话 gh 不可用，后续 PR 描述/comment 操作直接走"写 markdown + 让用户手贴"。
2. 不要每次有 PR 操作都试一遍 gh，浪费一轮对话。
3. PR 描述文件命名 `.scratch_pr_body.md` 放 worktree 根，未 commit（worktree 一般已 ignore 隐藏文件或 .scratch/ 目录）。
