---
title: "CI 环境与基础设施坑（runbook 汇编）"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, ci]
sources: ["vllm-omni-rebase-agent@122a9468:agent/skills/fix-bitsandbytes-libnvjitlink-ld-library-path/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/fix-flashinfer-jit-cache-version-mismatch/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/buildkite-skipped-build-rebuild-fratricide/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/fix-watchdog-non-fatal-false-positive/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/entrypoint-h100-timeout-1800s-runner-mismatch/SKILL.md"]
---

# CI 环境与基础设施坑（runbook 汇编）

环境/镜像/管线层面的坑——与 [ci-gotchas](ci-gotchas.md)（仓库配置坑）分工。
运营 runbook 以 rebase-agent 仓库为准，本页是知识树沉淀快照（2026-07-16，
agent @122a9468；skills 工作树含未提交遥测更新，快照以工作树为准）。

## 1. libnvJitLink.so.13 需 ldconfig 注册（CUDA-13 wheels × CUDA-12 基镜像）

skill 元数据：`fix-bitsandbytes-libnvjitlink-ld-library-path`，
modules=[worker_runner, model_executor]，status=active，run_count=62（本汇编最高），
2026-06-09 创建 / 07-11 最后使用。

- 症状（运行时）：CI 日志 `libnvJitLink.so.13: cannot open shared object file` /
  `OSError: libnvJitLink.so.13`，随后 `Diffusion worker(s) died unexpectedly`；
  **单卡过、多卡（spawn worker）挂**。症状（构建时，v0.24.0+/CUDA-13）：镜像构建在
  nvjitlink 步骤失败 `No solution found ... nvidia-cuda-nvjitlink-cu13 was not
  found in the package registry`（该包名不存在）。
- 诊断：核对基镜像 toolkit 与 wheels 的 CUDA 大版本——v0.24.0 基镜像
  `/usr/local/cuda` 是 CUDA **12**，cu130 torch/vllm wheels 需要 `.so.13`；该库
  **不在** `/usr/local/cuda/...`，只在 `nvidia-nvjitlink` pip 包里；cu130 torch
  force-reinstall 已带入 `nvidia-nvjitlink==13.0.88`（构建日志 torch 步可见），
  库在、只是不在动态加载路径上。
- 修法：`docker/Dockerfile.ci` 在 cu130 torch force-reinstall **之后**，find 定位
  已装库并用 ldconfig 注册（不要硬装包）：

  ```dockerfile
  RUN NVJITLINK_LIB="$(find / -name 'libnvJitLink.so.13*' 2>/dev/null | head -1)" && \
      if [ -z "$NVJITLINK_LIB" ]; then \
          uv pip install --system "nvidia-nvjitlink-cu13" && \
          NVJITLINK_LIB="$(find / -name 'libnvJitLink.so.13*' 2>/dev/null | head -1)"; \
      fi && \
      test -n "$NVJITLINK_LIB" && \
      dirname "$NVJITLINK_LIB" > /etc/ld.so.conf.d/nvjitlink-cu13.conf && \
      ldconfig && \
      echo "Registered ${NVJITLINK_LIB} with ldconfig"
  ```

  ldconfig 系统级生效、能活过子进程 env 重置（spawn worker），比 LD_LIBRARY_PATH
  稳。未来 CUDA-14 基镜像：`.so.13`→`.so.14`、`-cu13`→`-cu14`。
- 验证：`docker build -f docker/Dockerfile.ci .` 打出
  `Registered /.../libnvJitLink.so.13 with ldconfig`（无 "not found in the package
  registry"）；运行时多卡 diffusion 测试不再 OSError。
- 禁止：装 `nvidia-cuda-nvjitlink-cu13`（多了 `cuda-`，包名不存在；且无条件安装
  冗余——torch 依赖已带库）；当基镜像 toolkit 与 wheels 的 CUDA 大版本不一致时
  依赖 `ENV LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib`（CUDA-12 基
  镜像根本没有 `.so.13`，静默失效——该做法只在基镜像已带所需 `.so.N` 时可用）。
  ^[SK-fix-bitsandbytes-libnvjitlink-ld-library-path]

## 2. flashinfer-jit-cache 版本陈旧 → 全部 TP worker 启动即死（vLLM 0.25）

skill 元数据：`fix-flashinfer-jit-cache-version-mismatch`，
modules=[worker_runner, model_executor]，status=active，run_count=1，2026-07-12 创建 / 07-12 最后使用。

