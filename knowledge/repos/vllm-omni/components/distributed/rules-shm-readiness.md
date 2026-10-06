---
title: "SHM arrival readiness 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components]
sources: ["PR #8184"]
---

# SHM arrival readiness 规则

## DIST-WAKE-1a — FIFO wakeup 只能作为提示，正确性必须保留有界 polling

- 触发：修改 SharedMemoryConnector arrival wakeup、native receiver loop、send/receive work event 或 connector shutdown。
- 强制：launcher 为同一 deployment 的 SHM connectors 生成并序列化同一 wakeup_scope，接收者各持 UUID FIFO；put 后非阻塞广播目标 stage 的所有当前 FIFO，校验 FIFO 类型且不跟随 symlink。receive 在 poll 前取 generation、无 progress 后等新 generation，不能以已存在未来 chunk 的 key 作 readiness predicate。发送和接收分别用独立 event，shutdown 唤醒两者；graceful close 只删自己 FIFO，空目录才移除。wakeup 不可达/禁用/满 pipe 时保留 timed polling；poll ms 必须 finite/positive，否则 warning 后 5 ms，两个等待路径都用最终间隔。
- 禁止：按 EngineCore parent 分裂已声明的 deployment scope；缓存跨 receiver restart 的 writer；清理 peer FIFO；让 receive 清掉 send wakeup；把本机 FIFO 提示声称为 multi-node transport 或 hard-crash 自动回收保证。
- 验收：不同 parent、多个 replica/restart、hint-before-poll、blocked future chunk、满/缺失 FIFO、无效 poll interval 与 shutdown 并发分别覆盖；禁用 wakeup 仍交付同一数据且不忙等。 ^[PR #8184]
