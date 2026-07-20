---
title: "近期 maintainer 审核模式"
created: 2026-07-20
updated: 2026-07-20
type: guide
tags: [vllm-omni, review]
sources: ["PR #3576", "PR #3642", "PR #4106", "PR #4281", "PR #4341", "PR #4718", "PR #4730", "PR #4980", "PR #5001", "PR #5031", "PR #5037", "PR #5052", "PR #5084", "PR #5087", "PR #5088"]
confidence: high
---

# 近期 maintainer 审核模式

本页给 performance 模式直接使用。它不是“看到关键词就报错”的清单；每条意见仍须绑定当前 diff，并用仓库代码验证 producer、consumer 和失败路径。原始 review 时点和修复证据见 [2026-07 review cases](../history/2026-07-merged-pr-review-cases.md)。通用审查方法见 [review execution contract](../../../../general/review/guides/review-execution-contract.md)。

## 可选依赖：测试必须真的模拟未安装环境

- 新增可选包时，检查模块是否在 skip/假模块建立前就被顶层 import。测试里 `mocker.patch("pkg.symbol", create=True)` 不等于包可导入。
- 无依赖单测可以先向 `sys.modules` 注入最小假模块；真实 kernel smoke 再单独用 availability marker。
- patch `Tensor.cuda`、descriptor 或 bound method 时验证 `self` 绑定和真实返回 shape；至少执行包含该 fixture 的目标测试，不能只看 mock 能创建。

触发签名：optional dependency、lazy import、`find_spec`、`sys.modules`、descriptor mock、`Tensor.cuda`。来源：PR #5037。

## Benchmark：先证明测量和判定本身正确

- warmup 必须发生在 wall-clock 起点前；compile/init 首次成本不能混入扩展性比较。
- 小样本 percentile 使用 nearest-rank 或标准实现；`int(q*n)-1` 会把两样本 p90 算成最小值。
- 请求失败或零成功必须非零退出，避免 CI/脚本把坏数据标成成功。
- 并行隔离不能用“相同 prompt + 相同 seed 得到相同 hash”证明。使用不同请求输入，分别与单副本 baseline 对齐，并比较完整 key 集合，不能允许结果是 baseline 的真子集。

触发签名：throughput、p90/p99、replica/data parallel、warmup、hash/isolation、PASS/exit code。来源：PR #5052。

## 重构兼容性：迁移符号时保留身份和旧行为

- 删除公开 import 路径前全仓搜索 docs、examples 和下游 import；兼容 shim 必须 re-export，而不只是发 warning。
- 避免旧/新模块各保留一份 class 定义，否则 `isinstance`、registry 和序列化会因 class identity 不同而失效。
- 搬迁 accumulator/formatter 时逐项迁移旧语义，例如 metadata tensor 的特殊归类；结构移动成功不代表行为等价。
- 返回值有时是 `incoming`、有时是原对象的“伪 in-place” API 要改成显式名字/合同，调用方必须保存返回值。

触发签名：move/rename module、deprecation shim、duplicate class、payload/output consolidation、metadata routing。来源：PR #4980。

## Checkpoint remap：从序列化名追到真实 consumer

- 映射一个 scale/tensor 前检查目标 layer 实际注册和消费哪些 parameter；“加载时静默过滤”比显式失败更危险。
- producer 有而当前 vLLM consumer 不支持时，必须 fold/map 或 fail fast，不能假装加载成功。
- 多条 key-resolution 路径要核对输出名是否对称；若一条保留 source name、一条返回 remapped name，必须由调用合同解释并覆盖测试。
- 依赖 upstream 当前行为的拒绝信息写明版本边界，防止未来升级继续执行陈旧假设。

触发签名：checkpoint adapter、weights mapper、scale、registered parameter、unconsumed tensor、upstream version。来源：PR #5087。

## 配置、文档与 scope：以真实入口为准

- PR/文档宣称的 alias 必须能通过 registry 和 CLI；否则注册完整或删除宣称。
- 硬件支持表必须与运行时 platform gate、最低 capability 完全一致；unsupported 不能写成“未验证”。
- 文档字段名与 parser/schema 当前实现逐字对齐，避免 `mark`/`marks` 之类近义漂移。
- 重复配置分支若上游分支已经填充同一字段，先用“删掉后测试仍过”证明它是 no-op，再要求删除。
- review 中出现与目标无关的文件改动时单独核对 scope；不要让顺手修改混入修复。

触发签名：alias、hardware matrix、capability、schema field、redundant branch、unrelated file。来源：PR #5037、#5084、#5087。

## 新模型接入：沿加载、路由、桥接、输出四段验证

