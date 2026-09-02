---
title: "Serving upstream 兼容规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #5976", "PR #5957", vllm_omni/engine/stage_engine_startup.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/entrypoints/utils.py, vllm_omni/request.py, tests/engine/test_stage_engine_startup_cache_env.py]
confidence: high
---

# Serving upstream 兼容规则

## SERV-7a — upstream launcher 生命周期兼容必须保持模式检测语义

- 触发：upstream launcher、renderer warmup 或 shutdown 读取的 engine-client 属性变化。
- 强制：pure-diffusion client 只在 launcher-facing `vllm_config.shutdown_timeout` 上提供最小 adapter，
  其余属性透明转发，内部 `get_vllm_config()` 仍返回 `None`；chat template warmup 调用 upstream 当前
  owner `online_renderer`。多 replica spawn 时 replica 0 复用默认 compile cache，后续 replica 在持锁
  的 spawn env 中获得 stage/replica 唯一 `VLLM_CACHE_ROOT`，离开 scope 必须恢复环境。
- 禁止：让 adapter 改变 pure-diffusion detection；调用已删除的 serving-chat warmup；所有 replica
  共写 AOT cache，或永久污染父进程环境。
- 验收：pure diffusion 正常 shutdown 且 detection 不变；renderer 恰好 warmup；cache-env 测试覆盖
  replica 0、多个 stage/replica、嵌套恢复和异常恢复。^[PR #5976]

## SERV-7b — 加速器镜像落后一版时兼容层必须按能力探测

- 触发：CUDA 主线升级 vLLM 后，XPU/NPU 等镜像仍使用前一版 renderer、tool parser
  import 或 request layout。
- 强制：可选 renderer warmup 用属性能力探测；Mistral tool-call parser 只在新 import 不存在时
  回退旧路径；`OmniRequest` 仅为缺失的 `num_stale_output_tokens` 提供零初值，
  不覆写新版 owner 已有的值。
- 禁止：用 platform name 猜测 API；为兼容旧版跳过新版必需初始化；将临时 shim 宣称为
  长期 public API。
- 验收：新/旧 renderer、两条 Mistral import 和有/无 stale counter 的 request layout 都能初始化，
  且新版既有 counter 原值不变。^[PR #5957]
