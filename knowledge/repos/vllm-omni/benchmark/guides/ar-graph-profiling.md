# Remote Debug · AR graph serve / profiling 状态机

## 通用 profiling 规则：先读经验，再锁 artifact 契约

这条不只适用于 Hunyuan AR graph；用户说 `profiling`、`trace`、`算子`、`时序图`、`chrome trace`、`Perfetto`、`Nsight` 时，默认目标是 trace artifact，不是 benchmark stats。

开跑前必须先做三步：

1. **读经验**：先读 [profiling 错题](../incidents/_index.md)，再读本文件的 profiling 状态机。遇到相似模型/路径时，再读对应模型的 `history/` 成功案例。禁止不读既有经验就从 CLI / 源码接口重新摸索。
2. **锁 artifact contract**：写清本轮要交付哪类文件。Torch trace 至少要 `trace_rank*.json(.gz)`；Nsight 至少要 `.nsys-rep`。只有 `diffusion_result*.json`、stage duration、吞吐/延迟表时，必须标成 benchmark stats，不准叫 trace profiling。
3. **按状态机推进**：`service ready -> start_profile 200 -> target request done -> stop_profile 200 -> trace exported -> local saved -> resources released`。任一状态缺证据，只能汇报当前状态和 blocker，不能说“跑完了”。

正式交付 profiling 前必须有 trace quality summary：

```text
trace files: trace_rank*.json(.gz) / *.nsys-rep
size: per file
event_count: per rank if JSON trace
coverage: rank / pid / tid
contains: python_function if needed, aten::, CUDA runtime/kernel, NCCL/memcpy when relevant
local artifact path: tar and extracted dir
resource cleanup: this-run PGID gone, GPU/process state checked
```

如果完整请求窗口采集导致 worker 死亡、`/stop_profile` empty reply、trace 没落盘，结论是“完整 trace 采集失败”，不是“换一个短请求/关掉字段后继续当正式结果”。降级为 bounded smoke、关闭 stack/shapes、缩短 output、加 `max_iterations` 前，必须明确这是 plumbing smoke，不能作为用户要的正式 profiling。

## AR graph serve / profiling 必须按状态机推进

**2026-06-05 HunyuanImage3 AR graph profiling 反例 / 修正**：用户要的是 “图模式 + CLI 路径” 的 AR 性能和 trace，不是 offline `end2end.py` profiler，也不是 DiT `/v1/images/*`。正确服务路径是 `vllm serve ... --deploy-config hunyuan_image3_ar.yaml`，客户端打 `/v1/chat/completions`，backend 用 `openai-chat-omni`。

本轮耗时来自三类问题叠加：

1. HunyuanImage3 AR serve 本身启动重：157G checkpoint、KV profiling、torch compile cache load、CUDA graph capture。热缓存后 `torch.compile` 仍有几十秒，完整服务 ready 仍可能 15-25 分钟。
2. profiler 不是 bench 加 `--profile` 就会产 trace；Omni worker 必须在 AR stage config 里提前配置 `profiler_config`，否则 `/start_profile` / `/stop_profile` 是 404。
3. 状态汇报混淆：`trace 已落盘`、`stop_profile 返回`、`bench wrapper 退出`、`服务仍在占 GPU` 是四个不同状态，必须分开报。

### AR-only 口径 gate

AR-only graph + CLI benchmark 必须固定口径：

```text
deploy: hunyuan_image3_ar
endpoint: /v1/chat/completions
bench backend: openai-chat-omni
extra_body: {"modalities":["text"]}
not: /v1/images/generations
not: /v1/images/edits
not: offline examples/offline_inference/.../end2end.py profiler
```

启动前必须显式确认：

```bash
test -f "$CHAT_TEMPLATE"
grep -n "pipeline: hunyuan_image3_ar" "$DEPLOY"
grep -n "enforce_eager: false" "$DEPLOY"
```

不要假设 chat template “默认有”。vLLM 会把 path-like 字符串当路径校验；文件不存在会直接报：

