---
title: "features-clawhubsearchmodal 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-clawhubsearchmodal 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/ClawHubSearchModal/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6368b164a304e1c0474197a0aa753f62560856cb3264210d34153fed89be6efe -->
**`jiuwenswarm/channels/web/frontend/src/features/ClawHubSearchModal/index.tsx`**

- 源码声明的类型、组件或调用边界：`LoadState`, `ClawHubSkillItem`, `ClawHubSearchModalProps`, `ClawHubSearchModal`, `withSession`, `showMessage`, `fetchToken`, `data`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from "react";`；`import { useTranslation } from "react-i18next";`；`import { webRequest } from "../../services/webClient";`；`import { getSkillAvatar } from "../../utils/skillAvatar";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/ClawHubSearchModal/index.tsx#L1-L737)。
<!-- /kb:file -->
