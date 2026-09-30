---
title: "AFD plugin 仓库规则"
created: 2026-08-05
updated: 2026-09-30
type: rule
tags: [afd-plugin, review, config, distributed, model-executor]
sources:
  - "afd-plugin@a432692:AGENTS.md"
  - "afd-plugin@a432692:README.md"
  - "afd-plugin@a432692:pyproject.toml"
  - "afd-plugin@a432692:afd_plugin/v1/worker/npu/mla_graph.py"
  - "afd-plugin@a432692:tests/unit/v1/worker/test_npu_mla_graph.py"
  - "afd-plugin@a432692:.github/workflows/cpu-only-ci.yml"
  - "afd-plugin@a432692:.agents/skills/run-e2e/SKILL.md"
---

# AFD plugin 仓库规则

只在当前任务明确属于 `vllm-project/afd-plugin` 时应用本页。先按 [AFD 入口](_index.md) 确认仓库身份，再结合 [组件 owner](components/_index.md) 读取最近专项页面。插件入口与 patch 的细化规则已分别路由到 [plugin-boundary rules](components/plugin-boundary/rules.md) 和 [compatibility rules](components/compatibility/rules.md)。

## 1. 仓库身份和权威来源

- AFD-1a：review 或 issue 回答前必须确认目标是 canonical `vllm-project/afd-plugin`，不能把 vLLM-Omni 的知识树、模型规则、远端策略或 rebase 假设带入 AFD。
- AFD-1b：AFD 仓库自己的 `AGENTS.md`、`CLAUDE.md`、`.agents/skills/run-e2e/SKILL.md`、CI workflow 和仓库脚本是权威来源；InferMatrixCopilot 只做只读路由、提示和证据组织。
- AFD-1c：默认路径保持只读；不能自动发 PR 评论、push、改 protected branch，不能要求 AFD runtime 行为因为本 adapter 初始化而改变。

## 2. 上游兼容和历史证据边界

- AFD-2a：兼容结论必须精确写当前声明的 runtime：vLLM `0.26.0`；Ascend NPU 以 vLLM-Ascend source commit `80d8c194f` 及与该 snapshot 匹配的 CANN/torch/torch-npu 环境为证据。仓库未声明 released vLLM-Ascend v0.26 package/container，不得推断更宽版本范围。
- AFD-2e：当前 DeepSeek-V3.2 NPU PCP8 recipe 是 `v0.19.1rc1` 历史实验，不是 v0.26 启动样例；不得把旧 recipe、旧镜像或 PCP 部署当作 v0.26 model-runner-v1 支持证据。

## 3. Connector、worker 和平台 review

- AFD-3c：`afd_plugin/connectors/`、`afd_plugin/distributed/` 改动必须审 rank 布局、attention/ffn 数量约束、同步/异步语义、端口/host、进程组生命周期、资源 cleanup 和跨 role 同步失败路径。
- AFD-3d：`afd_plugin/v1/worker/`、`afd_plugin/model_executor/` 改动必须审自动 worker 选择、role-specific runner、Attention/FFN 组件加载边界、scheduler-driven FFN fail-fast、CUDA/ACL graph 模式和 DBO/ubatch 条件。
- AFD-3e：`csrc/gpu/`、`csrc/npu/` 改动必须区分 CUDA 与 Ascend CANN/ACLNN toolchain；NPU op 构建只能在明确 Ascend 环境或显式 `AFD_BUILD_ASCEND_OPS=1` 下作为证据。
- AFD-3f：CUDA `P2pNcclAFDConnector` 只允许 eager 或 `FULL_DECODE_ONLY` CUDA Graph；原生 DBO 只允许两个 ubatch。改 graph/DBO 路径时必须证明 Attention 控制面先传 stage metadata、FFN graph key/cache 与 connector state 在 capture/replay 中一致，其他组合必须在运行前拒绝。
- AFD-3g：Ascend `CAMP2pAFDConnector` 只允许 eager 或 `FULL_DECODE_ONLY` ACL Graph；原生 DBO 只允许两个 ubatch，common 和 connector-local `compute_gate_on_attention` 都必须为 `false`，`quant_mode` 必须为 `0`，并且运行前必须存在 plugin CANN ops。
- AFD-3h：Ascend `CAMAsyncAFDConnector` 只支持 eager prefill；必须拒绝 vLLM 原生 DBO。可选 `async_moe_ubatching` 是独立的两阶段 request-boundary pipeline，不得当作原生 DBO；当前 v0.26 硬件声明只覆盖 no-PCP `2A2F` DeepSeek-V2-Lite，且要求 `async=true`、common `compute_gate_on_attention=true`、`dynamicQuant` 为 `0` 或 `1`。
- AFD-3i：Ascend MLA + 原生 DBO Full Graph 修改必须同时保持两个 ubatch、`FULL_DECODE_ONLY` 和禁用 speculative decoding 的门禁；每个 stage 独立捕获 `GraphParams`，回放前按 layer-major/stage-minor 合并，AFD 上下文外必须回退到上游 resolver。

