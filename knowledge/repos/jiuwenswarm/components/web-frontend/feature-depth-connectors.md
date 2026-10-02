---
title: "连接器市场与 MCP 授权流程：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L14-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L146-L169]
---

# 连接器市场与 MCP 授权流程：实现深读

[功能概览](feature-connectors.md) · [owner 入口](_index.md)

<!-- kb:depth feature=connectors facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b79b9d5a981378d366e22ede958d2a670e94ac8eb8c1df946331474fec678563 -->
**去掉 MOCK FALLBACK、按方法内联字段映射**
设计推断（非作者历史意图）：

事实：mcp.* 方法不再有 tryReal() 包装，失败即抛错，只有后端未实现的 pluginPackagesApi 保留 mock 兜底；snake_case→驼峰转换在每个方法内联（fromRawSummary/fromRawDetail/fromRawConnect），不建通用转换器。推断：这样换来问题不被假数据掩盖、每个响应形状独立可控，代价是字段增减时要在多处内联映射里同步修改，且无兜底时后端故障会直接以错误暴露给用户。

来源：[jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L14–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L14-L30), [jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L146–L169](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L146-L169)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","start":14,"end":30,"sha256":"79a296ab2b4790b7e34df699594a8bc930294c175f766c4be502d74f24e02d82"},{"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","start":146,"end":169,"sha256":"123783bff7b7a22e03db130ae9e80b042db9cfbb420975b14eef4a304b46dd1a"}],"trace":[]} -->
<!-- /kb:depth -->
