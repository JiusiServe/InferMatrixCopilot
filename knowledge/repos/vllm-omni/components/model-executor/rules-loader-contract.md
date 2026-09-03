---
title: "loader 合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #4730", "PR #4765", "PR #4958", "PR #5777", "PR #5824", vllm_omni/model_executor/model_loader/]
confidence: high
---

# loader 合同

`loader-contract` 审查组的 `EXEC-2a`–`EXEC-2c`：dtype 与 config 获取、fused shard 完整性、多模块 checkpoint 载入。触发条件与其余审查组见 [model-executor 共享规则](rules.md) 的 Direct 代码快速入口。

## EXEC-2a — loader 的 dtype 与 config 获取必须显式、最小化

- 触发：模型 loader 构造 text encoder、VAE、transformer 或只读取 checkpoint config。
- 强制：所有子模块显式接收目标 dtype；读取单个 config 使用精确文件/metadata 获取路径。
- 禁止：为读取 `config.json` 同步下载整套权重；依赖默认 fp32 后再靠下游 cast 修补。
- 验收：mock 下载层证明只请求目标 config，loader 测试断言各子模块 dtype；真实 smoke
  记录峰值显存和 dtype。Krea 2 的具体约束见
  [Krea 2 规则](../../models/krea2/rules.md)。 ^[PR #4730]

## EXEC-2b — fused shard 必须按 source 完整性与布局数值闭环

> H3 text encoder 当前有 fused QKV 与 gate/up owner；Qwen3 code predictor 仍使用分离
> projection，其 PR #4958 fusion 已由 PR #5777 回退，不能把 H3 现状外推给 Qwen。

- 触发：准备合并 q/k/v、gate/up 等 projection，修改 HF shard 映射、wrapper/talker
  loader、packed projection TP plan 或平台 override。
- 强制：weight 与可选 bias 都按 forward split 的同一顺序数值拼装；部分 shard 和
  整组 shard 缺失都硬失败。bookkeeping 必须按 source shard id；expected 集合从实际 fused
  owner 预置，才能捕获零 shard，不能以任一 source 命中的 target name 代表完整。所有声明
  同一 fused module 的 consumer 必须委托给共享 loader，wrapper 并恢复 returned loaded-name
  的模型前缀；平台 override 同步使用新
  fused 属性与共享 split helper。
- 禁止：不得用逐 tensor `default_weight_loader` 绕过 fused assembler；不得只记录 skipped
  shard 后让随机初始参数继续；不得只用 shape 或 returned-name 断言顺序正确。GQA
  下错误偏移仍可形状合法。plain packed `nn.Linear` 不得声明泛化 colwise TP；
  未有 TP-aware packing/loading/split 与 TP=2 测试时，TP plan 保持空。
- 验收：数值比较 fused 参数与 `cat([q,k,v])`/`cat([gate,up])`，覆盖 bias、
  部分/整组缺 shard、每个 consumer 的委托和前缀；以非等 q/KV width 证明 split 能识别
  GQA 错序。平台测试或静态 guard 证明不再引用已删除的 projection 属性。H3 eager text
  encoder 还须对任何未加载 plain retained parameter 在启动时硬失败；unknown checkpoint key
  可继续告警，因为它不会留下 model parameter 未初始化。^[PR #4958] ^[PR #5777] ^[PR #5824]

## EXEC-2c — 多模块 checkpoint 载入必须按配置块与参数集闭环

- 触发：模型 checkpoint 将主干 LM 与 DiT、patch encoder、vocoder、speaker encoder 等辅助模块拆分到不同配置块、文件或命名空间，或需要额外的 latent statistics 文件。
- 强制：从 checkpoint 配置块构造并校验各模块尺寸；单次遍历权重迭代器，按每个模块的精确 `state_dict` key 集合路由，并分别处理 `llm.model.*`、辅助模块和非 safetensors 统计文件；记录各模块实际加载数与期望数。
- 禁止：缺失配置块时静默套用其他 checkpoint 的默认值；以命中一个 target name 代表整组权重完整；让 speaker 权重落入 VAE catch-all；重复消费只能遍历一次的权重迭代器，或用默认初始化掩盖未加载参数。
- 验收：对已验证 checkpoint 逐模块核对加载计数、无 missing/extra tensor 和预期 dtype；对缺失配置块、架构常量不匹配、部分 shard 及错误命名空间执行 fail-fast 测试，并确认推理前就暴露错误。^[PR #4765]

相关执行流见 [model-executor architecture](architecture.md)；跨 stage 合同见 [bridge/batch 规则](rules-bridge-batch.md)。
