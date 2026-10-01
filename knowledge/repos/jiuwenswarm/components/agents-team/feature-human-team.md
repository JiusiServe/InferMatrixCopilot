---
title: 人类团队成员与人工协作 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/AgentTeam人类成员联机协作.md
---

# 人类团队成员与人工协作 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-human-team facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

人类成员加入团队后参与消息与任务协作。成员身份、频道来源和团队会话关系需要同时保留，不能把普通聊天消息自动等同于团队指令。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/agents/harness/team/team_manager.py:L1–L3365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L1-L3365)；[docs/zh/AgentTeam人类成员联机协作.md:L1–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AgentTeam%E4%BA%BA%E7%B1%BB%E6%88%90%E5%91%98%E8%81%94%E6%9C%BA%E5%8D%8F%E4%BD%9C.md#L1-L129)。

<!-- kb:knowledge owner=feature-human-team facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `sync_team_observability()`；`shutdown_team_observability()`；`TeamRailMountContext`；`TeamManager [has_stream_task, pop_stream_task, begin_request, end_request, has_inflight_request]`；`is_team_session_running(session_id)`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/agents/harness/team/team_manager.py:L1–L3365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L1-L3365)；[docs/zh/AgentTeam人类成员联机协作.md:L1–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AgentTeam%E4%BA%BA%E7%B1%BB%E6%88%90%E5%91%98%E8%81%94%E6%9C%BA%E5%8D%8F%E4%BD%9C.md#L1-L129)。

<!-- kb:knowledge owner=feature-human-team facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游文档将 HITT 描述为默认开启，团队配置显式设置 enable_hitt=false 时禁用。Web 创建人类席位后，由支持频道的 join 指令绑定账号、团队 session 与席位；能收发普通聊天不表示已经加入该团队。

源码与文档：[jiuwenswarm/agents/harness/team/team_manager.py:L1–L3365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L1-L3365)；[docs/zh/AgentTeam人类成员联机协作.md:L1–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AgentTeam%E4%BA%BA%E7%B1%BB%E6%88%90%E5%91%98%E8%81%94%E6%9C%BA%E5%8D%8F%E4%BD%9C.md#L1-L129)。

<!-- kb:knowledge owner=feature-human-team facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：人类席位映射为团队 Agent，复用团队消息与任务体系；代价是人类账号、频道身份、席位和团队会话需要绑定。普通聊天、席位发言和显式团队指令有不同语义，人工输入的等待与成员退出也必须成为可观察的团队状态。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/agents/harness/team/team_manager.py:L1–L3365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L1-L3365)；[docs/zh/AgentTeam人类成员联机协作.md:L1–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AgentTeam%E4%BA%BA%E7%B1%BB%E6%88%90%E5%91%98%E8%81%94%E6%9C%BA%E5%8D%8F%E4%BD%9C.md#L1-L129)。

<!-- kb:knowledge owner=feature-human-team facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

人类成员加入团队后参与消息与任务协作。成员身份、频道来源和团队会话关系需要同时保留，不能把普通聊天消息自动等同于团队指令。 联调时结合[多智能体团队协作](feature-team.md)、[SwarmFlow 工作流与 HITL](feature-swarmflow.md)、[飞书 频道](../gateway-channels/feature-im-feishu.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/agents/harness/team/team_manager.py:L1–L3365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L1-L3365)；[docs/zh/AgentTeam人类成员联机协作.md:L1–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AgentTeam%E4%BA%BA%E7%B1%BB%E6%88%90%E5%91%98%E8%81%94%E6%9C%BA%E5%8D%8F%E4%BD%9C.md#L1-L129)。

<!-- kb:knowledge owner=feature-human-team facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

在 Web 创建包含人类席位的团队，从支持频道执行 join，验证席位身份与消息转交。覆盖普通发言、指令语法、任务完成、退出和禁用 HITT，检查错误会话或未加入用户不能驱动该席位。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/agents/harness/team/team_manager.py:L1–L3365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L1-L3365)；[docs/zh/AgentTeam人类成员联机协作.md:L1–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AgentTeam%E4%BA%BA%E7%B1%BB%E6%88%90%E5%91%98%E8%81%94%E6%9C%BA%E5%8D%8F%E4%BD%9C.md#L1-L129)。
