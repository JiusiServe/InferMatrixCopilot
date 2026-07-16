#!/usr/bin/env bash
# wt-write-guard.sh — PreToolUse(Write|Edit|NotebookEdit) 门禁
# 硬规则（CLAUDE.md §2.4）：D:\vllm-omni\vllm-omni 主仓只作干净基准，
# 业务改动必须在 wt-<purpose> worktree。此 hook 直接拦截对主仓的写入，
# 不再依赖模型自觉检查 git root。
#
# exit 2 = block（stderr 会反馈给模型）；其他情况放行。

input=$(cat)

# 提取 file_path / notebook_path（Write/Edit 用 file_path，NotebookEdit 用 notebook_path）
path=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    obj = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = obj.get("tool_input") or {}
print(ti.get("file_path") or ti.get("notebook_path") or "")
')

[[ -z "$path" ]] && exit 0

# 归一化：反斜杠转正斜杠，去掉大小写差异的盘符
norm=$(printf '%s' "$path" | tr '\\' '/' )
norm_lc=$(printf '%s' "$norm" | tr '[:upper:]' '[:lower:]')

# 主仓根（vLLM-Omni 干净基准）。wt-* worktree 在 d:/vllm-omni/wt-*，不会命中此前缀。
MAIN_REPO="d:/vllm-omni/vllm-omni/"

if [[ "$norm_lc" == ${MAIN_REPO}* ]]; then
    echo "BLOCKED by wt-write-guard: '$path' 位于主仓 D:\\vllm-omni\\vllm-omni（干净基准，禁止直接写入）。" >&2
    echo "业务改动必须在 wt-<purpose> worktree 里做：用 'git -C D:/vllm-omni/vllm-omni worktree list' 找现有 worktree，或新建 wt-<purpose> 后再写。规则见 workflow-starter/CLAUDE.md §2.4。" >&2
    exit 2
fi

exit 0
