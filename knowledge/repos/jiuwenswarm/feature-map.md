---
title: "JiuwenSwarm 功能、API、配置与设计取舍导航"
created: 2026-10-01
updated: 2026-10-01
type: guide
tags: [jiuwenswarm]
sources: []
---

# JiuwenSwarm 功能、API、配置与设计取舍导航

理解一项功能时，先沿下面的功能入口找职责、数据流与公共 API，再看实际配置、关联组件和设计取舍。源码事实采用现有知识页的固定基线 `f0a69728c96b`；设计取舍页把基于代码的推断明确标出，避免把分析写成作者历史决策。

本页只连接已有的唯一正文，不复制配置表或接口定义。审查必须执行的约束仍在各 owner 的规则页；知识用途也包括理解、配置、设计和排障。

| 功能或问题 | 架构与 API 入口 | 配置或数据契约 | 关联功能 | 设计取舍 |
|---|---|---|---|---|
| 启动、桌面与多实例 | [启动入口](components/launch/jiuwenswarm.md) | [实例配置与端口](components/launch/jiuwenswarm-instance-manager.md) | 共享配置、Runtime 生命周期 | [实例隔离与导入时机](components/launch/design-tradeoffs.md) |
| 命令行、机器执行与会话操作 | [进程式 CLI](components/gateway-channels/jiuwenswarm-channels-process-cli.md) | [机器协议与租约](components/gateway-channels/jiuwenswarm-process-cli-machine.md) | Runtime、交互与取消 | [本地调用与结果交付](components/gateway-channels/design-tradeoffs.md) |
| 模型选择、权限与 MCP | [共享配置](components/common-core/jiuwenswarm-common.md) | [模型目录与校验](components/common-core/jiuwenswarm-common-model-catalog.md) | 登录模型、Runtime、Cron | [缓存与运行时视图](components/common-core/design-tradeoffs.md) |
| 登录、凭据透传与续期 | [登录鉴权](components/login-auth/jiuwenswarm-common-auth.md) | [模型目录与凭据句柄](components/login-auth/jiuwenswarm-login-models.md) | 配置目录、请求身份、模型调用 | [并发续期与跨进程同步](components/login-auth/design-tradeoffs.md) |
| 扩展与应用插件 | [注册与加载](components/extensions-plugins/jiuwenswarm-extensions.md) | [应用绑定与前端贡献](components/extensions-plugins/jiuwenswarm-application-plugins.md) | 频道方法、共享加解密 | [元数据加载与插件启用](components/extensions-plugins/design-tradeoffs.md) |
| 轨迹采集、查看与保留 | [轨迹管线](components/observability/jiuwenswarm-observability.md) | [保留与查看器投影](components/observability/jiuwenswarm-trajectory-retention.md) | 执行事件、会话删除、前端查看 | [有界队列与最终结果](components/observability/design-tradeoffs.md) |
| Agent 执行、会话协调与控制输入 | [公共 Runtime](components/agent-runtime/jiuwenswarm-runtime.md) | [Session 协调器](components/agent-runtime/jiuwenswarm-runtime-session.md)、[交互与取消](components/agent-runtime/jiuwenswarm-runtime-control.md) | CLI、登录凭据、轨迹、调度 | [租约与异步交付](components/agent-runtime/design-tradeoffs.md) |
| 定时任务与跨后端调度 | [Cron 任务模型](components/cron-scheduling/jiuwenswarm-runtime-cron.md) | [文件与 etcd 后端](components/cron-scheduling/jiuwenswarm-cron-store.md) | Runtime、模型绑定、输出频道 | [本地持久化与 HA](components/cron-scheduling/design-tradeoffs.md) |
| 技能图谱、规划与经验演化 | [Symphony 集成](components/symphony-orchestration/jiuwenswarm-symphony.md) | [服务与候选安装](components/symphony-orchestration/jiuwenswarm-symphony-service.md)、[动态演化](components/symphony-orchestration/jiuwenswarm-symphony-evolution.md) | 技能、Runtime、配置、候选通知 | [图谱复用与安装复核](components/symphony-orchestration/design-tradeoffs.md) |

## 阅读时怎样判断证据

- API、参数默认值、优先级和已实现行为沿正文中的固定源码引用核对；表里的名称不是完整 HTTP 或 WebSocket API 清单。
- 设计推断解释收益、代价与限制；没有明确文档或注释时，不推断作者曾考虑或放弃过某个方案。
- 验证入口说明既有测试在哪里、覆盖什么行为。静态知识不能单独证明测试已运行、真实 OAuth/模型端点可用或某个性能结论。
- owner 间的关系用于继续查证，不意味着一个组件继承另一个组件的规则或配置。

