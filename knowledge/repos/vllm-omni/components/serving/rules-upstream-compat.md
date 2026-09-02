---
title: "Serving upstream 兼容规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #5976", vllm_omni/engine/stage_engine_startup.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/entrypoints/utils.py, tests/engine/test_stage_engine_startup_cache_env.py]
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
