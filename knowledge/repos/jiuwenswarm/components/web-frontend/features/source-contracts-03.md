---
title: "features 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/teamPanelState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=09f6670e1fb91289dffc62c1b17a47189ee26f66832213ef0bc392974fc924aa -->
**`jiuwenswarm/channels/web/frontend/src/features/teamPanelState.ts`**

- 源码声明的类型、组件或调用边界：`TeamPanelState`, `TEAM_PANEL_STATE_KEY`, `TEAM_PANEL_STATE_EVENT`, `UseTeamPanelStateResult`, `loadTeamPanelState`, `saveTeamPanelState`, `notifyTeamPanelState`, `openTeamPanel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import type { TabType, TeamDetailTab } from '../components/teamArea/shared';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/teamPanelState.ts#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/teamTaskProgressBaseline.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d3c0d0ad19ed4dc0572a6b763698e47903dd1b2c9a9c58fb4268db013c85820 -->
**`jiuwenswarm/channels/web/frontend/src/features/teamTaskProgressBaseline.ts`**

- 源码声明的类型、组件或调用边界：`TaskProgressBaseline`, `createTaskProgressBaseline`, `registerConfirmedTaskCreation`, `mergeTaskProgressBaseline`, `getTasksForCurrentProgress`, `excludedTaskIds`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TeamTask } from '../stores/sessionStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/teamTaskProgressBaseline.ts#L1-L39)。
<!-- /kb:file -->
