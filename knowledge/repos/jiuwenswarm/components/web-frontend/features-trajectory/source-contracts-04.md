---
title: "features-trajectory 源码接口与集成边界 04"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-trajectory 源码接口与集成边界 04

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/search-index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b8753e19c4567676d7fbb0e423ed6205d0eee563028f3c0deef3c1acd4c89ca -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/search-index.ts`**

- 源码声明的类型、组件或调用边界：`SearchEntry`, `searchableJson`, `sameSources`, `markdownPreview`, `resultPreview`, `recordSources`, `blocks`, `TrajectorySearchIndex`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectoryTurnModel } from './model.ts'`；`import type { TrajectoryCellProps } from './record.ts'`；`import { trajectoryRecordId } from './record.ts'`；`import { trajectoryDisplayText, trajectoryPreviewText } from './preview.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/search-index.ts#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/timeline.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ef9ee79dfbac6fdb90ac6fb442681f4d6413d6c8d3042f5ee3c152aba52d64ae -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/timeline.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryTimelineMode`, `TrajectoryTimelineSegment`, `TrajectoryTimeRange`, `TrajectoryTimelineSpan`, `TrajectoryTimelineTurnBoundary`, `TrajectoryTimelineModel`, `clamp`, `boundedViewport`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectoryTurnModel } from './model.ts'`；`import { formatDurationMillis, liveElapsedSeconds } from './record.ts'`；`import type { TrajectoryCellKind, TrajectoryCellProps } from './record.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/timeline.ts#L1-L416)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/virtual-rows.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=09924a11fa0fea15d6cceb988227399a529b59ff3d1696b395d95d46c494ce7b -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/virtual-rows.ts`**

- 源码声明的类型、组件或调用边界：`CONTENT_ROW_HEIGHT`, `COLLAPSED_SUMMARY_HEIGHT`, `TERMINAL_BOUNDARY_HEIGHT`, `VirtualizableTrajectoryRecord`, `TrajectoryVirtualRowEntry`, `TrajectoryVirtualRow`, `trajectoryVirtualRecordKey`, `identity`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectoryCellProps } from './record.ts'`；`import { trajectoryRecordId } from './record.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/virtual-rows.ts#L1-L89)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryArchive.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8a5a34aaf3c5a2ffe9fed3e51c3d3b8659e7e6d16216532e9df37b078c56014 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryArchive.ts`**

- 源码声明的类型、组件或调用边界：`UnzipFile`, `TrajectoryRetentionCheckpoints`, `TrajectoryDetailRecord`, `TrajectoryRecordVersion`, `TrajectoryChainBucket`, `TRAJECTORY_ARCHIVE_FORMAT`, `TRAJECTORY_ARCHIVE_VERSION`, `TRAJECTORY_ARCHIVE_ENTRY_NAME`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Unzip, UnzipInflate, type UnzipFile } from 'fflate';`；`import type { WebConnectionState } from '../../types';`；`import { isTeamAgentMode } from '../planMode/wireMode';`；`import type { OtlpExportTraceServiceRequest } from './shared/otlp';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryArchive.ts#L1-L812)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryCheckpoints.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=675097bcaacd4d3a12ab558b40b85cde90bafa0889648f14d124d82daac1cb10 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryCheckpoints.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryV2SubjectSeed`, `SequenceCache`, `TRAJECTORY_CHECKPOINT_STATE_VERSION`, `TrajectoryRetentionCheckpoints`, `EMPTY_TRAJECTORY_CHECKPOINTS`, `SUBJECT_KINDS`, `object`, `count`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`；`import {`；`import type { OtlpExportTraceServiceRequest } from './shared/otlp';`；`import type { TrajectoryDetailRecord } from './trajectoryClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryCheckpoints.ts#L1-L259)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a3062b58808da74519115cf93e19c6c5bd3ce0e75830f2937087b8c51416ea3b -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryClient.ts`**

