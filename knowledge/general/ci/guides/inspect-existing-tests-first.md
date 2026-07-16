# 规则：先看现有代码，再谈方案

## 反面教训（2026-04-21）

做 HunyuanImage-3 精度 CI 时，我绕了一大圈：
- 提议 GenEval + mmdet → mmcv 在 Py3.12 装不上 → 建独立 venv → 讨论怎么接 buildkite
- 讨论"用 CLIP-score 替代"、"改 GenBench 砍 it2i"、"采集 9 小时 baseline"
- 写了 300 行方案对比文档

结果用户直接去看仓库：
```
tests/e2e/accuracy/test_gebench_h100_smoke.py
```
**已经存在**，跑的就是 type3/type4 T2I，用 `/v1/images/generations`，judge 是 VLM-as-judge（Qwen2.5-VL-7B-Instruct），**零 mmdet/mmcv 依赖**。

`--gebench-model` 还是 CLI 参数。加一行 `--gebench-model Tencent/HunyuanImage-3.0-Instruct` 就能跑。

我前面所有工作（踩 mmcv 坑、建 Py3.10 venv、写 GenEval 集成代码）全部白做。

## 原则

**"团队同款 CI / 同款测试 / 同款 pattern"类需求，第一件事**：

1. 打开 `tests/` 目录看文件名
2. 找**语义最接近**的现有测试（model 换一下就能复用的）
3. 读它的 conftest fixture、CLI option、运行方式
4. **考虑能不能直接复用 / 复制一份改名**

**把这 3 步做完再开始讨论方案**。不做这 3 步的方案讨论都是空想，容易导致：
- 重复造轮子
- 引入团队没用过的依赖（reviewer 不信任）
- 方案复杂度远高于必要

## 具体到 vllm-omni 精度 CI 的文件清单（2026-04-21 查证）

| 目录 | 内容 |
|---|---|
| `tests/e2e/accuracy/` | 所有精度 CI 入口 |
| `tests/e2e/accuracy/conftest.py` | fixture 和 CLI option（`--gebench-model`, `--gedit-model`, `--accuracy-judge-model` 等） |
| `tests/e2e/accuracy/test_gebench_h100_smoke.py` | T2I 精度（type3/type4）用 VLM judge |
| `tests/e2e/accuracy/test_gedit_bench_h100_smoke.py` | IT2I 精度，同款 judge 路径 |
| `tests/e2e/accuracy/helpers.py` | `reset_artifact_dir` 等 |
| `vllm_omni/benchmarks/accuracy/text_to_image/gbench.py` | GEBench 实现（type3/type4 走 `/v1/images/generations`，type1/2/5 走 `/v1/images/edits`） |

## 下一次做新模型精度 CI

抄 `test_gebench_h100_smoke.py`，改 `--gebench-model` 参数。完成。
**除非有强理由**（比如新模型 T2I endpoint 不同、判据不同），否则不要考虑 GenEval / CLIP-score / 自研评分器。

## 判据模板

用户问"做 XX 精度 CI"时，先回答 3 个问题再提方案：
1. 团队现有类似测试文件？叫什么名字？
2. 它的 fixture 和 CLI option 我的模型能复用吗？
3. 跑一下 `pytest --gebench-model <my-model>` 会发生什么？报错才说明需要改，没报错就结束了

## HunyuanImage3 现成 IT2I accuracy pytest（2026-06-02）

用户要跑 Hunyuan PR 分支精度时，不要重新找 benchmark runner。仓库已经有现成入口：

```bash
tests/e2e/accuracy/test_hunyuan_image3.py::test_image_to_image_alignment
```

这条 pytest 会跑 HunyuanImage3 image-to-image alignment，并直接打印 COT / image similarity / SSIM / PSNR 表。

在 B3 `root@<REMOTE_HOST> -p 31449` 上跑 PR 分支的可复用环境：

