# MCP PR 审核测试评估

## 测试概况

- 测试对象：`vllm-project/vllm-omni#5156`
- PR 规模：2 个文件，新增约 60 行
- MCP Run：`run-20260717-114911-0c74e5`
- 使用模型：`gpt-5.6-sol`
- 运行模式：`eco`
- 最终状态：`done`
- 审核结论：`REQUEST CHANGES`
- 完整报告：`C:\Users\user\.omni-copilot\runs\run-20260717-114911-0c74e5\RUN_REPORT.md`

## 1. 耗时评估

成功运行的端到端耗时为 **288 秒（4 分 48 秒）**。

| 阶段 | 耗时 |
|---|---:|
| 拉取 PR diff | 2.99 秒 |
| Gate 检查 | 2.77 秒 |
| Agent 审核 | 279.23 秒 |
| 生成报告 | 0.01 秒 |

Agent 审核占总耗时约 **97%**。

本次采用多个并行审核 lens，累计 LLM 请求耗时约 636 秒，通过并行执行压缩至约 288 秒墙钟时间。

如果把测试期间的 Windows MCP 兼容性排障计算在内，从第一次调用到最终成功约 16 分钟。兼容性问题修复后，正常单次运行预期约为 5 分钟。

## 2. 实际操作

执行流程：

```text
start_review
→ 拉取 PR #5156
→ 检查 diff 和 gate
→ 运行 4 个并行审核 lens
   ├─ behavior
   ├─ logic
   ├─ contracts
   └─ verification
→ 合并审核结果
→ 生成 RUN_REPORT.md
→ get_result 返回 done
```

资源消耗：

- LLM 请求：26 次
- 工具调用：114 次
- 输入 tokens：约 111 万
- 输出 tokens：约 1.9 万
- 缓存读取 tokens：约 74.7 万
- 内部估算成本：约 3.62 美元
- Push：0
- GitHub 评论发布：0
- CI 执行时间：0

主要工具调用：

| 工具 | 次数 |
|---|---:|
| `grep` | 42 |
| `read_file` | 38 |
| `repo_map` | 12 |
| `doc_read` | 7 |
| `gh_ci_read` | 4 |
| `gh_pr_view` | 4 |
| `skill_search` | 3 |
| `list_dir` | 2 |
| `doc_search` | 2 |

本次审核没有实际运行 pytest，而是通过代码、测试文件和现有 CI 状态进行静态验证。

## 3. 审核结果

最终结论为 **REQUEST CHANGES**，共发现：

- 1 个 major
- 3 个 minor

### Major

新增加的时间预算警告只覆盖已解码的 `ref_audio`。当请求使用预计算 `voice_profile` 时，代码会保留 `voice_profile`、令 `ref_audio` 为 `None`，从而跳过警告。

这个问题具有跨文件证据，审核检查了：

- Serving 请求处理路径
- `build_voxcpm2_prompt`
- Speaker profile 缓存与验证逻辑
- 现有预计算 voice 测试

该发现可信度较高，值得作为 blocker 交由 PR 作者确认和修复。

### Minor

1. 实际警告阈值为 29.5 秒，但提示文字描述为“超过约 30 秒”，边界语义不一致。
2. Reference-only 模式也可能收到仅针对 continuation 时间线设计的警告，需要确认产品语义。
3. 新测试只覆盖 helper，没有覆盖实际 serving 请求路径和 logging 分支。

后两个问题包含一定的设计意图推断，适合由作者确认，不宜完全自动判定为 blocker。

## 4. 兼容性问题与修复

测试过程中确认并修复了两个 Windows MCP 兼容性问题：

1. MCP server 会收到宿主控制台传播的 `SIGINT`，导致 `KeyboardInterrupt` 和 stdio 断线。
2. 审核子进程继承 Windows GBK 编码，在输出 `✓` 等字符时触发 `UnicodeEncodeError`。

当前修复方式：

- Windows MCP stdio server 忽略继承的 `SIGINT`，正常关闭仍由 stdin EOF 控制。
- 审核子进程强制设置 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`。

修复后，MCP 完成了 `start_review → running → done → get_result` 的完整端到端流程。

## 5. 当前问题

### 成本过高

对一个只有 2 个文件、约 60 行新增代码的小 PR，消耗约 111 万输入 tokens 和 3.62 美元，明显偏重。

### 只读边界不彻底

审核过程中会更新 skill 的 `run_count` 和 `last_used_at`。虽然不修改被审仓库，但会污染 copilot 自身工作区。本次测试产生的计数变更已经撤销。

### 未实际执行测试

当前 MCP PR review 是只读静态审核，只读取已有 CI 状态，不会执行 pytest。因此部分验证结论仍依赖代码推理和作者确认。

### High reasoning 未得到验证

运行记录显示模型为 `gpt-5.6-sol`、模式为 `eco`。当前没有证据表明内部请求实际传入了 `reasoning_effort=high`。

## 6. 综合评价

| 维度 | 评分 | 说明 |
|---|---:|---|
| 功能完整性 | 8/10 | MCP 可以启动、执行、轮询并返回正式报告 |
| 审核价值 | 7/10 | 找到了至少一个有实际价值的跨路径问题 |
| 执行效率 | 3/10 | 小 PR 的 token 和成本消耗过高 |
| 部署成熟度 | 5/10 | Windows 问题已修复，但只读副作用仍需处理 |

## 7. 建议

建议将审核分为两个档位：

### 普通审核

- 使用单 lens
- 目标耗时：1–2 分钟
- 目标输入：20 万 tokens 以内
- 适合普通、小规模 PR

### 深度审核

- 使用 4 个并行 lens 和 reducer
- 仅用于高风险模块、大型 PR 或发布前审核
- 保留当前跨文件验证和知识库检索能力

此外，应在正式启用前完成：

1. 禁止只读 MCP 审核写回 skill 使用计数。
2. 为普通模式建立明确的 token、工具调用和迭代预算。
3. 明确区分模型名称、工作流模式和 reasoning effort。
4. 增加真实 pytest 执行能力，或在报告中明确标注“静态审核、未运行测试”。

## 结论

当前 MCP PR review 已经能够完成真实端到端审核，结果具有一定工程价值，但默认配置明显偏向高成本深度审查。

现阶段更适合作为重要 PR 的深度审核工具，不适合对所有小 PR 默认启用完整 ensemble。完成成本分级和只读边界修复后，再考虑作为常规 PR 审核入口。