- 源码声明的类型、组件或调用边界：`TrajectorySubjectSummary`, `TrajectorySubjectListResponse`, `TrajectorySessionUsageItem`, `TrajectorySessionUsageResponse`, `TrajectoryDetailRecord`, `TrajectoryStreamFrame`, `TrajectoryStreamFramesResponse`, `TrajectorySubjectRecordsResponse`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { getApiBase } from '../../utils/env';`；`import type { OtlpExportTraceServiceRequest } from './shared/otlp';`；`import type { TrajectoryUsage } from './trajectory/model';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryClient.ts#L1-L615)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryFrames.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=353bdcd04c0bd50e5cd3b3e1c29c6dbb1af3801648805ff40072f67e486164e4 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryFrames.ts`**

- 源码声明的类型、组件或调用边界：`StreamingSpanText`, `StreamFrameState`, `emptyStreamFrameState`, `spanKey`, `blank`, `withFrame`, `next`, `callId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`；`import type { TrajectoryStreamFrame } from './trajectoryClient'`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryFrames.ts#L1-L233)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryLayout.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=24f45b1ce8e4d8c8d34acdac82694f5aeda2a8b223b336a292ed9abc91e43c49 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryLayout.ts`**

- 源码声明的类型、组件或调用边界：`RAW_INSPECTOR_DEFAULT_HEIGHT`, `RAW_INSPECTOR_MIN_HEIGHT`, `RAW_INSPECTOR_MAX_RATIO`, `RAW_INSPECTOR_KEYBOARD_STEP`, `RawInspectorHeightBounds`, `shouldInsetTrajectoryForFloatingTasks`, `trajectoryComposerClearance`, `rawInspectorHeightBounds`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryLayout.ts#L1-L90)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectorySequences.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=68314c70b8bb3381e5f44284dfd258cd9119684ffea17c2d71fbf2ce97c6c662 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectorySequences.ts`**

- 源码声明的类型、组件或调用边界：`SequenceCache`, `createSequenceCache`, `parseSequenceReference`, `parts`, `depth`, `absorbSequencePage`, `missingSequenceContent`, `missing`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectoryDetailRecord } from './trajectoryClient'`；`import type { OtlpExportTraceServiceRequest } from './shared/otlp'`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectorySequences.ts#L1-L239)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectorySubjects.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e4a9b0789893bb17b64f7a48344b67b2edb2721fc4074f20f399520cb4e72391 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectorySubjects.ts`**

- 源码声明的类型、组件或调用边界：`OtlpExportTraceServiceRequest`, `MAIN_TRAJECTORY_SUBJECT_ID`, `UNASSIGNED_TRAJECTORY_SUBJECT_ID`, `TrajectorySubjectKind`, `TrajectorySubject`, `TrajectorySubjectGroup`, `TrajectorySubjectGroups`, `TrajectoryRetiredSubject`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { OPENJIUWEN_ATTRIBUTES } from './semconv/constants';`；`import { stringAttribute, type OtlpExportTraceServiceRequest } from './shared/otlp';`；`import type { TrajectoryDetailRecord } from './trajectoryClient';`；`import { detailRecordIdentity, spansOf } from './trajectoryWindow';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectorySubjects.ts#L1-L435)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryTurnGaps.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e7a0d56e4200c5dec646f3e6a6bef21c7c734288addd969abbf4c9bef69dcbe9 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryTurnGaps.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryTurnRange`, `unrecordedTurnRanges`, `numbers`, `ranges`, `expected`, `turn`, `countTurns`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryTurnGaps.ts#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryWindow.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b3ade55994e4534895bb3d094a17b65497cecf3da5ac0659bf913172f298d291 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryWindow.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryChainBucket`, `TrajectoryRecordVersion`, `TrajectoryWindowState`, `SubjectRefreshWindow`, `TrajectoryOperationCoordinator`, `TrajectoryTraceHintCoordinator`, `StagedTrajectoryChain`, `TrajectoryContentMode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`；`import type { TrajectoryUsage } from './trajectory/model';`；`import type {`；`import { emptyStreamFrameState } from './trajectoryFrames';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectoryWindow.ts#L1-L495)。
<!-- /kb:file -->
