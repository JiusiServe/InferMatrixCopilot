vllm-omni 是多 stage 架构，每个 stage 在 yaml 的 `engine_args` 字段单独配 `tensor_parallel_size` / `pipeline_parallel_size` / `enable_prefix_caching` 等。但 vllm 的 `EngineArgs` **顶层**也有这些字段的默认值（tp=1 等）。

**`end2end.py` 这类官方 example script 里有一句关键调用**：

```python
from vllm_omni.engine.arg_utils import nullify_stage_engine_defaults
nullify_stage_engine_defaults(parser)
args = parser.parse_args()  # EngineArgs 顶层字段全变 None
omni = Omni(**vars(args))   # 顶层 None → stage_config yaml 是唯一来源
```

`nullify_stage_engine_defaults` 把 EngineArgs **顶层** 8-10 个字段（tp / pp / prefix_caching / max_num_batched_tokens / dtype 等）默认值全清成 `None`。这样 Omni() 看到顶层 None 就走 stage_config yaml 配置，不会冲突。

**Why:** 直接绕过 argparse 写 `Omni(model=..., stage_configs_path=..., enforce_eager=True, mode="text-to-image")` 这种调用方式，**EngineArgs 顶层 `tensor_parallel_size` 默认 1**。yaml 里 stage 0 / stage 1 各 `tensor_parallel_size: 2`，每 stage 期望 2 GPU。但 launcher 按顶层 tp=1 切分 CUDA_VISIBLE_DEVICES，每 stage 只给 1 个可见 GPU。Stage 1 worker 实际只看到 `['0','1']`（被错切的子集），yaml 说要 logical `['2','3']`，跟 visible 不匹配 → `Stage 1 has logical IDs ['2', '3'], none of which map to the visible devices ['0', '1']` AssertionError 启动失败。painterly debug 时实测踩坑。

**How to apply:**
- 写测试 / probe / 一次性 script 直接 `Omni(...)` 实例化时，必须**显式传** `tensor_parallel_size=None, pipeline_parallel_size=None, enable_prefix_caching=None` 等所有 stage_config 已配的字段——告诉 Omni "走 yaml，别用顶层默认"
- 或者：拷贝 `end2end.py` 的 argparse + `nullify_stage_engine_defaults(parser)` 模板，在它基础上加自己的逻辑
- 探针 / 注入测试推荐做法：**直接 patch `end2end.py`** 加 env-gated 行为，复用它已经处理过的 nullify 逻辑，比重写 script 安全

具体踩坑案例：painterly debug session 写 inject HF cot script，绕过 argparse 直接 `Omni()` 启动 → 启动 300s 后 timeout，stage 1 设备分配 AssertionError。改成 patch `end2end.py:158` 加 env-gated cot inject，2 分钟跑通。