- 模型 loader 必须显式传递目标 dtype；只为读取 config 不得同步下载整套权重。支持表中的 online、HSDP、offload、VAE parallel 等勾选项必须各有对应证据。
- architecture 名称非版本唯一时，registry 不能只做集合相交；增加 config/version predicate，避免旧模型落入新 pipeline。
- 多阶段模型逐段核对 runner 实际写入的 bridge 字段、下一阶段读取字段和最终 `OmniOutput`/multimodal payload 包装。单元测试直接调用模型不等于真实 stage handoff 可用。
- 一个 stage 声明 `max_num_seqs > 1` 时，禁止只消费 `runtime_info[0]` 或把单元素结果广播给整批请求；无法逐请求处理就把并发上限收紧为 1。

触发签名：new model、pipeline registry、stage wrapper、runtime info、multimodal output、batch handoff。来源：PR #3642、#4730、#5001。

## 优化路径必须复刻 eager 数值和请求语义

- CUDA Graph/compile/fused 路径要逐项对齐 eager：初始噪声、solver/timestep dtype、每步 cast 边界、最后一步更新和 CFG=0 等边界分支；只比较 shape 或“能运行”不足以证明等价。
- 随机采样必须使用请求本地 generator，不能在并发请求中改 process-global RNG；同时核对依赖版本是否真的消费传入 generator。
- 零值不能与“未提供”共用 truthy sentinel；如果 API 宣称支持 `0.0`，要从 request 构造一路证明它能到达 consumer。

触发签名：CUDA Graph、compile、solver、CFG、scheduler、seed/generator、`x or default`。来源：PR #4341、#5001。

## Serving 在产生第一个 chunk 前完成合同校验

- 流式接口若在文本 chunk 发出后才发现 audio/format 等参数无效，会表现为 HTTP 成功但静默缺失后半段输出。所有可预判错误应在 streaming/non-streaming 分支前返回 4xx。
- 支持格式、默认值和协议类型只能有一个定义来源；protocol、validator 与 encoder/backend capability 必须引用同一常量，不能各维护列表。
- 不要把 backend 实际不支持的格式列为合法值，再靠中途 fallback 掩盖失败。

触发签名：SSE/stream、extra body、audio format、late ErrorResponse、protocol defaults。来源：PR #4718。

## 并行、设备与真实集成测试

- strategy/deploy 中只列真正可翻译的 axis；保留值应明确 fail，不能静默忽略。headless 与标准启动路径必须转发相同 override，stage 用稳定名称而非可漂移索引寻址。
- 同卡多 stage 的 `gpu_memory_utilization` 要求和不超过可用预算；TP/replica 的设备数、routing 与负载均衡来源必须在示例中自洽。
- mock 只验证调用参数时，不能声称覆盖真实分布式语义。HSDP/FSDP 修复至少走一次真实 `fully_shard`，断言 float 参数成为 DTensor，而 packed/scalar 参数保持本地。
- 关键配置文件缺失时测试应失败，不能 conditional skip 把路径漂移变成绿灯。

触发签名：strategy axis、stage override、headless、device map、memory utilization、HSDP/FSDP mock。来源：PR #4281、#5031、#5088。

## 异步资源与指标按 owner 管生命周期

- side-stream D2H 复制必须保证源 tensor/buffer 在事件完成前不被下一 step 重写；使用显式 stream ordering、retain/`record_stream` 或消费屏障。
- pinned CPU allocation 要按 CUDA availability 建立 fallback，不能先在 CPU-only 环境构造失败、后面才禁用异步路径。
- throttle 必须按 scheduler/stage/replica 隔离；全局时间戳会让先上报的 replica 饿死其他 replica 的指标。
- gauge 应在 request cleanup 后计算；collector 重建时只保护本项目 family，仍保留 upstream collector 的 unregister，避免同进程重复注册。

触发签名：side stream、pinned memory、persistent buffer、Prometheus、replica metric、request cleanup。来源：PR #3576、#4106。

## 大 PR：先校准 diff 边界，再按模块覆盖

- base 必须是 review head 的祖先；若不是，先取 merge-base。禁止把后来 main 的增删误当成 PR 内容，否则 review 会产生高置信度的无关意见。
- 先按 changed files 建 scope ledger，至少覆盖每个 scope 一次，再按 churn 和跨模块调用链分配深度；不能只顺着一个醒目的大文件读到底。
- finding 的改动点必须落在 pinned diff 内；可以读取未改文件证明 impact path，但不能把上下文里的既有问题当作本 PR 回归。
- 大 diff 最终自检每个历史模式是否真的检查过：loader/registry/bridge/output、随机数与优化 parity、streaming preflight、并行设备合同、异步资源生命周期。

触发签名：large diff、merge commit、branch drift、many files、cross-module refactor、review replay。

## 输出合同

命中以上模式后，review comment 必须包含：当前 diff 做了什么、沿哪个调用/数据路径造成什么结果、验证过的文件或命令、应在本 PR 内采取的具体修法。只有关键词相似而未验证 consumer 的内容留在调查记录，不作为阻塞意见。
