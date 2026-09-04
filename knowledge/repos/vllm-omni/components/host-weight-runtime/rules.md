---
title: "Host Weight Runtime 规则"
created: 2026-08-23
updated: 2026-09-04
type: rule
tags: [vllm-omni, components]
sources: ["PR #6419", "PR #6427", "PR #6445", "PR #6486", "PR #6591", vllm_omni/host_weight_runtime/]
confidence: high
---

# Host Weight Runtime 规则

只有 `HWR-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| typed outcome、preferred/required、producer、timeout | `HWR-1a` | `runtime.py` → `outcomes.py`/`errors.py` → store/writer |
| lease/lock、fork、deny、cleanup、filesystem locality | `HWR-1b` | `lease.py` → `filesystem/{locks,store,writer}.py` |
| ordered producer、write-time digest、fsync/READY ordering | `HWR-1d` | `protocols.py` → `filesystem/writer.py` |
| plan/commit、manifest/schema、fallback model | `HWR-2a` | `protocols.py`/`manifest.py` → consumer restorer |

## HWR-1a — fallback 只消费显式 retryable typed outcome

- 触发：store mkdir/write/publish、producer、identity 或 timeout 路径变化。
- 强制：所有 `OSError` 转成 typed result 并清临时目录；preferred 只对明确 retryable 的 miss、
  lock/domain/capacity failure fallback，producer、identity、publication 和配置错误必须 fail startup。
  Timeout 只承诺实现能强制的 coordination/lock 范围。
- 禁止：preferred 泄漏裸异常或吞掉 semantic error；把同步 producer 描述成可取消的总时限。
- 验收：mkdir/writer failure、retryable miss、nonretryable producer/publication 和 lock timeout 逐项
  断言 terminal outcome、fallback 决策和临时目录清理。 ^[PR #6419]

## HWR-1b — lease 返回和本地 store 状态必须线性一致

- 触发：lease close、fork、deny/quarantine、cleanup 或 filesystem 检测变化。
- 强制：并发 `close()` 返回即代表 teardown/锁释放完成；fork child 只关闭继承 FD，不得解锁
  parent lease；打开 lease 后在共享锁内重查 deny；无 artifact 的孤儿 deny 自愈为 MISS。node-local
  backend 只接受明确 allowlist，并记录真实 filesystem type。
- 禁止：teardown 未完先返回；child 对继承 FD 执行 `LOCK_UN`；让 NFS/CIFS/Lustre/Ceph 或 unknown
  mount 静默满足 local backend。
- 验收：线程 close、fork、open-vs-deny race、orphan deny 和 remote/unknown filesystem 回归分别
  证明锁、状态和 typed result；cleanup 不移除活跃 mapping。 ^[PR #6419]

## HWR-1c — post-load publication 只温热未来启动

- 触发：canonical model 完成加载后需要通过 `POST_LOAD_ONLY` producer 显式温热缺失的 host artifact。
- 强制：调用同步 `publish_after_load()`，由 runtime 统一执行 store policy；`allow_post_load_publish` 与 pre-load 的 `allow_local_build` 独立控制；成功取得的 validated lease 必须在返回前关闭，并通过独立 publication report 反馈 `PUBLISHED`、`ALREADY_PRESENT` 或 `JOINED`。
- 禁止：让 `POST_LOAD_ONLY` producer 进入 pre-load `resolve()`；绕过 runtime 直接调用 store；恢复、rebind 或修改当前启动使用的 canonical model；让 post-load failure 改写已完成的 canonical-fallback resolution。
- 验收：验证 policy-disabled/runtime-disabled 不运行 producer，pre-load 不调用 post-load producer，成功 publication 关闭 lease 且后续 `resolve()` 命中；验证 publication failure、`JOINED`、unexpected store status 和 observer 回调均产生正确的独立 typed report。 ^[PR #6427]

## HWR-1d — publication 优化不得越过 digest 与 durability barrier

- 触发：producer 增加 `ordered` 声明，或修改 payload write、checksum、`fsync`、manifest/`READY`
  publication 顺序。
- 强制：只有按 canonical storage-key order 发出 payload 的 producer 才可声明 `ordered=True`，由 writer
  在写入时计算 file/tensor SHA256，并将已关闭 payload 的 `fsync` 与后续 producer work 重叠；未声明
  ordered 的 producer 必须保留并行 readback checksum。两条路径都须等待全部 payload digest 与
  `fsync` 完成后才能发布 manifest 和 `READY`。
- 禁止：用 write-time hash 跳过 durable completion；在 payload future 未完成时暴露 ready artifact；
  把 producer 顺序提示写进 artifact identity，或让 unordered output 复用 ordered fast path。
- 验收：覆盖 ordered write-time digest、unordered parallel readback、payload `fsync` failure、digest
  mismatch 与 publication barrier，断言失败不产生可命中的 `READY` artifact。^[PR #6591]

## HWR-2a — restore 是 validation-only plan 加一次性 commit

- 触发：manifest/schema、producer/restorer identity 或模型 hydration 变化。
- 强制：`plan_restore` 只校验且不变更 model/lease；`commit()->None` 是唯一一次性 mutation；
  producer、manifest 和 restorer schema/version 必须精确匹配。commit 开始后失败只能丢弃 model，
  fallback 必须新建实例。
- 禁止：planning 提前写权重；失败后复用半 hydration model；malformed safetensors 或未知
  post-load policy 当 cache miss。
- 验收：plan failure 保持原 model，commit failure 后 fresh model fallback；schema/version mismatch、
  malformed artifact 和 unsupported policy 均 fail-closed。 ^[PR #6419] ^[PR #6445]

## HWR-2b — cross-boundary lease handoff 必须是 process-local single-take

- 触发：consumer 把 restored lease 从 loader 交给 runner/backend，或修改 carrier serialization、
  startup cleanup、store publication hardening。
- 强制：commit 后用 carrier 保留唯一 loader-owned open lease；transport owner 在任何 async work
  前 `take()` 一次，随后只由 backend teardown/abort close。carrier 未被 take 时的 close 释放 lease，
  taken/closed carrier 拒绝再次 take，且不得可序列化。filesystem artifact 在 atomic rename 后再
  harden；harden failure quarantine artifact。
- 禁止：复制 lease、让 loader and backend 同时 close，或在 source directory immutable 前 rename；
  不能把 overlayfs-compatible publication 顺序改回 rename 前只读目录。
- 验收：验证 duplicate take、serialization、loader-side abort、backend-side teardown、enable failure
  cleanup 与 closed lease rejection；filesystem test 覆盖 writable staging → atomic rename → read-only
  artifact，以及 hardening failure quarantine。^[PR #6486]

## HWR-2c — registered mapping 的 ownership 必须晚于 CUDA、早于 lease close

- 触发：为 immutable HWR mmap 增加/修改 CUDA 或其他 platform host registration、direct H2D、
  registration budget 或 teardown。
- 强制：transport owner 对完整 page-aligned mapping 先做 capability/budget preflight，再原子地注册；
  partial failure 必须 reverse rollback。clean rollback 是 transport unavailable，不改变 HWR identity 或
  artifact outcome；rollback/unregister 留有 live range 则保留 registration 和 open lease 以便 retry，
  且跨 backend GC/fresh retry 仍保持强引用。正常 teardown 必须先停止使用这些 source、unregister every
  range，最后 close lease。
- 禁止：为 registered/staged transport 生成不同 artifact identity；budget/capability miss 后部分启用
  direct H2D；在 CUDA 仍注册时 close/finalize lease；将 clean registration failure 升级成 required-HWR
  artifact miss。
- 验收：覆盖 capability/budget gate、mid-registration rollback、PyTorch pinned-source verification、
  unregister retry 与 retained-owner GC，并断言 successful direct path 无 private staging allocation。^[PR #6591]
