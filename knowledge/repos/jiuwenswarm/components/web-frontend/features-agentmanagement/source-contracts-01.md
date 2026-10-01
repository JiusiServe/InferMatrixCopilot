---
title: "features-agentmanagement 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-agentmanagement 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/adapter.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=23fe0cfc0c27afae2a73604357b46eec68c458046b2c50c739ec3064a8354212 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/adapter.ts`**

- 源码声明的类型、组件或调用边界：`SupportedLocale`, `resolveLocalizedText`, `normalizeAgentSource`, `normalizeAgentGroupSource`, `normalizeAgentConnectionState`, `isPreviewableFile`, `lowerPath`, `normalizeCapability`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`；`import type {`；`import { normalizeEquipmentIdentity, normalizeEquipmentSource } from '../equipmentMarketplace';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/adapter.ts#L1-L272)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/groupClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8428f77d85b6db99c10263e3c83850255a3610bc5193d4bb8748b94648670da3 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/groupClient.ts`**

- 源码声明的类型、组件或调用边界：`AgentGroupListOptions`, `AgentGroupManagementClient`, `readErrorCode`, `current`, `depth`, `record`, `rethrowGroupError`, `webError`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../../services/webClient';`；`import { withCatalogCache } from '../catalogCache';`；`import { getAgentManagementLocale } from './locale';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/groupClient.ts#L1-L140)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/limits.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=943628252f710c344dbd18ae98cb8c2b6cece057a0a0703317b449c3c3c1c26f -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/limits.ts`**

- 源码声明的类型、组件或调用边界：`AGENT_NAME_MAX_LENGTH`, `AGENT_DESCRIPTION_MAX_LENGTH`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/limits.ts#L1-L2)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/locale.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=692c644995cedc65b1cdb907c88275621fe3d985b8dfa9e85541102f6c4d2f90 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/locale.ts`**

- 源码声明的类型、组件或调用边界：`getAgentManagementLocale`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import i18n from '../../i18n';`；`import type { SupportedLocale } from './adapter';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/locale.ts#L1-L6)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/pendingInstallQueue.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd6682f046aedb07a4ba9d6749330f50b31575bd15d3daa3e24f37c435c86881 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/pendingInstallQueue.ts`**

- 源码声明的类型、组件或调用边界：`PendingInstallMode`, `PendingInstallJob`, `PendingInstallQueue`, `createPendingInstallQueue`, `enqueuePendingInstall`, `advancePendingInstallQueue`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/pendingInstallQueue.ts#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/port.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4e566bc3b96d1777ee6487621a3eaa2df40e26237129be6a8ffc42fa8a2a60d -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/port.ts`**

- 源码声明的类型、组件或调用边界：`AgentInstallResult`, `AgentManagementError`, `AgentInstallPendingError`, `AgentCatalogListOptions`, `SkillListOptions`, `AgentManagementClient`, `AgentGroupListOptions`, `AgentGroupManagementClient`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CatalogCacheMetadata, CatalogItems } from '../catalogCache';`；`import type {`；`import { resolveAgentTagPayload } from './tagOptions';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/port.ts#L1-L205)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/presentation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b06af608bd814348da13dd612e05fb246ae55485f965beda46bf3b6bda683c7b -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/presentation.ts`**

- 源码声明的类型、组件或调用边界：`getAgentAvatarUrl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentCatalogItem } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/presentation.ts#L1-L5)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/raw.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed01bea997de5bb836aff96a3a970e25ba56b2b00fb4d3f99ce6f38c3367fcd7 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/raw.ts`**

- 源码声明的类型、组件或调用边界：`RawLocalizedText`, `RawAgentTemplateListItem`, `RawAgentCapability`, `RawAgentTag`, `RawAgentTemplateDetail`, `RawAgentGroupMember`, `RawAgentGroupCapabilities`, `RawAgentGroupListItem`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CatalogCacheMetadata } from '../catalogCache';`；`import type { AgentConnectionState } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/raw.ts#L1-L170)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/selection.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecefa375c4dab8eb8e46074fa9e61d49b14218b4dc5670a1c3ed959f6690f6a6 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/selection.ts`**

- 源码声明的类型、组件或调用边界：`SelectionSourceTab`, `LOCAL_SKILL_SOURCES`, `TEAM_MARKET_PLUGIN_TYPES`, `isTeamSkillOption`, `isMineSkillOption`, `isMarketplaceSkillOption`, `isSkillVisibleInSourceTab`, `SortableSelection`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentCatalogItem, McpOption, RequestStatus, SkillOption } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/selection.ts#L1-L112)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/state.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56847a8362e7dbb1c8d089d1524c356a4bf7af6a79668575aedc3d4a7c83c28e -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/state.ts`**

- 源码声明的类型、组件或调用边界：`AgentManagementState`, `createInitialAgentManagementState`, `initialAgentManagementState`, `AgentManagementAction`, `agentManagementReducer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/state.ts#L1-L151)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/tagOptions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=16341e7b53ba9edbb150d964bd2ae79e62ea1053c88dd6f67ddb2b45d5b57f1c -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/tagOptions.ts`**

- 源码声明的类型、组件或调用边界：`AGENT_TAG_OPTIONS`, `resolveAgentTagPayload`, `labels`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/tagOptions.ts#L1-L19)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=95fdf7e760c32975e91a3c51190ce884c2d43ed5b7646d6f6eec135c43378889 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/types.ts`**

- 源码声明的类型、组件或调用边界：`AgentSource`, `AgentConnectionState`, `AgentManagementSource`, `RequestStatus`, `AgentCatalogItem`, `AgentCapability`, `AgentDetail`, `AgentGroupSource`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/types.ts#L1-L179)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/upload.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c5a8cd8eb0b1dc2b87d9d1549f73db7d258d68392e9e9d091d446d084133671e -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/upload.ts`**

- 源码声明的类型、组件或调用边界：`AGENT_ARCHIVE_EXTENSIONS`, `AGENT_GROUP_ARCHIVE_EXTENSIONS`, `isAgentUploadFilename`, `lower`, `extractRpcErrorMessage`, `payload`, `apiError`, `mapLocalPackageImportError`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/upload.ts#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentManagement/viewModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ac318366566aa574ff302414217c395256ab5037d1f2488355adc47d3ce129c -->
**`jiuwenswarm/channels/web/frontend/src/features/agentManagement/viewModel.ts`**

- 源码声明的类型、组件或调用边界：`CatalogScope`, `CatalogViewModel`, `GroupCatalogScope`, `GroupCatalogViewModel`, `CATEGORY_ALIASES`, `matchesCategory`, `aliases`, `GROUP_CATEGORY_ALIASES`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentCatalogItem, AgentDetail, AgentGroupCatalogItem, AgentGroupDetail, DefinitionFile`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/viewModel.ts#L1-L187)。
<!-- /kb:file -->
