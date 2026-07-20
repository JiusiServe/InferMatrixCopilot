---
title: "跨模型与模块的近期 review/fix 样本"
created: 2026-07-20
updated: 2026-07-20
type: history
tags: [vllm-omni, review, models, runtime]
sources: ["PR #3576", "PR #3642", "PR #4106", "PR #4281", "PR #4341", "PR #4718", "PR #4730", "PR #5001", "PR #5031", "PR #5088"]
confidence: high
---

# 跨模型与模块的近期 review/fix 样本

采集日期：2026-07-20。仅记录已合入 PR 中能沿原始 commit、review comment 和后续修复 commit 对齐的结论。

## PR #5001 — Cosmos3 Edge / Distilled

- `5c4baf2b`/`371cc41b`：Edge UND tower 漏掉 layerwise-offload block 声明；distilled scheduler 未强制 stochastic sampling；pipeline 通过修改全局 RNG 实现逐步重加噪，并发请求会互相干扰；`0.0` guidance 在 request `__post_init__` 中被当作未提供。
- `bce4727e` 回应上述评论：补 offload 属性和测试，强制/验证 scheduler 参数，并把 generator 传到 step。该链也暴露 diffusers 0.38 不消费 generator、0.39 才修复的版本边界，随后形成 PR #5176。
- 支持表最初把未发布的 Edge 标成完整支持但没有命令、延迟、显存和输出证据；`7d520945` 先移除文档宣称，待 checkpoint 可验证后再恢复。
- 证据：[offload contract](https://github.com/vllm-project/vllm-omni/pull/5001#discussion_r3575535537)、[scheduler mode](https://github.com/vllm-project/vllm-omni/pull/5001#discussion_r3575535977)、[request-local RNG](https://github.com/vllm-project/vllm-omni/pull/5001#discussion_r3575536250)、[zero sentinel](https://github.com/vllm-project/vllm-omni/pull/5001#discussion_r3575536706)、[support evidence](https://github.com/vllm-project/vllm-omni/pull/5001#discussion_r3570724994)。

## PR #4730 — Krea 2 text-to-image

- 初始接入只覆盖 offline，却在 PR 中宣称 `vllm serve`/images endpoint；review 要求 online e2e。文档同时勾选 HSDP、layerwise offload、VAE patch parallel，但没有逐项证据。
- loader 未给 text encoder/VAE 传 `torch_dtype=od_config.dtype`，会默认 fp32、放大显存并制造 dtype mismatch；为读取 `vae/config.json` 使用全权重下载模式，会同步阻塞启动。
- 后续 `f51f81ae` 补 online serving 和分布式测试；review 后改成精确 config 获取、传递 dtype，并收紧无证据的 capability 宣称。
- 证据：[online coverage](https://github.com/vllm-project/vllm-omni/pull/4730#discussion_r3521676092)、[capability evidence](https://github.com/vllm-project/vllm-omni/pull/4730#discussion_r3534268336)、[config-only fetch](https://github.com/vllm-project/vllm-omni/pull/4730#discussion_r3534268331)、[loader dtype](https://github.com/vllm-project/vllm-omni/pull/4730#discussion_r3534268332)。

## PR #3642 — MiniCPM-o 4.5

- API server 曾无条件 `trust_remote_code=True`，绕过用户安全选择；`a83e8bcb` 改为受 CLI 解析值控制。TTS 依赖只写文档、初始化异常被吞后返回空音频，最终 `fd8336ae` 声明 extra，`4ddafeb0` 对非 import 初始化失败 fail loudly。
- pipeline 只按通用 `MiniCPMO` architecture 匹配，可能把 1.0/2.6 路由到 4.5；`13663b4a` 增加 HF config predicate。
- talker stage 声明批量并发却只消费 `runtime_info[0]`，存在请求 0 音频广播给其他请求的风险；`5960db3a` 先把 `max_num_seqs` 收紧为 1。
- 直接 TTS class 不读取 runner bridge 字段，且 tuple waveform 会被 runner 当 hidden state；`fb6abc24` 改由 wrapper 接收 runtime info 并包装 `OmniOutput`。
- 证据：[remote-code gate](https://github.com/vllm-project/vllm-omni/pull/3642#discussion_r3254188999)、[batch contamination](https://github.com/vllm-project/vllm-omni/pull/3642#discussion_r3294149293)、[registry collision](https://github.com/vllm-project/vllm-omni/pull/3642#discussion_r3294149294)、[bridge wiring](https://github.com/vllm-project/vllm-omni/pull/3642#discussion_r3294814659)、[output packaging](https://github.com/vllm-project/vllm-omni/pull/3642#discussion_r3294814661)。

## PR #4341 — Ming-Omni-TTS MoE / CFM CUDA Graph

- graph sampler 最初把整个 10-step ODE solve 放在 bf16；eager 则保持 noise、timesteps、SDE 和积分为 fp32，只在 DiT forward 边界 cast。`05279f14` 恢复相同 dtype 边界。
- graph 路径遗漏 eager 的 `cfg < 1e-5` unconditional 分支，`8bd1a553` 对该边界回退 eager；`0054b46b` 又修正最后一步 SDE shift，匹配 `Solver.integrate`。
- MoE 类顶层 import 会让缺少新 vLLM 模块的 dense Ming-TTS 也无法 import；`add586b8` 移到 MoE 分支内 lazy import。
- 证据：[fp32 solver](https://github.com/vllm-project/vllm-omni/pull/4341#discussion_r3394171867)、[CFG zero](https://github.com/vllm-project/vllm-omni/pull/4341#discussion_r3394171875)、[lazy import](https://github.com/vllm-project/vllm-omni/pull/4341#discussion_r3394182443)、[last-step parity](https://github.com/vllm-project/vllm-omni/pull/4341#discussion_r3468496305)。

## PR #5031 — legacy stage config 迁移

- Step-Audio2 最初为 async chunk 建独立 pipeline，review 要求同一冻结 topology 同时携带 sync/async processor，由 deploy flag 决定 wiring，避免重复 YAML 漂移。
- model package `__init__` 不应做重 import；pipeline config 不应绑定 FP8 等 deploy acceleration；发现的 payload contract bug 与 config migration 没有直接依赖时要明确 scope。
- 迁移后的 TP=2 stage 0 在 GPU 1 预留 0.8，stage 1 又在同卡预留 0.3，预算和为 1.1；`f327ea8f` 后修正设备/利用率。
- 证据：[single topology](https://github.com/vllm-project/vllm-omni/pull/5031#discussion_r3568048774)、[lightweight init](https://github.com/vllm-project/vllm-omni/pull/5031#discussion_r3568075526)、[pipeline/deploy boundary](https://github.com/vllm-project/vllm-omni/pull/5031#discussion_r3568085862)、[scope coupling](https://github.com/vllm-project/vllm-omni/pull/5031#discussion_r3568111107)、[device budget](https://github.com/vllm-project/vllm-omni/pull/5031#discussion_r3581697640)。

## PR #4281 — composable parallel strategy

- Phase 1 spec 暴露 11 种 axis，但只有部分能翻译；review 要求区分 wired/reserved 并让 unsupported axis 明确失败。示例中的 CLI LB policy 又与 strategy routing 自动推导冲突。
- 测试用 deploy 文件不存在时 conditional skip 会把路径漂移隐藏为绿灯；后续删除 skip。headless serve 漏传 `--stage-overrides`，相同命令会和标准路径解析出不同拓扑；`7eb96015` 统一转发。
- stage 以 index 寻址在 pipeline 变体或拆分后不稳定，review 倾向使用必填且可读的 `model_stage` 名称。
- 证据：[axis contract](https://github.com/vllm-project/vllm-omni/pull/4281#discussion_r3385158757)、[LB source](https://github.com/vllm-project/vllm-omni/pull/4281#discussion_r3385158754)、[fail instead of skip](https://github.com/vllm-project/vllm-omni/pull/4281#discussion_r3478411116)、[stable stage identity](https://github.com/vllm-project/vllm-omni/pull/4281#discussion_r3478438959)、[headless parity](https://github.com/vllm-project/vllm-omni/pull/4281#discussion_r3496170565)。

## PR #4718 — chat audio format

- `audio.format` 来自 extra body，没有 Pydantic 前置校验。旧实现可能先发出完整文本 SSE，再在音频分支发现 AAC 无效并静默结束，客户端看到成功响应但没有音频。
- `c306d09e` 把 format 校验移到 `_create_chat_completion` 的 streaming/non-streaming 分叉之前，统一返回 400，并增加 Qwen3-Omni streaming e2e。
- supported/default format 曾分散在 protocol、serving 和 encoder；review 后集中到 protocol 常量，并移除 bundled libsndfile 不支持的 AAC。
- 证据：[single source](https://github.com/vllm-project/vllm-omni/pull/4718#discussion_r3482056775)、[backend capability](https://github.com/vllm-project/vllm-omni/pull/4718#discussion_r3475617148)、[validate before stream](https://github.com/vllm-project/vllm-omni/pull/4718#discussion_r3539737061)。

## PR #4106 — async prefix-cache writes

- `050903e3` 在 async path 判定前无条件分配 pinned CPU tensor，CPU-only PyTorch 构造即失败；`e96212d4` 按 CUDA availability 建立 fallback。
- side-stream copy 使用会被下一 step 重写的 persistent `slot_mapping_gpu`，同时没有为 hidden/mm GPU tensor 建立 retention/`record_stream`。若 drain 提前返回，D2H 可能读到新 step 的行。
- 证据：[pinned allocation](https://github.com/vllm-project/vllm-omni/pull/4106#discussion_r3349219225)、[source-buffer lifetime](https://github.com/vllm-project/vllm-omni/pull/4106#discussion_r3421834194)。

## PR #3576 — multi-stage Prometheus metrics

- orchestrator 的全局一秒 throttle 会让 stage 0 replica 0 更新时间后，其余 replica 的新 stats 被跳过；`6f821733` 删除全局 gate，服从各 scheduler 自己的 throttle。
- waiting gauge 在 request state pop 前计算，单请求结束后可能长期显示 waiting=1；`e859c8b1`/后续逻辑按最终态计算并在 cleanup 后再发布。
- 把 upstream unregister 整体置空会在同进程重建 engine 时重复注册 timeseries；最终只保护 `vllm:omni_*`，保留 upstream family 清理。
- 证据：[per-replica throttle](https://github.com/vllm-project/vllm-omni/pull/3576#discussion_r3328965688)、[post-cleanup gauge](https://github.com/vllm-project/vllm-omni/pull/3576#discussion_r3328965891)、[collector lifecycle](https://github.com/vllm-project/vllm-omni/pull/3576#discussion_r3233663933)。

## PR #5088 — packed parameters under HSDP

- 原测试只断言传给 mock 的 kwargs，无法证明 FSDP2 bug 被修复。review 要求真实初始化单 rank Gloo process group 和 CPU DeviceMesh，执行 `fully_shard`。
- 最终 `d4da4fdd` 断言普通 float parameter 转成 DTensor，packed uint8/scalar parameter 保持原本 local identity。
- 证据：[real fully_shard test](https://github.com/vllm-project/vllm-omni/pull/5088#discussion_r3575534190)。
