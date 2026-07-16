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

- 全局 CLI、deploy YAML 和 per-stage override 合并：`vllm_omni/config/stage_config.py` 的 `build_stage_runtime_overrides` 及其 config factory 调用方。
- stage devices、replica 布局和启动前容量：`vllm_omni/engine/stage_runtime.py`、`vllm_omni/engine/stage_init_utils.py`。
- 子进程设备可见性和 worker 启动：`vllm_omni/engine/stage_engine_startup.py`。
- AR/LLM worker rank 与设备选择：`vllm_omni/worker/gpu_ar_worker.py`。
- runner 到模型的预处理 metadata、prefill/decode 分类和 MTP 路由：`vllm_omni/worker/gpu_model_runner.py` 的 `_preprocess`。
- 共享 runner 回归测试：`tests/worker/test_omni_gpu_model_runner.py`；具体模型怎样消费 metadata：`tests/model_executor/models/`。

启动类错误优先沿“最终 stage 配置 → runtime devices → 启动前校验 → worker rank”读取这四段。只有其中一段把错误状态交给其他模块时才横向展开。

## 怎样判断问题归属

多个模型共用的 stage 生命周期、配置解析、runner 预处理合同或数据桥接问题归这里；某个模型怎样解读 metadata、token、attention 或 checkpoint 的问题归对应 `models/<模型>/`。

源码会变化，具体类名和路径在改代码前必须以目标仓库当前版本为准。
