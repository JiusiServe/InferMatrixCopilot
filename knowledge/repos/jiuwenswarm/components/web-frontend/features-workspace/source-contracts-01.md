---
title: "features-workspace 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-workspace 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b4724913bdcd65bacd39779a90de3173447d7d0e7d170227588460578d6e8932 -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskClient.ts`**

- 源码声明的类型、组件或调用边界：`ArchivedSession`, `ArchivedListResponse`, `ArchivedSessionListResponse`, `ArchiveWarning`, `ArchivedListParams`, `BatchSessionResultEntry`, `BatchSessionArchiveResponse`, `ArchiveRequest`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../../services/webClient';`；`import type { WorkMode } from './projectTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskClient.ts#L1-L186)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskGrouping.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1747e245f1c3973661ecb421af3e423ea8352e6001a71585704c50cf5cc50ebb -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskGrouping.ts`**

- 源码声明的类型、组件或调用边界：`ArchivedTaskGroup`, `UNASSIGNED_GROUP_KEY`, `buildArchivedTaskGroups`, `groups`, `groupByKey`, `ensureGroup`, `group`, `session`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskGrouping.ts#L1-L137)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/localFilePicker.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c1847313130511d796175b65b168afd3aeac593e4777804aa44047ad0a7038c -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/localFilePicker.ts`**

- 源码声明的类型、组件或调用边界：`LocalFilePick`, `LocalFilePickResult`, `DESKTOP_LOCAL_FILES_EVENT`, `DESKTOP_READY_EVENT`, `DESKTOP_FILE_DRAG_EVENT`, `DESKTOP_DIRECTORY_DROP_REJECTED_EVENT`, `DESKTOP_VIRTUAL_FILE_DROP_REJECTED_EVENT`, `DesktopLocalFilesEventDetail`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/localFilePicker.ts#L1-L415)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/projectDirectoryPicker.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=89489869be5c18ba062e864a8fcad19a8c7bcf48e8b69c01162104007b4f386e -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/projectDirectoryPicker.ts`**

- 源码声明的类型、组件或调用边界：`ProjectDirectoryPickResult`, `ProjectFilePickResult`, `SelectProjectFileOptions`, `DIRECTORY_PICKER_TIMEOUT_MS`, `FILE_PICKER_TIMEOUT_MS`, `getProjectDirectoryApi`, `getProjectFileApi`, `isProjectDirectoryPickerSupported`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/projectDirectoryPicker.ts#L1-L171)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/projectRegistryClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5572f96dd6c7aa29c408fe90e2973c29c164295c4d4bf88afc2c9c1bdce11d5a -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/projectRegistryClient.ts`**

- 源码声明的类型、组件或调用边界：`ProjectSessionBatchResult`, `ProjectRemoveResult`, `projectRegistryClient`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../../services/webClient';`；`import type { Session } from '../../types';`；`import type { ProjectInfo, WorkMode } from './projectTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/projectRegistryClient.ts#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/projectTypes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ff2f80d04106ebb6f7076a7394049044f34c0e3106a7289f1dd28e50f028ec8b -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/projectTypes.ts`**

- 源码声明的类型、组件或调用边界：`WorkMode`, `ProjectGitSnapshot`, `ProjectInfo`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/projectTypes.ts#L1-L29)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/workspace/workModeStorage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c796208c12a9e4912d5183ae699aa986bcd9197de9bc972c3556fd0d93276efe -->
**`jiuwenswarm/channels/web/frontend/src/features/workspace/workModeStorage.ts`**

- 源码声明的类型、组件或调用边界：`WORK_MODE_STORAGE_KEY`, `DEFAULT_WORK_MODE`, `readStoredWorkMode`, `persistWorkMode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WorkMode } from './projectTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/workspace/workModeStorage.ts#L1-L22)。
<!-- /kb:file -->
