---
title: "代码模式分支选择器（初始化/切换/创建分支）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L36-L36, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L195-L204, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx:L4-L6, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx:L47-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L48-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L80-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L192-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L36-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L84-L97, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L262-L270, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L277-L285]
feature: "code-mode-branch-selector"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx", "jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx"]
---

# 代码模式分支选择器（初始化/切换/创建分支）：实现深读

[功能概览](feature-code-mode-branch-selector.md) · [owner 入口](_index.md)

<!-- kb:depth feature=code-mode-branch-selector facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bb923d771c989d5b17a2c2578f820c7be63b6f75efcb7f2cd452cd34fe14e74d -->
**挂载时加载状态；仅在 project 存在、work_mode='code' 且非默认项目时渲染**
组件挂载后 useEffect 调用 loadStatus()（依赖 [loadStatus]）；若 !project、project.work_mode !== 'code' 或 project.is_default 则整个组件返回 null。当目录不是 Git 仓库时渲染 data-variant='init' 的“初始化 Git”按钮，点击触发 initializeGit()，disabled 条件为 disabled || operating。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L80–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L80-L82), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L192–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L192-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":82,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"d0e62e5b47fc91240a15b2b3f6e86a9f6423a827969a16e3041bf321d21caa55","start":80},{"end":207,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"e0498530b1acb105564333841fba43607eddd4d3c4b1b9fcbdea309b6f5cba1d","start":192}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-branch-selector facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a1e7aa722d82ba9a5d21220845963f4384a9441c0e2381dca968e06f32cf5b8 -->
**props 契约：compact/disabled/variant/liveRepo 均有默认值**
签名 { project, compact = false, disabled = false, variant = 'default', liveRepo = null }。调用方 CodeEnvironmentPanel 传入 compact、variant="environment"、disabled={isProcessing}、liveRepo={diffWatch.summary?.repo ?? null}，即处理期间禁用、用 diffWatch 的仓库摘要实时同步分支状态。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L36–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L36-L37), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx:L47–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx#L47-L49)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":37,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"2d8010c5ea4a3276812cbba3e032e34a1c0533dfa0d45ca60aa76af10b389c10","start":36},{"end":49,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx","sha256":"3c56cbff5f0fee0fcc71c112496f07d2be9de2ffac4c18e3acd59a4a2a7e3ca1","start":47}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-branch-selector facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b316521d42c141641df83725281ab220bf8ad0d9d7a5c7361ffd0c35e51fcb39 -->
**默认 compact=false、disabled=false、variant='default'、liveRepo=null**
四个可选 prop 均有默认值；compact 追加 code-branch--compact 类，variant==='environment' 追加 code-branch--environment 类；disabled 与内部 operating 共同禁用初始化按钮。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L36–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L36-L36), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L195–L204](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L195-L204)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":36,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"0de2fb96dddce85e30155d27e6ed1fdf97f18bf37c4de38c6e5b5b4eeadd14ce","start":36},{"end":204,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"008364f0fbeeac5ac2432f6b1ae56b7e7c965071dab798439e2e163c6558e135","start":195}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-branch-selector facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df4aa6cfe6a2f01544baa1491d2f31c48eac1d9d6ecb105544366609369936f0 -->
**被 CodeEnvironmentPanel 组合：liveRepo 来自 diffWatch，uses useWorkspaceStore 的 loadProjects**
CodeEnvironmentPanel 从 './CodeBranchSelector' 导入并在分支行渲染它，liveRepo 取自 diffWatch.summary?.repo，disabled 取 isProcessing，因此选择器的实时仓库状态与 diff 监听耦合；组件自身还从 useWorkspaceStore 取 loadProjects。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx:L4–L6](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx#L4-L6), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx:L47–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx#L47-L49), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L48–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L48-L48)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":6,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx","sha256":"88194bad7a122cea0eb57d5f8f889437631129977d5c1290fcad4dfb4c50cde5","start":4},{"end":49,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeEnvironmentPanel.tsx","sha256":"3c56cbff5f0fee0fcc71c112496f07d2be9de2ffac4c18e3acd59a4a2a7e3ca1","start":47},{"end":48,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"defd13e840e97bcbd953b82524a8b4d9aac3440f9a432bcbdbbd1b35291428ce","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-branch-selector facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5887221f258233883342004f52c94e3c2fc651ce11316101115fe3c5ebe399b2 -->
**liveRepo 同步避免重新请求，但仅在已有 status 时合并**
设计推断（非作者历史意图）：

当 liveRepo 存在且 project.work_mode === 'code' 且非默认项目时，用 liveRepo 的 is_git/repo_root/branch/head/transient 覆盖本地 status.repo。收益：父面板的 diffWatch 摘要可直接驱动分支显示，无需再次 loadStatus；代价（推理）：若 previous 为 null（状态尚未加载成功），该 effect 不填充 status，初始状态仍依赖 loadStatus 的结果。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L84–L97](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L84-L97)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":97,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"d6997778d4396288d21cde11a3dad99a55c3ecbd172e04529e9a16c31462ac70","start":84}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=code-mode-branch-selector facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3dbb826f0ebffa81fa91d330532a90da57d236154b9cefd5b676b95ad69ef666 -->
**错误以可关闭的 alert 呈现；空仓库（isUnbornHead）时禁用创建分支按钮**
当 error 非空时，菜单内渲染 role='alert' 的错误块（含文案与关闭按钮，点击将 error 置为 null）；当 isUnbornHead 为真时，创建分支按钮因 branchWritesBlocked || isUnbornHead 被禁用，并显示提示“空仓库需要完成首次提交后才能创建其他分支”。

来源：[jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L262–L270](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L262-L270), [jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx:L277–L285](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx#L277-L285)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":270,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"acaf59f9fc8a001e46fa99fb2b171af61b3747942489ec35fd729dd4a6feb222","start":262},{"end":285,"path":"jiuwenswarm/channels/web/frontend/src/features/code-mode/CodeBranchSelector.tsx","sha256":"fbd52d8857b044318598d9a8d063676ddc544888c6d57d27348aac9b54ff6dd1","start":277}],"trace":[]} -->
<!-- /kb:depth -->
