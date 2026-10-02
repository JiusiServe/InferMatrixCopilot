---
title: "工具权限与安全治理：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py:L112-L123, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L71-L82]
feature: "permissions"
entry_points: ["jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py", "jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py"]
source_globs: ["jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py", "jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py", "jiuwenswarm/server/*"]
---

# 工具权限与安全治理：实现深读

[功能概览](feature-permissions.md) · [owner 入口](_index.md)

<!-- kb:depth feature=permissions facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=051be25e6dfcc70fa71f37b072fd9cb4e428f9a4d18af088bc58d3a22eb6428d -->
**checker 构造失败与 workspace 解析失败的传播**
SendFilePathGuardEvaluator.evaluate 中 build_file_guard_checker 抛出的任何异常都被捕获并转为 reason 为 send_file_path_guard_checker_failed 的不可评估结果（不向调用方抛出）；_sync_engine_workspace_root 在 resolver 抛 OSError/RuntimeError/TypeError/ValueError 时仅记 debug 日志并直接返回，不更新 engine 的 workspace 也不重建 file_guard。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py:L112–L123](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py#L112-L123), [jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L71–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L71-L82)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py","start":112,"end":123,"sha256":"d39dc5c964538e4825d757fa9dfed6f28a5ba0fde6cc49f3b46341a037b17cf0"},{"path":"jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py","start":71,"end":82,"sha256":"d6c39871e735335a6c78a8e8748c72922ded26dd89bae0759b6c96104ccb8692"}],"trace":[]} -->
<!-- /kb:depth -->