## 4. 验证和证据

- AFD-4a：CPU-safe 默认检查是 `uv run pytest`、`uv run pytest -q tests/unit -m "not gpu and not vllm_runtime"`、`uv run ruff check .`、`uv run ruff format --check .`；它们不能证明 GPU/NPU runtime、模型精度或性能。
- AFD-4b：GPU/NPU E2E 必须通过 AFD 仓库 `.agents/skills/run-e2e/SKILL.md` 或仓库测试入口运行，记录 backend、设备数、模型路径、vLLM/vLLM-Ascend/CANN/torch 版本、拓扑、connector、graph/DBO/async 配置和 skipped 原因。
- AFD-4c：性能、精度或硬件支持 claim 必须给可复现证据：硬件型号、软件版本、driver/toolchain、rank 拓扑、命令、日志或 pytest node id；CPU import/config smoke 不能替代硬件证据。
- AFD-4d：changed files 没有命中 adapter route 时，必须把 unmatched path 明确留给 host reviewer 继续人工审，不得把它当作已覆盖。

## AFD-I1 — ModelRunnerV2 的支持状态在 README 与设计文档之间互相矛盾，改 V2 时两边都要核对

- README 的 Known gaps 写着 V2 不受支持，还要求设置 `VLLM_USE_V2_MODEL_RUNNER=0`。设计文档和 E2E 文档却写着 CUDA V2 已经实现，DP2/TP2 用例也在 PR CI 里。凡是改动 `attention_model_runner_v2.py`、`npu/attention_model_runner_v2.py` 或 V2 校验逻辑的 PR，都要确认 README 与设计文档说法一致；行为变了就同步更新 README。
- 写支持声明时要分清证据：CUDA V2 有 DP2/TP2 eager 和 graph 的 E2E 证据；Ascend V2 只有单元测试证据。PR 描述和文档都不能说 Ascend V2 经过了硬件验证。
- V2 的约束和 V1 不同，不能直接套用 V1 的约束：
  - 拒绝 DBO 和 ubatching；
  - 要求 `compute_gate_on_attention=false`、PP=PCP=DCP=1、角色 rank 数等于 DP×TP、静态 EP；
  - CUDA V2 只能用 eager 或 `FULL_DECODE_ONLY`，Ascend V2 还可以用 `FULL`。
- FFN 虽然不使用原生 V2 runner，但会执行同一套配对拓扑校验。修改 V2 约束时，Attention 和 FFN 两侧的校验要一起改。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I2 — 新增或重命名 connector 时，配置 allow-list 和 factory 注册要同时改

- 配置里的 connector 名称 allow-list 是硬编码的，不从 `AFDConnectorFactory` 的注册表生成。只在 factory 里注册，配置校验仍会拒绝新名称。所以要检查 `role`/`connector` 校验和 factory 是否一起改了。
- factory 的 loader 必须是懒加载，并且要解析成 `AFDConnectorBase` 的子类。导入 factory 时不能连带导入 CUDA 或 Ascend 的实现。
- 新 connector 要实现 `parse_extra_config()`，对 `connector_extra_config` 使用封闭 schema，遇到未知字段就报错。`P2pNcclAFDConnector` 的 extra config 必须为空。
- 实现文件放在对应后端的包下：`afd_plugin.connectors.gpu` 或 `afd_plugin.connectors.npu`。
- 同时更新三张表：README 的 connector 表、Attention runtime 的 runtime selection 表、FFN runtime 的 runtime selection 表。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I4 — `compute_gate_on_attention` 的合法取值因 connector、模型和 runner 而不同，而且有两个同名字段

  - `P2pNcclAFDConnector`：true、false 都支持；
  - 同步 NPU 的 `CAMP2pAFDConnector`：公共字段和 connector 本地字段都必须是 `false`；
  - `CAMAsyncAFDConnector`：公共字段必须是 `true`，`async_moe_ubatching` 也依赖 `true`；
  - Qwen3 MoE、Qwen3.5/3.6 以及所有 V2 路径：都拒绝 `true`。
- CAMP2P 有两个同名字段：`AFDConfig` 上的公共字段，和 `connector_extra_config.compute_gate_on_attention`。改动其中一个的解析或校验时，要确认另一个也被检查到了。
- 不支持的组合必须在执行前失败，由 `compat/npu/feature_validation.py` 或 worker 初始化负责拦截。不能在运行时悄悄回退。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I6 — 控制面的副作用必须在正式图捕获之外完成

- `send_dp_metadata_list` 和 `update_state_from_dp_metadata` 必须在进入 `torch.cuda.graph(...)` 或 `torch.npu.graph(...)` 之前执行。图里只能捕获模型和数据面的操作。
- 不带 ubatch 的捕获要先显式发送 padded shape。带 ubatch 的捕获由平台 wrapper 按 stage 发送。
- V2 的要求：
  - 每个原生 descriptor 只能发布一次 warmup payload 和一次 capture payload；
  - 原生 full-graph replay 不会创建 `ForwardContext`，所以 replay 前必须通过实例级 hook 发布 padded shape；
  - 所有临时 hook 都要在 `finally` 里恢复。
