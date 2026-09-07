---
title: "CI 并行测试与 engine fixture 合同"
created: 2026-08-23
updated: 2026-09-07
type: rule
tags: [vllm-omni, ci]
sources: ["PR #3422", "PR #5074", "PR #5255", "PR #5310", "PR #5402", "PR #5524", "PR #5543", "PR #5670", "PR #5713", "PR #5780", "PR #5823", "PR #5836", "PR #5957", "PR #5976", docker/Dockerfile.ci, docker/Dockerfile.xpu, .buildkite/intel/scripts/run-xpu-test.sh, .buildkite/cuda/test-merge.yml, .buildkite/cuda/test-ready.yml, "PR #5845", "PR #5872", "PR #6008", "PR #6048", "PR #6056", "PR #6096", "PR #6102", "PR #6202", "PR #6208", "PR #6273", "PR #6293", "PR #6311", "PR #6339", "PR #6343", "PR #6468", "PR #6523", "PR #6613", "PR #6555", "PR #6650", .buildkite/common/scripts/run_cov_split.sh, pyproject.toml, tests/helpers/tests/test_mark.py, tools/pre_commit/check_test_marks.py, .buildkite/common/scripts/upload_pipeline.py, .buildkite/cuda/test-nightly.yml, .buildkite/cuda/test-weekly.yml, .buildkite/npu/test-npu-nightly.yml, .pre-commit-config.yaml, tests/helpers/clean.py, tests/helpers/client.py, tests/helpers/mark.py, tests/helpers/runtime.py, tests/helpers/stage_config.py, tests/buildkite/test_upload_pipeline.py, tests/dfx/perf/scripts/run_benchmark.py, tests/dfx/perf/tests/test_minicpmo_4_5.json, tests/dfx/perf/tests/test_minicpmo_4_5_duplex_seed_tts.json, tests/dfx/perf/tests/test_qwen_image_vllm_omni.json, tests/dfx/stability/, tests/e2e/accuracy/minicpmo_4_5/test_minicpmo_4_5.py, tests/e2e/online_serving/helpers/minicpmo_4_5_duplex.py, tests/e2e/online_serving/test_flux_kontext_expansion.py, tests/e2e/online_serving/test_minicpmo_4_5.py, tests/e2e/online_serving/test_minicpmo_4_5_duplex.py, tests/e2e/online_serving/test_minicpmo_4_5_expansion.py, tests/e2e/online_serving/test_qwen_image_expansion.py, tests/e2e/online_serving/test_minimax_h3_dlo_dp2_t2va.py, tests/model_tests/diffusion/diff_model_builders.py, tests/model_tests/diffusion/model_settings.py, tests/model_tests/diffusion/test_alignment.py, tools/nightly/run_nightly_jobs.sh, tools/pre_commit/check_tts_adapter.py, tests/tools/test_check_tts_adapter.py, .buildkite/amd/scripts/bootstrap-amd-omni.sh, .buildkite/amd/test-amd-merge.yml, .buildkite/amd/test-amd-ready.yml, tests/diffusion/distributed/test_tensor_parallel.py, tests/diffusion/offloader/test_diffusion_layerwise_offload.py, "PR #6704", tests/dfx/perf/tests/test_qwen3_omni_async_chunk.json, tests/dfx/perf/tests/test_qwen3_omni_no_async_chunk.json, "PR #6743", "PR #6696", vllm_omni/benchmarks/metrics/metrics.py, vllm_omni/benchmarks/patch/patch.py, tests/benchmarks/metrics/test_metrics.py, tests/benchmarks/patch/test_patch.py, "PR #6674", docker/Dockerfile.npu, docker/Dockerfile.npu.a3, docker/Dockerfile.npu.ci, docker/Dockerfile.npu.ci.a3, "PR #6818", "PR #6830", "PR #6884", tests/diffusion/conftest.py, tests/diffusion/attention/test_flash_attn.py, tests/buildkite/test_amd_pipeline.py, tests/e2e/offline_inference/test_qwen3_omni_colocate_async.py, "PR #6947"]
confidence: high
---

# CI 并行测试与 engine fixture 合同

入口与其他规则见 [共享规则](rules.md)。

## OMNI-CI-2b — 并行测试基础设施隔离任务失败和共享状态

- 触发：xdist、共享下载 fixture、长寿命 judge/transcriber worker、进程池 retry、spawned
  `torch.distributed` process group，或测试修改 PyTorch process-global default state。
- 强制：任务级异常后丢弃污染 worker；submit/result 串行，只有进程崩溃可 retry-once；传给
  xdist 的参数可序列化，依赖固定兼容 major；共享文件在读锁前显式检查存在，写入保持锁语义。spawned `torch.distributed` 必须为每个 group 传入新鲜 `file://` rendezvous URL，不能先释放 TCP port 再把其数字交给子进程；`get_open_port` 只用于真实 TCP service。
