---
title: "IM Channel Hot Reconfiguration (_apply_channel_config lifecycle across 11 channels)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L362-L364, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3191-L3196, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3205-L3242, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2579-L2586, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2729-L2745, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3210-L3212, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3197-L3203, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3229-L3239, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L366-L387, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2475-L2517]
feature: "im-channel-hot-reconfig"
entry_points: ["jiuwenswarm/gateway/app_gateway.py"]
source_globs: ["jiuwenswarm/gateway/app_gateway.py", "jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py"]
---

# IM Channel Hot Reconfiguration (_apply_channel_config lifecycle across 11 channels)：实现深读

[功能概览](feature-im-channel-hot-reconfig.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-channel-hot-reconfig facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be5727ad4fc85dbbcd31116d1cc5d449ab4b229ed9d47701694ff35bc4d28b74 -->
**ChannelManager.get_conf_revision returns the per-channel write revision, defaulting to 0**
get_conf_revision(channel_id) returns self._conf_revisions.get(channel_id, 0), so callers reading a channel that has never had a configuration write recorded observe revision 0. The retry helper consumes this value to detect newer configuration writes.

来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L362–L364](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L362-L364), [jiuwenswarm/gateway/app_gateway.py:L3191–L3196](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3191-L3196)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":364,"path":"jiuwenswarm/gateway/channel_manager/channel_manager.py","sha256":"25c2936ca4e575bb3c4fe935df20990073a4ccea1707f78c850ee97ba6ebced4","start":362},{"end":3196,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"fbbf1e8f735f53672465e3384f62410000b1b010b3dc6ed7cd71cca656c038f3","start":3191}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-channel-hot-reconfig facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d14a6828bdd182dca2c4aa52a35d6f921c12376f325cdb509444baee251b0e05 -->
**Retry delay starts at 2.0s and backs off doubling capped at 60.0s per failed attempt**
Inside _retry, delay_seconds starts at 2.0; after each failed set_conf it is updated to min(delay_seconds * 2, 60.0) and expected_revision is re-read from channel_manager.get_conf_revision before the next attempt.

来源：[jiuwenswarm/gateway/app_gateway.py:L3205–L3242](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3205-L3242)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3242,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"b093829f3e3101fabd86541060c905df6342f2aa08bdb65e4e821332e8d75f2d","start":3205}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-channel-hot-reconfig facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f056d1f584e4ad7352d323f57fb761bdbb1c88ec007cca6f920d24afbb27f14 -->
**Reapply is coupled to ChannelManager pop/stop and adapter registries; retry is coupled to get_conf_revision**
The feishu/xiaoyi apply branches call channel_manager.pop_channels_by_id and _stop_channel, and lazily import the platform connect module only inside the non-empty-apps branch, keeping heavy platform dependencies off disabled paths. _schedule_channel_config_retry depends on channel_manager.get_conf_revision(channel_name); a differing revision makes the retry stale.

来源：[jiuwenswarm/gateway/app_gateway.py:L2579–L2586](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2579-L2586), [jiuwenswarm/gateway/app_gateway.py:L2729–L2745](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2729-L2745), [jiuwenswarm/gateway/app_gateway.py:L3210–L3212](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3210-L3212)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2586,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"a6129a92dfe81dfd0c62011d1082d9b1426b57c3f08ff005c327212871ccb034","start":2579},{"end":2745,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"fcc4e2bb533435da38ec8d5a2bb334d669f5f2fec220f707c76481064794a6e9","start":2729},{"end":3212,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"6ee8c11d50ef84cae74d73f0ae1902fd00763cea9cb60251f20aba9880f7338d","start":3210}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-channel-hot-reconfig facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=730e53bb3fcc5eafe91763ab628e569a37c0dc740730ebdd807cd4f4f5cc16b6 -->
**ChannelManager.set_conf rolls back its config dict and re-raises when the rebuild callback throws**
set_conf increments the channel's revision and stores a merged config before awaiting the on_config_updated callback; if that callback raises, the previous config dict is restored and the exception propagates to the caller. Only the manager's config dict is restored — the shown lines state no guarantee about already-stopped integrations.

来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L366–L387](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L366-L387)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":387,"path":"jiuwenswarm/gateway/channel_manager/channel_manager.py","sha256":"f8f7c16ce5f4ac7f601189e40fe993fc5240db80272d6f664e65c76154902b36","start":366}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-channel-hot-reconfig facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5dd1f1242d5e7e74c3ea687d49109e7cc45d519d0cc1632ba88cc72a9ff8e536 -->
**Detached retry isolates optional-channel failures without blocking startup, at the cost of resurrection risk handled only by revision checks**
设计推断（非作者历史意图）：

Benefit (documented in the docstring): retrying one failed optional channel avoids delaying Web/Cron startup. Cost (inference): a stale snapshot could resurrect a config the user disabled, mitigated only by comparing get_conf_revision to expected_revision each 2–60s cycle; the reset-to-empty set_conf on error is another extra write that can itself fail and only be logged.

来源：[jiuwenswarm/gateway/app_gateway.py:L3197–L3203](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3197-L3203), [jiuwenswarm/gateway/app_gateway.py:L3229–L3239](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3229-L3239)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3203,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"af4716de28938728523a66fd27acbe6c49039898652356adceb577391c25afdb","start":3197},{"end":3239,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"4c956d424ce9c4bed12e56342a2e77d4bd1142e697234c8bf6b9b550e79135c0","start":3229}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-channel-hot-reconfig facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4969f178a0ec4a2adc0170d656a956a43d6508efa5f9688f0bd2ddf11ee115ac -->
**_stop_channel cancels the channel task, awaits it with a 5s timeout (or in background), stops the channel with a 10s timeout, then unregisters it**
在 app_gateway.py 的 _stop_channel 中：若 task 非空则 task.cancel()，非 background_wait 分支用 asyncio.wait_for(task, timeout=5.0) 等待，TimeoutError/CancelledError/其他异常均只记 warning 或 pass；随后对非空 channel 调 channel.stop()（timeout=10.0，超时或异常仅记日志），最后 channel_manager.unregister_channel(channel.channel_id)。该本地分支不保证停止一定成功——超时后仅记录日志并继续注销。

来源：[jiuwenswarm/gateway/app_gateway.py:L2475–L2517](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2475-L2517)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2517,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"0df23083451998c5ac1f776a8864a26bea75702fa439a373fa18ba643751d1c4","start":2475}],"trace":[]} -->
<!-- /kb:depth -->
