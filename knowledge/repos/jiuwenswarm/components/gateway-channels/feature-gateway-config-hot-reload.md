---
title: "Gateway Config-Save Hot Reload（_on_config_saved：agent.reload_config 重试、重启兜底与副作用）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2065-L2072, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2113-L2124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2032-L2086, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2119-L2125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2057-L2058, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2090-L2135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2039-L2058, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2137-L2159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2080-L2084, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L2102-L2125]
feature: "gateway-config-hot-reload"
entry_points: ["jiuwenswarm/gateway/app_gateway.py"]
source_globs: ["jiuwenswarm/gateway/app_gateway.py"]
---

# Gateway Config-Save Hot Reload（_on_config_saved：agent.reload_config 重试、重启兜底与副作用）

<!-- kb:knowledge owner=feature-gateway-config-hot-reload facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证入口**

所示代码范围内没有测试引用或断言；验证线索仅有运行时日志：重试 warning（含 attempt 计数与延迟）、失败后的 critical 日志、以及 ValidationError/browser restart/proactive sync 的非致命 warning，可作为人工验证的行为信号。代码中的注释描述了历史故障模式（首登 config.set 前端卡死+1001、沙箱 code 80004），属维护者经验性证据而非测试。

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2065–L2072](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2065-L2072), [jiuwenswarm/gateway/app_gateway.py:L2113–L2124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2113-L2124)

<!-- kb:knowledge owner=feature-gateway-config-hot-reload facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**_on_config_saved 的入口契约**

`_on_config_saved(updated_env_keys, *, env_updates, config_payload, reload_options) -> bool` 是配置保存后的内部入口。它先调用 `client.set_or_update_server_config` 更新网关侧配置，再构造 `ReqMethod.AGENT_RELOAD_CONFIG` 信封发送给 AgentServer，params 含 `config`（保存后的完整快照，Agent 应优先于本地 yaml）、`env`（增量更新，缺失键表示未变），`reload_options` 中的键会经 `**dict(reload_options or {})` 展开覆盖同名字段。返回 True 表示重载成功，False 表示校验错误短路或重试耗尽（后者会安排网关重启）。信封固定 user_id="agentos_test"、session_id="sess_reload"。

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2032–L2086](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2032-L2086), [jiuwenswarm/gateway/app_gateway.py:L2119–L2125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2119-L2125)

<!-- kb:knowledge owner=feature-gateway-config-hot-reload facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**控制流与副作用顺序**

重载请求最多尝试 `_reload_max_retries + 1`（4）次，成功即提前跳出；被拒绝的响应若错误文本含 "ValidationError"/"validation error"/"Field required" 之一则直接返回 False，不重试也不重启；`send_request` 抛出的异常进入重试路径，重试间隔为 `2.0 ** (attempt + 1)` 秒（2、4、8）。重试耗尽后记 critical 日志并调用 `_schedule_gateway_restart(restart_request)`，返回 False。成功后依次执行：`message_handler.update_evolution_auto_save(config_payload)` 刷新内存值（流式热路径不重新读盘）、以 3.0 秒延迟调度 `_schedule_agent_prewarm_sync`、按 env 键条件触发 browser runtime 重启与 proactive cron 同步。

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2057–L2058](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2057-L2058), [jiuwenswarm/gateway/app_gateway.py:L2090–L2135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2090-L2135)

<!-- kb:knowledge owner=feature-gateway-config-hot-reload facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**硬编码参数与触发键集合**

重试次数（3）、退避基数（2.0 秒）和 prewarm 同步延迟（3.0 秒）均为函数内硬编码局部量，非外部可配置项。副作用触发依赖 `updated_env_keys` 集合：仅当与 `browser_runtime_keys`（MODEL/VISION/AUDIO/VIDEO 的 PROVIDER、MODEL_NAME、API_BASE、API_KEY 等 16 个键）有交集时才发送 `BROWSER_RUNTIME_RESTART`；仅当含 `proactive_recommendation_enabled` 时才调用 `sync_proactive_tick_job`。内存刷新与 prewarm 同步不受这些键集合条件控制。重载信封固定复用 `agentos_test` 用户及其 warm instance。

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2039–L2058](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2039-L2058), [jiuwenswarm/gateway/app_gateway.py:L2137–L2159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2137-L2159)

<!-- kb:knowledge owner=feature-gateway-config-hot-reload facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的行为与条件**

功能包括：(1) 配置保存后的全局热重载，向 AgentServer 传完整 config 快照与增量 env；(2) 校验错误短路——错误文本匹配三个子串之一时记 warning 并返回 False，不重试、不重启；(3) 重试耗尽后的网关重启兜底；(4) 成功后的条件副作用——browser runtime 重启仅在 browser 相关 env 键变更时触发且失败仅记 warning（非致命），proactive.tick 任务同步仅在 `proactive_recommendation_enabled` 变更时触发且失败不阻断配置保存。

Sources / 来源：[jiuwenswarm/gateway/app_gateway.py:L2080–L2084](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2080-L2084), [jiuwenswarm/gateway/app_gateway.py:L2102–L2125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2102-L2125), [jiuwenswarm/gateway/app_gateway.py:L2137–L2159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L2137-L2159)