- 共享 helper 的边界必须清晰：请求 client 从 `tests/helpers/client.py`、环境/设备清理由
  `clean.py`、server/runner 生命周期由 `runtime.py` 提供；pytest plugin `conftest.py` 只注册
  fixture，调用方不得依赖它的隐式或 star-import re-export。`__init__` 或 `__enter__` 的启动失败
  不会调用 `__exit__`，所以必须立即回滚已启动的 stage 子进程、关闭已打开的日志 FD 并清除临时
  日志；只有显式 `VLLM_OMNI_KEEP_LOG` 调试选择可保留日志文件。测试 deploy helper 只接受新
  schema 的顶层 `stages`；不得静默回退 `stage_args`，缺失时 consumer error 必须指出配置文件。
  `tests/diffusion/` 的 autouse fixture 还必须在每个 test 前 snapshot `torch.get_default_dtype()`，
  并在 `finally` 恢复，使失败、skip 和正常返回采用同一 cleanup。
- 禁止：普通 task error 复用同一进程；为 pytest 生命周期不可达的竞态堆测试；把并行参数或
  活对象隐式跨进程传递；把 file rendezvous 套用于 Mooncake/RDMA 等真实监听服务；依赖 collection
  order 掩盖 `torch.set_default_dtype` 泄漏，或把 diffusion-tree fixture 称为树外测试的保护。
- 验收：OOM、普通异常和 BrokenProcessPool 分别验证隔离/重试；online/offline xdist 均通过，
  并发 cache miss 只产生一个完整文件；spawned Gloo/NCCL group 使用独立 file rendezvous，真实 TCP
  service 仍使用 port helper。另以 dtype-mutating predecessor + default-sensitive F32 test 覆盖正常与
  exception cleanup。该 fixture 只覆盖 `tests/diffusion/`；Ovis 的原始 leak 若在树外运行，仍须在
  source 修复。^[PR #6208] ^[PR #6339] ^[PR #6468] ^[PR #6523] ^[PR #6830]

## OMNI-CI-2c — 昂贵 engine fixture 复用必须恢复状态并隔离拓扑

- 触发：为减少 checkpoint cold start，把 function-scoped engine/server 提升到 class/module
  scope，或合并 sleep/wake 等重模型 case。
- 强制：不兼容 topology 使用不同 class-scoped fixture，保证同一时刻只有一个 heavy engine；
  module 前后各做一次 device cleanup；每个 case 在 `finally` 将共享 engine wake/reset 到可用
  状态。不可逆的 level-2 sleep case 放在独立 module-scoped server 的最后，结束后只 teardown。
- 禁止：共享 engine 后依赖测试顺序留下的 sleep/tag/cache 状态；在 module-scoped
  `omni_server` 持有 fixture lock 时再创建 function-scoped server，造成锁等待或 GPU 争用；
  为省 cold start 删除 topology、TP 或 post-wake generation 的独立覆盖。
- 验收：分别覆盖 LLM、diffusion 与 multi-stage topology；每个可恢复 case 后下一 case 从 awake
  开始；level-2 terminal case 之后不再复用 server；统计目标 lane 确实只初始化预期数量的
  engine，且 cleanup 后无 worker/device state 遗留。^[PR #5713]

- Qwen-Image nightly 为减少 cold start 可将 18 个「两 checkpoint × 九 feature」case 收敛为
  九个「每 feature 一个 checkpoint」case，但必须保留全部 feature pytest ID、原单卡/双卡 H100
  marker 和明确的 checkpoint→feature 映射；这只改变权重 coverage 的频率，不能宣称保留了每个
  feature 在每个权重上的组合覆盖。共享 step-execution perf server 时，保持 sequential 与
  concurrency-sweep `benchmark_params`、共同的 `max-num-seqs: 8` capacity 及既有 H100
  baseline artifact；没有实际 lane 结果或显式 consumer 时，不得把 PR 预期或 JSON baseline
  说成性能不变或 regression-gate verdict。^[PR #6613]

## OMNI-CI-2d — diffusion tiny builder 必须替代资源缩减而不是能力缩减

- 触发：重模型 online E2E 因显存 OOM 迁移到 tiny-model framework，或修改
  `DIFFUSION_TEST_SETTINGS` / `EXCLUDED_MODELS`。
- 强制：builder 从真实 pipeline/config 构造缩小 checkpoint，按组件分别收缩 encoder/DiT；
  attention head dim 改变时同比缩放 `axes_dims_rope`，并保留 architecture 要求的轴数与总维度。
  settings 必须列出真实 supported tasks 和每个 acceleration group；只有 builder/settings 已接通
  common tests 后，才从 alignment exclusion 删除模型。
- 禁止：为消除 OOM 直接删除 TP/CFG/cache/offload coverage；把 online suite 从双卡 parallel cases
  缩为单卡 base 后仍声称 online lane 覆盖这些组合；从 tiny checkpoint 通过外推 full checkpoint
  显存、数值质量或吞吐。
- 验收：alignment 双向断言 registry 中每个非排除 pipeline 有 settings，且 settings 不指向排除项；
  common offline suite 对每个 task 跑 base，并逐组执行声明的 acceleration。Flux Kontext 当前 tiny
  contract 是 text-to-image + image-to-image，附加 TP+CPU offload、CFG+CPU offload、以及
  TP+CPU offload+Cache-DiT；online expansion 只保留单 L4 base smoke，parallel coverage 的所有权迁到
  common offline suite，不代表 full-model OOM 已被修复。tiny builder 从收缩后的真实组件配置初始化
  random BF16 weights，只证明 construction、routing 与 control-flow，不证明真实 checkpoint 加载、
  输出质量、显存或吞吐。^[PR #5823]

