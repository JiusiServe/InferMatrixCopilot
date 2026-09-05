---
title: "OmniInteract Realtime Benchmark"
created: 2026-09-04
updated: 2026-09-05
type: guide
tags: [vllm-omni, benchmark]
sources: ["PR #6522", "PR #6696", "PR #6818", vllm_omni/benchmarks/metrics/metrics.py, vllm_omni/experimental/fullduplex/openai/protocol.py, vllm_omni/experimental/fullduplex/openai/chat_fallback.py, tests/benchmarks/metrics/test_metrics.py, tests/benchmarks/patch/test_patch.py, docs/cli/bench/serve.md, vllm_omni/benchmarks/data_modules/omniinteract_dataset.py, vllm_omni/benchmarks/omniinteract.py, vllm_omni/benchmarks/patch/patch.py, vllm_omni/entrypoints/cli/benchmark/cli_args.py]
confidence: high
---

# OmniInteract Realtime Benchmark

`omniinteract` is a `vllm bench serve --omni` dataset: each selected official
`1q1a`、`1q1a_math` or `1qna` video is one MiniCPM-o native-duplex WebSocket
session, not a text-prompt workload. It is a runner/artifact integration; it
checks transport, lifecycle and artifact completeness, not answer accuracy or a
production deployment contract. ^[PR #6522]

## Invocation and selection contract

- It requires `--backend openai-realtime-duplex`, `/v1/realtime`, and an
  existing `--omniinteract-ref-audio`; incompatible backend/endpoint and
  `--ignore-eos`、`--profile`、`--skip-tokenizer-init` or positive
  `--probe-request-rate` fail before the run. Omitted endpoint is normalized to
  `/v1/realtime` by parser explicitness, not by trusting the upstream default.
- `--num-prompts` omitted means 3; explicit `0` selects all, and an oversize
  value selects all available cases. The default concurrency is 1 and any
  explicit value must be positive. Dataset input may be an extracted tree,
  `data.tar[.gz]`, or a Hugging Face dataset ID; absent path resolves the
  official `lucky-lance/OmniInteract` archive.
- Selection is deterministic for seed/`--disable-shuffle`; it validates subset
  layout, confined mapping paths, duplicate videos and archive members.

## Workload, timing and memory boundary

- Before benchmark timing, every selected video is probed and rejected above
  the configured duration limit, then decoded by timeout-bounded `ffmpeg` into
  mono 16-kHz PCM16 and at 1 FPS. Input audio replays in 200-ms chunks and
  video uses real-time pacing. Thus selected decoded media stays client-resident
  and `--max-concurrency` does not bound preparation memory.
- The runner configures the native-duplex session and streams the reference WAV,
  input media, final commit, response lifecycle, drained playback ACK and
  explicit close. A successful final input needs an accepted model LISTEN or a
  non-cancelled response after commit; buffering/unmarked LISTEN and unrelated
  pre-commit active-response terminals do not satisfy it. LISTEN-only is valid
  benchmark output unless `--omniinteract-require-response` requests functional
  E2E semantics.
- Client request timing begins at receipt of `response.created`: TTFT is first
  non-empty text delta, TTFP first audio packet, and RTF is through final audio
  packet divided by emitted-audio duration. TPOT/ITL derive only from stage-0
  timing; ITL is reported only when all required intervals exist. Missing
  measurements remain missing rather than becoming zero, so request goodput
  cannot pair metrics from different responses.
- TPOT 样本必须 finite 且严格大于零。native duplex 的逐段 Stage-0 metrics 是增量，需累加；只有
  token count 完整时使用 exact ITL，否则全部 segment 都有正有限 `tpot_ms` 时才按 interval 加权；
  最后仅在 client 观察到 `text_latency > ttft > 0` 时按总 token 数回退。^[PR #6696]
- `openai-chat-omni` 使用不同的 source precedence：client receive interval 只要有正有限 sample 就是
  authoritative；只有没有正 client ITL 且最终 token 数大于一，才读取 latest cumulative Stage-0
  snapshot。其正 `num_tokens_out` 必须与最终累计 usage 完全相等；完整 finite/nonnegative exact ITL
  且总和为正优先，否则用正有限 Stage-0 TPOT 按 interval 投影。不得由 server 覆盖正 client timing，
  也不得混合 snapshot 或把 mismatch/zero/NaN 变成样本；无有效来源时保持 unavailable。^[PR #6818]

## Artifact and evidence contract

- A completed case writes `output.wav`, `wav_transcript.json`, `events.json`,
  `result.json`, then `.done`; failures use `.failed.json`. The batch writes
  `batch_summary.json` and `official_eval_manifest.jsonl`. One output-root lock
  serializes complete runs; publication happens after the measured request clock
  freezes, so artifact I/O is not serving throughput.
- Transcript timestamps are the serialized playback-queue timeline; raw event
  timing remains in `events.json`. Cancelled output or audio clipped beyond the
  rounded video horizon stays auditable but is excluded from the official
  manifest. Artifact success and official-evaluation eligibility are distinct.
- PR #6522 reported a three-case MiniCPM-o smoke (one case per layout) and
  runner tests. Those numbers are environment-specific evidence only: this
  commit adds no performance threshold consumer, no answer-quality evaluation,
  and no 12-video nightly/production configuration. Do not promote its example
  command, default model, or smoke result to a runtime guarantee.
- 若某 hardware baseline 配置了 `mean_tpot_ms`，结果必须同时有正的 `num_tpot_samples` 和 finite
  aggregate；仅有字段或 `NaN` 不能通过 gate。目标 JSON serializer 仍允许 non-standard `NaN`，
  因而 artifact consumer 仍需显式拒绝，不能把序列化成功当作 strict JSON/metric validity。^[PR #6696]
