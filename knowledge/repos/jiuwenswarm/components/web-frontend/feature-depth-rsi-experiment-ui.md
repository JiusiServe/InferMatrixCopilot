---
title: "RSI 自我改进实验页（创建/列表/配置回显）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L28-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L58-L76, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx:L39-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L105-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L50-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L78-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L89-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L114-L132]
feature: "rsi-experiment-ui"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx", "jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetail.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiRail.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/rsiStore.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/types.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/styles/rsi.css", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiIntroduction.tsx", "jiuwenswarm/channels/web/frontend/src/features/rsi/mockData.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/rsiPresentation.ts", "jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiSelectedInfo.tsx", "jiuwenswarm/agents/harness/common/rsi/paper_provider.py", "jiuwenswarm/agents/harness/common/rsi/projector.py", "jiuwenswarm/channels/web/frontend/src/features/rsi/useRsiEvents.ts"]
---

# RSI 自我改进实验页（创建/列表/配置回显）：实现深读

[功能概览](feature-rsi-experiment-ui.md) · [owner 入口](_index.md)

<!-- kb:depth feature=rsi-experiment-ui facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc1fa6baa583b90d96fd938b45a189788eaa45f1a14040adc09046950f33ae97 -->
**RsiPage 挂载时拉取列表并自动选中第一个实验**
RsiPage 挂载后调用 rsiStore 的 loadList 拉取实验列表；当列表加载完成、未选中且 list.length > 0 时通过 selectTask 选中 list[0].task_id，页面根据 selectedTaskId 是否存在切换 RsiRail+RsiDetail 或 RsiIntroduction 布局。

来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L28–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx#L28-L41), [jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L58–L76](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx#L58-L76)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":41,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx","sha256":"a3baa282d30fb915b89a07cbcf8dac203df2f2278a204084a7e6dde92177fd57","start":28},{"end":76,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx","sha256":"ec8ec49899c59fd9210c762accc6efaad04d718a93abe59b290f1c15e24b7c4d","start":58}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-experiment-ui facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f78823b14f8213a3f531f5f4519fe5e2fda19fa4ce0cc8c7e603eeeb4de31222 -->
**CreateExperimentDialog 的 props 契约为 { open, onClose, onCreated }，父组件用回调把新任务写入列表并选中**
CreateExperimentDialog 接收 open/onClose/onCreated 三个 props（CreateExperimentDialog.tsx:105）。RsiPage 以 createOpen 状态控制打开、onCreated 传 handleCreated：该回调对新建项调用 upsertListItem 后再 selectTask(item.task_id)，onClose 时将 createOpen 置回 false。

来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L105–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx#L105-L112), [jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L50–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx#L50-L56), [jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx:L78–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx#L78-L78)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":112,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx","sha256":"5c0168474b0af01705865569e6dc3247360eb451fc1db5585c51f23364f765b6","start":105},{"end":56,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx","sha256":"9ff7d38c20f236b7fda3821153cb4a9492c21cbe720a3c2f36cbf16923ef10c1","start":50},{"end":78,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx","sha256":"623afc2520d44efe06d92ce38b18619bbab13789ddc3499f34d1f7c78c572c9e","start":78}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-experiment-ui facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3bc945c8c785d08038619a907c98eff7b2e8b93eb6c35b7ed7ea71059c94f13 -->
**创建表单初始默认值：scenario='HARNESS'、artifactType='PAPER'、evaluationMethod='agent'、maxIterations=2**
useState(defaultForm) 以 defaultForm 作为惰性初始化器生成初始 FormState：name/optimizer/tester/datasetFile/optimizationInstruction/artifactPath/webProxy 均为空字符串，scenario 默认 HARNESS，maxIterations 默认 2。所示片段未显示对话框每次打开时重置表单的逻辑。

来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L89–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx#L89-L107)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":107,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx","sha256":"23fd72e377758f214f86c548c9c179900c6ba6d1d1a5ce0f8dc8b22058d2dbf1","start":89}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-experiment-ui facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1777a54ab4bc51f6660881f5275e46a5b549d0ee7bc02808ac89903374545a49 -->
**按分支守卫的表单校验：HARNESS 需数据集与 tester，PAPER 需指令或路径之一，PROGRAM 必须有路径**
useMemo 在每次表单字段变化时重算 validationErrors：name 与 optimizer 必填；branch==='HARNESS' 时 datasetFile、tester 必填；branch==='PAPER' 时 optimizationInstruction 与 artifactPath 至少其一；branch==='PROGRAM' 时 artifactPath 必填。有错误时 hasValidationErrors 为真（所示片段未包含提交按钮的禁用分支）。

来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx:L114–L132](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx#L114-L132)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":132,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx","sha256":"d5e59b96859337b07827e4c15cc907f8f954dadf75691ed874572ea9cbc6aea7","start":114}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-experiment-ui facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ff674cf2522a46b79f4de29c5324a94ccd21f7902b66d448abf0024c129d2dd1 -->
**配置回显按场景条件裁剪字段换取简洁，代价是信息受守卫限制**
设计推断（非作者历史意图）：

推断：ConfigInfoDialog 仅在对应守卫成立时展示字段（如 HARNESS 才显示 tester/input_file，isPaper 才显示 optimization_instruction 与 web_proxy 的已配置/未配置状态，isProgram 不显示 max_iterations），减少了无关字段，但用户在这些条件外看不到相应配置。

来源：[jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx:L39–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx#L39-L65)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":65,"path":"jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx","sha256":"2d080d45d29bdec3565e7f3048d5961b0a2508bd2d0586692f4116c5a5e4e44e","start":39}],"trace":[]} -->
<!-- /kb:depth -->
