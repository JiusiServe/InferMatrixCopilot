---
title: "配置面板 handler（config_panel）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 配置面板 handler（config_panel）

承载 Web 侧和 TUI 侧 config / models 域的 handler 实现，从 gateway 的 app_web_handlers 和 tui_connect 迁出。AgentServer 进程里的 ConfigAdapter 和 gateway 共用这一份实现，只维护一处代码。

**入口**

- `jiuwenswarm/common/config_panel/config_set_handlers.py` — Web 侧入口，register_config_set_handlers 在 channel 上注册 config.set / config.save_all；apply_config_payload 负责写盘（.env 等）
- `jiuwenswarm/common/config_panel/models_handlers.py` — Web 侧入口，register_models_handlers 注册 models.list / models.replace_all / config.validate_model / models.validate
- `jiuwenswarm/common/config_panel/tui_models_handlers.py` — TUI 侧入口，register_tui_config_handlers 注册 config.get / config.set / config.validate_model / models.list，以及 TUI 专属的 command

**关键文件**

- `jiuwenswarm/common/config_panel/config_set_handlers.py` — ConfigChangeSet 和 ConfigApplyResult 表示一次改动的结果（改了哪些键、要重载哪些范围）；flatten_* / build_*_config_update 负责 symphony、skill retriev
- `jiuwenswarm/common/config_panel/models_handlers.py` — 处理模型列表：前端传入的模型转成默认配置、replace_all 时的合并、环境变量占位符比较、provider 规范化、reasoning level 序列化；ConfigPanelBadRequest 是请求错误
- `jiuwenswarm/common/config_panel/tui_models_handlers.py` — TUI 契约与 Web 侧不一致，文件头明确禁止合并；包含 build_config_schema、Auto-Harness 的 git 用户与 gitcode token 设置、模型增删改和切换，以及后台重载配置

**相关文档**

- `docs/zh/E2A-protocol.md` — 改动涉及 AgentOS 多用户的 E2A 代理分叉时读。这部分由 gateway 侧的 _register_config_proxy 包装，本模块只提供本地 handler
- `docs/zh/AutoHarness.md` — 改动 TUI 侧 Auto-Harness 配置项（git user、gitcode token）时读
- `docs/zh/AgentTeam.md` — 改动 modes team 配置的展开，或 team 相关的 codex 请求判断时读
- `TESTING.md` — 给 config / models handler 补测试时参考；文中有过期路径，先看 tests/ 下已有用例

**路由**

- `jiuwenswarm/common/config_panel/`
