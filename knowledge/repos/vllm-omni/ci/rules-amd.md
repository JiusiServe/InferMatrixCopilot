---
title: "AMD/ROCm CI 规则"
created: 2026-09-05
updated: 2026-09-12
type: rule
tags: [vllm-omni, ci]
sources: ["PR #6704", "PR #6830", "PR #6884", .buildkite/amd/, tests/helpers/clean.py, tests/helpers/stage_config.py, tests/buildkite/test_amd_pipeline.py, tests/e2e/offline_inference/test_qwen3_omni_colocate_async.py, "PR #7234"]
confidence: high
---

# AMD/ROCm CI 规则

## OMNI-CI-2f — AMD CI stabilization 必须保留有界执行与测量信号

- 触发：AMD/ROCm Buildkite bootstrap、long-running shard timeout/quarantine、GPU-memory assertion、
  cleanup diagnostics、Qwen3-TTS argv，或 Qwen3-Omni sleep/abort control-plane E2E 变更。
- 强制：debug-only READY+MERGE composition 保留 normal branch selection、一个 shared build dependency
  和 named groups；MI300 long steps 有 explicit bounds，已知 failing case 保持独立、time-bounded
  `NonBlocking`。memory comparisons 在 model/offload 后采样、减每 run initial device use 并清 cache；
  optional cleanup diagnostic 也必须 bounded。ROCm offload threshold 只是一项机制 signal，不是
  portability/capacity/performance claim。^[PR #6704]
- 强制：MI300 blocking layerwise-offload step 只 deselect exact Stable Audio parameter，并以 dependent
  `mi300_1` `NonBlocking` step 保留该 case；其余 params、spawn/log env 不变。ROCm BF16 AITER
  cross-attention 仅可用 `assert_close(rtol=1e-2, atol=1.5e-2)`，CUDA/XPU 保持 strict。^[PR #6830]
- 强制：AMD Qwen3-TTS Base step 是 direct `pytest`（无 nested `bash -c`），列出两个 Base test files，
  marker 精确为 `advanced_model and cuda`、`--run-level` 为 `advanced_model`，保留 env/timeouts；这只证明
  rendered argv/collection，不证明 CUDA/ROCm runtime。Qwen3-Omni control-plane E2E 使用命名
  `ci/qwen3_omni_moe_colocate_async.yaml`：thinker-only stage 0、single GPU、8K、`max_num_seqs=1`、
  eager、no prefix cache。CUDA 保留 `.9` percentage/no byte cap；ROCm 仅该 MI300-ish fixture 清 percentage
  并 pin 2 GiB KV。test marks 是 `advanced_model`+`omni`、one-card `H100`/`MI325`。^[PR #6884]
- 禁止：把 debug override 当默认 routing、用邻近 green shard/NonBlocking/旧 head 宣称 target case
  resolved，或让 diagnostic hang bypass timeout；不得把 absolute device use 当 model peak、ROCm tolerance
  扩展到其它平台/path/quality/runtime parity，或把 2 GiB 外推为生产/其他 model/SKU sizing。
- 验收：render merge/ready/combined/malformed selection、timeouts/quarantine/dependency；分别检验 ROCm
  sampling/cleanup 与 model assertion。PR #6884 必须 parse argv 与 platform overlay，断言 marker/run-level、
  CUDA preserve、ROCm-only clear/pin；最终需 exact final-head real MI300 L3 跑完两个 target jobs。该 PR
  未提供该 run，现有证据仅 author-reported local/static validation。^[PR #6704] ^[PR #6830] ^[PR #6884]

## OMNI-CI-2g — 单卡 AMD diffusion model job 必须排除全部 multi-card marker

- 触发：修改 `.buildkite/amd` 的 Diffusion Model Test、sequence-parallel/`mi300_2` 任务，或给 diffusion 模型测试加 `cards_N` / ROCm hardware marker。
- 强制：`mi300_1` 一类单卡 model job 的 pytest marker 必须 `not (cards_2 or … or cards_8)`，同时保留无 `cards_1` 的 legacy 单卡用例；真正需要双卡的用例（如 LTX2 Ulysses parity）改到已有双卡 lane，并声明 `rocm` 资源与 `device_count >= world_size` 早失败。
- 禁止：让 `cards_2+` 测试在单卡 worker 上 spawn rank1→GPU1 导致 `invalid device ordinal`；用邻近 green shard 宣称 multi-GPU routing 已修好。
- 验收：pipeline argv/collection 断言单卡 job 排除 multi-card markers、双卡 job 收集目标文件；硬件 marker helper 覆盖 ROCm 声明。^[PR #7234]

## OMNI-CI-2i — AMD bootstrap 必须按 ready/merge-test 标签选择 L2/L3 suite

- 触发：修改 `.buildkite/amd` bootstrap、`select_test_suites.py`、AMD PR label 路由，或 skip-ci 对 AMD suite 的过滤。
- 强制：`ready` 选 L2（ready suite），`merge-test` 选 L3（merge suite）；两标签同时存在时合并多 suite 且共享一次 image build；`DEBUG_TEST_YAML` 优先；main 继续 L3；无 tier 标签的 PR 可保留 legacy ready fallback。PR labels 精确匹配且失败时 fail closed；skip-ci 必须对已选 L2/L3 独立过滤。
- 禁止：凡 PR 一律上传 ready suite；用子串匹配 labels；在仓库侧假装已改变 Buildkite 外部 trigger 条件；把 `nightly-test` 当成已有 AMD L4 覆盖。
- 验收：selector/bootstrap 单测覆盖 ready-only、merge-only、both、debug override、main、label fetch failure 与 per-suite skip-ci；日志报告实际 `TEST_SPECS`。^[PR #6966]
