---
title: "Diffusion component lifecycle 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5720", "PR #5884", vllm_omni/diffusion/cache/base.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/lora/manager.py, vllm_omni/diffusion/offloader/module_collector.py, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, tests/diffusion/cache/test_cache_backends.py]
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
  目标 `CacheBackend` 只有 enable/refresh/is_enabled；future 若增加 shutdown/teardown，必须清理同一
  resolved target。^[PR #5884]