```bash
cd <REMOTE_WORK_ROOT>/wt-pr3297-accuracy
export CUDA_VISIBLE_DEVICES=4,5,6,7   # 换成当前空闲的 4 张物理卡
export VLLM_USE_FLASHINFER_MOE_FP16=0
export HF_HOME=/data/model
unset TRANSFORMERS_CACHE HF_HUB_CACHE
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HUNYUAN_MODEL_PATH=/data/model/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2
export PYTHONPATH=<REMOTE_WORK_ROOT>/pydeps-pr3297-accuracy:<REMOTE_WORK_ROOT>/wt-pr3297-accuracy:${PYTHONPATH:-}
export TMPDIR=/tmp

<REMOTE_WORK_ROOT>/.venv/bin/python3 -m pytest -s -v \
  tests/e2e/accuracy/test_hunyuan_image3.py::test_image_to_image_alignment \
  --tb=short
```

运行前要做硬 gate：选中的 4 张物理 GPU 都低于 5 GiB，并连续检查几轮。这个测试里 Stage 0 AR 用可见卡里的逻辑 `0,1`，Stage 1 DiT 用逻辑 `2,3`；例如 `CUDA_VISIBLE_DEVICES=4,5,6,7` 时，AR 落物理 4/5，DiT 落物理 6/7。共享节点会在 gate 之后仍被其他任务抢占，失败时先用 `/proc/<pid>/cwd` 确认进程归属，只清理本次 `<REMOTE_WORK_ROOT>/wt-pr3297-accuracy` 进程组，不能误杀其他人的 `<REMOTE_WORK_ROOT>` 或 `<REMOTE_WORK_ROOT>` 任务。

踩坑记录：

