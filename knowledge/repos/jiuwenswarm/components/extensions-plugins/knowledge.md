---
title: "jiuwenswarm 扩展与插件：video_duplex 实时音视频 RPC 与 AgentOS Router 客户端"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/application-plugins.md:L57-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/application-plugins.md:L145-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/video_live.py:L692-L698, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/video_live.py:L170-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/video_live.py:L210-L250]
---

# jiuwenswarm 扩展与插件：video_duplex 实时音视频 RPC 与 AgentOS Router 客户端

<!-- kb:knowledge owner=extensions-plugins facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证入口**

上游文档说明内置 `jiuwenswarm/extensions/video_duplex` 是应用插件的完整参考示例，其配置与测试保留在插件目录内；插件发现与静态资源可用通用 HTTP 接口 `GET /api/application-plugins` 与 `GET /api/application-plugins/{plugin_id}/assets/{asset_path}` 检查。注册成功本身也会写一条 `video_handlers_registered` 事件日志，可作为装配发生的运行时信号。本页展示的输入未包含这些测试文件本身，故不描述其覆盖范围。

Sources / 来源：[docs/zh/application-plugins.md:L57–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/application-plugins.md#L57-L62), [docs/zh/application-plugins.md:L145–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/application-plugins.md#L145-L149), [jiuwenswarm/extensions/video_duplex/backend/video_live.py:L692–L698](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_live.py#L692-L698)

<!-- kb:knowledge owner=extensions-plugins facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**环境变量开关与双 Provider 配置**

运行模式由 `VIDEO_LIVE_MODE` 决定：缺省 `joyai`，仅当值（大小写不敏感）为 `realtime` 时切换到 Qwen Omni 实时模式。`VIDEO_DUPLEX_ENABLED` 缺省视为启用，取值 `0/false/no/off` 时禁用。JoyAI 模式下 `_realtime_config` 读取 `joyai_provider.model_config()`，任一为空即以 `VIDEO_CONFIG_ERROR` 返回错误信息“请配置 JOYAI_API_BASE 和 JOYAI_MODEL_NAME”（具体读取逻辑在未提供的 joyai_provider 中）；realtime 模式则由 `QwenOmniRealtimeConfig.from_environment()` 构造并 `validate()`，仅 `validate()` 抛出的 ValueError 被转为 `VIDEO_CONFIG_ERROR`，`from_environment()` 本身在 try 块之外。

Sources / 来源：[jiuwenswarm/extensions/video_duplex/backend/video_live.py:L170–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_live.py#L170-L187), [jiuwenswarm/extensions/video_duplex/backend/video_live.py:L210–L250](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_live.py#L210-L250)

