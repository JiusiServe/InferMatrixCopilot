---
title: "进程式 CLI 频道（process_cli）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 进程式 CLI 频道（process_cli）

进程式 JiuwenSwarm CLI 频道：交互式 REPL 给每条命令启动一个独立的 Runtime worker 进程；另有两类入口，一类是面向机器的一次性执行（NDJSON 输出，可选双工应答/取消控制），另一类是只读查询。所有入口都通过进程内客户端调用共享的 Agent Runtime Public API。

**入口**

- `jiuwenswarm/channels/process_cli/main.py` — CLI 总入口：main() 与 build_parser()（中文 argparse），处理工作目录切换、stdio 转发和 Windows worker 的中断
- `jiuwenswarm/channels/process_cli/repl.py` — run_repl：交互式启动器，给每条命令拉起 worker 进程，并处理 /new、/resume、/branch、/delete 等斜杠命令
- `jiuwenswarm/channels/process_cli/app.py` — run/execute：单条命令在 worker 进程里的完整生命周期，包括会话创建/切换/分叉/删除、交互应答和事件消费
- `jiuwenswarm/channels/process_cli/machine_entry.py` — execute_source：机器模式的轻量启动入口，先设置好 stdout/cwd 再导入 Runtime，分文档输入和双工输入两种方式
- `jiuwenswarm/channels/process_cli/query_entry.py` — execute_query_source：只读查询的启动入口，先校验输入再导入 Runtime

**关键文件**

- `jiuwenswarm/channels/process_cli/client.py` — InProcessRuntimeClient：进程内调用共享 Runtime Public API 的客户端，负责会话准备/提交/回滚、流式调用、应答和取消
- `jiuwenswarm/channels/process_cli/protocol/model.py` — 一次性执行的值契约：OneShotRunInput、OneShotEvent、OneShotRunResult、AgentSpec、WorkspaceSpec 等
- `jiuwenswarm/channels/process_cli/protocol/jsonl.py` — 一次性执行记录的严格 NDJSON 编解码，并校验记录身份
- `jiuwenswarm/channels/process_cli/protocol/version.py` — 机器 schema 的版本标记和版本支持校验
- `jiuwenswarm/channels/process_cli/machine.py` — run_machine：通过共享 Runtime 执行一条机器请求，收集结果并清理资源
- `jiuwenswarm/channels/process_cli/machine_io.py` — 机器模式的有界单文档输入读取，以及 OneShotWriter 流式输出
- `jiuwenswarm/channels/process_cli/duplex_control.py` — DuplexController：把单条命令在 stdio 上收到的应答/取消控制路由过去；执行和审批仍由 Runtime 负责
- `jiuwenswarm/channels/process_cli/duplex_protocol.py` — 双工控制记录（answer/cancel）的严格解码，只携带关联 ID 和应答值
- `jiuwenswarm/channels/process_cli/duplex_input.py` — DuplexLineReader：可取消、有长度上限的 stdin 行读取，Windows 与 POSIX 走不同实现
- `jiuwenswarm/channels/process_cli/session_guard.py` — SessionLease：机器模式下同一个 Session 的跨进程所有权租约
- `jiuwenswarm/channels/process_cli/live_input.py` — LiveSessionInputController：TTY 实时补充输入（steer），以及投递回执的分类
- `jiuwenswarm/channels/process_cli/render.py` — EventRenderer：把 Runtime 事件流渲染成 human、JSON 或 JSONL 输出

**相关文档**

- `docs/zh/Quickstart.md` — 想了解用户怎样启动和使用 JiuwenSwarm 时读；本模块的机器协议字段以 protocol/ 下的源码为准
- `TESTING.md` — 为 CLI 改动补测试时参考；其中有过期路径，要先对照 tests/ 下现有的用例

**路由**

- `jiuwenswarm/channels/process_cli/`
