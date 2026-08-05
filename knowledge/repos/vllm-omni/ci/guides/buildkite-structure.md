---
title: "Buildkite 管线结构"
created: 2026-07-16
updated: 2026-08-05
type: guide
tags: [vllm-omni, ci]
sources: [".buildkite/cuda/pipeline.yml", ".buildkite/cuda/rebase-pipeline.yml", "vllm-omni-rebase-agent@122a9468:agent/config.py", "vllm-omni-rebase-agent@122a9468:config.sh"]
---

# Buildkite 管线结构

仓库侧事实在 `v0.26.0 @ a4ea67a2` 复核；运营侧事实（管线名、队列→硬件映射）来自
rebase-agent 配置快照（@122a9468），**属运营观测、可能漂移**，用前核对。

## `.buildkite/` 布局（仓库侧）

- **`cuda/pipeline.yml`**（CUDA hook entry）：由
  `.buildkite/common/scripts/upload_pipeline.py` 读取 `cuda/bootstrap-upload-steps.yml`
  并上传实际子管线；skip-ci 的 step key 是 `upload-ci-pipeline`，不再依赖根目录
  `pipeline.yml` 的 two-doc 结构。
- 分级 → 子管线映射：**L2 → `test-ready.yml`**（带 `ready` label 的 PR，diff-aware；
  或 main+nightly）；**L3 → `test-merge.yml`**（`merge-test` label 或 main+nightly）；
  **L4 → `test-nightly.yml`**（main+nightly 定时，或 PR label + rebuild）；
  **L5 → `test-weekly.yml`**（每周，依赖镜像构建）。
- 平台管线：`intel/pipeline-intel.yml`、`npu/pipeline-npu.yml`、
  `npu/pipeline-npu-a3.yml`；AMD 变体 `amd/test-amd-ready.yml`/
  `test-amd-merge.yml` +
  `test-template-amd-omni.j2` + bootstrap 脚本；发布/对齐：
- `release/release-pipeline.yml` 是发布管线；对齐管线现在是
  `cuda/rebase-pipeline.yml`，分别上传 ready、merge 和 nightly 子管线。
- 测试树按 owner/feature 归档：原 `tests/ar_diffusion/` 归入
  `tests/diffusion/ar_diffusion/`，full-duplex、custom pipeline、RLHF 和 ComfyUI
  归入 `tests/e2e/features/<feature>/`；新增 component 测试放在对应
  `tests/{component}/`，不创建平行的旧顶层目录。
- `cuda/test-ready.yml` 的 CPU fast lanes 仍按 `tests/diffusion`、
  `tests/model_executor`、`tests/entrypoints` 和 `tests/engine` 分组；feature lane
  使用 `tests/e2e/features/custom_pipeline/` 与 `tests/e2e/features/fullduplex/`，跑在
  `gpu_1_queue`、CI docker 镜像内、`HF_HOME=/fsx/hf_cache`。

## 运营事实（rebase-agent 观测，@122a9468）

- Buildkite org：`vllm`。管线：`vllm-omni-release`（CI）、`vllm-omni-rebase`
  （nightly 与 main CI）；rebase 分支 `dev/vllm-align`，wheel 变体 `cu130`，
  上次 rebase 的 vLLM 提交 pin `1acd67a795ebccdf9b9db7697ae9082058301657`。^[CFG-buildkite]
- 队列 →（最少卡数, 硬件约束）映射：`gpu_1_queue` →（1, any）——实际为 1×L4 机器；
  `gpu_4_queue` →（4, any）——实际为 4×L4；`mithril-h100-pool` →（N, h100）——
  H100/H800（`can_run_ci_test` 把 H800 视同 H100）。^[CFG-queue-map]

## 相关

- 分级定义见 [test-tiers](test-tiers.md)；Buildkite skipped-build/rebuild 互杀等
  环境坑见 [ci-environment-gotchas](ci-environment-gotchas.md)；rebase 管线的
  工作流见 [rebase 主题](../../rebase/_index.md)。
