---
title: "Chrome Trace JSON 生成器（trace_collector）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L32-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L22-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L338-L352, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py:L124-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L372-L382, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py:L71-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L367-L400, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L58-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/verify_trace_scaffold.py:L14-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L104-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L338-L363]
feature: "ascend-chrome-trace-generator"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_save.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/inspect_rank_pt.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/bootstrap_trace_toolchain.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/verify_trace_scaffold.py"]
---

# Chrome Trace JSON 生成器（trace_collector）

<!-- kb:knowledge owner=feature-ascend-chrome-trace-generator facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**数据流与处理阶段**

流水线分四段：(1) load_all_ranks 用 glob 按文件名解析 rank id，torch.load 每个由 trace_utils.save_profiling_data 产出的按核类型分组的 tensor 列表；(2) parse_profiling_data 按核读取记录——tensor[core,0] 是计数器（记录数 = 计数 - 1），ID 自 [1+i] 正向、时间戳自 [-2-i] 反向读取，与首时间戳 [-1] 做无符号差后除以 CLOCK_DIVISOR 得微秒；组合 ID 拆为低 32 位 base_point_id 与高 32 位 extra_id（均按补码转有符号）。(3) generate_chrome_trace 按 (rank, core_type, core_id) 生成 pid/tid 元数据，做 B/E 配对与深度过滤；(4) 写出 {traceEvents, displayTimeUnit:'us', otherData:{统计与参数}}。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L32–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L32-L55), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L22–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L22-L29), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L338–L352](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L338-L352), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py:L124–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py#L124-L148)

<!-- kb:knowledge owner=feature-ascend-chrome-trace-generator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**配置项与默认值**

命令行配置：`-o/--output`（默认 chrome_trace.json）、`--clock-divisor`（float，默认 50.0，即 MHz，cycle→us；赋给模块级 CLOCK_DIVISOR）、`--extra-mode`（legacy|seq，默认 seq）、`--depth`（int，默认 0 = 不过滤；非 0 时按 depth_from_leaf <= depth 保留区间）。上游 trace_utils 还受环境变量 MOE_USE_1C2V（默认 "0"；为 "1" 时核数列表从 [24,48] 变为 [24,24,24] 并改用 1c2v 核映射）以及 base.h 宏 PROF_SIZE_PER_CORE（默认 2048）和 ENABLE_MOE_PROFILING 影响。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L372–L382](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L372-L382), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py:L71–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py#L71-L85)

<!-- kb:knowledge owner=feature-ascend-chrome-trace-generator facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**入口与调用契约**

公开入口是命令行 `main()`：位置参数 `data_dir`（含 rank*.pt 的目录）与 `mapping_file`（point_map.json），选项 `-o/--output`（默认 chrome_trace.json）、`--clock-divisor`、`--extra-mode`、`--depth`。主流程为 load_all_ranks → （空则报错并提前 return）→ load_mapping → diagnose_mapping_overlap → generate_chrome_trace。generate_chrome_trace 也可作为库函数直接调用，返回写出的 trace 字典。错误契约：load_all_ranks 对单个 .pt 加载失败仅告警跳过；load_mapping 对文件缺失或非对象结构返回 {}，但 open/json.load 未捕获异常，损坏 JSON 会直接抛出。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L367–L400](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L367-L400), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L58–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L58-L90)

<!-- kb:knowledge owner=feature-ascend-chrome-trace-generator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**现有验证入口**

verify_trace_scaffold.py 检查构建目录是否包含 trace_preprocessor/trace_utils/trace_save/trace_collector 四个必需脚本，缺文件时退出码 1；可选 --compile-script 检查编译脚本是否含 TRACE_PREPROCESSOR_HOOK_START/END 钩子标记。运行期诊断：generate_chrome_trace 结束时若 skipped_no_mapping>0 发出警告，统计写入 otherData；diagnose_mapping_overlap 仅当 rank*.pt 中的唯一 id 集合与 point_map 键集合均非空且交集为空时，才提示 point_map.json 与内核构建不匹配、应改用同一 ascend_kernels_*_proj 目录编译进 OPP 的 point_map.json，并输出双方样本 id。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/verify_trace_scaffold.py:L14–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/verify_trace_scaffold.py#L14-L54), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L104–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L104-L125), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py:L338–L363](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L338-L363)

