---
title: "共享 Agent 运行时（jiuwenswarm/runtime/service.py AgentRuntime）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L3-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L296-L328, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L791-L829, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L613-L659, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:.doc_project_maintainer/modules/runtime-session/README.md:L19-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L296-L305, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L881-L939, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L941-L976, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L1762-L1839, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L307-L346, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L486-L518, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L204-L262, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L547-L601]
---

# 共享 Agent 运行时（jiuwenswarm/runtime/service.py AgentRuntime）

<!-- kb:knowledge owner=agent-runtime facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**传输无关的 Runtime 生命周期所有者**

AgentRuntime 是共享 Agent 运行时的生命周期所有者：它持有唯一的 AgentManager、PlanModeController、RuntimeSessionProvisioner 和 RuntimeSessionCoordinator，模块文档明确声明它不承载任何传输关注点——AgentServer 与进程式 CLI 各自拥有一份实例并调用其公共操作，WebSocket 帧仍留在 AgentServer。类文档还规定它是 one-shot 的：close 之后不可再次 start，未终态的 PreparedSessionProvision 会在 close 前被拒绝，避免 finalizer 运行在已拆除的 Runtime 上。

Sources / 来源：[jiuwenswarm/runtime/service.py:L3–L8](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L3-L8), [jiuwenswarm/runtime/service.py:L296–L328](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L296-L328)

<!-- kb:knowledge owner=agent-runtime facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**跨会话消息与能力目录**

send_session_message 从持久化元数据解析源/目标会话，要求目标有 channel、属同一 user（否则 PermissionError）、且为 Work/Code Normal 模式，未加载的目标会幂等恢复注册，然后以 SESSION_MESSAGE 工作类型异步排队并返回执行快照——文档说明其异步性是为了避免两会话互等模型执行而死锁。Runtime 还提供模型/模式目录（list/resolve_model_capability、list/resolve_mode_capability）、权限快照与本地 MCP 名称校验，均要求已 start。

Sources / 来源：[jiuwenswarm/runtime/service.py:L791–L829](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L791-L829), [jiuwenswarm/runtime/service.py:L613–L659](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L613-L659), [.doc_project_maintainer/modules/runtime-session/README.md:L19–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/modules/runtime-session/README.md#L19-L22)

<!-- kb:knowledge owner=agent-runtime facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**公共入口：预置事务与执行路由**

AgentRuntime 是一次性生命周期拥有者：进程式 CLI 每条命令一份、AgentServer 服务生命期一份；close 后不可重启，close 拒绝尚未 commit/abort 的预置事务。prepare_session_create/switch/fork 在 lifecycle 锁内只做计数与 started 检查，真正的 provisioner 调用在锁外执行，prepared 对象在 finally 中加入 _pending_session_provisions；commit_session_provision 仅当结果是 SessionCreateResult 或 SessionSwitchResult 且模式为单 Agent（Work/Code Normal）时才注册会话，fork 结果不注册。执行入口 invoke/stream 先用 session_work_kind 分类：CONTROL_INPUT 走 _deliver_control，SESSION_INPUT 走 stream_session_input，其余有 work kind 的走协调器 run_unary/run_stream，没有 work kind 的请求绕过协调器直接执行。

Sources / 来源：[jiuwenswarm/runtime/service.py:L296–L305](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L296-L305), [jiuwenswarm/runtime/service.py:L881–L939](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L881-L939), [jiuwenswarm/runtime/service.py:L941–L976](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L941-L976), [jiuwenswarm/runtime/service.py:L1762–L1839](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L1762-L1839)

<!-- kb:knowledge owner=agent-runtime facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**构造参数决定进程依赖与扩展的归属**

构造注入决定进程级依赖管理：initializer 为 None 时（默认）_manage_runner 与 _initialize_extensions 均为 True，start() 会获取进程全局 checkpointer/Runner 并初始化扩展；传入自定义 initializer 则只调用该 initializer，不再管理 Runner 与扩展。扩展获取分两种情形：当前不存在 ExtensionRegistry 实例时创建 registry 与 ExtensionManager 并 load_all_extensions（不含传输扩展）；若 AgentServer/Gateway 已预加载 registry，则仅借用该实例并返回 False，不参与其生命周期、也不加载扩展。模型目录方面，get_default_models 抛错时抛 ModelCatalogError("model catalog is unavailable", code="MODEL_CATALOG_UNAVAILABLE", retryable=True)；条目无法通过 build_model_from_entry 构造时按原位跳过，避免目录选择静默落到 Adapter 默认模型。

Sources / 来源：[jiuwenswarm/runtime/service.py:L307–L346](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L307-L346), [jiuwenswarm/runtime/service.py:L486–L518](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L486-L518), [jiuwenswarm/runtime/service.py:L204–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L204-L262), [jiuwenswarm/runtime/service.py:L547–L601](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L547-L601)

