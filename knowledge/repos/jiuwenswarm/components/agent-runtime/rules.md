---
title: "agent-runtime 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7792"]
confidence: high
---

# agent-runtime 审查规则

## JW-RUN-PERM-1a — Process CLI 能力覆盖只作用于本次 run，且不能削弱已安装 deny

- 触发：修改 Process CLI run 请求的 model/skills/mcp/permissions，或 runtime.run_permissions 与工具允许列表。
- 强制：model 先在 Runtime 目录解析；显式空 skills/mcp 保留不选择语义。权限只接受 allow/ask/deny，run overlay 不写全局配置且保留已安装 deny；run 策略期间禁用永久批准写入。工具允许列表在模型可见侧和执行侧同时执行，并涵盖后注册工具。
- 禁止：把本次调用覆盖扩散到 Web/TUI 常驻 channel；只过滤工具 schema 而放过执行；将一次批准写回配置；把合法的 work/code 能力拒为错误。
- 验收：验证 deny 不被 run allow 覆盖、请求间无污染、后注册工具仍受限；非交互 run-json 遇 ask 返回 INTERACTION_REQUIRED，JSONL 由交互回调处理。^[PR #7792]
