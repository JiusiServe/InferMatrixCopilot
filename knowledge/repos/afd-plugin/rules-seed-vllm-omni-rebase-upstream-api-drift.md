---
title: "AFD plugin 评审规则：上游漂移与跨文档隐含不变量"
created: 2026-09-30
updated: 2026-09-30
type: rule
tags: [afd-plugin]
sources: []
---

# AFD plugin 评审规则：上游漂移与跨文档隐含不变量

## AFD-I15 — 保持 CPU-safe 导入边界，CUDA/Ascend 类互不继承

- `vllm` 只是 optional extra，默认的 `uv run pytest` 要能在没有 CUDA wheel 的 CPU/macOS 环境运行。以下模块在导入时不能 import torch/vLLM 的 CUDA 运行时、`torch_npu` 或 `vllm_ascend`：
  - 顶层 `afd_plugin`；
  - 图策略 helper（`validate_cuda_graph_mode()`）；
  - `afd_plugin/connectors/factory.py`。
- factory 使用 lazy loader。注册新 connector 时要保持惰性加载，不能在 factory 模块顶层 import `connectors/gpu` 或 `connectors/npu` 的实现。
- Ascend 原生算子通过 `ensure_cam_p2p_ops_available()` 在 connector 初始化时才加载。算子缺失应该在 connector 初始化时报错，不能在包导入时报错。
- NPU 类不能继承 CUDA AFD 类，反过来也一样。例如 `AFDNPUFFNModelRunner` 直接继承 vLLM-Ascend 的 `NPUModelRunner`，不继承 `GPUFFNModelRunner`。共享逻辑放在 config、connector payload、metadata、validation 或小 helper 里。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I16 — 新增 connector 或 connector 配置字段时要多处同步

- 只在 `AFDConnectorFactory` 注册是不够的。配置层有一份独立的硬编码 allow-list（即 README 中 `connector` 允许的三个名字），它不从 factory 派生。不同步的话，新 connector 会在配置校验阶段被拒绝。
- 实现要放在 `afd_plugin.connectors.gpu` 或 `afd_plugin.connectors.npu` 下，继承 `AFDConnectorBase`，并实现闭合 schema 的 `parse_extra_config()`，未知字段必须报错。`P2pNcclAFDConnector` 的 `connector_extra_config` 必须是空映射。
- `compat/npu/feature_validation.py` 通过 factory 解析同一份 schema。新增字段时要在这里拒绝不支持的组合。
- 要明确是否安装 `control_plane`。`GPUFFNModelRunner` 构造时断言 `connector.control_plane is not None`，所以 CUDA connector 必须提供 control plane。运行时只能按 `connector.control_plane is None` 分支，不能按具体类名判断。
- 不要假设所有 connector 的 world 排序相同：
  - `P2pNcclAFDConnector` 和 `CAMP2pAFDConnector` 是 FFN-first，要求 `num_attention_ranks >= num_ffn_ranks`，但不要求整除；
  - `CAMAsyncAFDConnector` 是 Attention-first。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I17 — connector 构造必须轻量，集体 rendezvous 延迟到权重加载之后

- 构造函数和 `parse_extra_config()` 不能创建 process group、communicator 或算子注册。这些都只能在 `init_afd_connector()` 里完成。
  - Attention 在 `load_model()` 末尾初始化，时间点在 AFD/Ascend ubatch wrapper 安装之后；
  - FFN 在 `initialize_from_config()` 中初始化，时间点在空 KV-cache surface 之后、daemon 线程启动之前。
- 如果把初始化提前到权重加载之前，两个角色就不能再重叠加载权重。rendezvous 必须在 Attention 做显存 profiling 或首次 forward 之前完成。
- `close()` 必须满足：
  - 清理该 connector 自己创建的 registry、pending queue、communicator 和 process group。
- connector 变更要测试 cleanup，以及重试或重新初始化。
- 模型代码可以通过 forward metadata 调用 connector 的 data-path 方法，但不拥有这些资源。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I18 — 特性组合矩阵分散在多份文档，放宽或收紧时要整体一致

- `compute_gate_on_attention`：
  - CUDA V1 + P2P 两个值都可以，取决于模型是否支持；
  - Qwen3 MoE 和 Qwen3.5/3.6 只允许 `false`；
  - 任何 V2 部署只允许 `false`；
  - CAMP2P 要求通用字段和 connector-local 的同名字段都为 `false`；
  - CAM async 要求通用字段为 `true`，`async_moe_ubatching` 同样要求 `true`。
- 图模式：CUDA（V1 和 V2）只接受 `FULL_DECODE_ONLY`；Ascend V2 还接受 `FULL`；CAM async 只允许 eager。
- DBO 和 ubatching：
  - V1 原生 ubatching 只接受恰好两个 ubatch；
  - V2 在两个平台上都拒绝 DBO 和 ubatching；
  - CAM async 拒绝原生 DBO，它只有 AFD 自己管理的两阶段 `async_moe_ubatching`，两者不能混为一谈。
- 不支持的组合必须在 config、worker 或 runner 初始化阶段失败。
- 改动矩阵中任意一项时，都要同步以下三处：README 的「Known gaps」、`execution_platforms.md` 的 tested runtime matrix、对应 validator 的测试。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I19 — README 和设计文档对 ModelRunnerV2 的支持说法互相矛盾

  - 设计文档和 E2E 契约记录了 CUDA V2 的 DP2/TP2 eager/graph 证据，CI 在 `l4_4` 上按 node ID 运行 4 个 `afd-v2-*` 用例。
