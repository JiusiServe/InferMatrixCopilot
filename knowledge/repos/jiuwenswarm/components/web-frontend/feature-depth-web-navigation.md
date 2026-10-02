---
title: "Web 页面与功能入口：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/App.tsx:L397-L397, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/App.tsx:L858-L870, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/App.tsx:L466-L482, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/App.tsx:L872-L876, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/App.tsx:L484-L501]
---

# Web 页面与功能入口：实现深读

[功能概览](feature-web-navigation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=web-navigation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b68f5066cb3705d6f22a187d4effc94ecbaec8734dbc0804d2320f10892cf9b -->
**jiuwen:nav 与设置模块导航事件的窗口事件契约**
外部代码可向 window 派发 CustomEvent('jiuwen:nav')，detail 为 MainNavKey 时监听器调用 setActiveNav 切换主导航；detail 为假值时被忽略。SETTINGS_MODULE_NAVIGATION_EVENT 的监听器则不做该判空：收到事件即把 detail 存入 requestedSettingsModuleId 并切到 'settings'，因此调用方必须提供合法的 SettingsModuleTarget。

来源：[jiuwenswarm/channels/web/frontend/src/App.tsx:L484–L501](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/App.tsx#L484-L501)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/App.tsx","start":484,"end":501,"sha256":"3256cb7140b286f9038c1e851c3c8c76dba675e2f7898b905d24940de237a76c"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-navigation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e4d99f606655e841148e7885c9b681d39df249c2389822a120320616ef50e707 -->
**导航项隐藏规则与默认入口**
activeNav 默认为 'chat'（useState 初始值）。hiddenNavItems 的取值顺序：先取 getHiddenNavItemsForPlatform(frontendPlatform) 作为基础，再按 rsiFeatureEnabled 追加 'experiments'、按 FEATURE_PERSONAL_CONTEXT_UI 追加 'personalContext'/'personalContextSettings'，masterEnabled 为 false 时仅隐藏 'personalContext'（保留设置页入口以便打开总开关）。

来源：[jiuwenswarm/channels/web/frontend/src/App.tsx:L397–L397](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/App.tsx#L397-L397), [jiuwenswarm/channels/web/frontend/src/App.tsx:L858–L870](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/App.tsx#L858-L870)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/App.tsx","start":397,"end":397,"sha256":"fed533d7b609e50405f6eb157c34f3ce6bd1f54dd648666e3ed97b7ff7f29547"},{"path":"jiuwenswarm/channels/web/frontend/src/App.tsx","start":858,"end":870,"sha256":"23a741dc67227a3c420cb3c7c3177517a9401dfdc1736d8f6b57c304e7307112"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-navigation facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3976d1b31016022103b7ac22bb43a95607d3e6dd936816e16a7eafd3c1bc348e -->
**功能关闭时的导航回退**
若 activeNav 停在被功能开关禁用的页面（如 FEATURE_APP_UPDATER_UI 为 false 时的 'updatepanel'、RSI 关闭时的 'experiments'、个人上下文总开关关闭时的 'personalContext'），effect 会把 activeNav 重置为 'chat'，避免渲染不可用入口。

来源：[jiuwenswarm/channels/web/frontend/src/App.tsx:L466–L482](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/App.tsx#L466-L482), [jiuwenswarm/channels/web/frontend/src/App.tsx:L872–L876](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/App.tsx#L872-L876)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/App.tsx","start":466,"end":482,"sha256":"e1928d6526465d80c4a061dae1d88eb3f689447e1a161dbb9a9996984414e563"},{"path":"jiuwenswarm/channels/web/frontend/src/App.tsx","start":872,"end":876,"sha256":"0840dfb6e0fbd39c211b6bd208ba0027102a602fe350dc79922646d6030abb58"}],"trace":[]} -->
<!-- /kb:depth -->
