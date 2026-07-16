#!/usr/bin/env bash
# stop-gate.sh — Stop hook 综合门禁
#   1. 检测本轮有代码改动 → 提醒去远端跑测试
#   2. 检测本轮有实际工具执行失败 → 提醒写入最近的 incidents/ 或稳定指南

input=$(cat)
transcript_path=$(printf '%s' "$input" | grep -oE '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed -E 's/.*"([^"]+)"$/\1/')

if [[ -z "$transcript_path" || ! -f "$transcript_path" ]]; then
    exit 0
fi

last=$(python3 - "$transcript_path" <<'EOF'
import sys, json

path = sys.argv[1]
lines = open(path).readlines()

# 找最后一个 role=user 的位置，只取之后的内容（本轮 assistant 工具调用）
last_user_idx = -1
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
        if obj.get("role") == "user" or obj.get("type") == "user":
            last_user_idx = i
    except Exception:
        pass

for line in lines[last_user_idx + 1:]:
    print(line, end="")
EOF
)
if [[ -z "$last" ]]; then
    exit 0
fi

has_code_change=false
has_tool_failure=false

if echo "$last" | grep -qE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+\.(py|cpp|cu|cuh|h|hpp|cc)"'; then
    has_code_change=true
fi

# 只匹配实际工具执行失败的强信号（Python 栈回溯、GPU OOM、测试框架 FAIL 输出）
# 不匹配对话中讨论错误的弱信号
if echo "$last" | grep -qE '(Traceback \(most recent call last\)|CUDA out of memory|OOM|pytest.*FAILED|AssertionError|"exit_code"[[:space:]]*:[[:space:]]*[1-9])'; then
    has_tool_failure=true
fi

if ! $has_code_change && ! $has_tool_failure; then
    exit 0
fi

msg="📡 本轮总结："

if $has_code_change; then
    msg="${msg}\\n• 检测到 .py/.cpp 改动 → 是否需要去远端跑测试验证？"
fi

if $has_tool_failure; then
    msg="${msg}\\n• 检测到工具执行失败 → /claudeception 判断是否写入最近的 incidents/ 或稳定指南（diff 给用户确认后再写）。"
fi

msg="${msg}\\n\\n回 'skip' 跳过。"

printf '{"systemMessage": "%s"}\n' "$msg"

exit 0
