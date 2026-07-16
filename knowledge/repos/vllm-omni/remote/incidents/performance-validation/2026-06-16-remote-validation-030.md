# 2026-06-16 — LTX2.3 PR #4464 性能看护验证多次跑偏

- 编号：`inc-2026-06-16-remote-validation-030`
- 归属：`repos/vllm-omni/remote`
- 状态：已验证
- 搜索词：LTX2.3 PR #4464 性能看护验证多次跑偏
- 影响范围：repos/vllm-omni/remote

**症状**：用户要求 LTX2.3 T2V L4 perf PR #4464 用官方固定 prompt 重新跑 `e2e_latency_ms`、`throughput_qps` 和 profiling。过程中连续出现多个低级问题：先没有直接基于 PR #4464 head 跑；远端使用了错误的 `HF_HOME=<REMOTE_WORK_ROOT>/hf-home`；offline 模式下用模型 id 触发 tokenizer hub lookup 失败；fixed prompt 先落成被 `.gitignore` 命中的 `tests/dfx/perf/tests/data/*.jsonl`；runner 子进程 cwd 不同导致相对 `dataset-path` 找不到文件；GPU0 被别人进程占用后仍尝试启动导致 OOM；跑完后还残留了本轮 profiling/serve 进程，需要补清理。

**实际有效结果**：

```text
PR head: 6372f0dee3bd2aa446480f8a7ad101ba4bc34be1
vllm: 0.23.0
HF_HOME: /data/models
HF_HUB_CACHE: /data/models/hub
snapshot: /data/models/hub/models--dg845--LTX-2.3-Diffusers/snapshots/01fc4e67e5c88bf8c44f5217b9669b7e496fb985
GPU: CUDA_VISIBLE_DEVICES=6
baseline artifact: <REMOTE_WORK_ROOT>/ltx23_t2v_pr4464_official_prompt_inline_gpu6_20260616_140355/results/diffusion_result_test_ltx2_3_vllm_omni_snapshot_20260616-140420.json
throughput artifact: <REMOTE_WORK_ROOT>/ltx23_t2v_pr4464_throughput_inline_gpu6_20260616_140641/results/diffusion_result_test_ltx2_3_vllm_omni_snapshot_20260616-140703.json
```

Baseline fixed-prompt result:

```text
workload: /v1/videos, 512x384, 25 frames, 20 steps, max_concurrency=1, 3/3 completed
throughput_qps: 0.1663
latency_mean: 6.0142s
peak_memory_mb_max: 73290
stage_0_gen_ms mean: 5123.98
text_encoder.forward mean: 142.31ms
vae.decode mean: 8.81ms
serving path: pure diffusion mode, single diffusion stage
attention: DIFFUSION_ATTENTION_BACKEND=FLASH_ATTN
```

**问题链路和根因**：

1. **没有先锁 PR head**：用户已经给了 PR #4464，正确动作应该是远端 `git fetch origin pull/4464/head` 并记录 `HEAD`。我先绕到本地/临时配置和旧分支判断，导致用户质疑“为什么不直接用 PR 跑”。根因是没有把“PR head 是唯一被测对象”写成 scope lock。
2. **HF cache 路径凭旧印象写错**：我临时设置了 `<REMOTE_WORK_ROOT>/hf-home`，没有先查 live env 或正在跑进程的 `/proc/<pid>/environ`。真实 cache 是 `HF_HOME=/data/models`、`HF_HUB_CACHE=/data/models/hub`。这违反了 `Live facts > knowledge`。
3. **模型 id 和 offline snapshot 混淆**：PR 配置里保留 `dg845/LTX-2.3-Diffusers` 是对的，但远端 offline 测量时模型 id 会在 `AutoTokenizer.from_pretrained(..., subfolder="tokenizer", local_files_only=True)` 查询 repo-root config 并失败。正确测量方式是先做 tokenizer gate，确认模型 id 失败、绝对 snapshot 成功，然后仅在临时测量 config 中把 `model` 改成 snapshot。
4. **数据集路径没过 cwd gate**：fixed prompt 先用 `dataset-path: tests/dfx/perf/tests/data/...`，但 runner 启动 benchmark 子进程时 cwd 是 `$WT/tests`，相对路径变成 `$WT/tests/tests/dfx/...`。此外 `tests/dfx/perf/tests/data` 被 `.gitignore` 的 `data/` 规则影响，需要 `git add -f`。正确做法是复用现有 Hunyuan perf 的 `dataset-path-inline`，让 runner 生成临时 JSONL。
5. **没有先验证远端 remote 能不能用 Taffy alias**：远端没有 `github-taffy` SSH alias，第一次 fetch fork branch 失败。正确方式是对 public PR 直接 fetch upstream `pull/<id>/head`，不要依赖本机 SSH alias。
6. **GPU ownership gate 做晚了**：GPU0 初始空闲，但后来被 `<REMOTE_WORK_ROOT>/scripts` 进程占用 125GB，我没有在重跑前重新查 `nvidia-smi` + `/proc/<pid>/cwd`，导致 OOM。正确处理是每次启动前都重查 compute apps，且只能选择当前空闲 GPU；占用方不是本轮 cwd 时禁止 kill。
7. **cleanup gate 不够前置**：throughput 后发现本轮还有 `<REMOTE_WORK_ROOT>/wt-ltx23-t2v-profile` cwd 的 serve/worker 进程，占用 GPU4。虽然最后按 cwd/PID 清了，但应该在每轮 pytest 结束后立即检查并清理本轮进程。
8. **PR body provenance 滞后**：PR body 里一度还写旧 head 和旧 profiling 值。性能 PR 体必须在最终跑完后按 head SHA、artifact path、completed/failed、metric 同步更新，不应保留旧证据。

