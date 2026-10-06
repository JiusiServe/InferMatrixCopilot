---
title: "登录鉴权与免费模型"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# 登录鉴权与免费模型

- [华为账号登录与免费模型凭据（common/auth）](jiuwenswarm-common-auth.md) — 覆盖 OAuth/PKCE 登录与待完成登录表、续期并发合并、AES-256-GCM 加密会话存档与跨进程共享、Gateway 凭据消毒、AgentServer 运行时句柄登记表与请求钩子、登录模型目录缓存

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：登录、华为账号、Account Kit、OAuth、PKCE、id_token、refresh_token、免费模型、积分、APIG、远端配置、auth。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| 登录、华为账号、Account Kit、OAuth、PKCE、id_token、refresh_token、免费模型、积分、APIG、远端配置、auth | 入口 | `jiuwenswarm/common/auth/service.py`、`jiuwenswarm/common/auth/account_kit.py`、`jiuwenswarm/common/auth/session_store.py` |

## 专题入口

- [登录模型目录与跨进程凭据句柄](jiuwenswarm-login-models.md) — 说明登录模型在 Gateway 与 AgentServer 间的凭据传递、稳定句柄、请求钩子和目录缓存；OAuth 登录与加密会话持久化见登录主页面。

- [登录凭据与续期的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [账号登录与凭据续期 功能知识](feature-login.md)
- [login-auth 源码接口与集成边界 01](source-contracts-01.md)
- [账号登录与凭据续期：实现深读](feature-depth-login.md)
- [login-auth：华为账号登录与免费模型凭据（common/auth）](knowledge.md)
