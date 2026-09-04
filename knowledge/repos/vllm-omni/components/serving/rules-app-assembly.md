---
title: "Serving app assembly 规则"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #6609", "PR #6707", vllm_omni/config/endpoint_policy.py, vllm_omni/entrypoints/openai/api_server.py, tests/config/test_endpoint_policy.py, tests/entrypoints/openai/test_profiler_endpoints.py, tests/entrypoints/openai_api/test_api_server_guards.py]
confidence: high
---

# Serving app assembly 规则

## SERV-5s — 覆盖 upstream HTTP route 前必须先移除同 method/path 的旧 route

- 触发：assembled app 用 Omni handler 覆盖 upstream HTTP endpoint，尤其是附带可选 request body
  或 stage scope 的 conditional router。
- 强制：唯一公开 helper `endpoint_policy.remove_route_from_app(app, path, methods)` 的 `methods` 为必传
  的 method set、没有 `None`/wildcard 语义；它只移除 `Route`、path 精确相等、`route.methods` 非 `None`
  且与所给 set 相交的条目，保留非 `Route`、不同 path 与 method 不相交的 routes。API server 必须导入
  此 helper，不得保留第二份实现或由 endpoint policy 反向导入 API server。调用在 `include_router()` 前，
  并置于 feature 启用的同一条件分支；用于 endpoint restrictions 与 API/profiler overrides。FastAPI/
  Starlette 不会因后注册同 path/method 而替换旧 route，dispatch 会命中先注册者。
- 禁止：只检查 router 自身存在，或只断言 HTTP 200；这不能证明 assembled app 没有重复 route，
  也不能证明 request body 到达 Omni handler。
- 验收：unit test 构造同 path 的 `Route`（相交和不相交 methods）及非 `Route`，断言仅移除相交者；
  assembly test 验证 API server 使用同一 helper、没有本地 duplicate/circular import，并为 upstream 和
  Omni 注册相同 method/path 后断言仅剩 Omni endpoint。公开 endpoint test 发送 `stages` 并断言 engine
  client 收到原值。`/start_profile` 与 `/stop_profile` 是当前实例。PR #6707 现有测试没有直接 method
  partition 或 API assembly 覆盖；review 的批准边界是 static review、merge tree 与 CI，不能据此作
  broad compatibility/E2E 声明。^[PR #6609] ^[PR #6707, merged 2026-09-02]
- 已知边界：同一 assembled app 的 upstream `GET /health` 仍先于 Omni health route 注册，当前
  first-match dispatch 会遮蔽 Omni 的 diffusion fallback/JSON handler；测试 fake upstream 也未注册
  该 sibling route。该 review thread 在本提交获批时明确 defer，不能据 profiler 修复声称所有重复
  route 已清零，后续修复还需核对 render-only `engine_client is None` 时 200/503 的语义差异。^[PR #6609]
