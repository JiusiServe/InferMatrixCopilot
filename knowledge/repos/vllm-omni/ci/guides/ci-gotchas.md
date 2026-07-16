vllm-omni CI 上反复踩到的三个具体配置坑——合一篇。

## 1. .gitignore 排 *.json，新增 JSON test config 必须 git add -f

vllm-omni 的 `.gitignore` line 241 有 `*.json`，会忽略所有 JSON 文件。

**Why:** 项目里有大量生成的 JSON（benchmark results 等），所以全局忽略。但 `tests/dfx/perf/tests/*.json` 是手写的 test config，需要被 track。

**How to apply:** 新增 JSON test config 文件时必须 `git add -f <file>` 强制添加，否则 git status 不会显示为 untracked，容易漏提交。

## 2. 单阶段 diffusion pipeline 必须 async_chunk: false

单阶段 diffusion 模型（如 HunyuanImage3 DIT_ONLY）启动时必须加 `--no-async-chunk`，或创建 deploy YAML。

**Why:** `DeployConfig.async_chunk` 默认 `True`。没有 deploy YAML 时用默认值。单阶段 pipeline 没有 next-stage processor，`async_chunk=True` 直接报 `ValueError`。

**How to apply:**
- 永久修法：创建 `vllm_omni/deploy/<model_type>.yaml`，写 `async_chunk: false`
- 临时修法：启动命令加 `--no-async-chunk`
- 判断依据：单阶段 pipeline（只有 DiT，没有 AR→DiT bridge）= 必须 `async_chunk: false`

## 3. Hunyuan perf test 已从 mandatory CI 拆出

PR #2495 把 HunyuanImage3 perf test 从 mandatory "Diffusion X2I(&A&T) · Perf Test" 拆出。

**Why:** Hunyuan 80B MoE 在 CI 4×H100 上 dummy run OOM（原因：多个 parametrized test case 在同一 pytest session 里 server 没杀干净就起下一个，显存叠加爆了）。EXIT5 传播到 Qwen step 的 exit code，导致整个 mandatory step 失败。

**How to apply:**
- Hunyuan perf test 现在是独立 Buildkite step，`soft_fail: true` + `RUN_HUNYUAN_IMAGE3_PERF=1` env gate（默认不跑）
- 模型从 `tencent/HunyuanImage-3.0` 改为 `tencent/HunyuanImage-3.0-Instruct`（CI 节点 HF cache 里有 Instruct，没有 base，避免 30 分钟下载 + startup timeout）
- 原来一个 JSON（3 个 test case）拆成 3 个独立 JSON（tp4_fp8, tp2_fp8_sp2, tp2_fp8_cfgp2），每个 pytest 调用只起一个 server，防止显存残留
- profiling 脚本从 `scripts/profiling/` 移到 `tools/`，shell 脚本改为通用（model 作为 CLI 参数）
