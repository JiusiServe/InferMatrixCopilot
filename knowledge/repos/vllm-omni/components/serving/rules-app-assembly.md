---
title: "Serving app assembly 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #6609", vllm_omni/entrypoints/openai/api_server.py, tests/entrypoints/openai/test_profiler_endpoints.py, tests/entrypoints/openai_api/test_api_server_guards.py]
confidence: high
---

# Serving app assembly 规则

## SERV-5s — 覆盖 upstream HTTP route 前必须先移除同 method/path 的旧 route

- 触发：assembled app 用 Omni handler 覆盖 upstream HTTP endpoint，尤其是附带可选 request body
  或 stage scope 的 conditional router。
- 强制：在 `include_router()` 前，从 assembled app 移除相同 path 与 HTTP method 的 upstream route；
  只在该 feature 启用的同一条件分支执行替换。FastAPI/Starlette 不会因后注册同 path/method 而替换
  旧 route，dispatch 会命中先注册者。保留无关 upstream routes。
- 禁止：只检查 router 自身存在，或只断言 HTTP 200；这不能证明 assembled app 没有重复 route，
  也不能证明 request body 到达 Omni handler。
- 验收：assembly test 为 upstream 和 Omni 注册相同 method/path，断言仅剩一个 route 且 endpoint
  属于 Omni；公开 endpoint test 发送 `stages` 并断言 engine client 收到原值。当前
  `/start_profile` 与 `/stop_profile` 是此合同的实例。^[PR #6609]
- 已知边界：同一 assembled app 的 upstream `GET /health` 仍先于 Omni health route 注册，当前
  first-match dispatch 会遮蔽 Omni 的 diffusion fallback/JSON handler；测试 fake upstream 也未注册
  该 sibling route。该 review thread 在本提交获批时明确 defer，不能据 profiler 修复声称所有重复
  route 已清零，后续修复还需核对 render-only `engine_client is None` 时 200/503 的语义差异。^[PR #6609]