```text
The supplied chat template string (...) appears path-like, but doesn't exist
```

### comprehension stage gate

AR deploy 里 `is_comprehension: true` 可能解析到 stage 的 `engine_args`，而 serving path 可能只读 `stage.is_comprehension`。如果 `/v1/chat/completions` 返回：

```text
No comprehension stage (is_comprehension=True) found in stage configs
```

不要继续调 payload / image / prompt，先做 config parse gate：

```bash
cd "$REPO"
"$PYTHON" - <<'PY'
import os
from vllm_omni.entrypoints.utils import load_and_resolve_stage_configs
_, stages = load_and_resolve_stage_configs(
    "tencent/HunyuanImage-3.0-Instruct",
    None,
    {},
    deploy_config_path=os.environ["DEPLOY"],
)
s = stages[0]
print("stage.is_comprehension", getattr(s, "is_comprehension", None))
print("engine_args.is_comprehension", getattr(getattr(s, "engine_args", None), "is_comprehension", None))
PY
```

结论必须写清：这是 deploy parser / serving consumer contract mismatch，不是 benchmark request schema。

### profiler config gate

要拿 AR torch trace，必须在 AR stage 里加 `profiler_config` 后重新起 serve：

```yaml
profiler_config:
  profiler: torch
  torch_profiler_dir: /tmp/<run_dir>/torch_profiler
  torch_profiler_use_gzip: true
  torch_profiler_with_stack: true
  torch_profiler_with_memory: false
  torch_profiler_record_shapes: true
  torch_profiler_dump_cuda_time_total: true
```

如果目标只是验证 profiler plumbing，可临时把 `torch_profiler_with_stack` / `torch_profiler_record_shapes` 关掉；但这种轻量 trace 不算可交付分析材料。用户要求“能看进程、线程、Python 调用栈、CUDA/aten 细节”的 trace 时，默认必须开 stack + shapes，并接受导出更慢、文件更大。

服务 ready 前必须确认日志里出现：

```text
Omni torch profiling enabled. Traces will be saved to: ...
Profiler endpoints are enabled
Route: /start_profile
Route: /stop_profile
```

如果 bench `--profile` 后日志是：

```text
POST /start_profile HTTP/1.1" 404
POST /stop_profile HTTP/1.1" 404
```

这轮没有 profiler trace；不要去 `/tmp` 里盲找，直接判定服务没开 profiler endpoint，重启带 profiler config 的 AR serve。

### trace quality gate

交付 profiling 文件前，先确认 trace 质量，不要只看文件存在：

```bash
python - <<'PY'
import gzip, json, sys
for path in sys.argv[1:]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("traceEvents", [])
    pids = {e.get("pid") for e in events if e.get("pid") is not None}
    names = [e.get("name", "") for e in events]
    print(path)
    print("events", len(events), "pids", len(pids))
    print("has_python_stack", any(".py(" in n or ".py:" in n for n in names))
    print("has_aten", any("aten::" in n for n in names))
    print("has_cuda", any("cuda" in n.lower() or "kernel" in n.lower() for n in names))
PY "$OUT"/torch_profiler/*/trace_rank*.json.gz
```

验收标准按目标分级：

| 目标 | 合格 trace 应看到 |
| --- | --- |
| worker torch op 分析 | rank0/rank1 trace、`aten::` / CUDA kernel、shape/stack args、`profiler_out_0/1.txt` |
| 截图级 Python flame timeline | Python 函数调用栈、线程/进程长条、scheduler / multiprocessing / queue wait 等 CPU timeline |
| 全进程 serving 分析 | API server、orchestrator、StageEngineCoreProc、Worker_TP0/1、bench client 或 driver 进程都能区分 |
| graph/kernel 分析 | CUDA graph replay / kernel / NCCL / memcpy / stream timeline，而不是只有 Python wait |

本轮 2026-06-05 的废 trace 只满足“worker torch profiler plumbing 通了”：它有 rank0/rank1 worker trace，但没有完整 API server / orchestrator / bench client 多进程视图；轻量配置还关闭了 stack/shape。以后这种不能交付给用户当“分析级 trace”。

