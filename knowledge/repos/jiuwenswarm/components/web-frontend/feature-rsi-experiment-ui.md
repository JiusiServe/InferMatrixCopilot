---
title: "RSI 自我改进实验页（创建/列表/配置回显）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L247-L316, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py:L370-L398, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py:L400-L434, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts:L3-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L89-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx:L28-L65]
feature: "rsi-experiment-ui"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx", "jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetail.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiRail.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/rsiStore.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/types.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/styles/rsi.css", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiIntroduction.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/mockData.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/rsiPresentation.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiSelectedInfo.tsx", "jiuwenswarm/agents/harness/common/rsi/paper_provider.py", "jiuwenswarm/agents/harness/common/rsi/projector.py", "jiuwenswarm/channels/web/frontend/src/features/rsi/useRsiEvents.ts"]
---

# RSI 自我改进实验页（创建/列表/配置回显）

<!-- kb:knowledge owner=feature-rsi-experiment-ui facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**前后端契约：task.create / dataset.validate 与 Provider 适配接口**

前端创建实验走 rsiTaskCreate → rsiTrainingStart（启动）→ rsiTaskList（回查快照）的链路：字段按契约 §6.1 task.create 组装，HARNESS 分支带 input_file/model_refs.optimizer+tester/max_iterations/evaluation_method（'agent' 映射为 llm_as_judge），ARTIFACT 分支按 artifact_type 附加 optimization_instruction/artifact_path/web_proxy；启动或列表回查失败均被吞掉，不阻断创建反馈。后端 ArtifactEngineAdapter 暴露 run/resume/pause/terminate/read_state/read_report/get_tree/locate_artifact 作为 Provider 的公共入口，validate_input 将 Provider 结果归一为 RsiDatasetResult(valid, sample_count, errors)。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L247–L316](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx#L247-L316), [jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py:L370–L398](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py#L370-L398), [jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py:L400–L434](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py#L400-L434)

<!-- kb:knowledge owner=feature-rsi-experiment-ui facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**配置项：特性开关、表单默认值与配置回显**

RSI 特性开关 featureConfig.ts 默认启用（rsiFeatureEnabled = true），normalizeRSIEnabled 把非布尔值按字符串归一，仅 '0'/'false'/'no'/'off' 视为关闭，并通过 useSyncExternalStore 提供响应式读取。创建表单的默认值：scenario='HARNESS'、artifactType='PAPER'、evaluationMethod='agent'、maxIterations=2（切到 PROGRAM 时重置为 3 但不展示该字段），package_id 固定空串 DEFAULT_RSI_PACKAGE_ID；配置回显由 ConfigInfoDialog 只读展示 task.config 快照（模型、数据集、optimization_instruction、web_proxy 是否配置、artifact_path、max_iterations，按分支条件显示）。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts:L3–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts#L3-L33), [jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L89–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx#L89-L103), [jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx:L28–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx#L28-L65)

