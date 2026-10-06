---
title: 项目、会话与历史管理 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_lifecycle.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/项目与会话管理.md
feature: "projects-sessions"
entry_points: ["jiuwenswarm/runtime/session_catalog.py", "jiuwenswarm/runtime/session_lifecycle.py"]
source_globs: ["jiuwenswarm/runtime/session_catalog.py", "jiuwenswarm/runtime/session_lifecycle.py", "jiuwenswarm/runtime/session*.py", "jiuwenswarm/server/utils/diff_service.py", "jiuwenswarm/server/runtime/session/session_archive.py", "jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskGrouping.ts", "jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/useArchivedTaskLists.ts", "jiuwenswarm/common/cleanup.py", "jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts", "jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts", "jiuwenswarm/channels/browser/frontend/src/sidepanel/sidepanel.html", "jiuwenswarm/server/agent_ws_server.py", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InputArea.tsx", "jiuwenswarm/server/runtime/agent_adapter/interface.py", "jiuwenswarm/channels/web/frontend/src/multi-session/state/createConversationSession.ts", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ConversationSidebar.css", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ConversationSidebar.tsx", "jiuwenswarm/server/runtime/agent_adapter/session_message_input.py", "jiuwenswarm/server/control/history_service.py", "jiuwenswarm/server/control/health_service.py", "jiuwenswarm/server/control/methods.py", "jiuwenswarm/server/control/responses.py", "jiuwenswarm/server/control/project_service.py", "jiuwenswarm/server/control/repositories/project_repository.py", "jiuwenswarm/server/control/repositories/session_repository.py", "jiuwenswarm/server/control/session_service.py", "jiuwenswarm/channels/web/frontend/src/features/code-mode/gitClient.ts", "jiuwenswarm/gateway/app_gateway.py", "jiuwenswarm/common/utils.py", "jiuwenswarm/common/git_safe_directory.py", "jiuwenswarm/server/runtime/session/session_history.py", "jiuwenswarm/channels/web/frontend/src/components/AgentPanel/FileViewer.tsx", "jiuwenswarm/channels/web/frontend/src/features/historyRestore.ts", "jiuwenswarm/server/runtime/session/history_io.py", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageList.tsx", "jiuwenswarm/server/front/router.py", "jiuwenswarm/server/wire_truncate.py", "jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts", "jiuwenswarm/gateway/im_pipeline/im_session_input.py", "jiuwenswarm/server/runtime/session/session_metadata.py", "jiuwenswarm/agents/harness/common/session_ops_service.py", "jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationLifecycle.ts", "jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationPreviousSession.ts", "jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationProject.ts", "jiuwenswarm/server/runtime/offline_session_cleanup.py", "jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/channels/process_cli/app.py", "jiuwenswarm/channels/web/frontend/src/features/workspace/projectDirectoryPicker.ts", "jiuwenswarm/server/runtime/gateway_adapter/project_adapter.py", "jiuwenswarm/server/runtime/session/project_queries.py", "jiuwenswarm/channels/web/frontend/src/features/workspace/projectRegistryClient.ts", "jiuwenswarm/channels/web/frontend/src/features/workspace/projectTypes.ts", "jiuwenswarm/server/control/store/project_queries.py", "jiuwenswarm/server/runtime/session/project_store.py", "jiuwenswarm/common/projectless_workspace.py", "jiuwenswarm/runtime/session_provisioner.py", "jiuwenswarm/runtime/service.py", "jiuwenswarm/runtime/request.py", "jiuwenswarm/common/runtime_workspace.py", "jiuwenswarm/server/runtime/agent_adapter/sensitive_answers.py", "jiuwenswarm/channels/web/frontend/src/features/workspace/archivedTaskClient.ts", "jiuwenswarm/runtime/session/coordinator.py", "jiuwenswarm/runtime/session_delete.py", "jiuwenswarm/runtime/session/model.py", "jiuwenswarm/runtime/session/execution_registry.py", "jiuwenswarm/server/runtime/session/git_diff_status.py", "jiuwenswarm/server/runtime/gateway_adapter/session_adapter.py", "jiuwenswarm/channels/web/frontend/src/components/SessionsPanel/index.tsx", "jiuwenswarm/server/runtime/session/session_info.py", "jiuwenswarm/server/runtime/session/lifecycle.py", "jiuwenswarm/gateway/routing/session_map.py", "jiuwenswarm/server/runtime/session/model_selection_store.py", "jiuwenswarm/server/runtime/session/session_rename.py", "jiuwenswarm/server/runtime/agent_manager.py", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectArchiveDialog.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectArchiveModel.ts", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/useSidebarMenu.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectCreateMenu.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectCreateErrors.ts", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarActionMenu.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarMenuSchema.ts", "jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarModel.ts", "jiuwenswarm/server/runtime/agent_adapter/team_helpers.py", "jiuwenswarm/agents/harness/team/team_manager.py", "jiuwenswarm/channels/tui/frontend/src/app-state.ts", "jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/new.ts", "jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rename.ts", "jiuwenswarm/channels/tui/frontend/src/ui/app-screen.ts", "jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/resume.ts", "jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rewind.ts", "jiuwenswarm/gateway/channel_manager/tui/tui_connect.py", "jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sessions.ts", "jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/ArchivedTasksSettings.tsx", "jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/definition.ts", "jiuwenswarm/channels/web/frontend/src/features/historyPagination.ts", "jiuwenswarm/channels/web/frontend/src/App.tsx", "jiuwenswarm/channels/web/frontend/src/features/historyRecordReassembler.ts", "jiuwenswarm/gateway/channel_manager/web/lifecycle_handlers.py", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/dialogs/Dialogs.tsx", "jiuwenswarm/channels/web/frontend/src/multi-session/dialogs/dialogs.css", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/projectSelection.ts", "jiuwenswarm/channels/web/frontend/src/types/index.ts", "jiuwenswarm/channels/web/frontend/src/features/teamHistoryPanelRestore.ts", "jiuwenswarm/channels/web/frontend/src/stores/workspaceStore.ts", "jiuwenswarm/channels/browser/frontend/src/webview/chat.html", "jiuwenswarm/channels/web/frontend/src/features/workspace/workModeStorage.ts", "jiuwenswarm/common/work_mode.py"]
---

# 项目、会话与历史管理 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-projects-sessions facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

项目工作区与会话记录构成不同的数据边界。新建、恢复、切换和删除会话需要沿 Runtime 协调器确认对历史、执行和宿主状态的影响。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/runtime/session_catalog.py:L1–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L292)；[jiuwenswarm/runtime/session_lifecycle.py:L1–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_lifecycle.py#L1-L181)；[docs/zh/项目与会话管理.md:L1–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L1-L860)。

<!-- kb:knowledge owner=feature-projects-sessions facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `SessionCatalogError`；`SessionGetInput`；`SessionListInput`；`SessionSummary [to_dict]`；`SessionListResult [to_dict]`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/runtime/session_catalog.py:L1–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L292)；[jiuwenswarm/runtime/session_lifecycle.py:L1–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_lifecycle.py#L1-L181)；[docs/zh/项目与会话管理.md:L1–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L1-L860)。

<!-- kb:knowledge owner=feature-projects-sessions facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

该源码入口的构造或调用参数包括 `message`、`code`、`request`；它们是调用参数，不自动等同于全仓持久配置键。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/runtime/session_catalog.py:L1–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L292)；[jiuwenswarm/runtime/session_lifecycle.py:L1–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_lifecycle.py#L1-L181)；[docs/zh/项目与会话管理.md:L1–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L1-L860)。

<!-- kb:knowledge owner=feature-projects-sessions facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：项目归属使用 project_id，会话还受 work_mode 分类；这种组织便于按代码工程和办公任务分别管理，代价是列表、置顶、删除与 Git 视图都要保留一致的归属。会话生命周期操作不能只删除目录而忽略仍在运行的任务。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/runtime/session_catalog.py:L1–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L292)；[jiuwenswarm/runtime/session_lifecycle.py:L1–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_lifecycle.py#L1-L181)；[docs/zh/项目与会话管理.md:L1–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L1-L860)。

<!-- kb:knowledge owner=feature-projects-sessions facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

项目工作区与会话记录构成不同的数据边界。新建、恢复、切换和删除会话需要沿 Runtime 协调器确认对历史、执行和宿主状态的影响。 联调时结合[Agent、Code 与 Team 模式](../agent-server-runtime/feature-modes.md)、[Web 对话与流式状态](../web-frontend/feature-web-chat.md)、[Worktree 隔离工作](../agent-server-runtime/feature-worktree.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/runtime/session_catalog.py:L1–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L292)；[jiuwenswarm/runtime/session_lifecycle.py:L1–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_lifecycle.py#L1-L181)；[docs/zh/项目与会话管理.md:L1–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L1-L860)。

<!-- kb:knowledge owner=feature-projects-sessions facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

覆盖 session 和 project 的创建、重命名、置顶、列举与删除，核对响应身份和历史归属。Code 项目再验证 Git 状态、历史 diff 与撤销重做；运行中删除或切换会话时检查任务与订阅的收尾。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/runtime/session_catalog.py:L1–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L292)；[jiuwenswarm/runtime/session_lifecycle.py:L1–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_lifecycle.py#L1-L181)；[docs/zh/项目与会话管理.md:L1–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L1-L860)。
