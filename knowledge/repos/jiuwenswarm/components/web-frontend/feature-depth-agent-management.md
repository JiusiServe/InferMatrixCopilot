---
title: "智能体资产管理与工作区浏览：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx:L984-L1004]
---

# 智能体资产管理与工作区浏览：实现深读

[功能概览](feature-agent-management.md) · [owner 入口](_index.md)

<!-- kb:depth feature=agent-management facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a5c7cff822162c94da260ea25e1827749ac503cbe2cc6da009b86a5687bb479 -->
**installDefinition 的结果契约**
client.installDefinition 返回带 kind 字段的结果：调用方 handleInstall 在 result.kind === 'auth_required' 时抛出 t('agentManagement.states.authRequired') 中止流程；当安装因连接器未就绪抛出 AgentInstallPendingError 时，错误对象携带 pendingConnectors 列表，面板据此把任务入队等待连接完成后重试。调用方义务是捕获该错误类型而非当作普通失败。

来源：[jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx:L984–L1004](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx#L984-L1004)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx","start":984,"end":1004,"sha256":"bc1189ecfb029ebdb2dfb5e83bb01d4b31de3378eed784486ff122f428b9c5cb"}],"trace":[]} -->
<!-- /kb:depth -->