仓库入口见 [JiuwenSwarm 知识索引](_index.md)，稳定代码边界见 [组件索引](components/_index.md)，全仓协议和服务概览见 [architecture](architecture.md)。

## 功能覆盖清单

以下清单把第一方客户端、SDK、沙箱与独立频道纳入功能范围。功能入口覆盖基础职责、接口、配置、关联能力、取舍和验证方法；不是完整字段手册或测试通过声明。对应机器清单由 adapter 的 knowledge-coverage.yaml 维护，功能清单综合固定基线的 README、文档导航、Harness 索引与客户端能力目录，并逐项核对源码入口；代码中尚未实现的流程在对应知识页标明。新增能力应先更新该清单，再重新审计。

| 功能 | 知识入口 |
|---|---|
| 初始化与服务启动 | [职责、接口与配置](components/launch/feature-bootstrap.md) |
| 单机多实例 | [职责、接口与配置](components/launch/feature-instances.md) |
| 桌面宿主与自动更新 | [职责、接口与配置](components/launch/feature-desktop.md) |
| 打包与部署 | [职责、接口与配置](components/packaging-deploy/feature-deployment.md) |
| 机器执行与本地 CLI | [职责、接口与配置](components/gateway-channels/feature-process-cli.md) |
| 交互式命令行 | [职责、接口与配置](components/gateway-channels/feature-cli.md) |
| TUI 对话与命令 | [职责、接口与配置](components/tui-client/feature-tui.md) |
| Web 对话与流式状态 | [职责、接口与配置](components/web-frontend/feature-web-chat.md) |
| Web 页面与功能入口 | [职责、接口与配置](components/web-frontend/feature-web-navigation.md) |
| 项目、会话与历史管理 | [职责、接口与配置](components/agent-runtime/feature-projects-sessions.md) |
| Agent、Code 与 Team 模式 | [职责、接口与配置](components/agent-server-runtime/feature-modes.md) |
| 多智能体团队协作 | [职责、接口与配置](components/agents-team/feature-team.md) |
| 跨进程分布式 Team | [职责、接口与配置](components/agents-team/feature-distributed-team.md) |
| 人类团队成员与人工协作 | [职责、接口与配置](components/agents-team/feature-human-team.md) |
| SwarmFlow 工作流与 HITL | [职责、接口与配置](components/agents-team/feature-swarmflow.md) |
| Agent Loop 与 Rail 装配 | [职责、接口与配置](components/agent-server-runtime/feature-harness.md) |
| 任务规划与 Todo | [职责、接口与配置](components/agents-team/feature-planning.md) |
| 子代理派发与验证 | [职责、接口与配置](components/agents-team/feature-subagents.md) |
| 技能安装、挂载与发现 | [职责、接口与配置](components/agents-team/feature-skills.md) |
| 团队技能与能力复用 | [职责、接口与配置](components/agents-team/feature-swarm-skills.md) |
| Skill Hub 与市场流通 | [职责、接口与配置](components/agents-team/feature-skill-hub.md) |
| Skill 自演进 | [职责、接口与配置](components/agent-server-runtime/feature-skill-evolution.md) |
| Symphony 检索与图谱编排 | [职责、接口与配置](components/symphony-orchestration/feature-symphony.md) |
| Auto Harness 评测优化 | [职责、接口与配置](components/auto-harness/feature-auto-harness.md) |
| Harness Package 与热激活 | [职责、接口与配置](components/auto-harness/feature-rsi-packages.md) |
| FACT/TIP 双轨经验 | [职责、接口与配置](components/agent-server-runtime/feature-ttse.md) |
| 长期记忆 | [职责、接口与配置](components/agents-team/feature-memory.md) |
| 对话后自动记忆 | [职责、接口与配置](components/agents-team/feature-auto-memory.md) |
| Code 模式编码记忆 | [职责、接口与配置](components/agent-server-runtime/feature-coding-memory.md) |
| 任务经验检索与沉淀 | [职责、接口与配置](components/agents-team/feature-task-memory.md) |
| 上下文压缩与卸载 | [职责、接口与配置](components/agent-server-runtime/feature-context.md) |
| 工具权限与安全治理 | [职责、接口与配置](components/agent-server-runtime/feature-permissions.md) |
| 生命周期 Hooks 与扩展 | [职责、接口与配置](components/extensions-plugins/feature-hooks.md) |
| Application Plugin 与前端贡献 | [职责、接口与配置](components/extensions-plugins/feature-applications.md) |
| 音视频双工扩展 | [职责、接口与配置](components/extensions-plugins/feature-video-duplex.md) |
| E2A 统一请求响应协议 | [职责、接口与配置](components/protocols/feature-e2a.md) |
| A2A 接入与 AgentCard | [职责、接口与配置](components/protocols/feature-a2a.md) |
| ACP 与 stdio 桥接 | [职责、接口与配置](components/protocols/feature-acp.md) |
| SSH 频道与远程终端 | [职责、接口与配置](components/gateway-channels/feature-ssh.md) |
| A2UI 生成式界面 | [职责、接口与配置](components/a2ui/feature-a2ui.md) |
| 浏览器服务与网页工具 | [职责、接口与配置](components/agents-team/feature-browser-tools.md) |
| Chromium 浏览器扩展 | [职责、接口与配置](components/browser-client/feature-browser-client.md) |
| VS Code 客户端 | [职责、接口与配置](components/ide-clients/feature-vscode.md) |
| JetBrains 客户端 | [职责、接口与配置](components/ide-clients/feature-jetbrains.md) |
| Python 与 TypeScript SDK | [职责、接口与配置](components/sdk-clients/feature-sdk.md) |
| JiuwenBox 隔离执行 | [职责、接口与配置](components/sandbox-runtime/feature-sandbox.md) |
| 模型平台与 API 配置 | [职责、接口与配置](components/common-core/feature-models.md) |
| MCP 配置、凭据与资源 | [职责、接口与配置](components/common-core/feature-mcp.md) |
| 账号登录与凭据续期 | [职责、接口与配置](components/login-auth/feature-login.md) |
| 定时任务与调度存储 | [职责、接口与配置](components/cron-scheduling/feature-cron.md) |
| 执行轨迹与保留 | [职责、接口与配置](components/observability/feature-observability.md) |
| Debug Dump 与 OTel | [职责、接口与配置](components/observability/feature-debug-trace.md) |
| 多模态理解与媒体配置 | [职责、接口与配置](components/agents-team/feature-multimodal.md) |
| LSP 代码智能 | [职责、接口与配置](components/agent-server-runtime/feature-lsp.md) |
| Worktree 隔离工作 | [职责、接口与配置](components/agent-server-runtime/feature-worktree.md) |
| 已有 PR 自动修复 | [职责、接口与配置](components/tui-client/feature-autofix.md) |
| 飞书 频道 | [职责、接口与配置](components/gateway-channels/feature-im-feishu.md) |
| 微信 频道 | [职责、接口与配置](components/gateway-channels/feature-im-wechat.md) |
| 企业微信 频道 | [职责、接口与配置](components/gateway-channels/feature-im-wecom.md) |
| 钉钉 频道 | [职责、接口与配置](components/gateway-channels/feature-im-dingtalk.md) |
| 小艺 频道 | [职责、接口与配置](components/gateway-channels/feature-im-xiaoyi.md) |
| Slack 频道 | [职责、接口与配置](components/gateway-channels/feature-im-slack.md) |
| Telegram 频道 | [职责、接口与配置](components/gateway-channels/feature-im-telegram.md) |
| Discord 频道 | [职责、接口与配置](components/gateway-channels/feature-im-discord.md) |
| WhatsApp 频道 | [职责、接口与配置](components/gateway-channels/feature-im-whatsapp.md) |
| 智能体资产管理与工作区浏览 | [职责、接口与配置](components/web-frontend/feature-agent-management.md) |
| JiuwenMemory 进程内 SDK 接入 | [职责、接口与配置](components/agents-team/feature-jiuwen-memory-sdk.md) |
| 图片生成与产物落盘 | [职责、接口与配置](components/agents-team/feature-image-generation.md) |
| JiuwenBox 推理隐私代理 | [职责、接口与配置](components/sandbox-runtime/feature-sandbox-privacy-proxy.md) |
| 群聊数字分身与 owner 权限 | [职责、接口与配置](components/agents-team/feature-digital-avatar.md) |
| 连接器市场与 MCP 授权流程 | [职责、接口与配置](components/web-frontend/feature-connectors.md) |
| 外部 Claude 与 Codex CLI 智能体 | [职责、接口与配置](components/common-core/feature-external-cli-agents.md) |
| 持续目标与会话控制 | [职责、接口与配置](components/web-frontend/feature-goal-mode.md) |
| 计划模式与多入口切换限制 | [职责、接口与配置](components/web-frontend/feature-plan-mode.md) |
| 绑定会话的心跳续跑任务 | [职责、接口与配置](components/agent-server-runtime/feature-heartbeat.md) |
| 会话产物列表、预览与下载 | [职责、接口与配置](components/web-frontend/feature-artifacts.md) |
| 语音输入、回复朗读与停止 | [职责、接口与配置](components/web-frontend/feature-speech-interaction.md) |
| SkillDev 创建、评测与打包边界 | [职责、接口与配置](components/agent-server-runtime/feature-skill-development.md) |
| 主动推荐、频率限制与主 Agent 交付 | [职责、接口与配置](components/agent-server-runtime/feature-proactive-recommendation.md) |