如果用户给的目标图像是 Python flame timeline（如 `threading.py::_bootstrap`、`multiprocessing`、`queue.get`、`vllm/engine/...` 长条），不要承诺 torch worker profiler 能复现。应改用全进程 Python tracer（例如 VizTracer/py-spy 类工具，按远端可用性选择）包住 server/worker，或用 Nsight Systems 做 CUDA/NVTX 多进程 trace；必要时同时保留 worker torch profiler 作为 CUDA/aten 辅助视图。

### profiling 状态机

以后 profiling 进度只按下面状态汇报，不准混用“跑完”：

| 状态 | 证据 | 可以怎么说 |
| --- | --- | --- |
| service ready | `/health` 200；profiler run 还要有 `/start_profile` `/stop_profile` routes | 服务已 ready |
| request done | bench progress 100% 或 server 有 `POST /v1/chat/completions ... 200 OK` | AR 请求已完成 |
| trace exported | rank0/rank1 `trace_rank*.json(.gz)` 存在且大小稳定 | trace 已落盘 |
| profiler stopped | server log 有 `Profiler stopped` 且 `/stop_profile ... 200 OK` | profiler 已完整停止 |
| bench done | 无 `vllm bench serve` / bench wrapper 进程，且 bench JSON 存在 | bench 已完整退出 |
| local artifact saved | 本地 tar 和解包目录存在，列出 trace/profiler_out/bench json | 本地已保存 |
| resources released | 本轮 PGID 无进程，`nvidia-smi` 显存归零/系统占用 | 资源已释放 |

查状态模板：

```bash
OUT=/tmp/<run_dir>
date
curl -fsS -m 3 http://127.0.0.1:8091/health && echo HEALTH_OK || echo HEALTH_NOT_READY
ps -eo pid,ppid,pgid,stat,etime,cmd | grep -F "vllm bench serve" | grep -v grep || true
find "$OUT/torch_profiler" -maxdepth 3 -type f -ls 2>/dev/null | sort -k11
ls -lh "$OUT"/ar_profile_request_*/bench_ar_profile_1.json 2>/dev/null || true
grep -n -F "POST /stop_profile" "$OUT/serve.log" | tail -5
grep -n -F "Profiler stopped" "$OUT/serve.log" | tail -5
```

沟通规则：用户问“跑完没有”时，必须用上表回答，不要只说 trace 有了；如果 bench 还在等 `/stop_profile`，明确说“AR 请求已完成，但 bench 未完整退出”。

### artifact / resource 顺序

profile 文件一旦在远端完整，先打单个 tar 包并列内容；不要 `scp -r` 整目录黑盒拷贝。

```bash
OUT=/tmp/<run_dir>
tar -C /tmp -czf "$OUT.tar.gz" "$(basename "$OUT")"
ls -lh "$OUT.tar.gz"
tar -tzf "$OUT.tar.gz" | tail -40
```

推荐顺序：

1. 远端确认 `trace_rank0/1`、`profiler_out_0/1`、bench JSON 都存在。
2. 远端打 tar 并 `tar -tzf` 列内容。
3. 如果 GPU 资源紧张，tar 验证后可以先释放本轮 serve PGID，再下载 tar。
4. 本地下载 tar，解包，列文件和大小。
5. 最终用本轮 PGID 清理服务并查 `nvidia-smi`；如果第 3 步已释放，这一步只做复查。

本地保存后最终汇报必须包含：

```text
local tar: <path>
local extracted dir: <path>
trace_rank0: <path>
trace_rank1: <path>
profiler_out_0/1: <path>
bench json/log: <path>
remote GPU: <nvidia-smi summary>
```

不要在用户要求“释放资源”时只说文件路径；必须实际查 GPU 和 VLLM 相关进程。

### Graph mode profiling：先纯 graph，再包请求窗口

