---
title: "MRv2 选择、能力声明与 Qwen3-TTS 部署 profile"
created: 2026-10-09
updated: 2026-10-09
type: guide
tags: [vllm-omni, components, config]
sources: ["PR #7781", vllm_omni/config/stage_config.py, vllm_omni/config/omni_config.py, vllm_omni/deploy/qwen3_tts_mrv2.yaml, vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2.yaml, vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2_b4.yaml, vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2_single_gpu.yaml, docs/configuration/stage_configs.md, tests/config/test_config_factory.py, tests/config/test_omni_config.py]
---

# MRv2 选择、能力声明与 Qwen3-TTS 部署 profile

适用快照是 [PR #7781](https://github.com/vllm-project/vllm-omni/pull/7781) 的完整 head
`2e3c7fe2c171cd3429298094d175a64eacbdb341`。本页说明该版本的 deploy 级选择和现有
profile，不替代当前 main 的配置合同；后续 stage 级覆盖与 mixed runner 约束见
[topology 与部署 profile 规则](rules-topology-profiles.md)。

## flow

`load_deploy_config()` 先展开 `base_config`，把缺省 runner 解析为 `v1`；
`merge_pipeline_deploy()` 应用 platform overlay，再逐 stage 调用 `_build_engine_args()`，
把 deploy 选择投影为 `use_v2_model_runner`，把 pipeline 能力投影为
`supports_native_mrv2_data_plane`。这条 legacy 路径生成的是 worker 消费的 engine args。
[加载入口](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L780-L803)、
[逐 stage 构造](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L1110-L1146)、
[最终 flag](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L1031-L1052)。

structured 路径在 `from_pipeline_config()` 内应用同一 platform overlay，
`_build_model_config()` 为没有显式 engine 值的两个 flag 填入 deploy/topology 默认。
现有测试证明普通 `model_runner=v1|v2` 输入在 legacy 的 `yaml_engine_args` 与 structured
的 `model_config` 中逐 stage 一致；这不证明 structured 已承担全部生产 startup。
[structured overlay](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/omni_config.py#L2200-L2232)、
[typed 默认投影](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/omni_config.py#L1974-L1981)、
[parity 断言](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/config/test_omni_config.py#L788-L810)。

## api

公开选择是 deploy 顶层 `model_runner: v1|v2`，缺省 `v1`；YAML loader 对其它值抛
`ValueError`。`supports_native_mrv2_data_plane` 是 pipeline stage 的能力声明，缺省
`False`，不能用选中 V2 反推 stage 已支持 native transport。
[字段与默认](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L556-L577)、
[值校验](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L789-L798)、
[能力声明](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L244-L253)。

legacy merge 明确拒绝在 stage `engine_extras` 设置 `use_v2_model_runner` 或
`supports_native_mrv2_data_plane`，包括值为 `False` 的情况。该拒绝边界的现有约束继续
从 [topology 与部署 profile 规则](rules-topology-profiles.md) 查询；本页不复制规则正文。
[拒绝实现](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L1031-L1043)。

## configuration

下表是该 head 展开继承后的 CUDA profile；B2/B4/B8 是 codec graph batch 桶，
`max_num_seqs` 是各 stage 的调度容量，两者不是同一个配置量。

| profile | base_config | Stage 0/1：devices；max_num_seqs | decode_batch_max_size | decode_cudagraph_batch_sizes |
|---|---|---|---|---|
| `qwen3_tts_mrv2.yaml` | `qwen3_tts.yaml` | `"0"/"0"`；`64/64` | `4`（继承） | 未设，wrapper 默认 `[1]` |
| `qwen3_tts_high_concurrency_mrv2.yaml`（B2） | `qwen3_tts_high_concurrency.yaml` | `"0"/"1"`；`64/10` | `2` | `[1, 2]` |
| `qwen3_tts_high_concurrency_mrv2_b4.yaml` | B2 profile | `"0"/"1"`；`64/10` | `4` | `[1, 2, 3, 4]` |
| `qwen3_tts_high_concurrency_mrv2_single_gpu.yaml`（B8） | B2 profile | `"0"/"0"`；`128/32` | `8` | `[1, 2, 3, 4, 5, 6, 7, 8]` |

basic profile 将 Stage 0 `max_num_batched_tokens` 从 base 的 `32768` 覆盖为 `512`；
B2/B4/B8 从 high-concurrency base 继承 `512`。B2 显式设置
`code_predictor_prefix_graphs: false`、`ref_audio_artifact_cache_max_entries: 1024`，并将
Stage 1 `enforce_eager` 从 base 的 `true` 覆盖为 `false`；B4/B8 继承这些值。
四个 profile 都显式或经 base 继承在 NPU/XPU/ROCm/MUSA 上选 V1。
这里的 artifact cache 数值属于模型侧配置，具体消费见
[Qwen3-TTS MRv2 pipeline](../../models/qwen3-tts/mrv2-pipeline.md)；API waveform cache 的
ownership、entry/byte 预算与返回副本见 [reference audio cache](../serving/reference-audio-cache.md)。
[basic overlay](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_mrv2.yaml#L1-L18)、
[basic base 容量](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts.yaml#L56-L76)、
[basic base Stage 1](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts.yaml#L98-L115)、
[graph 默认桶](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/segmented_graph_wrapper.py#L48-L60)、
[B2 overlay](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2.yaml#L1-L28)、
[B2 base Stage 0](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency.yaml#L69-L80)、
[B2 base Stage 1](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency.yaml#L96-L109)、
[B4 overlay](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2_b4.yaml#L1-L8)、
[B8 overlay](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2_single_gpu.yaml#L8-L23)。

## dependencies

native data plane 的实际条件是 `use_v2_model_runner && async_chunk &&
supports_native_mrv2_data_plane`。Qwen3-TTS 两个 pipeline stage 均声明能力，默认 deploy
仍指向 `qwen3_tts.yaml`。runner 的 GPU state、输出顺序与释放见
[MRv2 runtime](../model-executor/mrv2-runtime.md)，请求等待与容量见
[native chunk lifecycle](../scheduler/native-chunk-lifecycle.md)，模型 hook 见
[Qwen3-TTS MRv2 pipeline](../../models/qwen3-tts/mrv2-pipeline.md)。
[组合条件](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py#L23-L32)、
[模型声明](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/pipeline.py#L30-L60)。

上游文档将该 opt-in 限定为 vLLM `0.29.0`；PR 明确不升级依赖，已核对的 PR changed-files
清单没有 `pyproject.toml` 或 `requirements/`。它不能作为其它 vLLM 版本、模型家族或
非 CUDA backend 的支持声明。
[版本与适用范围](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/docs/configuration/stage_configs.md#L294-L320)、
[依赖变更范围](https://github.com/vllm-project/vllm-omni/pull/7781/files)。

## failure_modes

没有 platform V1 overlay 时，NPU/XPU 最终仍选择 V2 会抛 `NotImplementedError`。
V2 stage 未声明 native capability 时，legacy merge 发出明确 warning 并保留 legacy
transport；这条 warning 表示组合尚未验证，不会把 runner 选择自动改回 V1。
[platform 校验](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L847-L867)、
[warning 分支](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/stage_config.py#L1042-L1052)。

不能把普通 runner parity 测试推广为 conflicting-extras parity：该 head 的 structured
`_stage_engine_overrides()` 读取 extras，随后 `_build_model_config()` 使用 `setdefault`，
与 legacy 的保留键拒绝实现不同；现有上述测试没有覆盖这条冲突输入。该组合的完整
entrypoint 等价性仍是验证缺口。
[structured extras](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/omni_config.py#L1484-L1500)、
[setdefault 边界](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/config/omni_config.py#L1974-L1981)。

## tradeoffs

上游文档区分 graph capture buckets 与显式 decode maximum：stateful graph 按已捕获桶
分组，stateless 路径也使用显式 maximum。因此配置 `decode_batch_max_size` 不能单独
证明所有 graph 调用都受同一上限约束。新增 graph shapes 增加编译成本；B4 保持
experimental，B8 文件注明更多 graph memory、面向吞吐并要求预热，不属于低延迟
profile。MPS 是外部 operator 设置，YAML 没有启用它。
[batch 与质量边界](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/docs/configuration/stage_configs.md#L352-L374)、
[B8 定位](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2_single_gpu.yaml#L1-L7)。

设计推断：独立 opt-in profile 便于保留 V1 control，但比较 V1/B1 与 V2/B2 同时改变
runner 和 batching，不能隔离 MRv2 收益。音频首包、连续播放、WER 与 speaker similarity
需要按相同 workload 分别验证；本页不把 profile 注释中的测量描述当作本轮性能结果。

## validation

`tests/config/test_omni_config.py` 的普通 `v1|v2` parity 测试直接断言两种配置产物；
同文件检查 NPU/XPU fail-fast、V1 base/V2 opt-in 和 B2 retune 不改变 V1 profile。
`tests/config/test_config_factory.py` 另外断言 CUDA/NPU 最终 legacy flag、未声明能力的
warning 次数与文字、两个 reserved extras 的拒绝。
[parity 与 profile 断言](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/config/test_omni_config.py#L788-L846)、
[platform、warning 与 reserved-key 断言](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/config/test_config_factory.py#L2710-L2758)。

这些是配置 helper 的自动化测试入口与具体断言，本轮未执行，不构成 GPU runtime、音质
或性能通过证据。上游已有人工验证要求是测 inter-chunk arrival、buffering、WER、speaker
similarity，比较 MPS 开关前后，并预热 B8 全流水线；这些步骤本轮也未执行。
[既有人工验证范围](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/docs/configuration/stage_configs.md#L363-L374)、
[B8 预热要求](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/deploy/qwen3_tts_high_concurrency_mrv2_single_gpu.yaml#L1-L7)。