- 症状：worker 栈止于 `flashinfer/jit/env.py: _get_aot_dir` 的
  `RuntimeError: flashinfer-jit-cache version (A) does not match flashinfer
  version (B)`；import 链 vLLM 0.25 `cuda_communicator.py` →
  `flashinfer_all_reduce` → `import flashinfer.comm`，**所有 TP worker 一起死**，
  引擎报 `Orchestrator initialization failed` / `Rank 0 scheduler is dead` /
  EOFError；硬失败前有 `WARNING "FlashInfer is unavailable; falling back"`。
- 诊断：`pip list | grep -i flashinfer` 出现三个包且 `flashinfer-jit-cache` 版本 ≠
  `flashinfer-python`；对照 upstream 期望
  `git show <vllm-tag>:requirements/cuda.txt | grep flashinfer`——v0.25.0 只 pin
  `flashinfer-python==0.6.13` 与 `flashinfer-cubin==0.6.13`，**没有** jit-cache
  pin；venv 里的 jit-cache 是早期手装残留。
- 修法：卸载残留包（不要用 FLASHINFER_DISABLE_VERSION_CHECK 绕过——那会让错配的
  缓存 kernel 继续生效），skill 原文命令（本机 venv 解释器）：
  `/rebase/.venv/bin/pip uninstall -y flashinfer-jit-cache` 后
  `/rebase/.venv/bin/python -c "import flashinfer.comm; print('ok', flashinfer.__version__)"`。
  没有 jit-cache 时 flashinfer 用匹配的 `flashinfer-cubin`（与 CI 镜像一致），
  kernel 选择对齐 CI。
- 验证：`import flashinfer.comm` 成功；此前失败的引擎启动（如 TP>1 deploy 的
  `examples/offline_inference/hunyuan_image3/end2end.py`）到达 "Loading
  safetensors" 并完成（2026-07-12 在 vLLM 0.25.0rc4.dev1+gdd10e03f9 的
  HunyuanImage3 golden 重基线期间验证）。
- 禁止：设 `FLASHINFER_DISABLE_VERSION_CHECK` 压错误（错配 kernel 可能加载、数值
  偏离 CI）；手工把 jit-cache pin 到匹配版本（upstream 对本栈不 ship/不 pin 它，cubin 才是
  受支持且漂移更小的工件）；重装 vllm/vllm-omni（引擎没坏，只是多了个陈旧包）。
  ^[SK-fix-flashinfer-jit-cache-version-mismatch]

## 3. Buildkite skipped-build / rebuild 互杀（fratricide）

skill 元数据：`buildkite-skipped-build-rebuild-fratricide`，modules=[]，
status=active，run_count=4，2026-07-11 创建 / 07-11 最后使用。

- 症状：build state=`skipped`/`not_run` 且只有 0-1 个 job；监控对着
  ":pipeline: Load pipeline" 卡数小时；一个 running build（常为定时 nightly）显示
  `canceled` 且 `finished_at` 与另一 build 的 `created_at` 相差 ~1s 内；
  "Incremental rebuild triggered" 但被观察的 build 状态永不变。
- 诊断：1) `GET /v2/organizations/vllm/pipelines/vllm-omni-rebase/builds/<N>`——
  `skipped`/`not_run` 意味着管线**拒绝**运行它，永远不会出 job：别再轮询、别把
  Load-pipeline job 当可重试的 incomplete。2) 列同 commit 的兄弟 build
  （**必须全长 40 位 SHA——短 SHA 静默返回空**）：
  `GET .../builds?branch=<branch>&commit=<full-sha>`；典型模式：我们的 `api` build
  `skipped`、一个 ~0.5s 后创建的 `webhook` build `not_run`（正是它 skip 了我们的）、
  可能还有真正跑起来的 `schedule`/后续 `api` build。3) 确认互杀：比对被 cancel
  build 的 `finished_at` 与分支上每个 build 的 `created_at`——差距 <~1s 即新 build
  的创建 cancel 了它（2026-07-11 实证：rebuild #2629 创建 200ms 内 cancel 了运行中
  nightly #2627，#2630 创建又 cancel 了运行中的 #2629）。4) 根因是管线配置：
  `skip_queued_branch_builds=true` **且** `cancel_running_branch_builds=true` 且
  分支过滤为空，作用在默认分支 `dev/vllm-align`（88-job 全量套件）上。
