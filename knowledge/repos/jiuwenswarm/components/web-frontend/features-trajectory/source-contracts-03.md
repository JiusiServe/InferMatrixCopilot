---
title: "features-trajectory 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-trajectory 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/attribute-resolver.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6ca49c7a1afe492e068842c91c0d7cac1145343e4d838813c400dbf22c199091 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/attribute-resolver.ts`**

- 源码声明的类型、组件或调用边界：`NormalizedTrajectoryAttributes`, `NormalizedTrajectoryStreamEvent`, `MutableNormalized`, `Resolved`, `NormalizedPart`, `NormalizedMessage`, `COMPATIBILITY`, `TRAJECTORY_KINDS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import {`；`import type { OtlpAttributeMap } from '../semconv/attributes.ts'`；`import type { OtlpAnyValue, OtlpKeyValue, OtlpSpanEvent } from '../shared/otlp.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/attribute-resolver.ts#L1-L848)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/otel-trajectory-projector.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=80a96803c4f2ad2bfa5936fc52d45fb0e8273cbe50e041a84446517dcd34a4f9 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/otel-trajectory-projector.ts`**

- 源码声明的类型、组件或调用边界：`ProjectedSpan`, `TrajectoryProjectionCheckpoint`, `TrajectoryLineageSeed`, `TrajectoryProjectionOptions`, `NO_UNRESOLVED_ATTRIBUTES`, `StructuredPart`, `StructuredMessage`, `MutableGroup`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import {`；`import {`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/otel-trajectory-projector.ts#L1-L2311)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/trajectory-v2-reducer.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6293be54166bcc5d2eef47eadac5f3bbeee1cd695807232502b2746ef0a34f33 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/trajectory-v2-reducer.ts`**

- 源码声明的类型、组件或调用边界：`ContextMessage`, `ContextDelta`, `ContextCommitPayload`, `HeldCompactionContext`, `ParsedEvent`, `TrajectoryV2EventProjection`, `TrajectoryV2SubjectProjection`, `TrajectoryV2Reduction`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { OPENJIUWEN_ATTRIBUTES, STANDARD_ATTRIBUTES } from '../semconv/constants.ts'`；`import { attributeMap } from '../shared/otlp.ts'`；`import type { OtlpExportTraceServiceRequest, OtlpKeyValue, OtlpSpan } from '../shared/otlp.ts'`；`import type { TrajectoryDiagnostic, TrajectoryPromptSnapshot } from '../trajectory/model.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/projector/trajectory-v2-reducer.ts#L1-L1610)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/attributes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8064a2910636ac38a42cd4632af9167810d132861680d561dc27388dc7b42d30 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/attributes.ts`**

- 源码声明的类型、组件或调用边界：`OtlpAttributeMap`, `exactAttributeMap`, `readStringAttribute`, `value`, `readBooleanAttribute`, `value`, `readInt64Attribute`, `value`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { OtlpAnyValue, OtlpKeyValue } from '../shared/otlp.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/attributes.ts#L1-L146)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/constants.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=212fd4c06a95f894c98a6b80eb064f833891084d50961ea6b1a854cc152c2b3a -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/constants.ts`**

- 源码声明的类型、组件或调用边界：`OTEL_SPEC_VERSION`, `OTLP_PROTO_VERSION`, `OTEL_SEMCONV_VERSION`, `STANDARD_ATTRIBUTES`, `OPENJIUWEN_ATTRIBUTES`, `OPENJIUWEN_EVENTS`, `STREAM_FRAME_KINDS`, `REQUEST_PURPOSES`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { GEN_AI_ATTRIBUTES } from './gen-ai-semconv.generated.ts'`；`import { OPENJIUWEN_SEMCONV } from './openjiuwen-semconv.generated.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/constants.ts#L1-L159)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/gen-ai-semconv.generated.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e8e6b0d266cb3555994733fb85c8af2363eed11f4bc729c0c6c9870f5d59ee46 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/gen-ai-semconv.generated.ts`**

- 源码声明的类型、组件或调用边界：`GEN_AI_SEMCONV_REVISION`, `GEN_AI_SEMCONV_SCHEMA_URL`, `GEN_AI_CORE_SEMCONV_SCHEMA_URL`, `GEN_AI_SEMCONV_ATTRIBUTE_COUNT`, `GEN_AI_ATTRIBUTES`, `GEN_AI_OPERATIONS`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/gen-ai-semconv.generated.ts#L1-L112)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/openjiuwen-semconv.generated.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d230b1dbed6167ccf64d0bafc8130d65855e0933c103c9ad2dd52049b4a7da9 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/openjiuwen-semconv.generated.ts`**

- 源码声明的类型、组件或调用边界：`TRAJECTORY_SPAN_SCHEMA_VERSION`, `SEQUENCE_REFERENCE_PREFIX`, `SEQUENCE_REFERENCE_VERSION`, `OPENJIUWEN_SEMCONV`, `TRAJECTORY_RECORD_KINDS`, `TRAJECTORY_EVENT_KINDS`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/semconv/openjiuwen-semconv.generated.ts#L1-L124)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/shared/otlp.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2d500e37ac4c8ac1400654b112981676073186638b353e003b805070be0a06f -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/shared/otlp.ts`**

- 源码声明的类型、组件或调用边界：`OtlpAnyValue`, `OtlpKeyValue`, `OtlpResource`, `OtlpInstrumentationScope`, `OtlpSpanEvent`, `OtlpSpanLink`, `OtlpStatus`, `OtlpSpan`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/shared/otlp.ts#L1-L142)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/teamTrajectoryLanes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9656c6ca0e5c85df97c27e6ff0ebe4412c2fcef2a60b7f6bc2e776644bdcb529 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/teamTrajectoryLanes.ts`**

- 源码声明的类型、组件或调用边界：`TeamMemberLaneStatus`, `TeamMemberLaneModel`, `laneStatusOf`, `hasRecords`, `hasRunning`, `hasError`, `lifecycle`, `buildTeamMemberLanes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectorySubjectGroup } from './trajectorySubjects';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/teamTrajectoryLanes.ts#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/theme/context.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=24457dc393d20213bd8dc6e399ca4052da6f76b2be78e7525e81b7bbf4b42f6a -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/theme/context.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `TrajectoryColorMode`, `TrajectoryColorModeContext`, `TrajectoryThemeProvider`, `useTrajectoryColorMode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createContext, type ReactNode, useContext } from 'react'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/theme/context.tsx#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/compaction.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d15caa7339e58cbcca693297ad2aff67194b2e282798c7616ab4270722a69e18 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/compaction.ts`**

- 源码声明的类型、组件或调用边界：`CompactionMetric`, `CompactionModifiedMessage`, `CompactionFacts`, `PHASE_TRIGGERS`, `record`, `nonEmptyString`, `finiteNumber`, `metric`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/compaction.ts#L1-L162)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/model.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a611e8d459ae34ef18f0d36f2ef04bc8d462011a8b1889feefd5deb9a5c7dbce -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/model.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryRequestConfig`, `TrajectoryRecordedFacts`, `TrajectoryToolSchema`, `TrajectorySystemMessage`, `TrajectoryPromptSnapshot`, `TrajectoryGroupModel`, `TrajectoryTurnModel`, `TrajectoryUsage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectoryCell } from './record.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/model.ts#L1-L151)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/preview.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b3230f00b42d81980b22c11ea016562446eb1e2f92bf8c210e5f84e375e40893 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/preview.ts`**

- 源码声明的类型、组件或调用边界：`PREVIEW_SOURCE_CHARACTERS`, `PREVIEW_OUTPUT_CHARACTERS`, `trajectoryPreviewText`, `source`, `compact`, `preview`, `trajectoryDisplayText`, `preview`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { extractMarkdownPlainText } from '../primitives/markdown/plain-text.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/preview.ts#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/record.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30187869ecb031f97acc0db8d412b1bed671fa7c15e573e9fd3650892c5b1dd6 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/record.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryCellKind`, `AssistantMetricDetail`, `TrajectorySourceBlock`, `TrajectoryCell`, `TrajectoryCellProps`, `trajectoryRecordId`, `formatDurationMillis`, `integer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TrajectoryPromptSnapshot } from './model.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/trajectory/record.ts#L1-L143)。
<!-- /kb:file -->
