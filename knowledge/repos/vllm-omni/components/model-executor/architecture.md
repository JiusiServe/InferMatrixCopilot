---
title: "Model Executor 共享架构"
created: 2026-07-10
updated: 2026-09-02
type: architecture
tags: [vllm-omni, components, model-executor]
sources: ["PR #4958", "PR #5610", docs/design/feature/omni_async_output_materialization.md, vllm_omni/model_executor/models/common/qwen3_code_predictor.py, vllm_omni/model_executor/models/moss_tts/modeling_moss_tts_local.py, vllm_omni/model_executor/models/moss_tts/modeling_moss_tts_talker.py, vllm_omni/model_executor/models/qwen3_tts/configuration_qwen3_tts.py, vllm_omni/platforms/npu/_310p/patch/qwen3_tts.py, vllm_omni/worker/gpu_model_runner.py, vllm_omni/worker/gpu_ar_model_runner.py, vllm_omni/platforms/npu/worker/npu_ar_model_runner.py, vllm_omni/config/stage_config.py, vllm_omni/config/omni_config.py, vllm_omni/engine/stage_runtime.py, tests/model_executor/models/moss_tts/test_moss_fused_load.py, tests/model_executor/models/qwen3_tts/test_code_predictor_dtype.py, tests/worker/test_omni_gpu_model_runner.py, tests/worker/test_gpu_ar_model_runner.py]
---

# Model Executor 共享架构

## 负责什么

`vllm_omni/model_executor/` 负责组织 AR/LLM 等非 diffusion stage 和具体模型实现；`vllm_omni/worker/` 负责共享 runner 执行、逐请求调度状态、runner 到模型的预处理合同和 MTP 路由。两者共同构成这里的 Model Executor owner；不能因为类名是 `ModelRunner` 就忽略 `worker/` 路径。

## 主要边界

- `stage_configs/` 描述 stage 组合和运行参数。
- `stage_input_processors/` 负责跨 stage 数据转换。
- `models/` 下的实现负责具体模型执行，但模型专有结论仍归对应模型目录。
- `vllm_omni/worker/gpu_model_runner.py` 拥有共享 GPU runner 的 `_preprocess`、逐行 metadata 生产和 `talker_mtp` 路由；平台 worker 可以继承或覆盖这些边界。

## 当前源码职责锚点

调查前用 current main 验证这些符号仍存在；路径变化时沿调用方更新本页，不保留失效副本。
（2026-08-05 在 `v0.26.0 @ a4ea67a2` 复核：下列 6 个锚点文件与
`build_stage_runtime_overrides`、`_preprocess` 符号全部存在。）

- 全局 CLI、deploy YAML 和 per-stage override 合并：`vllm_omni/config/stage_config.py` 的 `build_stage_runtime_overrides` 及其 config factory 调用方。
- stage devices、replica 布局和启动前容量：`vllm_omni/engine/stage_runtime.py`、`vllm_omni/engine/stage_init_utils.py`。
- 子进程设备可见性和 worker 启动：`vllm_omni/engine/stage_engine_startup.py`。
- AR/LLM worker rank 与设备选择：`vllm_omni/worker/gpu_ar_worker.py`。
- runner 到模型的预处理 metadata、prefill/decode 分类和 MTP 路由：`vllm_omni/worker/gpu_model_runner.py` 的 `_preprocess`。
- 共享 runner 回归测试：`tests/worker/test_omni_gpu_model_runner.py`；具体模型怎样消费 metadata：`tests/model_executor/models/`。

启动类错误优先沿“最终 stage 配置 → runtime devices → 启动前校验 → worker rank”读取这四段。只有其中一段把错误状态交给其他模块时才横向展开。

## AR async Omni output materialization

`GPUARModelRunner` 可把 `OmniModelRunnerOutput` 的 D2H、逐请求切片和 payload 构造从
decode critical path 移到 background builder；采样 token feedback 与下一步要读的
postprocess state 仍须同步完成。进入下一 decode step 前，scheduler/request mapping、token
span 和可复用 CUDA output 都要形成 step-owned snapshot，CUDA tensor 要 clone 后在独立
stream 搬到 pinned host buffer，并用 event 标记 ready。

snapshot 不包含 connector output：background builder 是该 output cycle 的唯一 drain
consumer，读取 live connector signal；`get_output()` join builder，同时是完成与异常传播边界。
启用条件是 AR async scheduling、`async_chunk`、model opt-in 且没有 prefix cache、speculative
decode、routed-expert output 等冲突状态；条件不满足时回退同步构造。CUDA/ROCm 是已验证范围，
不是代码里的 platform guard；XPU/MUSA 可能通过共享 GPU runner 进入但尚未验证，Ascend NPU
使用独立 runner 并保持同步 materialization。

## 共享 fused code-predictor loader 合同

Qwen3-TTS、Qwen3-Omni 和 MOSS-TTS Realtime 复用 `qwen3_code_predictor.py`。每层将
HF q/k/v 行按该顺序拼成 plain `nn.Linear` `qkv_proj`，将 gate/up 拼成
`gate_up_proj`；forward 必须按同样边界拆分，并在 SDPA 前把 packed k/v slice
重新物化为 contiguous。这保持线性代数，但 GPU kernel/累加顺序变化仍可导致
bit-level drift。

该表示的 loader、consumer、TP 与 platform 可执行验收合同见
[EXEC-2b](rules.md#exec-2b-fused-shard-必须按布局数值闭环且所有-consumer-委托共享-loader)。

## 怎样判断问题归属

多个模型共用的 stage 生命周期、配置解析、runner 预处理合同或数据桥接问题归这里；某个模型怎样解读 metadata、token、attention 或 checkpoint 的问题归对应 `models/<模型>/`。

源码会变化，具体类名和路径在改代码前必须以目标仓库当前版本为准。
