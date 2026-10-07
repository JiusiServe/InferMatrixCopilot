---
title: "上下文占用指示器（ContextUsageIndicator：环形触发器/悬浮提示/明细弹层）"
created: 2026-10-06
updated: 2026-10-07
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L152-L165, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L121-L140, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L273-L304, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L62-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142-L157, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18649-L18701, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L19-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L144-L164, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L233-L238, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L182-L201, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L218-L265, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18666-L18701, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142-L165, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L218-L245]
feature: "context-usage-indicator"
entry_points: ["jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.css", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.css", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/server/utils/stream_utils.py"]
---

# 上下文占用指示器（ContextUsageIndicator：环形触发器/悬浮提示/明细弹层）

<!-- kb:knowledge owner=feature-context-usage-indicator facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的交互与展示行为**

触发按钮显示 12px SVG 环形进度（`getContextRingPercent` 换算 occupancy_rate，null 时不画值弧）；hover 或键盘聚焦显示悬浮提示（占用率/已用/上限，可选 KV cache 命中率行）；点击打开明细弹层，含汇总指标、按类别的分段条形 breakdown 与类别 token 列表，类别顺序为已知 key 优先、未知类别追加并以原 category 名与次级色显示。明细支持 Escape 关闭并还原焦点、外点关闭，切换会话或快照消失时自动关闭（ContextUsageIndicator.tsx:76-77、98-107、121-140、152-165、203-215、273-304）。可访问性上使用 `aria-haspopup="dialog"`、`aria-expanded`、`aria-describedby`、role=tooltip/dialog 等（186-189、223-251）。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L152–L165](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L152-L165), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L121–L140](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L121-L140), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L273–L304](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L273-L304)

<!-- kb:knowledge owner=feature-context-usage-indicator facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**API 与数据契约**

前端入口是 React 组件 `ContextUsageIndicator()`，无 props：它从 `chatStore.activeSessionId` 和 `sessionStore.runtimes[id].contextUsageSnapshot` 读取数据，仅在 mode 为 `agent` 或 `team` 且快照存在时渲染（tsx:62-66、142）。消费的快照字段为 `context_window.occupancy_rate/input_tokens/limit_tokens`、`session_kv_cache_hit_rate` 与 `parts` 分类明细（tsx:145-157）。服务端侧 `get_context_usage_event(session_id, *, request_id)` 返回 `dict | None`：agent-core 缺少 `build_context_usage_snapshot` 或会话 context 未加载时返回 None；快照构造阶段的异常被捕获并降级为 None（interface_deep.py:18649-18701），但适配器创建/逐出与 context 查找发生在该保护之外。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L62–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L62-L77), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142–L157](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L142-L157), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18649–L18701](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L18649-L18701)

<!-- kb:knowledge owner=feature-context-usage-indicator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**可调常量与降级显示**

组件内没有外部配置项，弹层几何由模块常量控制：`VIEWPORT_GAP=8`、`TOOLTIP_GAP=5`、`TOOLTIP_ALIGN_OFFSET=3`、`DETAIL_GAP=7`（tsx:19-22）。显示降级分两类：occupancy_rate、input_tokens、limit_tokens 为 null 时显示 `chat.contextUsage.notReported` 文案（tsx:147-150）；KV cache 命中率为 null 时不显示对应行——tooltip 与明细中的该行仅在 `displayCacheRate !== null` 时渲染（tsx:151、233-238、306-311）。未知类别（无 category 定义）以原始 category 名作为标签、使用 `var(--color-text-secondary)` 颜色追加在已知类别之后（tsx:157-164）。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L19–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L19-L22), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L144–L164](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L144-L164), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L233–L238](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L233-L238)

<!-- kb:knowledge owner=feature-context-usage-indicator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证：data-testid 挂点与组件级可测状态**

