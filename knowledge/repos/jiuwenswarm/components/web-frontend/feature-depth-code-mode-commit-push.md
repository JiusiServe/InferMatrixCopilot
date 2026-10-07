---
title: "提交/推送对话框（commit、push、commit_push）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L95-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts:L5-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L117-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L133-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L10-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L1-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L133-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L139-L150, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts:L29-L34]
feature: "code-mode-commit-push"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx"]
---

# 提交/推送对话框（commit、push、commit_push）：实现深读

[功能概览](feature-code-mode-commit-push.md) · [owner 入口](_index.md)

<!-- kb:depth feature=code-mode-commit-push facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6602157f88eb594496c8aa9e220027eb9842df8e40a818fa521ada04c6c4df26 -->
**打开对话框后按 Escape 关闭（非提交中且非建分支中）**
对话框 open 时注册 document keydown 回调：按 Escape 且不在 submitting/creatingBranch 时，若分支创建区已展开则先收起并清空 branchDraft，否则 setOpen(false) 关闭整个对话框。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L95–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L95-L108)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":108,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"b3a30ef34337238e207b9b3443c7c0f388b510f5001c6668f24a1d30ce110755","start":95}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-commit-push facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0508788ad94ab1c30084a96184396168c0e9b181d8bc9e898d7baf510261a00d -->
**createBranch 回调契约：成功后调用 onSuccess()，仅抑制其异步拒绝**
createBranch 守卫为 status、非空 trim 后分支名且未在 creatingBranch/submitting；成功路径调用 gitClient.createBranch(project.project_id, nextBranch)，随后同步调用 onSuccess()，其返回 promise 的拒绝被 .catch(() => undefined) 抑制；同步抛出的异常落入外层 catch 设为 error。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L133–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L133-L151), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L10–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L10-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":151,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"e66366e6ae3cb7c63eb97b17b082d5a03afe017d6b3490e3b0fd420f22776f23","start":133},{"end":18,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"4babf5909a0d28c45b29723b1f584fa7c510aa2c7480614a6132e34dda467543","start":10}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-commit-push facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=93f677092541bd4d9a9a7f6492e02b623a8bf9c032893064150764de23e59757 -->
**默认提交信息按 filesChanged 生成，远程名缺省回退 'origin'**
message 为空白时用 defaultCommitMessage(filesChanged)：≤0 为 'Update project files'，1 为 'Update 1 file'，否则 'Update N files'；remoteNames 在无远程分支名时返回 ['origin']。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts:L5–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts#L5-L13), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L117–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L117-L119)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts","sha256":"062a841e33af6c587bceac3af6930b6f0fa75803789ebc21a82bfe3ef3d6ba35","start":5},{"end":119,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"03a3ed789f4e50409ff8ca1b3a3724bf13f25a126128086b75038abf8cebcdbc","start":117}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-commit-push facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=70bc42971d7b7d149233225f04352434dc30c424d7fcb61c73d515d35275ede6 -->
**组件依赖 gitClient 与 gitPublishState 的具名导出**
组件从 './gitClient' 导入 gitClient，从 './gitPublishState' 导入 defaultCommitMessage、gitPublishErrorMessage、remoteNames 与类型 GitPublishOperation；createBranch 回调内部 await gitClient.createBranch(project.project_id, nextBranch)。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L1–L8](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L1-L8), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L133–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L133-L148)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"31aece4932155cfddb8f232700be3d2834fa8b6a997f4b9c2a4774580fda2938","start":1},{"end":148,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"93827c1c33007978c7b939988280c27c988fc7bffed41bfc7712d6ad05e36044","start":133}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-commit-push facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f91d830c3b294de3023a7614fd0412ce670e470d997b2594bc622d256e9a379 -->
**createBranch 被拒时：错误经 gitPublishErrorMessage 归一，分支面板保持打开**
若 gitClient.createBranch 抛出 nextError，catch 分支用 gitPublishErrorMessage(nextError, '创建分支失败，请重试。') 写入 error；因 setBranchCreateOpen(false) 仅在 await 成功后执行，新建分支面板保持打开，finally 将 creatingBranch 复位为 false。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx:L139–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx#L139-L150), [jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts:L29–L34](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts#L29-L34)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":150,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeCommitPushControl.tsx","sha256":"f323a9fa1c214ceeccca273ad0f362127eb0aa21b749d9efcbb7332360dcb7b7","start":139},{"end":34,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/gitPublishState.ts","sha256":"bebd3b6b8af7124f16c0bfcecd2c01cc4ccdff35a43ba0a5214a52b13119a530","start":29}],"trace":[]} -->
<!-- /kb:depth -->
