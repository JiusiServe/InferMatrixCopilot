---
title: "Diffusion attention 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5887", "PR #5891", "PR #5897", "PR #5997", vllm_omni/config/omni_config.py, vllm_omni/config/stage_config.py, vllm_omni/diffusion/attention/backends/abstract.py, vllm_omni/diffusion/attention/backends/flash_attn.py, vllm_omni/diffusion/data.py, vllm_omni/engine/arg_utils.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/cli/serve.py, vllm_omni/platforms/npu/platform.py, tests/config/test_omni_config.py, tests/diffusion/attention/test_flash_attn.py, tests/diffusion/cache/test_teacache_extractors.py]
confidence: high
---

# Diffusion attention 规则

## DIFF-1f — deterministic flag 只对构造时选定的 local dense FA 生效

- 触发：修改 `--fa-deterministic`、diffusion config projection 或 local `FLASH_ATTN` dispatch。
- 强制：direct CLI 经 engine args/AsyncOmniEngine 传播到 `OmniDiffusionConfig`，attention impl 在构造
  时捕获；true 只在 dense unmasked `flash_attn_func` 传 `deterministic=True`，false 必须省略 kwarg
  保留 library default。structured deploy 必须由 `_DiffusionConfigProjection` 显式拥有字段。
- 禁止：把该 flag 描述成全 FlashAttention、跨平台或运行时动态 toggle。piecewise、packed-varlen、
  masked-varlen、dense-varlen fallback 以及 XPU/NPU path 不消费 kwarg，启用时只能 warning once。
- 验收：direct CLI 与 structured/deploy config 分别做 true/false 端到端传播；dense true/false 精确断言
  kwarg，每条 non-dense path 断言不传且只警告一次，构造后改 config 不得被误认为立即生效。目标 pin
  已将 `fa_deterministic` 加入 `_DiffusionConfigProjection`，因此 `from_kwargs` 不再过滤且派生
  config/stage-engine field set 会分类该字段；PR 引用/运行的既有 classification test 只断言字段分类
  集合与 projection dataclass 一致，没有以 non-default true 证明 structured/deploy→
  `OmniDiffusionConfig`→backend 的值传播，也没有重跑 Qwen accuracy。^[PR #5887] ^[PR #5897]

## DIFF-1g — NPU packed mask-free 是 model opt-in + backend fallback 双合同

- 触发：修改 `supports_packed_mask_free`、NPU `FLASH_ATTN`、packed cu/max metadata、
  `npu_attn_varlen`、`laser_input_scale` 或 MindIE-SD backend selection。
- 强制：base backend capability 默认 false；`FlashAttentionBackend` 只在 CUDA/NPU 报 true，XPU
  仍读 mask。NPU 新分支还必须由每次 forward 的 `extra["npu_attn_varlen"]` 显式 opt in；未设置的
  Wan/Cosmos 等 caller 保持原 masked `attention_forward`。quantized KV 在 `forward_npu` 更早转入
  `forward_fa_quant_npu`，不消费这套 mask-free metadata。显式选择 NPU `FLASH_ATTN` 且 MindIE-SD
  存在时，platform 必须在首次 custom-op registry snapshot 前 eager import 它。^[PR #5891]
- 强制：默认 opt-in 路径用 MindIE-SD TND varlen，host list 传累计 end offsets；只有 env 精确等于
  `ascend_laser_attention` 才改走 prefix K/V slice。resolver 只接受 non-causal、batch=1、四个 packed
  key 齐全、Q/K cu shape 相同且至多两 documents、Python-int max length 在 bounds 内，以及
  `[real,pad]` 中 real 不短于 pad；无 padding 的单 document 也接受。Q/K/V 从 BSND squeeze batch
  不复制；Laser 保留 full Q、只裁 K/V，padding-row output 必须由下游忽略。
- 强制：packed branch 拒绝 metadata 时，如果 caller 因 capability 没构造 mask，backend 必须用合法
  `valid_kv_length` 重建 prefix mask；缺失、非 int 或越界立即报错，不能对 padding 做 unmasked
  attention。重建路径仍会扩展 quadratic `full_qk`，所以是 correctness fallback，不是 memory
  fast path。Laser 可消费数值型 `input_scale>1`：Q/K/V 同除、softmax scale 乘平方、output 再乘回；
  absent/invalid scale 不缩放。模型只应给有硬件数值证据的 exact power-of-two factor。
- 禁止：把任意 `MINDIE_SD_FA_TYPE` 当作 honored selection；target 对除 exact Laser string 外的合法值、
  typo 和垃圾值都静默走 TND varlen。不得从 capability=true 推断任意 packed layout安全：resolver
  只检查 cu tensor shape、不读其 offset values，真实 producer 必须另证 `[0,used,total]` 内容。
- 验收：CPU/mock 覆盖 resolver 接受/拒绝矩阵、env dispatch、default caller masked path、fallback
  mask/fail-closed、host lists、Laser layout/slice/scaling；真实 NPU 再与 masked FP32/BF16 reference
  对照。target tests 覆盖前者但 mock kernel 不证明 MindIE 数值；NPU SDPA 的同类 `full_qk` churn
  未改。capability 是 classmethod，所有非 `AttentionBackend` duck-typed doubles/plugins 也须兼容；
  repo 内 TeaCache `FakeBackend` 已镜像 abstract default，显式返回 false 并恢复 masked-path
  extractor coverage。该修复只改 test double，没有给 production consumer 加 default-safe access，也
  没有证明 third-party registry override 或未继承 base class 的 backend 完成了 capability
  census；这些实现仍须继承合同或显式实现 method。^[PR #5891] ^[PR #5997]
