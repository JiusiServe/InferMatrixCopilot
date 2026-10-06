---
title: "代码模式提交/推送对话框（CodeCommitPushControl）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L10-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L73-L74, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L139-L142, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L162-L174, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L46-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L79-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L119-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L356-L361, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L121-L131, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L278-L291, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L365-L388, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L198-L205, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L243-L247, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L374-L384, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L407-L420, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L181-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L95-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L228-L233, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L63-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L153-L180, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L133-L145]
feature: "code-mode-commit-push"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx"]
---

# 代码模式提交/推送对话框（CodeCommitPushControl）

<!-- kb:knowledge owner=feature-code-mode-commit-push facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**组件接口与依赖的后端调用**

`CodeCommitPushControl` 是一个 React 函数组件，props 包括 `project`、`branch`、`hasChanges`、`filesChanged`、`isGit`、`transient`、`isProcessing`、`variant`（`environment` 或 `review`，决定触发按钮样式）和成功回调 `onSuccess`。它不直接访问网络层，而是通过 `gitClient` 的 `status`、`commit`、`push`、`createBranch` 方法完成全部 Git 操作，从 `gitPublishState` 复用 `GitPublishOperation` 类型、`defaultCommitMessage`、`gitPublishErrorMessage` 与 `remoteNames`。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L10–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L10-L20), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L73–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L73-L74), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L139–L142](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L139-L142), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L162–L174](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L162-L174)

<!-- kb:knowledge owner=feature-code-mode-commit-push facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**表单默认值与交互选项**

可配置项均为对话框内表单状态：远程仓库名默认取 `remoteNames(...)[0]`；`includeUnstaged`（提交时是否 stageAll）默认 true；`setUpstream` 默认根据 `status.repo.upstream` 是否存在决定，选择非当前分支时自动置 true。提交信息留空时回退到 `defaultCommitMessage(filesChanged)` 生成的默认消息，输入框 `maxLength=200` 并显示计数；新分支名输入 `maxLength=255`。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L46–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L46-L51), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L79–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L79-L82), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L119–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L119-L119), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L356–L361](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L356-L361)

<!-- kb:knowledge owner=feature-code-mode-commit-push facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的操作与守卫条件**

支持三种操作：仅提交、提交并推送、仅推送；提交时可勾选包含未暂存更改（透传为 `stageAll`），推送时可勾选设置上游分支。对话框内可新建并检出分支（unborn HEAD 或仓库处于 transient Git 操作时禁用该入口）。触发按钮在 `isProcessing`、非 Git 仓库或 `transient` 时禁用，并以 `title` 说明原因；提交按钮要求操作含提交时工作区有改动、含推送时已选分支和非空远程。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L121–L131](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L121-L131), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L278–L291](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L278-L291), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L365–L388](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L365-L388)

<!-- kb:knowledge owner=feature-code-mode-commit-push facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**测试挂载点**

Inference / 设计推断（非作者历史意图）：

组件暴露了密集的 `data-testid` 钩子，覆盖触发按钮（`code-mode-publish-trigger`，带 `data-variant`）、对话框本身、加载态、分支选择/新建、远程选择、提交信息、三种操作单选（`code-mode-publish-operation` 带 `data-variant`）、选项复选框、错误区和提交按钮，以及成功 toast（`code-mode-publish-toast`）。这些命名稳定的选择器即为端到端/组件测试的入口；本次输入未包含对应测试文件，具体用例无法确认。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L198–L205](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L198-L205), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L243–L247](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L243-L247), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L374–L384](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L374-L384), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L407–L420](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L407-L420)

<!-- kb:knowledge owner=feature-code-mode-commit-push facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**两阶段提交的失败恢复与关闭守卫的不对称**

Inference / 设计推断（非作者历史意图）：

commit 与 push 在前端拆成两次串行请求而非单一后端操作：当 `commit_push` 中提交成功而推送失败时，组件保留已提交的 hash，仍触发 `onSuccess` 刷新，把操作切回 `push` 并显示「提交已成功（hash），但推送失败」的错误，让用户只需重试推送（推断：以多次往返换取部分失败的可恢复性）。关闭守卫存在不对称：Escape 处理在 `submitting` 或 `creatingBranch` 时阻止关闭（建分支面板打开时 Escape 仅收起该面板），但遮罩点击关闭只检查 `submitting`，因此 `creatingBranch` 期间仍可能通过点击遮罩关闭对话框。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L181–L189](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L181-L189), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L95–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L95-L108), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L228–L233](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L228-L233)

<!-- kb:knowledge owner=feature-code-mode-commit-push facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**组件职责与数据/控制流**

`CodeCommitPushControl` 是一个自管理打开状态的 React 展示组件：对话框的 `open` 由内部 `useState` 维护，外部只通过 props 传入 `project`、`branch`、`hasChanges`、`isGit`、`transient`、`isProcessing`、`variant` 等上下文和 `onSuccess` 回调，不接收打开/关闭控制。数据流为：打开时（`open` 变为 true 的 effect）调用 `gitClient.status(project.project_id)` 拉取仓库状态，并据此初始化分支、远程、`setUpstream` 与默认操作类型（脏工作区且非 detached HEAD 时为 `commit_push`，detached 时为 `commit`，干净时为 `push`）；提交时按所选操作条件执行——含提交则先 `gitClient.commit`（透传 `stageAll`），含推送则 `gitClient.push`（远程、分支、`setUpstream`），成功路径为先调用 `onSuccess`，再关闭对话框并设置 3 秒自动消失的成功 toast（通过 `createPortal` 挂到 `document.body`）。新建分支是独立子流程，调 `gitClient.createBranch` 后用返回的 `status`/`branch` 就地刷新表单状态。

Sources / 来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L10–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L10-L20), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L63–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L63-L82), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L153–L180](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L153-L180), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L133–L145](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L133-L145)

