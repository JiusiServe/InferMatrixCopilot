---
title: "扩展机制与 openYuanRong 集成（jiuwenswarm/extensions/）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 扩展机制与 openYuanRong 集成（jiuwenswarm/extensions/）

负责 JiuwenSwarm 的扩展体系：查找、加载和管理扩展，用 ExtensionRegistry 统一登记 AgentServerClient、加密工具、第三方 Agent、应用插件等扩展点，并提供 Gateway/AgentServer 的 hook 事件与上下文；应用插件的 HTTP、WebSocket 路由和前端资源也在这里挂载。同一目录下还有 openYuanRong 集成：Frontend HTTP 客户端、对应的 AgentServerClient 扩展，以及 clawee FaaS 函数入口。

**从这里读起**

- `jiuwenswarm/extensions/manager.py` — ExtensionManager：从配置解析扩展目录，load_all_extensions / shutdown_all_extensions / list_extensions 管理全部扩展的生命周期
- `jiuwenswarm/extensions/registry.py` — ExtensionRegistry 单例：注册和获取各类扩展，register/unregister/trigger 负责 hook 事件分发；应用插件在这里绑定 web channel
- `jiuwenswarm/extensions/application_host.py` — 应用插件宿主：生成插件清单，挂载插件的 HTTP 路由和静态资源，枚举插件的 WebSocket 路由
- `jiuwenswarm/extensions/clawee.py` — openYuanRong 函数入口（init/handler/ahandler/pre_stop），复用 AgentWebSocketServer._handle_message，FaaS 链路和 ws 链路走同一套处理代码
- `jiuwenswarm/extensions/agent_client/extension.py` — YuanrongAgentServerClientExtension 与 register_extensions：把 Yuanrong 客户端注册为 AgentServerClient 扩展

**关键文件**

- `jiuwenswarm/extensions/loader.py` — ExtensionLoader：在搜索路径中识别扩展根目录，读取 manifest，安装依赖，导入入口模块
- `jiuwenswarm/extensions/sdk/base.py` — BaseExtension 抽象基类：initialize/shutdown 生命周期，从 YAML 读取元数据和配置
- `jiuwenswarm/extensions/sdk/application_plugin.py` — ApplicationPluginExtension、ManifestApplicationPlugin，以及 WebSocket 路由和前端贡献的数据结构
- `jiuwenswarm/extensions/sdk/agent_server_client.py` — AgentServerClientExtension 扩展点：提供 AgentServerClient
- `jiuwenswarm/extensions/sdk/crypto_utility.py` — CryptoUtility 扩展点：提供 CryptoProvider，由 registry 桥接加解密
- `jiuwenswarm/extensions/sdk/third_agent.py` — ThirdAgentExtension 扩展点：提供第三方 Agent
- `jiuwenswarm/extensions/hook_event.py` — GatewayHookEvents / AgentServerHookEvents：hook 事件名定义
- `jiuwenswarm/extensions/hooks_context.py` — Memory、Gateway 对话、AgentServer 对话、SystemPrompt 这几类 hook 的上下文对象
- `jiuwenswarm/extensions/types.py` — ExtensionMetadata / ExtensionConfig 类型
- `jiuwenswarm/extensions/callback_compat.py` — 兼容 openjiuwen<0.1.9 的 AsyncCallbackFramework：补上缺失的 unregister_sync
- `jiuwenswarm/extensions/yuanrong_frontend_client.py` — YuanrongFrontendAgentClient：调用 openYuanRong Frontend 函数，管理常驻 agent 沙箱，处理 trace id 和 TCP 探针配置

**路由**

- `jiuwenswarm/extensions/agent_client/`
- `jiuwenswarm/extensions/application_host.py`
- `jiuwenswarm/extensions/callback_compat.py`
- `jiuwenswarm/extensions/clawee.py`
- `jiuwenswarm/extensions/hook_event.py`
- `jiuwenswarm/extensions/hooks_context.py`
- `jiuwenswarm/extensions/loader.py`
- `jiuwenswarm/extensions/manager.py`
- `jiuwenswarm/extensions/registry.py`
- `jiuwenswarm/extensions/sdk/`
- `jiuwenswarm/extensions/types.py`
- `jiuwenswarm/extensions/yuanrong_frontend_client.py`
