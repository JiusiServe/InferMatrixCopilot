---
title: "components-skillgraphpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-skillgraphpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillGraphPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=998c711593fae3c7c9d66d3f68be65dff3954fe619156f156c48732c59e6e94a -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillGraphPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`RawRecord`, `BuildLogEntry`, `LLMTokenUsageTotals`, `LLMTokenUsageSummary`, `BuildProgress`, `SkillGraphPayload`, `SkillGraphUpdate`, `SkillGraphStatus`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import {`；`import { useTranslation } from 'react-i18next';`；`import { webRequest } from '../../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillGraphPanel/index.tsx#L1-L2075)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillGraphPanel/skillGraphLayout.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cde65ddb8a7a985d473f18c1d009979e78de6727be33b02aeb00603460436eef -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillGraphPanel/skillGraphLayout.ts`**

- 源码声明的类型、组件或调用边界：`LayoutNode`, `LayoutEdge`, `GraphLayoutComponent`, `REPULSION_BASE_COEFFICIENT`, `REPULSION_MAX_FORCE`, `REPULSION_MIN_DIST2`, `LINK_DISTANCE`, `LINK_FORCE_CAN_FEED`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillGraphPanel/skillGraphLayout.ts#L1-L209)。
<!-- /kb:file -->
