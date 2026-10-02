---
title: 工具权限与安全治理 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/工具权限与安全防护.md
feature: "permissions"
entry_points: ["jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py", "jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py"]
source_globs: ["jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py", "jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py", "jiuwenswarm/server/*"]
---

# 工具权限与安全治理 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-permissions facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

权限系统综合工具名称、参数、工作区和策略决定 allow、ask 或 deny。频道与宿主会影响审批能力，客户端的确认界面与服务端策略判定需要同时查证。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L1–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L1-L274)；[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L1–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L1-L351)；[docs/zh/工具权限与安全防护.md:L1–L366](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%B7%A5%E5%85%B7%E6%9D%83%E9%99%90%E4%B8%8E%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4.md#L1-L366)。

<!-- kb:knowledge owner=feature-permissions facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `JiuwenSwarmPermissionInterruptRail [update_config, set_trusted_dirs, installed_permission_config, resolve_interrupt, before_tool_call]`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L1–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L1-L274)；[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L1–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L1-L351)；[docs/zh/工具权限与安全防护.md:L1–L366](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%B7%A5%E5%85%B7%E6%9D%83%E9%99%90%E4%B8%8E%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4.md#L1-L366)。

<!-- kb:knowledge owner=feature-permissions facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `permissions.file_guard.enabled`、`permissions.file_guard.defaults.read`、`permissions.file_guard.defaults.write`、`permissions.file_guard.defaults.exec`、`permissions.file_guard.workspace.read`、`permissions.file_guard.workspace.write`、`permissions.file_guard.workspace.exec`、`permissions.file_guard.paths`。这些是示例字段，不单独证明源码默认值或全部优先级。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L1–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L1-L274)；[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L1–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L1-L351)；[docs/zh/工具权限与安全防护.md:L1–L366](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%B7%A5%E5%85%B7%E6%9D%83%E9%99%90%E4%B8%8E%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4.md#L1-L366)。

<!-- kb:knowledge owner=feature-permissions facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：策略综合工具、参数、路径与持久审批决定 allow、ask、deny，提供比只按工具名配置更细的边界；代价是规则顺序和覆盖层必须明确。不能提供审批交互的频道可能将 ask 降为 deny，客户端按钮不是服务端权限判断的替代。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L1–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L1-L274)；[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L1–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L1-L351)；[docs/zh/工具权限与安全防护.md:L1–L366](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%B7%A5%E5%85%B7%E6%9D%83%E9%99%90%E4%B8%8E%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4.md#L1-L366)。

<!-- kb:knowledge owner=feature-permissions facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

权限系统综合工具名称、参数、工作区和策略决定 allow、ask 或 deny。频道与宿主会影响审批能力，客户端的确认界面与服务端策略判定需要同时查证。 联调时结合[Agent Loop 与 Rail 装配](feature-harness.md)、[Agent、Code 与 Team 模式](feature-modes.md)、[人类团队成员与人工协作](../agents-team/feature-human-team.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L1–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L1-L274)；[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L1–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L1-L351)；[docs/zh/工具权限与安全防护.md:L1–L366](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%B7%A5%E5%85%B7%E6%9D%83%E9%99%90%E4%B8%8E%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4.md#L1-L366)。

<!-- kb:knowledge owner=feature-permissions facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

用工作区内外路径、明确拒绝规则和持久审批分别验证策略结果；覆盖 normal 与 strict 及 action 与 severity 的优先级。再通过不同频道检查 ask 的交互、取消和降级，核对持久目录信任是否按预期生效。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py:L1–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_interrupt_rail.py#L1-L274)；[jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py:L1–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/policy_eval.py#L1-L351)；[docs/zh/工具权限与安全防护.md:L1–L366](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%B7%A5%E5%85%B7%E6%9D%83%E9%99%90%E4%B8%8E%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4.md#L1-L366)。
