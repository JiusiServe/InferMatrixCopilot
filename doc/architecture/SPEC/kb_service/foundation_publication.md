# kb_service/foundation_publication.py —— 规范

<!-- verified-against: 2026-10-06 -->

## 职责

为显式 `--foundation-mode partial` 保存和复核基础知识发布收据，并为新深度批次
验证原发布记录。调用方的默认完整门槛保持不变；使用方式见
[部分发布说明](../../../knowledge/partial-foundation.md)。

## 不变量

- 只发布已经完成初轮扫描、保留真实原生任务的固定源码批次。已有基线未覆盖的
  功能和 owner 缺少初轮任务时拒绝发布；已处理范围不能称为已补齐全部知识。
- 生产文件结构覆盖达到原政策目标；源码、目录与政策身份、引用、格式及原生
  认可仍须有效。不能修改功能集合、分母、语义认可条件或失败记录来满足门槛。
- `freeze_receipt` 重放每个任务的原生证明，再冻结生成身份、KB/source SHA、
  全部终态任务的输入/结果摘要、实际进入页面的认可区块、输出文件哈希及未知项。
  收据按内容哈希在原始 Git 外阶段目录独占创建；既有字节或路径损坏必须拒绝。
- `verify_prepared_receipt` 核对原始 partial 模式、收据范围和 prepared 文件，
  从固定源码及实际准备发布的字节重新计算覆盖。不能只信检查点里的计数。
  旧 strict prepared 发布保持原行为，不能偷偷转换为 partial。
- `foundation_handoff` 只接受原始 published、非 dry-run 的 partial 记录。
  记录、收据、任务、prepared 文件、当前合并基线及政策必须一致，且真实 PR
  状态为 MERGED。返回原记录/收据路径与哈希、固定 pin、目录绑定和输出文件哈希。
  下游以这些字节建立新批次身份，发生变化即拒绝复用。
- 发布状态只表示 PR 传输。收据保留 `init_complete=false`、原六维目标结果和
  所有未知项；结构覆盖、六维基础知识、七维深度认可及实际测试执行分别表述。

## PR 正文与恢复

`render_partial_body` 只渲染汇总数量、固定身份、真实未知维度和收据引用；完整
模型输入、输出、评审及历史仍在 Git 外。费用未报告时为未知。
若原 prepared 发布因正文过长而未成功，官方恢复路径须先通过全部原生、源码和
收据校验，再仅刷新正文元数据：commit、文件字节、任务和修正次数不得改变，
不得重新生成知识或伪造发布状态。

## 验证

`test_kb_foundation_explicit_partial.py` 覆盖原生证明、范围、收据、恢复与门槛；
`test_kb_foundation_partial_interfaces.py` 覆盖 CLI、campaign、worker 与 assembly
身份传递；`test_kb_foundation_partial_prbody.py` 覆盖紧凑正文和官方正文恢复。
