---
title: "IM Channel Hot Reconfiguration (_apply_channel_config lifecycle across 11 channels)"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2466-L2517, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2576-L2643, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2552-L2564, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2591-L2643, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2669-L2721, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L4023-L4046, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L4277-L4288, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L4490-L4503]
feature: "im-channel-hot-reconfig"
entry_points: ["jiuwenswarm/gateway/app_gateway.py"]
source_globs: ["jiuwenswarm/gateway/app_gateway.py", "jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py"]
---

# IM Channel Hot Reconfiguration (_apply_channel_config lifecycle across 11 channels)

<!-- kb:knowledge owner=feature-im-channel-hot-reconfig facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Diff-driven stop/rebuild loop over channel_manager and IM adapters**

Control flow: `_should_restart_channel` compares old vs new per-channel config dicts (restart when presence differs or contents differ) and union with `channel_manager.pop_channel_restart_pending()` for forced restarts; only channels in `changed_channels` are torn down and rebuilt (app_gateway.py:2466-2473, 2550-2573). Teardown is centralized in `_stop_channel`: cancel the asyncio task (5s wait, or background wait), `channel.stop()` with a 10s timeout, then `channel_manager.unregister_channel`; feishu/xiaoyi multi-app instances are discovered via `channel_manager.pop_channels_by_id`, and digital-avatar adapters are unregistered/registered on `im_inbound`/`im_outbound` buses.

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2466–L2517](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2466-L2517), [jiuwenswarm/gateway/app_gateway.py:L2576–L2643](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2576-L2643)

<!-- kb:knowledge owner=feature-im-channel-hot-reconfig facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的频道与实例形态**

重配循环覆盖 11 个频道键：feishu、feishu_enterprise、xiaoyi、dingtalk、telegram、whatsapp、discord、slack、wecom、wechat、ssh（app_gateway.py:2552-2564）。feishu 支持 `apps` 列表多实例，所有实例共享 channel_id "feishu"，各自 `asyncio.create_task(channel.start())` 且任务挂在 `channel.start_task` 上；`group_digital_avatar` 为真时创建 FeishuIMPlatformAdapter 并注册到 im_inbound/im_outbound（app_gateway.py:2591-2643）。feishu_enterprise 以 bot_key→配置的映射管理，channel_id 为 `feishu_enterprise:{app_id}`，同样支持数字分身 adapter（app_gateway.py:2669-2721）。

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2552–L2564](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2552-L2564), [jiuwenswarm/gateway/app_gateway.py:L2591–L2643](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2591-L2643), [jiuwenswarm/gateway/app_gateway.py:L2669–L2721](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2669-L2721)

<!-- kb:knowledge owner=feature-im-channel-hot-reconfig facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**写配置前的参数校验**

Web 处理器在写配置前做输入校验：非 dict 的 params 返回 `BAD_REQUEST`（如 feishu set_conf、whatsapp/discord/slack/wecom/wechat set_conf，app_web_handlers.py:4023-4031, 4277-4285）。wechat set_conf 额外调用 `_validate_wechat_numeric_params`，在 `set_conf` 之前拒绝负数/0/极大值/浮点越界/非数字的数值参数并返回 `BAD_REQUEST`（app_web_handlers.py:4490-4500）。feishu set_conf 在持久化前先 `_normalize_feishu_conf` 归一化 apps（app_web_handlers.py:4040-4046）。

Sources / 来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L4023–L4046](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L4023-L4046), [jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L4277–L4288](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L4277-L4288), [jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L4490–L4503](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L4490-L4503)

