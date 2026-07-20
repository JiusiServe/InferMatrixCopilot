# 2026-07 已合入 PR review/fix 样本

采集日期：2026-07-20。这里保存 review 时点证据，不作为看到相同文件就直接发评论的规则。

## PR #5037 — BitsAndBytes W4

- `d16e0894`: 无 `bitsandbytes` 环境仍会在测试导入/fixture 路径失败；最终用 `_ensure_bitsandbytes_importable` 注入最小模块，真实 CUDA smoke 继续 availability-gated。
- `a57c5472`: `Tensor.cuda` mock 未保持 descriptor/binding 语义导致目标测试 `TypeError`；同一轮还发现 engine 分支重复填充同一 quantization 字段，删除后测试仍过。
- `c4ed933b`: PR 宣称 `bnb` alias 但 registry 只有 `bitsandbytes`；文档把实际不支持的 ROCm 写成未验证，并把 CUDA 门槛写宽。最终移除 alias 宣称，文档收紧到 CUDA SM75+、ROCm unsupported。
- 证据：[optional dependency](https://github.com/vllm-project/vllm-omni/pull/5037#discussion_r3575415047)、[descriptor mock](https://github.com/vllm-project/vllm-omni/pull/5037#discussion_r3575575723)、[redundant branch](https://github.com/vllm-project/vllm-omni/pull/5037#discussion_r3575576163)、[alias](https://github.com/vllm-project/vllm-omni/pull/5037#discussion_r3576639180)、[hardware docs](https://github.com/vllm-project/vllm-omni/pull/5037#discussion_r3576639250)。

## PR #5052 — replica data-parallel benchmark

- `ea0e11f8`: 计时包含冷启动；相同 prompt/seed 的 hash 不能证明隔离；请求全失败仍返回 0；小样本 p90 算法下报。
- `0ea2b05e`: 第一轮修复后，隔离比较仍允许 `got` 是 baseline 真子集；`1e76994e` 增加完整 key-set equality。
- 最终代码把 warmup 放到 timed batch 前，用 nearest-rank，给请求构造不同 seed/input，失败或 isolation mismatch 时 `sys.exit(1)`。
- 证据：[warmup](https://github.com/vllm-project/vllm-omni/pull/5052#discussion_r3577322239)、[distinct baseline](https://github.com/vllm-project/vllm-omni/pull/5052#discussion_r3577322320)、[exit status](https://github.com/vllm-project/vllm-omni/pull/5052#discussion_r3577322414)、[p90](https://github.com/vllm-project/vllm-omni/pull/5052#discussion_r3577332489)、[key set](https://github.com/vllm-project/vllm-omni/pull/5052#discussion_r3578699532)。

## PR #5087 — ModelOpt NVFP4 remap

- `6f14425c`: `pre_quant_scale` 被 remap，但 vLLM 0.25 的 layer 不注册/消费它，存在静默过滤后错误激活风险。
- 后续修法是对该 tensor 显式 fail fast，并要求导出时 fold；最终错误文本把假设绑定到 `vLLM 0.25.0`。
- 后续 review 还核对两条 resolution path 的输出名不对称，以及 PR 中混入的 `pd_utils.py` scope。
- 证据：[unconsumed scale](https://github.com/vllm-project/vllm-omni/pull/5087#discussion_r3575533457)、[resolution asymmetry](https://github.com/vllm-project/vllm-omni/pull/5087#discussion_r3581535595)、[version boundary](https://github.com/vllm-project/vllm-omni/pull/5087#discussion_r3581535606)。

## PR #4980 — output processor refactor

- `05f2abad`: 删除旧模块并在新旧位置保留重复 class，破坏公开 import 且产生不同 class identity；要求旧路径 re-export 新定义。
- `fa6e089d`: shim 只 warning、不 re-export；metadata scalar tensor 的旧 relocation 行为丢失；`append` 的返回合同在 empty/non-empty 情况不同。
- 最终 `engine/mm_outputs.py` re-export `outputs.mm_outputs`；`_METADATA_TENSOR_KEYS` 在 consolidation 前移入 metadata；API 改名 `merged_with` 并明确调用方保存返回值。
- 证据：[re-export/class identity](https://github.com/vllm-project/vllm-omni/pull/4980#discussion_r3550895296)、[shim incomplete](https://github.com/vllm-project/vllm-omni/pull/4980#discussion_r3581293307)、[metadata regression](https://github.com/vllm-project/vllm-omni/pull/4980#discussion_r3581293314)、[append contract](https://github.com/vllm-project/vllm-omni/pull/4980#discussion_r3581293322)。

## PR #5084 — L4 performance test marks

- `b876e2a0`: 硬件信息重复硬编码进多个 JSON，review 要求由 patch/function 集中生成。
- `61ac516d` 以后：文档示例与实现漂移；`mark`/`marks` 名称含混，最终继续调整文档和字段命名。
- 证据：[hardware duplication](https://github.com/vllm-project/vllm-omni/pull/5084#discussion_r3575523252)、[docs alignment](https://github.com/vllm-project/vllm-omni/pull/5084#discussion_r3588383402)、[field naming](https://github.com/vllm-project/vllm-omni/pull/5084#discussion_r3595607036)。