- `<REMOTE_WORK_ROOT>/.venv` 的 vLLM 0.22 会和 PR #3297 代码 ABI 不匹配，报 `split_routed_experts` import error；用 `<REMOTE_WORK_ROOT>/.venv/bin/python3`（vLLM 0.21.0）。
- target deps 放 `<REMOTE_WORK_ROOT>/pydeps-pr3297-accuracy`，至少需要 `FlagEmbedding`、`datasets`、`torchmetrics`；避免覆盖 venv 自带的 `numpy` / `huggingface_hub` 等核心包。
- B3 没有 `cublasLt.h`，默认 FlashInfer MoE JIT 会失败；必须显式 `VLLM_USE_FLASHINFER_MOE_FP16=0` 走 TRITON MoE。
- 不要把 `TMPDIR` 指到 `<REMOTE_WORK_ROOT>/tmp`，ZMQ IPC 会报 `Operation not supported (addr='ipc://<REMOTE_WORK_ROOT>/tmp/...')`；用 `/tmp`。
- PowerShell 到 SSH 的复杂脚本不要嵌套引号直接传。临时 Bash 脚本用本地 LF 文件按已批准的投递方式落到 `/tmp`，远端必须完整执行 [canonical fail-closed 投递门禁](../../remote/guides/debug-basics.md#远端-bash-脚本投递必须失败关闭)，避免空脚本、BOM、CRLF 和变量提前展开。

2026-06-02 跑 PR #3297（head `5b5a4b3850edf88cd84499ff3afbd23874d43a6f`）的有效结果目录：

```text
<REMOTE_WORK_ROOT>/pr3297_accuracy_v21_no_fi_gate6_20260602_193332
```

结果：

| Metric | Value | L20x Reference |
|---|---:|---:|
| COT similarity to reference | 0.9722 | 0.9644 |
| COT prefix match | 29 | 29 |
| Image-Image similarity | 92.5253 | 94.5538 |
| SSIM | 0.2379 | 0.2420 |
| PSNR (dB) | 13.73 | 14.10 |

pytest summary: `1 passed, 19 warnings in 494.51s (0:08:14)`.

## HunyuanImage3 Stage 0 `mm_encoder_attn_backend=TORCH_SDPA` 精度复跑（2026-06-04）

用户要求只在第 0 阶段重跑 `mm_encoder_attn_backend: TORCH_SDPA`，并打印字段确认生效。仍然复用同一条现有 pytest：

```bash
tests/e2e/accuracy/test_hunyuan_image3.py::test_image_to_image_alignment
```

本轮有效口径：

```bash
cd <REMOTE_WORK_ROOT>/wt-pr3297-accuracy
export CUDA_VISIBLE_DEVICES=2,3,5,6
export HUNYUAN_AR_DEVICES=5,6
export HUNYUAN_DIT_DEVICES=2,3
export STAGE0_MM_ENCODER_ATTN_BACKEND=TORCH_SDPA
export VLLM_USE_FLASHINFER_MOE_FP16=0
export HF_HOME=/data/model
unset TRANSFORMERS_CACHE HF_HUB_CACHE
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HUNYUAN_MODEL_PATH=/data/model/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2
export PYTHONPATH=<REMOTE_WORK_ROOT>/pydeps-pr3297-accuracy:<REMOTE_WORK_ROOT>/wt-pr3297-accuracy:${PYTHONPATH:-}
export TMPDIR=/tmp
```

不要用 wrapper import test module 后 monkeypatch `_DEPLOY_CONFIG`：pytest 会重新 import 模块，容易出现 wrapper 看到 `TORCH_SDPA`、真实 pytest 没吃到配置的假阳性。更稳的是对远端 worktree 做临时 on-disk patch，备份原文件，`trap` 里恢复，并在结束后保存 `post_restore.diff`。

必须打印四层证据：

```text
CONFIG_CHECK generated_yaml.stage0.mm_encoder_attn_backend=TORCH_SDPA
CONFIG_CHECK filtered_engine_args.stage0.mm_encoder_attn_backend=TORCH_SDPA
CONFIG_CHECK vllm_config.stage0.model_config.multimodal_config.mm_encoder_attn_backend=TORCH_SDPA
Using AttentionBackendEnum.TORCH_SDPA for MMEncoderAttention.
```

非连续 GPU 可见集要显式写 stage devices。`CUDA_VISIBLE_DEVICES=2,3,5,6` 时，如果只靠默认 Stage 0 `0,1` / Stage 1 `2,3`，Stage 1 会把 `2,3` 当物理卡使用，而 Stage 0 的 `0,1` 也可能 remap 到物理 `2,3`，导致两个 stage 抢同一组卡。解决方式是生成 YAML 时同时打印并设置：

```text
CONFIG_CHECK generated_yaml.stage0.devices=5,6
CONFIG_CHECK generated_yaml.stage1.devices=2,3
```

现有 pytest 的 cleanup 会全局扫描并终止 `vllm` 进程，本轮实际扫到并杀了旧 PID `3657851` / `3659955`。下次在共享节点复跑前，必须先 patch/override cleanup，只清理本轮 runner 进程组或 `/proc/<pid>/cwd` 属于本次 worktree 的进程；不能让测试自己的 cleanup 误杀其他人的 `vllm` 任务。

2026-06-04 跑 PR #3297（head `5b5a4b3850edf88cd84499ff3afbd23874d43a6f`）Stage 0 SDPA 结果目录：

```text
<REMOTE_WORK_ROOT>/pr3297_accuracy_stage0_mm_sdpa_patch3_20260604_113531
```

结果：

| Metric | Value | L20x Reference |
|---|---:|---:|
| COT similarity to reference | 0.9697 | 0.9644 |
| COT prefix match | 37 | 29 |
| Image-Image similarity | 92.6552 | 94.5538 |
| SSIM | 0.2371 | 0.2420 |
| PSNR (dB) | 14.02 | 14.10 |

pytest summary: `1 passed, 19 warnings in 449.44s (0:07:29)`. 临时 patch 已恢复，`post_restore.diff` 为 0 字节。