- FFN 的图 key 由 `make_ffn_graph_key()` 或 stage token 数生成，NPU 还要加上 A/F 拓扑。key 缺失时必须回退到 eager，不能报错，也不能复用错误形状的图。
- CUDA 图模式只接受 `FULL_DECODE_ONLY`，其他模式必须在运行前就被拒绝。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I7 — 临时替换上游符号时必须在 `finally` 里恢复，并把替换点列入升级审计

- 以下临时替换不在 `compat/patches/` 目录下，但都属于上游适配点：
  - CUDA worker 在 `Worker.init_device()` 期间替换 runner 符号；
  - dummy run 和 V2 执行时包装 `create_forward_context`；
  - V2 捕获时包装原生 input preparation；
  - full-graph replay 时安装 manager hook；
  - DBO 构建期间关闭 Attention metadata cache。
- 这些替换都必须在 `finally` 里恢复符号和 runner 状态。PR 要带上恢复路径和出错路径的测试。
- 新增类似的替换时，要在 `compatibility_and_patches.md` 里登记，并写明移除条件（参照 vLLM #48659 那一项的写法）。升级上游时，这些替换点都要纳入审计。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I9 — `register_afd` 导入补丁是 best-effort 的，对应的运行时路径必须能发现补丁缺失并报错

- 核心补丁在同一个 `try` 里导入，失败只打 debug 日志，可能出现只装上一部分的情况。新补丁如果加进这个块，依赖它的运行时路径就必须检查补丁是否已安装（比如检查 sentinel 或保存的原函数），缺失时明确报错，不能带着错误结果继续服务。
- 保存了原函数的补丁，在 reload 时不能用自己的 wrapper 覆盖已保存的原函数。初始化要么幂等，要么有显式守卫。
- Ascend 补丁要等 Ascend 插件完成平台初始化后才能应用。只用 CUDA 的注册路径不能导入 vLLM-Ascend。
- 新增或修改补丁时，要同步更新 inventory 表：守卫方式、幂等性、验证方式和移除条件。还要为非 AFD 分支写回归测试。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I10 — CPU 安全的导入边界：公共模块不能在导入时拉入设备栈

- `vllm` 是可选 extra，默认的 `uv run pytest` 要能在 CPU 或 macOS 上运行。顶层包、公共配置和校验、版本检查、图策略 helper（包括 `validate_cuda_graph_mode()`），以及 connector factory，都不能在模块级导入 `torch`、`vllm`、`torch_npu`、`vllm_ascend` 或 `afd_plugin._C_ascend`。
- 原生算子只在 connector 初始化时懒加载，例如 `ensure_cam_p2p_ops_available()`。缺少算子时应在 connector 初始化阶段失败，不能在 import 时失败。
- CUDA 或 Ascend 的 runtime 模块本身可以导入真实设备依赖，但公共模块不能反过来在导入时引用它们。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I11 — 依赖方向和平台隔离：不能跨平台继承，也不能反向依赖角色 worker

- NPU 的 AFD 类不能继承 CUDA 的 AFD 类，反过来也一样。平台扩展只能继承对应的上游类。`GPUFFNModelRunner` 保持为插件自有的最小 runner，`AFDNPUFFNModelRunner` 直接继承 `NPUModelRunner`。
- connector、模型和其他共享模块不能 import Attention 或 FFN 的 worker/runner 实现。生产代码不能依赖 `tests/e2e` 下的测试 harness。
- 代码按后端放置：connector 放在 `afd_plugin.connectors.gpu` 或 `afd_plugin.connectors.npu`，原生源码放在 `csrc/npu` 或 `csrc/gpu`。
- `compat/patches` 不能用来存放 AFD 自有的功能。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I12 — E2E gate 的拓扑：PR gate 只能用 2A2F 且不超过 4 张卡；文档对 2A1F 是否进 CI 说法矛盾

- 加入 PR gate 的 AFD 用例必须是 2A2F，而且最多用 4 张不同的卡。2A1F、16 卡的 DSV4 用例和 async CAM 的 NPU 冒烟用例都不能进 PR gate。
- 文档自相矛盾：E2E-INV-002 和 2A1F 那一节都说 2A1F 只在本地跑、不进 CI；但 weekly 的准确率 gate 包含 DeepSeek 的 `afd-graph-dbo-2a1f`，Qwen3.6 的默认套件也是 2A1F。PR 如果把 2A1F 用例放进定时 CI，必须同时修正相关文档，不能留下矛盾。
- 默认情况下，harness 触发 `SIGKILL` 必须判定用例失败。只有 async CAM 的 NPU 场景有例外：它通过 run id 和角色标记扫描 `/proc/*/environ` 来清理进程。这个例外不能扩展到其他用例。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->
