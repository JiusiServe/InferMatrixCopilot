---
title: "Buildkite 管线结构"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, ci]
sources: [".buildkite/pipeline.yml", "vllm-omni-rebase-agent@122a9468:agent/config.py", "vllm-omni-rebase-agent@122a9468:config.sh"]
---

# Buildkite 管线结构

仓库侧事实在 `main @ 5c390096` 复核；运营侧事实（管线名、队列→硬件映射）来自
rebase-agent 配置快照（@122a9468），**属运营观测、可能漂移**，用前核对。

## `.buildkite/` 布局（仓库侧）

- **`pipeline.yml`**（根入口，two-doc 模式）：文档 1 经
  `.buildkite/scripts/upload_pipeline.py` 做 skip-ci 判定（docs-only / pytest
  skip 标记，diff-aware）；`---` 后的文档 2 构建 CI 镜像（`docker/Dockerfile.ci` →
  `public.ecr.aws/q9t5s3a7/vllm-ci-test-repo`）并按条件上载子管线。
- 分级 → 子管线映射：**L2 → `test-ready.yml`**（带 `ready` label 的 PR，diff-aware；
  或 main+nightly）；**L3 → `test-merge.yml`**（`merge-test` label 或 main+nightly）；
  **L4 → `test-nightly.yml`**（main+nightly 定时，或 PR label + rebuild）；
  **L5 → `test-weekly.yml`**（每周，依赖镜像构建）。
- 平台管线：`pipeline-intel.yaml`、`pipeline-npu.yaml`、`pipeline-npu-a3.yaml`；
  AMD 变体 `test-amd.yaml`/`test-amd-ready.yaml`/`test-amd-merge.yml` +
  `test-template-amd-omni.j2` + bootstrap 脚本；发布/对齐：
  `release-pipeline.yaml`、`rebase-pipeline.yaml`。
- 硬件 runner 脚本：`scripts/`（`run-amd-test.sh`、`run-xpu-test.sh`、
  `run_npu_test.sh`、nightly-index 与 wheel/镜像发布脚本）。
- `test-ready.yml` 示例步骤组（"Simple Test"）：
  `pytest tests/diffusion tests/model_executor -m 'core_model and cpu'` +
  互补 "Other Test" + "Custom Pipeline Test"
  （`tests/e2e/offline_inference/custom_pipeline/ -m core_model`），跑在
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
  环境坑见 [ci-environment-gotchas](ci-environment-gotchas.md)。