- 评审时不要根据 README 把 V2 代码当成死代码，因此删除代码、跳过测试或放松校验。
- 改动 `attention_model_runner_v2.py`、`npu/attention_model_runner_v2.py` 或 `AFDMetadataProviderMixin` 的 PR，必须保证 `afd-v2-{eager,graph}-{dp2,tp2}` 继续通过。
- Ascend V2 只有单元测试证据，没有硬件 E2E。文档或 PR 描述里不能写成已经过硬件验证。
- V2 的限制是两个角色共同遵守的契约。FFN 虽然不用原生 V2 runner，也必须运行同一个 topology/feature validator。只改 Attention 侧校验是不完整的。
- 改变 V2 支持说法的 PR，要同时让 README 的 Known gaps、「Using the Plugin」和设计文档保持一致。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I20 — 临时替换上游符号时，必须在 `finally` 中恢复，并纳入升级审计

- 以下作用域替换都必须在 `finally` 中恢复所有符号和 runner 状态，异常路径也一样：
  - worker 在 `init_device()` 中替换 runner 符号；
  - dummy run 和 V2 执行时包装 `create_forward_context`；
  - V2 捕获时包装输入准备；
  - full-graph replay 的实例级 hook；
  - 构建多个 DBO ubatch 时临时禁用 Attention metadata cache。
- 新增这类接缝时，要补恢复路径和错误路径的单测，可参照 `tests/unit/v1/worker/test_attention_model_runner.py` 对 DBO workaround 的覆盖。
- 还要确保新接缝进入 `compatibility_and_patches.md` 里的作用域接缝清单。它们不是进程级 import-time patch，漏登记的话下次升级 vLLM 时容易被漏审。
- 优先用作用域级或实例级替换。不要把 AFD 自有行为藏进方便的进程级全局 hook。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I22 — vLLM-Ascend 基线只以源码 commit 记录

- 仓库不在 `pyproject.toml` 里声明 vLLM-Ascend 依赖，也没有 v0.26 的发布容器 tag。兼容证据就是 commit `80d8c194f` 加上已记录的 NPU 验证。
- 不要为了「补上依赖」去加包依赖，也不要把 v0.19.1rc1 镜像当作 v0.26 运行时。
- 刷新 Ascend patch 时，要引用确切的 vLLM-Ascend 源码 commit，并附上受影响路径的 NPU unit/E2E 证据。
- 如果前移基线，以下几处的 `80d8c194f` 要一起更新：README 的 Ascend 表格和 Environment 段、`compatibility_and_patches.md`、`execution_platforms.md`。
- v0.19.1rc1 基于 PCP 的部署在 v0.26 上不支持。legacy PCP8 recipe 只对应 `release/v0.19.1rc1`，不能当作 v0.26 支持的证据。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I23 — Ascend 原生算子的构建选择与打包

- `setup.py` 只在检测到 `torch_npu`、CANN 环境变量或默认 toolkit 路径时构建 Ascend 扩展，GPU 构建默认跳过。
- 环境变量的作用：`AFD_BUILD_ASCEND_OPS=1/0` 显式覆盖自动检测；`AFD_SKIP_ACLNN_BUILD=1` 只在产物已存在时跳过 ACLNN vendor build。改动不能让 CPU/GPU 环境默认触发 CANN 构建。
- 构建要在 `csrc/npu` 下完成 CANN vendor build，并打包 `_cann_ops_custom`（`setup.py` 和 `MANIFEST.in` 属于同一个 owner）。`csrc/gpu` 只是保留目录，目前没有插件自己的 CUDA 扩展。
- `CAMAsyncAFDConnector` 需要全部四个 `torch.ops.afd_ascend.afd_async_*` 算子。910C 包注册了它们，950 包没有注册，不要在 950 目标上假设这些算子存在。
- routed-only 算子的 host tiling 以 MiB 为单位读取 `HCCL_BUFFSIZE`。host helper 不查询实际窗口大小，所以引入或修改 `hccl_buffer_size` 覆盖时，要保证两者取值一致。
- 构建或原生算子的变更，要跑对应单测（如 `tests/unit/package/test_ascend_build_files.py`、`tests/unit/compat/test_ascend_ops.py`），并提供硬件 E2E 证据。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->

## AFD-I24 — E2E 的 CI 用例选择：PR 门禁和 2A1F 用例的边界（文档内部有冲突）

- PR 门禁只能按 pytest node ID 选以下用例：
  - 使用不超过 4 个设备、2 Attention + 2 FFN 的 legacy 用例；
  - 4 个 CUDA V2 DP2/TP2 用例。
- README 推荐的本地冒烟用例 `afd-eager-2a1f` 不能进 PR 门禁。
- `e2e_testing.md` 内部有冲突：一处说 2A1F 是「local-only」「run outside CI」；accuracy gate 表却把 DeepSeek `afd-graph-dbo-2a1f` 和 Qwen3 MoE/Qwen3.6 MoE 用例（Qwen3.6 套件是 2A1F）列进 weekly。
- 修改 `.buildkite/` 或 `.github/` 的调度时，2A1F 用例只能出现在 scheduled/weekly job 里，并应顺手让文档说法一致。
- CI 不能设置 `AFD_GSM8K_LIMIT`，也不能降低 `AFD_GSM8K_THRESHOLD`、样本数或必选用例集。DBO 用例要保留 24 个样本的下限和 12 个并发请求。
- CUDA 的 legacy 矩阵和 V2 矩阵各是一个独立的 40 分钟 job。更慢的覆盖放到 scheduled job。

<!-- kb:rule status=active since=init-9cae2d2ddaae -->