2026-06-08 HunyuanImage3 AR graph serve / profiler 的具体远端参数、artifact、错误签名和指标已经下沉到 [archive/hunyuan/ar_graph_online_profiling_20260608.md](../../models/hunyuan-image3/history/ar-graph-online-profiling-2026-06-08.md)。本页只保留机制。

用户说“图模式 / graph mode / enforce_eager=false”时，先跑最小变量，不要直接上 profiler：

1. 纯 graph serve：只改 graph 开关和必要启动参数。
2. 启动前 gate：`command -v ninja`、`ninja --version`、`command -v vllm`，并记录 `PATH`、`VLLM_CACHE_ROOT`、chat template 绝对路径。
3. READY 阶段证据：device mapping、`enforce_eager=False`、compile/cache 日志、graph capture finished、orchestrator ready、`/health`。
4. 失败时先切 worker root cause，不把所有 `READY` 前失败都写成 timeout。
5. 1 request smoke 过后再 10 request benchmark；smoke 指标和正式 benchmark 指标分开报。

图模式 trace 还要做同轮 provenance gate，避免把 eager trace 和 graph benchmark 混成一个结论：

```text
run dir: <same directory for server log, request json, trace>
mode evidence:
  - server command/log has no --enforce-eager
  - server log has "Model runner: transformer compiled with torch.compile"
request evidence:
  - target request json/log status 200
  - target workload matches user scope
trace evidence:
  - trace_rank*.json(.gz) mtime is after /start_profile and before/after /stop_profile export log
  - profiler_out_* exists when torch profiler writes one
  - event_count / category summary confirms aten + CUDA runtime/kernel
cleanup evidence:
  - actual server PID/PGID gone, not only outer shell PGID
  - GPU memory released or remaining owner identified
```

如果任一项缺失，不能说“开图 profiling 已完成”。只能分别说清楚：graph benchmark 是否完成、trace 是否存在、trace 是否属于 graph mode、资源是否释放。

只有纯 graph 路径可用后，才跑 online profiler。正式 trace 的采集窗口必须包住目标请求，不是 worker iteration 截断窗口：

```bash
# 1. serve 已经 /health=200，且日志有 Profiler endpoints are enabled
curl -fsS -X POST http://127.0.0.1:8091/start_profile \
  -H 'Content-Type: application/json' \
  -d '{"stages":[0]}'

# 2. 发目标 workload 请求：必须是用户要分析的真实请求
# AR chat: /v1/chat/completions + openai-chat-omni
# t2i / it2i: 用对应真实 /v1/images/* 或用户指定脚本，不要拿 random-mm smoke 代替
<run target request/bench>

# 3. 目标请求完成后立刻 stop
curl -fsS -X POST http://127.0.0.1:8091/stop_profile \
  -H 'Content-Type: application/json' \
  -d '{"stages":[0]}'
```

正式 profiler config 默认不要加 `max_iterations`，除非用户明确接受“只采样前 N 个 worker step”。示例：

```yaml
profiler_config:
  profiler: torch
  torch_profiler_dir: /tmp/<run>/torch_profile
  torch_profiler_use_gzip: false
  torch_profiler_record_shapes: false
  torch_profiler_with_memory: false
  torch_profiler_with_stack: true
  torch_profiler_with_flops: false
  torch_profiler_dump_cuda_time_total: false
  ignore_frontend: true
```

如果正式 trace 太大/worker 死亡，先报告“完整请求窗口采集失败”和服务端 root cause；再和用户确认是否降级为 bounded sample。不要自行改短请求或加 `max_iterations` 后把结果当正式 trace。

bounded smoke trace 只能证明 profiler endpoint、rank trace、导出逻辑可用；不能交付为正式性能 trace，也不能拿它解释完整请求窗口。正式 trace 验收要按 event 维度，而不是按“有文件”验收：原始 trace size、event_count、category_top、pid/tid_count、rank 覆盖、CUDA runtime/kernel/NCCL/vLLM/Omni category 都要列出来。

`/stop_profile` 返回成功也不等于资源释放；必须按本页 artifact / resource 顺序清 PGID、查残留 worker PID、复查端口和 GPU。
