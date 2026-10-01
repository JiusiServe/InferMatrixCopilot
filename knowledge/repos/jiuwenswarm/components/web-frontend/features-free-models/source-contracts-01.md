---
title: "features-free-models 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-free-models 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/free-models/campaign.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ba8207d0fac09ab53f320600b5bbd6350b64cd9833d2079355bb353b180478b4 -->
**`jiuwenswarm/channels/web/frontend/src/features/free-models/campaign.ts`**

- 源码声明的类型、组件或调用边界：`FreeModelsCampaign`, `useFreeModelsCampaign`, `state`, `enabled`, `initialized`, `refresh`, `recheck`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect } from 'react';`；`import type { CampaignState } from '../../services/authClient';`；`import { useAuthStore } from '../../stores/authStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/free-models/campaign.ts#L1-L34)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/free-models/chatError.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f558af1fdd1217798c34a55a2c7cc1dd1931d80a888699e19c4525884074501 -->
**`jiuwenswarm/channels/web/frontend/src/features/free-models/chatError.ts`**

- 源码声明的类型、组件或调用边界：`Translate`, `UPSTREAM_HINT_KEYS`, `LIFECYCLE_ERROR_KEYS`, `describeChatError`, `code`, `lifecycleKey`, `hintKey`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/free-models/chatError.ts#L1-L32)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/free-models/points.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d72e6fd5d37ac478dfe83c8a4dbf0794b54e65771bb880a3c48731498f387502 -->
**`jiuwenswarm/channels/web/frontend/src/features/free-models/points.ts`**

- 源码声明的类型、组件或调用边界：`PointsQuota`, `formatPoints`, `floored`, `usedRatio`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/free-models/points.ts#L1-L18)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/free-models/quotaReset.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d77d0110b7058d09debe02e3dbf5b5f95bc078d0367772fd631577ba69c7350b -->
**`jiuwenswarm/channels/web/frontend/src/features/free-models/quotaReset.ts`**

- 源码声明的类型、组件或调用边界：`QuotaResetText`, `Unit`, `parseResetPeriod`, `match`, `count`, `parseResetAt`, `date`, `formatTime`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/free-models/quotaReset.ts#L1-L78)。
<!-- /kb:file -->
