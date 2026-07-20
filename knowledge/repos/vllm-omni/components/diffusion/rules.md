---
title: "Diffusion 共享规则"
created: 2026-07-20
updated: 2026-07-20
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #4341", "PR #5001", "PR #5087", "PR #5088", "PR #5136"]
confidence: high
---

# Diffusion 共享规则

只有 `DIFF-数字字母` 是可审计规则 ID。模型专有常量和已验证偏差留在对应
[模型 owner](../../models/_index.md)；本页只承载多个 diffusion 模型共用的不变量。

## 优化路径与 eager 的等价合同

### DIFF-1a — graph/compile/fused 路径逐项复刻 eager 数值边界

- 触发：新增或修改 CUDA Graph、compile、fused scheduler/solver 或缓存执行路径。
- 强制：逐项对齐初始噪声、solver/timestep dtype、每步 cast 边界、最后一步更新、
  CFG=0/近零分支和输出 dtype；依赖行为有版本差异时固定并验证版本。
- 禁止：只比较 shape、无 NaN 或“能运行”；这些不能证明数值和请求语义等价。
- 验收：固定输入和 request-local generator，对 eager/优化路径逐步比较关键状态并覆盖
  零值和最后一步边界。Ming-TTS 的具体反例见
  [Ming-Omni-TTS 规则](../../models/ming-omni-tts/rules.md)。 ^[PR #4341]

### DIFF-1b — 随机状态属于请求，零值不是缺省值

- 触发：pipeline/scheduler 接收 seed、generator、guidance 或其他允许为零的数值。
- 强制：使用请求本地 generator 并证明当前依赖版本真正消费它；用 `is None` 区分
  缺省与 `0`/`0.0`。
- 禁止：并发请求中修改 process-global RNG；使用 `x or default` 吃掉合法零值。
- 验收：两个并发请求用不同 generator 可重复且互不影响，`0.0` 从 request 构造一路
  到达 consumer。Cosmos3 的落地约束见
  [Cosmos3 规则](../../models/cosmos3/rules.md)。 ^[PR #5001]

## Checkpoint 与分布式加载

### DIFF-2a — checkpoint remap 必须追到已注册且真实消费的目标

- 触发：增加或修改 weight mapper、scale 名称、quantization adapter 或 key resolution。
- 强制：从序列化 key 追到目标 layer 注册的 parameter/buffer 和 forward consumer；
  多条 resolution path 必须返回对称、由合同解释的目标名。
- 禁止：把 producer 有而当前 consumer 不支持的 tensor 静默过滤；必须 fold/map 或
  fail fast，并在错误中标明依赖的 upstream 版本边界。
- 验收：测试覆盖已消费 key、未知 key、当前版本不支持的 scale 以及两条 resolution
  path 的输出名。ModelOpt `pre_quant_scale` 是该规则的原始触发。 ^[PR #5087]

### DIFF-2b — HSDP/FSDP 修复必须执行真实 fully_shard

- 触发：改动 diffusion HSDP/FSDP 参数过滤、packed/scalar parameter 或 DeviceMesh。
- 强制：至少用单 rank Gloo + CPU DeviceMesh 执行一次真实 `fully_shard`。
- 禁止：只断言传给 mock 的 kwargs 后声称分布式语义已覆盖。
- 验收：普通 float parameter 变为 DTensor；packed uint8/scalar parameter 保持本地
  identity，并覆盖 loader 的真实调用边界。 ^[PR #5088]

### DIFF-2c — component quantization 独立解析且保留完整 owner 前缀

- 触发：diffusion pipeline 为 text encoder、transformer、VAE 等组件增加独立量化配置。
- 强制：每个组件独立解析量化配置，并把包含 component owner 的完整模块名前缀传到
  真正持有权重的 layer；只量化明确支持的 attention/MLP linear，embedding、LM head
  等排除项必须显式保持未量化。
- 禁止：先裁掉 `text_encoder` 等 owner 前缀再匹配 component 规则；用一个组件的配置
  隐式覆盖其他组件；因为同属一个模型就量化全部 linear。
- 验收：至少覆盖“只量化一个组件、其他组件保持 BF16”的真实构造与加载，逐层断言
  命中/排除集合，并验证 meta-device parameter 不会被提前 move。FLUX.2 的具体边界见
  [FLUX.2 规则](../../models/flux2/rules.md)。 ^[PR #5136]

## 质量阈值与资源辅助

### DIFF-3a — 质量阈值必须由完全相同的测试 case 产生

- 触发：新增 LPIPS/PSNR/相似度阈值，或用 CPU offload 等资源选项支撑量化质量测试。
- 强制：阈值证据与测试中的 step、seed、size、guidance、checkpoint 和量化组件完全一致；
  仅为避免 OOM 的 offload 必须在 baseline/candidate 对称启用并说明它不属于待比较变量。
- 禁止：用 50-step A/B 数字为 10-step 测试阈值背书；只写“需要 offload”而不说明
  是资源前提还是功能行为。
- 验收：运行测试文件中的 exact case，并在规则/配置旁保留最短资源原因；对称 baseline
  证明质量差异来自目标量化变量。 ^[PR #5136]

相关执行流见 [Diffusion architecture](architecture.md)；benchmark 证据合同见
[performance evidence](../../benchmark/guides/performance-evidence.md)。
