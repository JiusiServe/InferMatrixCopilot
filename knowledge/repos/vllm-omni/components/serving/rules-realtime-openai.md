---
title: "OpenAI Realtime 请求与会话规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #7285"]
confidence: high
---

# OpenAI Realtime 请求与会话规则

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| `/v1/realtime`、duplex query、Qwen stages | SERV-RT-1a | `entrypoints/openai/api_server.py::realtime_endpoint` → `entrypoints/duplex/openai.py::dispatch_realtime_websocket` |
| PCM16、session.update、turn detection | SERV-RT-1b | `entrypoints/openai/realtime/connection.py` 的 audio-format validation、session update 与 input buffer |
| response.cancel、max_output_tokens、terminal event | SERV-RT-1c | `OpenAIFullDuplexConnection._run_response`、`ActiveResponse` |
| history memory、deferred truncate、tools | SERV-RT-1d | `realtime/session.py` 的 history insert/replace → `connection.py` 的 truncate/tool admission |

## SERV-RT-1a — Realtime route 必须保留已配置 native duplex 的优先级

- 触发：修改 `/v1/realtime` 的 query routing、模型 stage 判定或 connection factory。
- 强制：已配置 native duplex handler 时，无 duplex query 或显式 `1/true/on` 继续进入该
  engine-owned handler；显式启用 duplex 却未配置 handler 时返回 unsupported error。
  其余请求才进入 OpenAI dispatch：Qwen3-Omni 必须具有 thinker/talker/code2wav 三个 stage，
  stage config 同时支持 mapping/object；非空 model query 必须匹配 served name。
  OpenAI connection 的 buffered input/`response.create` 生命周期与 native continuous duplex
  各自维持自己的输入与 response ownership。
- 禁止：按模型名把所有 Qwen 请求强行改走 OpenAI connection；给非 Qwen fallback 塞入
  Qwen token timing；把 client-driven buffer 宣称为同一 generation 的持续音频输入。
- 验收：路由矩阵覆盖 configured/unconfigured handler、缺失/true/false query、完整/缺失
  Qwen stage、两类 config 和错误 model；分别检查 native 与 OpenAI protocol 的生命周期。
  不要求 OpenAI 标准客户端发送自定义 `playback.ack` 才能完成会话。^[PR #7285]

## SERV-RT-1b — 输入格式、部分 session 更新与 VAD 能力必须显式验证

- 触发：修改 Realtime PCM decode、`session.update`、turn detection 或 buffer admission。
- 强制：只接收当前实现支持的 24 kHz PCM16；base64、偶数字节及单次 append/总 buffer
  上限在 decode/写入前验证。部分更新使用 `exclude_unset` 后递归合并；显式 null 是更新，
  不能当作缺省值忽略。OpenAI connection 当前将 server/semantic VAD 归一为 disabled，
  native handler 的 VAD 行为由自己的配置决定。
- 禁止：把任何输入音频格式静默按 PCM16 解码；因字段未出现就清空旧配置；把保留的
  VAD 字段或 session.update acknowledgement 当作 server VAD 已实现。
- 验收：覆盖不支持的格式/采样率、坏 base64、奇数字节、append/total overflow、嵌套部分
  更新及显式 null；已有 configuration 不因无关字段更新而丢失。^[PR #7285]

## SERV-RT-1c — 每个 response 必须有一次且只有一次真实终态

- 触发：修改 response task 的初次 send、取消、异常路径、token limit 或 final events。
- 强制：用户取消即使发生在初始 output item 发送之前，也以 cancelled/client_cancelled
  收尾；terminal-event fence 防止重复终态。`max_tokens` finish 转成 incomplete、原因
  `max_output_tokens`；只有未完成且非正常取消的路径才发送 server error，并释放 active response。
- 禁止：finally 将已取消任务改成 failed；重复发送 response.done；把达到 token limit 当作
  completed 成功或丢弃未完成原因。
- 验收：阻塞首次 send 后取消、生成中取消、disconnect、正常完成、token-limit 和异常
  分别断言终态类型、次数与 active state 清理；测试取消时序而不依赖固定 sleep。^[PR #7285]

## SERV-RT-1d — history 写入与延迟 truncate 必须在模型之外保有界和 identity

- 触发：修改 conversation item insert/replace/delete、音频 truncate、history memory 或 tool admission。
- 强制：history insert/replace 候选在写入前检查 64 MiB 上限，不依赖下一次 response.create。
  当前 response 未产生完整 token IDs 时保存整个 truncate event，含 item/content_index；
  完成后按同一 item 应用，已删除 item 保持删除。invalid content_index 或超出音频长度的
  请求先拒绝再修改 history；ack 保持请求的 content_index。
  不支持的 MCP tools 在 session 配置过滤，在 response 入口明确拒绝，不执行隐藏 fallback。
- 禁止：history 无限制增长直到生成时才检查；延迟 truncate 丢失 content_index 或把已删除
  item 重新插入；把 shared history storage 绑定某模型的 token/ms 算法。
- 验收：仅持续插入而不生成也命中 memory cap；覆盖 truncate-before-final、删除后延迟
  回调、invalid index/end、连续 truncate 最新值及不支持 tools。Qwen prefix 对齐细节归
  [模型规则](../../models/qwen-omni/rules-realtime.md)。^[PR #7285]

共用 worker drain 与 session close 合同见 [session lifecycle](rules-session-lifecycle.md)；
公共路由装配见 [app assembly](rules-app-assembly.md)。
