# 2026-05-18 — 跨主机同步代码用 patch/scp 走弯路，git push/fetch 才是正路

- 编号：`inc-2026-05-18-remote-validation-008`
- 归属：`repos/vllm-omni/remote`
- 状态：已验证
- 搜索词：跨主机同步代码用 patch/scp 走弯路，git push/fetch 才是正路
- 影响范围：repos/vllm-omni/remote

**症状**：Windows 本地改完代码想同步到远端 worktree，先试 `git diff | ssh apply -`（上下文不匹配失败）、再想 scp，最后才用 git commit + push fork branch + 远端 `git fetch + git checkout` 才稳定。中间反复 retry 占 5+ 分钟。

**根因**：纠结于"调试期不要 commit-push 循环"（B1）而绕远路。但 B1 管的是"fix attempt N"型的本地循环；**跨主机同步代码**本来就只有 git 这一条正路。

**解法**：跨主机同步用 git commit + push to fork branch + remote git fetch + git checkout FETCH_HEAD。`git diff | ssh apply` 在 line ending / 文件未保存 / context 漂移时必跪。

**怎么避免**：
1. B1 边界：单机本地试错走 `/tmp/test_xxx.py`；跨主机同步走 commit-push-fetch，禁用 patch/scp。
2. 远端 worktree 在 detached HEAD 时也可以 `git checkout -B branch FETCH_HEAD` 切干净。
3. fork 推送命令本地起好别名：`git remote add fork ...`；push 用 `git push fork HEAD:<branch> --force-with-lease`。