**硬规则**：

1. L4 perf PR 远端验证前 5 分钟必须写 scope lock：
   ```text
   PR:
   PR head SHA:
   vllm version:
   public config path:
   measurement-only patch:
   HF_HOME / HF_HUB_CACHE:
   snapshot:
   GPU:
   target tests:
   artifact root:
   valid metrics:
   stop condition:
   ```
2. public PR 测试必须先直接 fetch PR head：
   ```bash
   git fetch origin pull/<PR>/head:refs/remotes/origin/pr-<PR>
   git checkout -B <local-branch> refs/remotes/origin/pr-<PR>
   git rev-parse HEAD
   ```
   除非用户明确要测 fork 私有 branch，否则不要依赖远端是否配置 `github-taffy`。
3. HF gate 必须一次性输出：
   ```bash
   env | grep -E 'HF_HOME|HF_HUB_CACHE|TRANSFORMERS_CACHE|HF_HUB_OFFLINE|TRANSFORMERS_OFFLINE|CUDA_VISIBLE_DEVICES'
   test -d "$SNAP"
   readlink -f "$SNAP"
   python - <<'PY'
   from transformers import AutoTokenizer
   AutoTokenizer.from_pretrained(SNAP, subfolder="tokenizer", local_files_only=True)
   PY
   ```
   `HF_HOME` 不能凭记忆；没有 live evidence 禁止启动模型。
4. public config 和 measurement config 要分开：
   ```text
   public config: model id, repo-relative semantics, reviewer/CI-facing
   measurement config: absolute snapshot path only, offline/cache-facing
   ```
   最终 PR body 必须说明测量用的是同一 PR head，只替换了本地 snapshot 以满足 offline cache gate。
5. DFX perf custom dataset 默认用 `dataset-path-inline`。如果必须用 `dataset-path`，要先证明 benchmark 子进程 cwd 下能读到：
   ```bash
   python -c 'from pathlib import Path; print(Path("<dataset-path>").resolve(), Path("<dataset-path>").exists())'
   ```
   并检查该路径不被 `.gitignore` 意外吞掉。
6. 每次启动前重新做 GPU ownership gate：
   ```bash
   nvidia-smi --query-gpu=index,uuid,memory.used,memory.total --format=csv,noheader,nounits
   nvidia-smi --query-compute-apps=pid,process_name,gpu_uuid,used_memory --format=csv,noheader,nounits
   for pid in <candidate-pids>; do readlink -f /proc/$pid/cwd; ps -ww -p $pid -o pid,ppid,pgid,etime,cmd; done
   ```
   只选择空闲 GPU；非本轮 cwd 的进程一律 `KEEP`。
7. 每轮 pytest/benchmark 结束后立刻 cleanup gate：
   ```bash
   for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits); do
     cwd=$(readlink -f /proc/$pid/cwd 2>/dev/null || true)
     case "$cwd" in "$WT"*|"$OUT"*) echo DELETE; kill -TERM "$pid" ;; *) echo KEEP ;; esac
   done
   ```
   清理后必须确认目标 GPU 回到空闲。
8. 只有 `completed == num_prompts`、`failed == 0`、result JSON 非 fallback、日志显示真实请求完成，才允许汇报 `throughput_qps`、`e2e_latency_ms`、profiling mean。`fallback template` 或 `completed=0` 必须标成无效。
9. PR body 更新前必须做 provenance gate：
   ```text
   gh pr headRefOid == remote run HEAD
   artifact path exists
   result JSON rows completed/failed valid
   prompt/config matches PR intent
   private debug failures not included
   ```

**下次 LTX/DFX perf 固定流程**：

```text
1. Fetch PR head from upstream PR ref; print SHA.
2. Read config; print test names, model, dataset fields, workload.
3. Live env gate: venv versions, HF env, snapshot, tokenizer from snapshot.
4. GPU ownership gate; pick one free GPU.
5. Create measurement-only config under OUT; only replace model id with absolute snapshot if offline requires it.
6. Run one target pytest test first, not full sweep.
7. Extract result JSON with completed/failed/qps/latency/profiling.
8. Run remaining target sweep only after first result is valid.
9. Cleanup by cwd/OUT ownership.
10. Update PR body with only valid evidence.
```

**怎么避免**：这类任务不能把“我能把服务起起来”当进展。进展只按三件事算：当前 PR head 是否被测、目标 workload 是否有效完成、result/profiling 是否可发布。任何一步失败，先修 scope/gate，不要继续换路径、换 cache、换 GPU 做无约束探索。
