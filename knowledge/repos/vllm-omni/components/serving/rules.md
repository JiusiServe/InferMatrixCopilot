---
title: "Serving 规则"
created: 2026-07-20
updated: 2026-07-23
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #3576", "PR #4718", "PR #5157", "claude-workflow-starter-private@09dca46"]
confidence: high
---

# Serving 规则

只有 `SERV-数字字母` 是可审计规则 ID。

## SERV-1a — 所有可预判错误在第一个 streaming chunk 前返回

- 触发：SSE/streaming 接口新增 format、audio、output modality 或 extra-body 参数。
- 强制：在 streaming/non-streaming 分叉以及发送首个 chunk 前完成合同校验，非法请求
  返回结构化 4xx。
- 禁止：先发送文本成功 chunk，再在 audio/encoder 分支发现参数非法并静默结束；客户
  端会看到 HTTP 成功但缺失后半段输出。
- 验收：坏格式在两种模式都得到相同 4xx；测试证明坏请求没有产生任何 SSE chunk，
  合法请求仍按协议完成。 ^[PR #4718]

## SERV-1b — 支持格式、默认值和 backend capability 只有一个来源

- 触发：protocol enum、validator、encoder/backend 分别维护 format/default 列表。
- 强制：protocol、校验器和执行层引用同一 canonical 常量，并以实际 backend capability
  为上限。
- 禁止：把 backend 不支持的格式列为合法值，再靠中途 fallback；不同文件各复制列表。
- 验收：每个公开格式都有 encoder smoke；移除格式只改 canonical owner，协议和校验测试
  同步反映。 ^[PR #4718]

## SERV-2a — 指标节流和 gauge 按 scheduler/stage/replica owner 隔离

- 触发：orchestrator 聚合多 stage/replica stats，或新增全局 throttle/gauge。
- 强制：节流状态按实际 producer owner 隔离；request 状态 cleanup 后再计算 waiting 等
  gauge。
- 禁止：用一个全局时间戳让先上报的 replica 抑制其他 replica；在 pop/cleanup 前发布
  最终 gauge。
- 验收：同一窗口内两个 replica 都能上报；单请求完成并清理后 waiting=0。 ^[PR #3576]

## SERV-2b — collector 重建只保护本项目 family

- 触发：同进程重建 engine、注册 Prometheus collectors 或调整 unregister 行为。
- 强制：只保护需要跨实例保留的 `vllm:omni_*` family，并保留 upstream collector 的
  正常 unregister/cleanup。
- 禁止：把 upstream unregister 整体置空，导致重复 timeseries 注册。
- 验收：同进程连续创建/销毁两次 engine，无 duplicate-timeseries 错误且 Omni family
  仍可采集。 ^[PR #3576]

## 缓存 readiness 与失败隔离

### SERV-3a — readiness 必须表达 artifact 能力而非仅表达 identity

- 触发：serving 层按 URI/key 缓存预处理 artifact，并在后续请求剥离原始输入。
- 强制：readiness key 或 capability predicate 必须包含 consumer 真正需要的 mode/字段；
  只有 artifact 已具备全部必需字段时，才能进入 artifact-only 路径。
- 禁止：因为 `artifact_key` 相同就跨模式复用；原始输入已剥离后再让 worker 尝试补算
  缺失字段。
- 验收：覆盖“能力不足 artifact → 更强请求”与“能力超集 artifact → 较弱请求”，前者
  保留原始输入并重新计算，后者是否复用必须作为明确性能取舍。Qwen3-TTS 的方向性
  合同见 [Qwen3-TTS 规则](../../models/qwen3-tts/rules.md)。 ^[PR #5157]

### SERV-3b — readiness 状态迁移与错误存活性一起验证

- 触发：修改 artifact ready/track/mark/discard、失败清理或 eviction。
- 强制：所有状态入口使用同一 key/capability 合同；请求级 prompt/build 错误不得杀死
  engine，后续健康请求仍应成功。
- 禁止：只改 ready 查询而遗漏 mark/discard；只测同模式 cache hit，不测跨模式顺序和
  counterfactual failure。
- 验收：单测枚举状态迁移；E2E 复现原始坏顺序、证明修复后存活，并在回退修复代码时
  重新出现目标错误，避免测试空跑。 ^[PR #5157]

## 请求输入合同

### SERV-4a — 公开字段由 serving 显式拥有

- 触发：修改请求 allowlist、冲突字段集或兼容输入。
- 强制：逐项绑定真实 consumer，公开字段由 serving 边界显式声明。
- 禁止：从包含 tensor、KV 状态或运行时中间量的内部结构反射生成公开字段。
- 验收：加入一个内部同名字段反例，证明它不会被误算成公开 root 字段。

### SERV-4b — 多来源输入验证前不得合并

- 触发：请求同时支持 flattened、raw nested、声明字段、alias 或 canonical container。
- 强制：保留来源直到冲突检查结束；验证通过后若用字典展开构造并集，必须注明各映射
  已经不相交。
- 禁止：用 `or`、字典展开或 `update()` 决定重复值，制造未声明优先级。
- 验收：重复字段返回明确 4xx，不重叠字段全部到达最终 consumer。

### SERV-4c — 入口接受必须闭环到每个生产消费者

- 触发：新增请求字段或改变字段分流。
- 强制：对每条 dispatcher 追踪字段到 engine、pipeline、prompt 或 sampling 参数。
- 禁止：用 helper 返回值或 HTTP 成功代替传播证明。
- 验收：真实请求对象同时覆盖默认值和非默认值，并断言最终 consumer。

### SERV-4d — 同一请求合同错误跨 dispatcher 保持同一响应合同

- 触发：同一非法输入可进入 diffusion-only、multi-stage 或其他多个 dispatcher。
- 强制：使用一致的 status、错误类型和消息策略，并在公共边界转换一次。
- 禁止：一路本地映射为 4xx，另一路交给远处通用 `ValueError` 捕获。
- 验收：同一冲突输入经过每条受影响 dispatcher 时响应等价，且都在 engine/pipeline
  调用前失败。

### SERV-4e — 请求期弃用信号必须对 operator 可见

- 触发：serving 路径继续接收 deprecated 输入。
- 强制：使用项目 logger 的 `warning_once` 或明确限频策略。
- 禁止：使用仅写 stderr 且按调用点过滤的 `warnings.warn`。
- 验收：合法旧输入恰好记录一次警告；因冲突返回 4xx 的输入不记录兼容警告；用户响应
  合同与日志合同分别断言。

### SERV-4f — 一个请求合同只能在 serving 边界编译一次

- 触发：多个 dispatcher/stage 共享同类用户输入。
- 强制：由唯一 request-contract compiler 处理所有 raw ingress、默认值区分、alias、
  兼容字段、冲突验证和弃用事件，并产出规范化合同对象。
- 禁止：dispatcher 或 stage 再次读取 `request`、`model_extra`、`extra_body`，或自行决定
  冲突、HTTP 错误和弃用日志。
- 验收：每种支持的 dispatcher 运行同一组合法、冲突和 deprecated 输入，断言编译恰好
  一次、最终 consumer 一致、冲突响应一致、弃用日志至多一次且拒绝请求时不出现。

请求到 engine 的边界见 [Serving architecture](architecture.md)；公开协议通用检查见
[review contracts](../../../../general/review/guides/reviewer-lens-contracts.md)。