- 修法（代码侧，落在 feat/knowledge-layer 提交 8ae5268 + 8c1f8d2——重实现前先确认
  已存在）：1) `skipped`/`not_run` 立即视为终态（monitor 的 `BUILD_NO_RUN_STATES`；
  `MonitorReport.was_skipped` 阻断 `is_clean_pass`）；2) push 后**等 ~60s** 再
  `create_build`，让 webhook build 先落地（我们的 API build 成为最新、不被 skip；
  等待逻辑在 `phase4.py`，标识 "webhook build to settle"）；
  3) 仍落入 no-run 态时收养真正在跑的兄弟 build
  （`find_build_for_commit(full_sha, branch, exclude_numbers=(ours,))`）；
  4) 永不 `PUT /rebuild` 一个 no-run build、永不在**别的 commit** 的 build 运行时
  rebuild（创建即 cancel 它）、rebuild 触发后监控 response body 里的**新 build
  URL**（不是原 URL）。管线侧（真正的修复，需管理权限）：给 `skip_queued_branch_builds_filter` 与
  `cancel_running_branch_builds_filter` 设排除 `dev/vllm-align` 的过滤（如
  `!dev/vllm-align`），或关掉 `cancel_running_branch_builds`。
- 验证：`pytest agent/tests/test_phase34_fixes.py -q`（skipped-terminal、
  sibling-adoption、fratricide-guard、rebuild-follows-new-build 四类测试过）；
  Phase-4 push+trigger 后日志出现我们 build 的 `state=running...` 或
  `Adopting sibling build #<M>`，不再对 `skipped` build 挂 `still ...` 数小时；
  分支上没有 build 的 `canceled finished_at` 落在 agent 创建的 build ~1s 内。
- 禁止：轮询 no-run build 到超时/把它的 Load-pipeline job 当 incomplete
  （07-07/07-09 两轮烧了 6-9h）；rebuild skipped build "重试 flaky"（新 build 的
  创建 cancel 了正在跑的 nightly #2627）；rebuild 后监控原 URL（#2629/#2630 全量
  跑完无人观察，agent 盯着 skipped #2625）；用短 SHA 查 `builds?commit=`（返回空
  像"没有兄弟"）；到 vllm-omni 或 agent 测试逻辑里"修"它——纯管线配置 + 触发时序
  问题。^[SK-buildkite-skipped-build-rebuild-fratricide]

## 4. watchdog 大小写误报（agent 基础设施注记）

skill 元数据：`fix-watchdog-non-fatal-false-positive`，modules=[scheduler]，
status=active，run_count=5，2026-07-08 创建 / 07-11 最后使用。属 rebase-agent 自身
watchdog 的坑，非 vllm-omni 仓库问题——收录以防误归因。

- 症状：rc=143/SIGTERM；**查日志尾部**的 watchdog 消息 `[watchdog] CRITICAL error
  detected: ...`，指向一个测试名，其子串
  大小写不敏感地命中 Tier-1 模式（如 `non_fatal` 命中 `FATAL`）；**所有单测其实
  PASS**。
- 诊断/修法：单独重跑该测试（`cd /rebase/vllm-omni && python -m pytest <test_path>
  -xvs`）确认无真实失败；
  把子串加进 `agent/lib/test_watchdog.sh` 的 `WATCHDOG_SIMULATION_ALLOWLIST`
  （带原因注释，如 `"non_fatal"  # test_non_fatal_* 命中 Tier-1 "FATAL"`）。
- 验证（skill 原文）：`cd /rebase/vllm-omni-rebase-agent && source
  agent/lib/test_watchdog.sh` 后执行
  `_is_simulated_test_error "<matched_line>" "<test_group_name>" && echo "IGNORED - CORRECT"`；
  且受影响测试单独重跑通过。^[SK-fix-watchdog-non-fatal-false-positive]

## 5. entrypoint 超时 = 预算问题，不是代码 bug

skill 元数据：`entrypoint-h100-timeout-1800s-runner-mismatch`，
modules=[online_serving]，status=active，run_count=55，2026-06-06 创建 / 07-12
最后使用。

- 症状：`entrypoint_test_with_h100` / `entrypoint_test_with_l4` 超时——本地
  exit_code=124 或 Buildkite job `timed_out`；**已执行的测试全部 PASS（0 FAILED）**，
  日志到被杀前一直有新输出（model loading/warmup）。若输出在被杀前早已静默，
  那是 HANG（另一类问题，要真调试）。本地再查 `TIMEOUT: test ... exceeded NNNs`：
  NNN < 7200 说明 phase3.py 吃到了 stale 的 env 值；CI 则对照 job 时长与
  `.buildkite/test-merge.yml` 的 `timeout_in_minutes`（恰好在预算处被杀）。
