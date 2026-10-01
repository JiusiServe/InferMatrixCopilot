---
title: "features-modelsetupguide 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-modelsetupguide 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/modelSetupGuide/ModelSetupGuide.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5b788cbb4d94b5a2d627469d9f326967583d8be4af77a4645c6cc926cd35ac0d -->
**`jiuwenswarm/channels/web/frontend/src/features/modelSetupGuide/ModelSetupGuide.tsx`**

- 源码声明的类型、组件或调用边界：`ModelSetupGuideStep`, `ModelSetupGuideProps`, `SpotlightRect`, `TARGET_SELECTORS`, `toSpotlightRect`, `rect`, `padding`, `left`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { TeamMemberAvatar } from '../../components/TeamMemberAvatar';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/modelSetupGuide/ModelSetupGuide.tsx#L1-L279)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/modelSetupGuide/modelSetupGuideState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a9f70cee218b2902b7d97531716bba32f1f50fe5b4bc930155100315e9120443 -->
**`jiuwenswarm/channels/web/frontend/src/features/modelSetupGuide/modelSetupGuideState.ts`**

- 源码声明的类型、组件或调用边界：`ENABLED_VALUES`, `DISABLED_VALUES`, `isSetupGuideEnabled`, `normalized`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/modelSetupGuide/modelSetupGuideState.ts#L1-L17)。
<!-- /kb:file -->
