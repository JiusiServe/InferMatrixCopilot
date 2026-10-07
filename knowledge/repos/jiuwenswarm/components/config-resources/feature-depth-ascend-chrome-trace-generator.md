---
title: "Chrome Trace JSON 生成器（trace_collector）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L367-L404, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L372-L379, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L375-L382, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L78-L88, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L384-L387, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L15-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L373-L387, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py:L143-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L19-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L46-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L376-L382, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md:L371-L382]
feature: "ascend-chrome-trace-generator"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_save.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/inspect_rank_pt.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/bootstrap_trace_toolchain.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/verify_trace_scaffold.py"]
---

# Chrome Trace JSON 生成器（trace_collector）：实现深读

[功能概览](feature-ascend-chrome-trace-generator.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ascend-chrome-trace-generator facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=62d71eb5d6282950fd330ffbdfb72c5e86189da5d835f363495a855a7874180b -->
**main(): 解析参数后加载 rank 数据与 point_map，生成 chrome trace**
main() 配置日志、解析 CLI 参数，将 CLOCK_DIVISOR 设为 args.clock_divisor；load_all_ranks 读取 data_dir，若为空记录错误并 return；否则加载 mapping、打印诊断信息并调用 generate_chrome_trace(all_data, mapping, args.output, args.extra_mode, args.depth)。仅在 __main__ 时执行。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L367–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L367-L404)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":404,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"464ac70282b335d6263be2c014f308b788cb773baff751fa35f8818a34a3c4d4","start":367}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-chrome-trace-generator facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e3e73cd3f251517278920078d2ac040262201604011d0a5acf0a79bd95c577c5 -->
**位置参数 data_dir 与 mapping_file，可选 -o/--output 等 CLI 契约**
CLI 需要两个位置参数：data_dir（含 rank*.pt 的目录）与 mapping_file（预处理器的 point_map.json）；可选项 -o/--output、--clock-divisor、--extra-mode（choices=["legacy","seq"]）、--depth。调用方需先产生 rank*.pt 与 point_map.json 才能运行。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L372–L379](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L372-L379)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":379,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"228a58b1ed95defdd51c3889967cd1b15e393133e13a973e9a080ba285a3090d","start":372}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-chrome-trace-generator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc03e27e92ef93ec91fee25ea802866d8ee764607bd49e14780ad8b010c855f5 -->
**默认 output=chrome_trace.json、clock-divisor=50.0、extra-mode=seq、depth=0**
argparse 默认值：--output 默认 "chrome_trace.json"，--clock-divisor 默认 50.0（MHz 时钟频率），--extra-mode 默认 "seq"（仅允许 legacy/seq），--depth 默认 0 表示不过滤（0=all）。CLOCK_DIVISOR 全局变量在解析后被赋为该值。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L375–L382](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L375-L382)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":382,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"34663b3af372c32b918664721f22b84fcab6b53090e79ece89b67de4ca679f20","start":375}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-chrome-trace-generator facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0d56be32a2da11cd2f9f450c393fc967a5a85d8bd321795ac4eb580e5b4172a -->
**缺失 point_map 文件会记录错误并返回空字典；空 rank 数据会中止主程序**
如果路径不存在，load_mapping 会记录 'ERROR: point_map not found' 并返回 {}；如果 JSON 不是字典，它会记录 'point_map must be a JSON object' 并返回 {}。在 main 中，当 all_data 为空时会记录 'No rank*.pt files found' 并返回，不再进行后续生成。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L78–L88](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L78-L88), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L384–L387](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L384-L387)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":88,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"9301cfd414b3dd12ef10fc3e56d8c1bf9d6ad3c687574e3d73fe1a7ccb3da22e","start":78},{"end":387,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"528cd596f88777cc55639ba92b808dad5e4c3e585eb657718444900c37c695d8","start":384}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-chrome-trace-generator facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8dc8ed4e3b3ef23be1e5a185d2cf8aee02cb68eb38b8c4f0586d23bfa432bc6e -->
**trace_collector 导入 torch 并以 data_dir 中 rank*.pt 文件为输入**
trace_collector.py 导入 torch，CLI 接受包含 rank*.pt 文件的 data_dir 并传给 load_all_ranks；配套 trace_utils.py 用 torch.save 写出 rank{rank_id:03d}.pt，即两侧通过该 torch 序列化文件格式耦合（未显示加载实现细节）。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L15–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L15-L15), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L373–L387](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L373-L387), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py:L143–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py#L143-L149)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":15,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"b91a3bc5e2064d025a8ae122555c96948ec5b4895d53d809c4b66b71a4915133","start":15},{"end":387,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"9a65d669a00d901181f070dde5be194708b59eacbe5fc8c09d05321a516312f3","start":373},{"end":149,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py","sha256":"7e3b250f9bf34b254b606472dd475a8043ccaaf127162d2bc32467316e74e7c8","start":143}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-chrome-trace-generator facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2ef8fb9170a476086b54e7ac033b6aa4fa13f97b0a57317a9544f5d30dff1001 -->
**cycle→us 换算用可变模块全局 CLOCK_DIVISOR（默认 50.0，可被 --clock-divisor 覆盖）**
设计推断（非作者历史意图）：

默认 50.0（MHz），main 里通过 global 把 --clock-divisor 赋给 CLOCK_DIVISOR；换算处直接 diff / CLOCK_DIVISOR。收益是适配不同时钟频率；代价（推断）是可变模块全局让换算结果依赖解析 argv 的执行顺序。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L19–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L19-L19), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L46–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L46-L48), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L376–L382](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L376-L382)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"b063f004f0a1ebaeff5b390bc57bfe2b570e1d18a31f7ee7c5ede303b28feaad","start":19},{"end":48,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"3c5519c8197b6487776b7ca4820832dca48b264a6f6d8cee0bf4a535d52077ba","start":46},{"end":382,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py","sha256":"6c99402e92d59f139d691f9fe38c7089c9f785d3d4896ecbdeaa9a2ac9f3b548","start":376}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-chrome-trace-generator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4bdcae2d10c0fc1e47ee67b6c678a9c82d144a41b71b9c5524bae1736e95f0d4 -->
**记录的手动流程：运行 trace_collector.py 生成 chrome_trace.json（未执行）**
文档中的人工验收步骤（本轮未执行）：

reference.md 记录了手动命令 `python <skill_root>/scripts/trace_collector.py profiling_data point_map.json -o chrome_trace.json`，读取 rank*.pt 与 point_map.json 并生成 Chrome Trace 格式输出；文档还列出可选参数 --clock-divisor 50.0（时钟 MHz）、--extra-mode seq、--depth 0。此为文档记载的操作与预期结果，明确标注未执行（NOT EXECUTED），不据此断言任何测试已通过。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md:L371–L382](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md#L371-L382)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":382,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md","sha256":"81c851fe9896c15f9923e422dfa9055245ea6fcbf970ce2f4b854270ebd140e0","start":371}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