- 根因：entrypoint 套件每个 test class 重启一个 OmniServer（H100 上 ~30 次模型
  加载，其中 sleep-mode 测试含十次 ~27.5 GiB 的 Bagel 加载）；checkpoint 加载 I/O
  随节点 page-cache 状态大幅波动——同一 H100 job 的 `Model loading took` 总和实测
  34–43 分钟浮动（builds 2648/2650/2651/2655；**main 也超时**，不是 rebase 或 vLLM
  版本回归，wheel 间 prefetch 行为一致）。按快情形设的预算在慢情形必炸。
- 修法（本地三层全部 7200s）：1) `agent/orchestrator.py` 在
  `_export_all_settings(settings)` 后 `os.environ["TEST_TIMEOUT_SEC"]="7200"`；
  2) `agent/config.sh`：`CI_TEST_TIMEOUT_SEC["entrypoint_test_with_h100"]=7200` +
  默认 `TEST_TIMEOUT_SEC="${TEST_TIMEOUT_SEC:-7200}"`（bash 层 test.sh 实际执行
  `timeout "$job_timeout"`，取值链 `CI_TEST_TIMEOUT_SEC[$key]:-$TEST_TIMEOUT_SEC`）；3) `phase3.py
  _run_single_test()` 强制 `env["TEST_TIMEOUT_SEC"]="7200"`；另
  `test_omni_sleep_mode.py` 的 llm_engine fixture `init_timeout=900`。
  CI 层：`.buildkite/test-merge.yml` 的 `timeout_in_minutes`——2026-07-12 起
  H100=90 / L4=45（PR #5038 align / #5039 main）；L4 job 冷镜像拉取额外 ~11 分钟。
  monitor 已把"仍在推进的超时"自动分类为 `budget_timeout`
  （`agent/buildkite/monitor.py::_is_budget_timeout`）且不派 debug agent——
  Phase-4 报告里见到 `budget_timeout`，修的是管线 YAML 不是代码。
- 验证：本地 `bash agent/tasks/90_run_pipeline_tests.sh entrypoint_test_with_h100`
  在 H100 上 ~60-70 分钟全过；CI entrypoint job 在新预算内完成（验证 build：
  vllm-omni-rebase #2659）。
- 禁止：对全绿超时 job 派代码 debug agent（build 2655 白改了
  `qwen3_code_predictor.py` 一轮）；重跑赌 runner I/O（一小时一掷的硬币）；用被
  GPU 门禁 skip 的测试"验证"修复（需 4 卡只有 2 卡时 skip 证明不了任何事——
  phase3.py `_shell_skipped` 时间戳前缀 bug 已修，2026-07-12）；用单次 build 断言
  wheel 版本背锅（先拉多个 build 的 `Model loading took` 分布）。
  ^[SK-entrypoint-h100-timeout-1800s-runner-mismatch]

## 6. GPU 资源竞争 OOM（基础设施，非代码）

debug-memory 记录 #447（key=`test_abort_cuda_oom_gpu_contention`，
module=input_output，status=active，run_count=1）：`test_async_omni_engine_abort.py::test_abort` 报
`RuntimeError: Engine core initialization failed`，根因 CUDA OOM——GPU 0 共
139.81 GiB，但别的进程（PID 211293）已占 31.11 GiB；测试模型
（Qwen2.5-0.5B-Instruct）加载到 GPU 时撞上已被占用的显存。**无代码修复**——纯基础设施问题，跑前清理 GPU；
其余 191 个测试全过。判定要点：先查同卡他进程占用，再谈代码。^[DM-447]

## 症状索引（正文在 owner 页）

| 症状 | 去哪里 |
|---|---|
| 多 stage 共卡加载期 OOM（`create_weights`） | [Config 规则 CONF-1a](../../components/config/rules.md) |
| voxcpm2 L4 decode 期静默后被杀 | [Config 规则 CONF-2a](../../components/config/rules.md) |
| 并发小 token 预算 GPU hang | [Scheduler 规则 SCHED-2a](../../components/scheduler/rules.md) |

## 相关

- 仓库配置坑见 [ci-gotchas](ci-gotchas.md)；分级与管线见
  [test-tiers](test-tiers.md) / [buildkite-structure](buildkite-structure.md)；
  精度失败先归因见 [accuracy-attribution](accuracy-attribution.md)。
