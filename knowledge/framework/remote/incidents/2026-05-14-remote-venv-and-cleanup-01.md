# 2026-05-14 — cp -r 复制别人的 venv 想"独立"反而踩坑

- 编号：`inc-2026-05-14-remote-venv-and-cleanup-01`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：cp -r 复制别人的 venv 想"独立"反而踩坑
- 影响范围：framework/remote

## 原文件说明

# Error Book: 远端 venv / 清理

**症状**：用户在新节点（`root@<REMOTE_HOST>:31449`）要求"new own venv"，我没用 `uv venv` 而是 `cp -r <REMOTE_WORK_ROOT>/venv .venv`，8.8GB 源拷成 25GB+ 还没生成 `bin/python`，半天动不了。换 `cp -rP` 重试仍然异常膨胀
**根因**：venv 是 "site-packages 指针 + wheel 安装记录" 的元数据集合，不是普通目录。cp 行为受 symlink / uv cache / 并行 fs 语义影响（cpfs 这次明显异常）。更根本的——**复制后仍然不是"own"，只是别人 venv 状态的 fork**。用户的"new owner venv"字面就是 `uv venv` 从零建一个
**解法**：永远走
```bash
cd /<my-new-project-dir>
uv venv .venv --python <existing system python>
.venv/bin/uv pip install vllm==<EXACT_VERSION>      # 命中 uv wheel cache 秒过
.venv/bin/uv pip install -e . --no-build-isolation  # vllm-omni 不在 requirements pin vllm，确认过
```
**对未来的提醒**：(1) 看到 "new"/"own"/"独立 venv" → 自动 `uv venv` 不要找捷径；(2) `du -sh source` vs `du -sh dest` 差异 >1.5x → 立刻停手反问"是不是走错路"；(3) 用户第一次骂之后**还原意图**（uv venv 新建）而不是"换个差不多的动作"（cp 复制）继续硬上 — 这是 P2 派生 / B4 反例
