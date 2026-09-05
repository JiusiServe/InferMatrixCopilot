---
title: "vLLM-Omni Benchmark 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, benchmark]
sources: ["PR #6817", tests/dfx/perf/scripts/run_benchmark.py, tests/benchmarks/test_omniinteract.py]
confidence: high
---

# vLLM-Omni Benchmark 规则

只有 `BENCH-数字字母` 是可审计规则 ID。证据口径和远端 scope lock 见
[evidence gate](guides/evidence-gate.md)；模型专有的 MiniCPM-o 行为见
[MiniCPM-o 4.5 rules](../models/minicpm-o-4-5/rules.md)。

## BENCH-1a — perf JSON 的显式 warmup 覆盖必须保留零值

- 触发：新增或修改 `tests/dfx/perf/tests` 的 perf JSON，或修改它传给 benchmark client 的
  warmup 解析。
- 强制：仅在字段缺失时使用 runner 默认值；显式的非负整数（包括 `0`）原样传递到
  client。将测量目标标为冷请求时，在 JSON 明示 `num_warmups: 0`，而不是依赖并发数或
  truthiness 推导。
- 禁止：用 `value or default`、`max(default, value)` 或类似逻辑把显式零值改成默认
  warmup 数。
- 验收：metadata/unit test 同时断言字段缺失得到默认值、`num_warmups: 0` 仍为零，且负数、
  bool 或非整数被拒绝。 ^[PR #6817]

## BENCH-1b — realtime workload 的完成、artifact 与质量资格分层

- 触发：runner 为 realtime/OmniInteract 一类 workload 增加 PASS/FAIL 断言或汇总字段。
- 强制：先断言计划请求全部完成，再断言 workload 汇总的 total、success、failed 与计划
  一致以及必需 artifacts 完整；把 official manifest eligibility 作为单独报告的质量信号。
  LISTEN-only 合法路径可以没有 response audio 或 transcript chunk。
- 禁止：用 manifest eligibility、非空 WAV 帧数、或是否有回应音频替代 transport/lifecycle
  成功；也不能在 artifact 缺失或 request 失败时继续产出性能结果。
- 验收：完整 lifecycle/artifact fixture 通过；缺 summary、请求计数不符、失败请求或
  `artifacts_complete=false` 的 fixture 必须失败；clipped/cancelled 等不合资格输出仍能被
  报告为本地 lifecycle 成功。 ^[PR #6817]

## BENCH-1c — checked-in 外部 benchmark workload 必须可复现

- 触发：把 Hub dataset 或媒体 archive 写入 checked-in 本地 perf JSON。
- 强制：使用 `org/repo@immutable-revision` 形式的 dataset 标识，固定 subset、请求顺序和
  输出目录；filesystem fallback 同时支持 plain `org/repo` 与带 revision 的路径。
- 禁止：让已提交的性能 workload 跟随 Hub 默认分支，或只测试不带 revision 的 fallback。
- 验收：配置中的 dataset 标识含 revision；fallback unit coverage 覆盖 plain 与 revision
  两种输入；每个固定 subset 的 case 数、并发与 warmup 设置可由 JSON 直接审计。 ^[PR #6817]
