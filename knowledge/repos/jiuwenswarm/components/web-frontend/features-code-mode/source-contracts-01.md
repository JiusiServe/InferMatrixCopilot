---
title: "features-code-mode 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-code-mode 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec9eec2f749acdc4478e2863f6fff9043db19272e141acea87fb12edb3cfa0fc -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx`**

- 源码声明的类型、组件或调用边界：`CodeBranchSelectorProps`, `getErrorMessage`, `webError`, `CodeBranchSelector`, `rootRef`, `unbornHintId`, `loadProjects`, `closeMenu`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';`；`import { AlertCircle, Check, LoaderCircle, Plus, Search, X } from 'lucide-react';`；`import CodehubBranchIcon from '../../assets/code-mode/codehub-branch.svg?react';`；`import type { ProjectInfo, WebError } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L1-L338)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeChangesCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ede9da28dcafe42d139bc75cab997572bbf1d7ba9f788f90d1628bab99ae3259 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeChangesCard.tsx`**

- 源码声明的类型、组件或调用边界：`CodeChangesCardProps`, `CodeChangesCard`, `files`, `visibleFiles`, `reviewTarget`, `discarded`, `canChangeTurn`, `actionLabel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { ChevronDown, ChevronUp, LoaderCircle, RefreshCw } from 'lucide-react';`；`import { resolveFileIconType } from '../../components/FileIcon';`；`import folderIcon from '../../assets/file-icons/folder.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeChangesCard.tsx#L1-L106)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fcdab896c0b2e8cdd4cad21223657bd4a684afbdbf55c9a481cfc963c6c0f39f -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx`**

- 源码声明的类型、组件或调用边界：`GitPublishOperation`, `CodeCommitPushControlProps`, `operationIncludesCommit`, `operationIncludesPush`, `CodeCommitPushControl`, `timer`, `disposed`, `currentBranch`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { CheckCircle2, LoaderCircle, Plus, Upload, X } from 'lucide-react';`；`import type { ProjectInfo } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L1-L429)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d425e4364e7fe0446686ed84ea583e0766e1f6e4fbf3eeab4af41db9d27aa054 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx`**

- 源码声明的类型、组件或调用边界：`CodeEnvironmentPanelProps`, `CodeEnvironmentPanel`, `stats`, `loading`, `currentUnavailable`, `unavailable`, `repoIsParentOfProject`, `repoRoot`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { FileDiff } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import type { ProjectInfo } from '../../types';`；`import { CodeBranchSelector } from './CodeBranchSelector';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx#L1-L63)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeReviewPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed12f3f6abf1b5aade93af3b7267b28f61796b4f83ec3a9dcac48a1620ed21f4 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeReviewPanel.tsx`**

- 源码声明的类型、组件或调用边界：`DiffViewMode`, `DiffLineKind`, `RenderedDiffLine`, `FileTreeFile`, `FileTreeDirectory`, `FileTreeNode`, `MutableFileTreeDirectory`, `fileTreeCollator`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { Check, ChevronDown, ChevronRight, ChevronUp, FileCode2, Folder, LoaderCircle, Search } from`；`import CollapseAllIcon from '../../assets/collapse-all.svg?react';`；`import ExpandAllIcon from '../../assets/expand-all.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeReviewPanel.tsx#L1-L807)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/codeTurnChangeEvents.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9a477b71b6fa61fa0615d43826348f4877f556624dfa726ca3b82a141ba1f7f5 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/codeTurnChangeEvents.ts`**

- 源码声明的类型、组件或调用边界：`CodeTurnChangeEvent`, `CodeTurnChangeListener`, `listeners`, `emitCodeTurnChange`, `subscribeCodeTurnChange`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/codeTurnChangeEvents.ts#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/codeTurnDiffBinding.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e65c2e314a8c76b666c40917ba1db7be8b96ca778759e01f8350a12c4d4521e0 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/codeTurnDiffBinding.ts`**

- 源码声明的类型、组件或调用边界：`isUserFacingTeamEvent`, `jsonStr`, `payload`, `event`, `type`, `fromMember`, `toMember`, `isP2PToUser`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Message } from '../../types';`；`import type { GitTurnDiff } from './types';`；`import { latestModifiedTurn } from './turnChangeState.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/codeTurnDiffBinding.ts#L1-L159)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/gitClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2236c2f0d75ed5650b07862cc6444a8bb89f29e0cde191b90b12d93ec451af34 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/gitClient.ts`**

- 源码声明的类型、组件或调用边界：`gitClient`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../../services/webClient';`；`import type { GitCommitResult, GitPushResult, GitRepoStatus, GitTurnDiff, GitTurnDiffList, ProjectGi`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/gitClient.ts#L1-L103)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=507f66d3381ee7c00ceb9cc913a8213e0d2b2f537a5eb0ff1cdbfe29de15ffae -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts`**

- 源码声明的类型、组件或调用边界：`GitPublishOperation`, `defaultCommitMessage`, `remoteNames`, `names`, `ERROR_MESSAGES`, `gitPublishErrorMessage`, `webError`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WebError } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts#L1-L34)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/gitWatchClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=549f712cac7a2358e5cc5433c9df46e3403fa944b961f5ea342ac47071737718 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/gitWatchClient.ts`**

- 源码声明的类型、组件或调用边界：`EventHandler`, `StateHandler`, `PendingRequest`, `DEFAULT_TIMEOUT_MS`, `MAX_RECONNECT_DELAY_MS`, `buildGitWsUrl`, `configuredBase`, `protocol`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WebConnectionState, WebError, WsEvent, WsResponse } from '../../types';`；`import { getWsBase } from '../../utils/env';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/gitWatchClient.ts#L1-L219)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/turnChangeState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2c7b0f2b2c9667610cc8a04a2e9e61b333e283430bca8bccdfec112d668bdccd -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/turnChangeState.ts`**

- 源码声明的类型、组件或调用边界：`TurnChangeResultIdentity`, `turnDiffKey`, `hasFileChanges`, `latestModifiedTurn`, `latest`, `turn`, `updateTurnChangeStatus`, `matches`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WebError } from '../../types';`；`import type { GitTurnChangeAction, GitTurnDiff } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/turnChangeState.ts#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=60c74c252d3a2d5f1c5a5efca4ccea2de13827504ef62c8f36a3c34bf190ef25 -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/types.ts`**

- 源码声明的类型、组件或调用边界：`GitRepoStatus`, `GitDiffHunk`, `GitDiffFile`, `GitDiffSummary`, `GitDiffStats`, `GitTurnDiff`, `GitTurnDiffList`, `GitTurnChangeAction`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/types.ts#L1-L202)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/code-mode/useCodeGitDiffWatch.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7636864690e966b4d6843fe3d5b928431b807c1ef29592ac10db84264b05873e -->
**`jiuwenswarm/channels/web/frontend/src/features/code-mode/useCodeGitDiffWatch.ts`**

- 源码声明的类型、组件或调用边界：`UseCodeGitDiffWatchOptions`, `CodeGitDiffWatchController`, `errorMessage`, `eventPayload`, `revisionTimestamp`, `timestamp`, `acceptRevision`, `previous`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import type { WebConnectionState, WebError, WsEvent } from '../../types';`；`import { gitClient } from './gitClient';`；`import { gitWatchClient } from './gitWatchClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/useCodeGitDiffWatch.ts#L1-L399)。
<!-- /kb:file -->