该组件为 UI 测试提供了四个稳定的 `data-testid` 挂点：`chat-panel-context-usage-trigger`（触发按钮）、`chat-panel-context-usage-tooltip`（悬浮提示）、`chat-panel-context-usage-detail`（明细弹层）与 `chat-panel-context-usage-close`（关闭按钮），配合受控的 hover/focus 状态和 `detailSessionId` 生命周期（Escape 关闭并还原焦点、外点关闭、切换会话或快照消失时重置）可作为组件测试的断言入口。在本次展示的输入中未包含直接针对 ContextUsageIndicator 的测试文件；展示的 Python 测试（如 test_subagent_runtime_integration.py、test_task_rail.py）覆盖的是同一 JiuWenSwarmDeepAdapter 的其他职责。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L182–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L182-L201), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L218–L265](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L218-L265)

<!-- kb:knowledge owner=feature-context-usage-indicator facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**容错降级与兼容性取舍**

服务端将快照构造视为尽力而为：agent-core 缺少 `build_context_usage_snapshot`（滚动升级兼容）或会话 context 未加载时返回 None；快照构造抛出的异常被捕获降级为 None，注释明确 usage 遥测不得导致 /compact 失败（interface_deep.py:18674-18701）。前端对缺失字段做显示降级：occupancy_rate/input_tokens/limit_tokens 为 null 时显示 notReported 文案，KV cache 命中率为 null 时省略对应行（ContextUsageIndicator.tsx:142-151, 233-238, 306-311）。

Sources / 来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18666–L18701](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L18666-L18701), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L142-L151), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L233–L238](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L233-L238)

<!-- kb:knowledge owner=feature-context-usage-indicator facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**前后端职责划分与数据流**

数据流分两段。前端 `ContextUsageIndicator()` 是无 props 的纯消费组件：从 `chatStore.activeSessionId` 与 `sessionStore.runtimes[id].contextUsageSnapshot` 取数，仅在 mode 为 agent/team 且快照存在时渲染，快照的 `context_window`、`session_kv_cache_hit_rate` 与 `parts` 直接驱动环形弧长、悬浮提示与明细弹层（含按类别分段的 breakdown），弹层通过 createPortal 挂到 document.body 并基于触发按钮的 getBoundingClientRect 定位（tsx:62-77、142-165、218-245）。服务端侧 `JiuWenSwarmDeepAdapter.get_context_usage_event` 负责产出快照：非会话作用域适配器先委托/复用按会话适配器并在结束后逐出空闲适配器；会话作用域路径从 `react_agent.context_engine.get_context(session_id)` 取上下文，调用 agent-core 的 `build_context_usage_snapshot`（phase="post_compact"）并经 `normalize_context_usage_payload` 归一化返回，异常保护仅覆盖快照构造与归一化这一段（interface_deep.py:18649-18701）。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L62–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L62-L77), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142–L165](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L142-L165), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L218–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L218-L245), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18649–L18701](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L18649-L18701)

<!-- kb:knowledge owner=feature-context-usage-indicator facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**前后端职责划分与数据流**

前端 `ContextUsageIndicator()` 是无 props 的纯消费组件：从 `chatStore.activeSessionId` 与 `sessionStore.runtimes[id].contextUsageSnapshot` 取数，仅在 mode 为 agent/team 且快照存在时渲染，快照的 `context_window`、`session_kv_cache_hit_rate` 与 `parts` 驱动环形弧长、悬浮提示与明细弹层，弹层经 createPortal 挂到 document.body 并按触发按钮的 getBoundingClientRect 定位。服务端 `JiuWenSwarmDeepAdapter.get_context_usage_event` 负责产出快照：非会话作用域适配器先委托按会话适配器并在结束后逐出空闲适配器；会话作用域路径从 `react_agent.context_engine.get_context(session_id)` 取上下文，调用 agent-core 的 `build_context_usage_snapshot`（phase="post_compact"）并经 `normalize_context_usage_payload` 归一化返回。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L62–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L62-L77), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142–L165](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L142-L165), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L218–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L218-L245), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18649–L18701](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L18649-L18701)

