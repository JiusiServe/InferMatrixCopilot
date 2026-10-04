---
title: "features-contextusage 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-contextusage 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/contextUsage/contextUsageCategories.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1cba9dc7707900f757dad319da4145bfe7f1e061a35076b1e535decb02a18e53 -->
**`jiuwenswarm/channels/web/frontend/src/features/contextUsage/contextUsageCategories.ts`**

- 源码声明的类型、组件或调用边界：`CONTEXT_USAGE_CATEGORY_DEFINITIONS`, `KnownContextUsageCategoryKey`, `CONTEXT_USAGE_CATEGORY_KEYS`, `getContextUsageCategoryDefinition`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/contextUsage/contextUsageCategories.ts#L1-L30)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/contextUsage/contextUsageModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a2b30e615fe94e4eaf0e8e4c7b36661ce144c6b65a2a3e8819244815014e3218 -->
**`jiuwenswarm/channels/web/frontend/src/features/contextUsage/contextUsageModel.ts`**

- 源码声明的类型、组件或调用边界：`isRecord`, `isNonNegativeNumber`, `isNullableNumber`, `isTokenCount`, `isNullableTokenCount`, `isNullableString`, `isOptionalContextRole`, `isSupportedContextUsagePhase`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ContextUsagePart, ContextUsageSnapshot } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/contextUsage/contextUsageModel.ts#L1-L142)。
<!-- /kb:file -->
