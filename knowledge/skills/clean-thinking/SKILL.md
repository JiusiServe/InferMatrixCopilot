---
name: clean-thinking
description: |
  清理 JSONL 对话文件中的 thinking 块，解决 API 报错 "Invalid `signature` in `thinking` block"。
  当遇到 400 invalid_request_error + invalid signature in thinking block 时自动触发。
  用法: /clean-thinking [文件路径|--all|--current]
  - 无参数或 --current: 清理当前会话的 JSONL 文件
  - --all: 清理所有项目的 JSONL 文件
  - 指定路径: 清理指定的 JSONL 文件
author: user
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Clean Thinking Blocks

你是一个专门清理 Claude Code 对话文件中 thinking 块的工具。

## 触发条件

当用户遇到以下报错时应该使用此 skill：
- `Invalid 'signature' in 'thinking' block`
- `invalid_request_error` + `thinking` + `signature`

## 执行步骤

### 1. 确定要清理的文件

根据用户输入决定清理范围：

- 如果用户指定了文件路径，直接使用该路径
- 如果用户说 `--all`，清理所有项目的 JSONL
- 如果用户说 `--current` 或无参数，找到当前会话的 JSONL 文件

找当前会话文件的方法：
```bash
# 当前项目目录下最近修改的 JSONL 文件
ls -t "$HOME/.claude/projects/"*"/"*.jsonl 2>/dev/null | head -5
```

### 2. 执行清理

运行清理脚本：

```bash
python3 "$HOME/.claude/scripts/clean_thinking_blocks.py" <目标文件或--all>
```

### 3. 告知用户结果

- 清理了多少个 thinking 块
- 备份文件的位置
- 建议用户执行 `/clear` 或重启会话以加载清理后的对话

## 注意事项

- 脚本会自动备份原文件为 `.jsonl.bak`
- 只移除 `type: "thinking"` 的块，不影响其他消息内容
- 如果清理后某条 assistant 消息的 content 为空，该消息行会被跳过
