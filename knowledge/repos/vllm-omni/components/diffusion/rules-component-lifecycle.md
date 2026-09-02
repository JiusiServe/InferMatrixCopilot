---
title: "Diffusion component lifecycle 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5720", "PR #5853", "PR #5884", vllm_omni/diffusion/cache/base.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/cache/cachedit/runtime.py, vllm_omni/diffusion/lora/manager.py, vllm_omni/diffusion/models/interface.py, vllm_omni/diffusion/offloader/module_collector.py, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/sched/interface.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/cache/test_cache_dit_request_runtime.py, tests/diffusion/test_diffusion_scheduler.py]
confidence: high
---

# Diffusion component lifecycle 规则

本页承载共享 diffusion owner 的 multi-DiT component discovery 合同；模型专有 component 名和
residency 留在模型 owner。规则入口与其他共享机制仍见 [Diffusion 共享规则](rules.md)。

### DIFF-2f — 多 DiT pipeline 的 component list 是所有共享 lifecycle 的唯一集合

- 触发：pipeline 增加第二个 DiT、task-dependent transformer，或修改 `_dit_modules`。
- 强制：registry SP injection、loader strictness、Cache-DiT enable/refresh/summary、regional
  compile、LoRA、offloader/module collection 都遍历运行时实际存在的 `_dit_modules`；允许实例按
  task 收窄 list，不得由 class 默认预建不存在的组件。模型规则只补 task/权重选择与 residency。
- 禁止：硬编码 `transformer`/`transformer_2` 或把非 canonical attribute 静默漏掉；不能用
  第一个 DiT 成功推断第二个已启用 cache/compile/offload。
- 验收：用非 canonical 第二属性覆盖每个 consumer 的 enable/refresh/summary/discovery，并覆盖
  task 收窄后的缺省属性；至少一个真实双 DiT pipeline 逐 route 验证。^[PR #5720]

### DIFF-2g — dotted component path 必须跨 consumer 解析为稳定且唯一的 module identity

- 触发：`_dit_modules` 增加含点 path、alias，或 consumer 新增 discovery/getter/mutation。
- 强制：把名称视为逐段 attribute path；中间 attribute 缺失或最终值为 `None` 才算未实例化。
  discovery、enable、refresh、compile、SP、LoRA 与 offload 必须解析到同一 object；结果按 identity
  去重或明确禁止 alias，lifecycle 内不得悄悄替换已解析 target。
- 禁止：把含点字符串传给单层 `getattr`/`hasattr`；依赖 conventional direct alias 代替 canonical
  declaration；同一 object 因重复 path 被 enable 两次。目标 pin 只有 Cache-DiT 与 offloader 使用
  `attrgetter`，generic compile、registry SP 与 LoRA 仍未统一，因此不能宣称 cross-consumer parity。
- 验收：flat、dotted、missing-middle、`None`、非字符串、重复 alias 与 enable 后 identity replacement
  分别覆盖所有 consumer。当前 mock 只覆盖 Cache-DiT dotted enable/refresh/summary，没有真实
  cross-consumer identity 或异常覆盖。^[PR #5884]

### DIFF-2h — Cache-DiT summary 只汇报 active cached target

- 触发：修改 Cache-DiT summary、custom enabler、`BlockAdapter.is_cached` 或声明包含 uncached DiT。
- 强制：discovery 与 summary 使用同一 path 解析，但调用 `cache_dit.summary` 前按真实 active cache
  context 过滤；必须定义全部 discovered target 都 uncached 时的可观察结果。Cosmos3 等 pipeline
  可声明只执行一次而刻意不缓存的 nested DiT，声明存在不等于 cache 已启用。
- 禁止：对所有 declared DiT 无条件 summary；依赖 “no transformer” warning 判断 active cache。
  当前实现对 all-uncached 情况静默无 summary、也无 warning，调用方必须接受或另加显式信号。
- 验收：混合 cached/uncached、all-uncached、无 declared target 和 repeated summary 分别断言调用与
  日志。当前 mock 覆盖混合列表只汇报 cached outer target；没有真实 exception 或 teardown 证据。
  request-scoped runtime 已增加 disable，但 summary 测试没有覆盖 disable 后状态。^[PR #5884]

### DIFF-2i — request-scoped Cache-DiT 状态迁移必须保持唯一、可恢复的 ownership

- 触发：pipeline 接管 runner 启动的 Cache-DiT，或 request 字段选择 cache profile/reference path。
- 强制：只有实现 opt-in protocol 的 pipeline 才接管已 enabled backend；runner 转移 ownership 后
  清空自己的引用。每个 request 在 denoise 紧邻边界解析 desired spec：同 installation key 只 refresh，
  key 改变先 disable 旧 hooks 再 enable/refresh 新 profile，`None` disable 且 repeated `None` no-op；
  disable/enable 失败时必须保留尚未清理的 target 或 rollback 已安装 hooks，使下一次 transition 能恢复。
- 禁止：runner 与 pipeline 同时拥有同一 backend；按 config object equality 代替 stable installation
  key；enable 前覆盖既有 target list；第一个 disable exception 后忘记其余 target；在 cleanup 未完成时
  仅清 runtime key/reference 并宣称 disabled。非 opt-in 模型继续使用 runner-owned lifecycle，其他
  cache backend 不变。
- 验收：覆盖 startup adoption、omit→lossless→accelerated→omit、无 startup 的 accelerated→lossless、
  same-key repeated refresh、different-key reinstall、partial multi-target enable、每个位置的 disable
  exception、取消与 worker shutdown，并断言 policy prepare 严格先于 denoise。当前实现的正常迁移有
  fake backend 覆盖；但 enable 可留下未被 runtime 接管的部分 hooks，disable 在首个 exception 后仍在
  `finally` 丢弃全部 target/state，因此不能称为 failure-atomic，也没有真实 hook 的并发、rollback、取消
  或 shutdown 证据。^[PR #5853]

### DIFF-2j — process-wide request policy 必须参与 batch compatibility identity

- 触发：request 字段或模型 policy 会切换 worker-wide hook、adapter、compile/cache profile。
- 强制：所有会改变同批执行状态的 intent 必须进入 request-mode 与 step-mode compatibility key；保留
  omitted 与 explicit value 的原始区别，只有 exact key 相同的 request 才能 co-batch。若模型把其他
  request-local 字段纳入 installation key，则这些字段也必须进入 batch key，或由可执行检查保证该模型
  始终一次只处理一个 request。
- 禁止：在 batch 内按第一条 request 的 policy 切换 process-wide hooks；把 `None` 正规化成某个显式值；
  只更新 request scheduler 而漏掉 step scheduler。目标 pin 的 `quality` 已进入两套 key；H3 的 refresh
  hint 没进入 key，但 H3 `forward` 明确拒绝 `len(prompts) != 1`，不得把该例外推广到 batched adopter。
- 验收：两套 scheduler 都覆盖 same intent co-batch、accelerated/reference 分离、omitted/explicit 分离；
  每个新 policy input 用 mixed batch 证明 key 完整，或测试 single-request guard。^[PR #5853]
