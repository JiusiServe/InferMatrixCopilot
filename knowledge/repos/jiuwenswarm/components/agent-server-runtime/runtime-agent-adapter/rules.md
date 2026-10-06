---
title: "Agent adapter 运行时规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7689"]
confidence: high
---

# Agent adapter 运行时规则

## JW-RUNTIME-ROUTING-1a — Code 的模型路由 rail 由规范化 sub-mode 决定

- 触发：修改 `CodeAdapter._build_agent_rails`、Code session 重建或模型档位路由的挂载。
- 强制：以规范化后的 `sub_mode` 区分 profile；`normal`/`plan` 分支追加 `_model_routing_rail`，builder 为 `_build_model_routing`，参数使用同一 `config_base`；team 分支将该属性设为 `None`。重建时顶层 `mode="agent"` 的兼容默认不能替代 sub-mode 判定。
- 禁止：只凭顶层 mode 决定挂载；给已由 relay 解析具体模型 ID 的 team profile 再挂同一档位 rail；把挂载 diff 或注释当作四档实际转换已验证的证据。
- 验收：分别检查默认/规范化后的 `normal`、`plan` 与 team 分支，断言 builder、config 和属性清除一致；需要宣称档位转换有效时另核对 rail 的转换实现及实际路由测试。^[PR #7689]
