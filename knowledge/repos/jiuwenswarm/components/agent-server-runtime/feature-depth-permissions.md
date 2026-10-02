---
title: "工具权限与安全治理：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py:L112-L123, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L71-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L158-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L180-L198, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L14-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L260-L271, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L24-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L272-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L290-L294, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L328-L346]
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

<!-- kb:depth feature=permissions facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7455f52d0a9f23094576b16191e9ff7fa372fdb05faba4b5eaca6b508f2426ff -->
**场景钩子裁决路径：仅当宿主暴露可调用 permission_scene_hook 时参与**
构造 PermissionSceneHookInput(ctx, tool_call, user_input=None, …) 后调用宿主钩子，可等待则 await；"approve" 映射 allow（reason=scene_hook_approved），"reject" 映射 deny（reason 默认 scene_hook_rejected），非元组或其余决策返回 None。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L158–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L158-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":207,"path":"jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py","sha256":"0d3f01c03b6645d734d7e8984574a7338456245c4270b8845c763113c5badb28","start":158}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=permissions facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a831dd64e19db8db8eccd2390ae50d8e1891343b4bc65f933df9b8c33b05e7e5 -->
**_persist_allow_always：回调存在且有活动 attempt 才返回其布尔值，其余分支返回 False 或转交 super()**
设置了 _exact_persist_callback 且 _EXACT_PERSIST_ATTEMPT.get() 非 None 时，标记 attempt.attempted=True 并返回 bool(callback(normalized_name, dict(tool_args), accesses))；无活动 attempt 或回调抛 Exception 返回 False；未设回调转交 super()._persist_allow_always。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L180–L198](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L180-L198)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":198,"path":"jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py","sha256":"f7db207f851c2ecaf689bbb931e83f1b452d65c68924f969cdf7182c496786ca","start":180}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=permissions facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ee6f6b1d88fb8cb69eb10d245082d7ff1510ede50ed7f1aa72a684ffb6b3a08 -->
**_evaluation_from_permission_result 对非 deny 级别在畸形 external_paths 上失败关闭为 ask**
external_paths 非 list 或条目数超过 _MAX_EXTERNAL_PATHS（64）时 _validated_external_paths 返回 None；此时非 deny 级别在该函数返回值中被改写为 ask，reason="malformed_policy_external_paths"、source="fail_closed"。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L24–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L24-L30), [jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L272–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L272-L281), [jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L290–L294](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L290-L294)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":30,"path":"jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py","sha256":"6165b4d0136c02b43563ebcc79e94e553268af430f7e629899140a929c22adbd","start":24},{"end":281,"path":"jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py","sha256":"d78b0f02a0a01f9e2944c489ce64c03023952e3a209e1c7822908291db80b365","start":272},{"end":294,"path":"jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py","sha256":"d1f95e100d042bdab1c21d69a252817ed191c74f233e1ac03fbfed2a808112cb","start":290}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=permissions facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3341183554d85ba56a690addcdc60aa53e2093a52b86cd18b6da9801bb280373 -->
**before_tool_call：无非权限恢复时委托 openjiuwen 基类 PermissionInterruptRail 并标记权限中断请求**
root_nonpermission_resume_from_context(ctx) 非 None 时 before_tool_call 直接返回；否则同步 workspace root 后 await super().before_tool_call(ctx)（基类来自 openjiuwen.harness.security 的 PermissionInterruptRail）；捕获 AbortError 且 cause.request 非 None 时调用 mark_permission_interrupt_request(ctx, request) 再原样 re-raise。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L14–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L14-L17), [jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L260–L271](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L260-L271)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":17,"path":"jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py","sha256":"e18df3cc553b54323805732543506aa0541289e12ed80af72e383f315dfc38ef","start":14},{"end":271,"path":"jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py","sha256":"1d7741276480476b17ca3966ba294145c7b77a4643488c765650f04e12dead80","start":260}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=permissions facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=416ecc00b784a6201deaad476ef227cfde93731ef621c59cef8d006f989b21a8 -->
**策略合并取最严候选：级别不弱于任一候选，但 reason 仅来自最严候选（推断）**
设计推断（非作者历史意图）：

_strictest_evaluation 在 L332–L334 过滤 None 候选后按 {ALLOW:0, ASK:1, DENY:2}、未知级别按 1 取最严候选；L344–L346 显示返回的 PolicyEvaluation 的 level 与 reason 均取自该候选。推断收益：在该优先级比较下合并级别不弱于任一候选；推断代价：较宽候选的去重匹配规则（L335–L340 收集）不会体现在返回的 reason 字段。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L328–L346](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L328-L346)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":346,"path":"jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py","sha256":"5c3b9b9d6d3c5ebe2b391bdee8b46fe6ba76c6e38fa9f2a59874471bd4cf2486","start":328}],"trace":[]} -->
<!-- /kb:depth -->
