---
title: "华为账号登录与免费模型凭据（common/auth）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 华为账号登录与免费模型凭据（common/auth）

负责华为账号 Account Kit 登录（OAuth2 授权码 + PKCE）、登录会话的加密落盘与 token 续期，并在登录后通过 APIG 通道发现免费模型、查询积分。Gateway 转发请求时附上用户的 id_token。AgentServer 的模型配置里只存 `jiuwen-login:<ref>` 占位句柄，请求发出前才换成真 token。

**从这里读起**

- `jiuwenswarm/common/auth/service.py` — AuthService 是各 channel 共用的唯一登录入口，负责发起授权、回调、认领、登出、状态查询和续期；模型层通过 live_session / resolve_id_token 取凭据
- `jiuwenswarm/common/auth/passthrough.py` — Gateway 侧：normalize_model_auth 先删掉客户端传来的凭据键，再由服务端决定是否挂上该用户的 id_token
- `jiuwenswarm/common/auth/login_credentials.py` — AgentServer 侧：按句柄登记 token，并用 SDK httpx 钩子（inject_login_credential / apply_login_credential_patch）在请求发出前换成真 token
- `jiuwenswarm/common/auth/remote_config.py` — 官网下发的远端配置（get_config / warm_up_in_background），决定登录和免费模型功能是否开启

**关键文件**

- `jiuwenswarm/common/auth/account_kit.py` — OAuth 流程本身：PKCE 生成、待完成登录表 PendingLogins、换码、认领、refresh_token 续期
- `jiuwenswarm/common/auth/session_store.py` — 登录会话存在内存里，并用 AES-256-GCM 加密落盘（密钥在 ~/.jiuwenswarm/auth/.install_key）；Gateway 与 AgentServer 靠它共享登录态
- `jiuwenswarm/common/auth/model_catalog.py` — 用 id_token 发现账号可用的模型并缓存，转成 models.defaults 条目；这些模型永远不写进 config.yaml（is_login_model 负责拦截）
- `jiuwenswarm/common/auth/apig.py` — APIG 客户端：模型列表、积分查询（ModelQuota）、推理接入点，积分用完时抛 QuotaExhausted
- `jiuwenswarm/common/auth/session_owners.py` — 记录对话会话由哪个账号选了免费模型，让飞书等 IM 通道中没有登录会话的请求也能找回凭据
- `jiuwenswarm/common/auth/net.py` — 登录链路的出网请求封装，以及 SSL 校验开关

**改动路由**

- `jiuwenswarm/common/auth/`
