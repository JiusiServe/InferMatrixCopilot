---
title: "ascend-moe-optimizer-auto-trace-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ascend-moe-optimizer-auto-trace-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bf18159d8701b187a0a236d12353dc9f5f0c04fe7bfca744cf79c32c360e8d27 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh`**

- 脚本执行边界：`python3 "${SKILL_ROOT}/scripts/bootstrap_trace_toolchain.py" --build-dir "${BUILD_DIR}"`；`python3 "${SKILL_ROOT}/scripts/patch_build_pipeline.py" \`；`python3 "${SKILL_ROOT}/scripts/verify_trace_scaffold.py" \`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/bootstrap_trace_toolchain.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2011df0bf75b091d1721fa3eacb4532504463b0d0f5cdfa43101fccddf9c6e55 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/bootstrap_trace_toolchain.py`**

- 源码对模块职责的说明：Deploy the trace toolchain Python scripts into a target build directory (flat layout).。
- 调用入口 `deploy_file(src, dst, force, dry_run)`；声明返回 `tuple[str, bool]`。
- 调用入口 `main()`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import shutil`。
- 模块级配置或常量名称：`SCRIPT_DIR`, `TOOLCHAIN_FILES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/bootstrap_trace_toolchain.py#L1-L124)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/check_compile_safety.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c7bc3003f7cc7cb9677ce31939498d722645368ec7b37e69b149e2c58a71ffd -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/check_compile_safety.py`**

- 源码对模块职责的说明：Static compile-safety checker for MoeTracing instrumentation.。
- `CheckResult` 定义类型边界；方法入口：`__init__`, `error`, `warn`, `ok`。
- 调用入口 `read_lines(path)`；声明返回 `List[str]`。
- 调用入口 `strip_comments_and_strings(line)`；声明返回 `str`。
- 调用入口 `check_brace_balance(path, lines, result)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import re`。
- 模块级配置或常量名称：`COMMENT_LINE`, `STRING_LITERAL`, `MOETRACING_CALL`, `TRACE_POINT_RE`, `MOETRACING_FULL`, `INCLUDE_RE`, `COMMON_LOOP_VARS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/check_compile_safety.py#L1-L305)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/generate_instrumentation_plan.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3a96f3f9785451641a0d91a5e489a81efc2d1480b9dc7e7370419821dc79fb4 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/generate_instrumentation_plan.py`**

- 源码对模块职责的说明：Generate a function-level instrumentation plan (max depth=5) for Ascend operator code. This script does not modify source files.。
- `FuncInfo` 定义类型边界。
- 调用入口 `iter_code_files(root)`；声明返回 `List[pathlib.Path]`。
- 调用入口 `extract_functions(path)`；声明返回 `List[FuncInfo]`。
- 调用入口 `extract_block(text, open_brace_idx)`；声明返回 `Tuple[str, int]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。
- 模块级配置或常量名称：`FUNC_DEF_RE`, `CALL_RE`, `KEYWORDS`, `HOT_WORDS`, `MAX_DEPTH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/generate_instrumentation_plan.py#L1-L164)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/inspect_rank_pt.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83e2098f269802dee921e2511ec3ce31a16bae2c7472083c1b394a046f1e7e25 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/inspect_rank_pt.py`**

- 源码对模块职责的说明：Inspect rank*.pt produced by save_profiling_data: shapes, counters, sample trace IDs.。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import logging`；`import os`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/inspect_rank_pt.py#L1-L90)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a5c318e6352d4d5a353620a64b99c1d99324241fa35e485cefa10ca3ed7f894 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py`**

- 源码对模块职责的说明：Apply TRACE_POINT instrumentation to operator source files with function-level granularity. Rules: - Root label defaults to 'processing' - Max depth defaults to。
- `FunctionBlock` 定义类型边界。
- 调用入口 `find_functions(text)`；声明返回 `List[FunctionBlock]`。
- 调用入口 `find_match_brace(text, open_idx)`；声明返回 `int`。
- 调用入口 `normalize_label(func_name)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import pathlib`。
- 模块级配置或常量名称：`FUNC_RE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L1-L128)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dfb540efc0a91250bbb5b7d3c925528f37f4e274821dada718821a2a0f038140 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py`**

- 源码对模块职责的说明：Patch compile/build script to inject trace preprocessor command. Idempotent by marker comments.。
- 调用入口 `inject_hook(script_text, cmd)`；声明返回 `str`。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import re`。
- 模块级配置或常量名称：`START_MARK`, `END_MARK`, `ANCHOR_PATTERNS`, `FALLBACK_PATTERN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py#L1-L85)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f54ddc8f3c02ed735daf4e675e10742045aa5e18e8b768317247239894113b38 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py`**

- 源码对模块职责的说明：从 rank*.pt 和 point_map.json 生成 Chrome Trace JSON。 支持 64 位组合 ID 解析、B/E 配对、区间深度过滤。。
- 调用入口 `extract_point_id_parts(combined_id)`；声明返回 `Tuple[int, int]`。
- 调用入口 `parse_profiling_data(tensor, core_type, core_id)`；声明返回 `List[Dict]`。
- 调用入口 `load_all_ranks(data_dir)`；声明返回 `Dict[int, List[Dict]]`。
- 调用入口 `load_mapping(path)`；声明返回 `Dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import glob`；`import json`；`import logging`；`import os`。
- 模块级配置或常量名称：`CLOCK_DIVISOR`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_collector.py#L1-L404)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=323d660787531541b63a369e99c93af7d75f0d96a72c332032f202f609d4b799 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py`**

- 源码对模块职责的说明：TRACE_POINT 预处理器：扫描源码中的 TRACE_POINT("label", "B/E")， 为每个调用分配唯一 point_id（int32），替换源码后生成 point_map.json 映射表。 支持事件 ID 分配、嵌套校验、映射表导出。。
- `TracePreprocessor` 定义类型边界；方法入口：`__init__`, `process_file`, `process_directory`, `save_mappings`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import json`；`import logging`；`import os`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L1-L139)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_save.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de9d6da4c48786a3d30740b677321bd2d2d7c8d48b01d11f1411112435b38174 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_save.py`**

- 源码对模块职责的说明：加载原始 profiling tensor（.pt），调用 trace_utils 按核类型拆分并保存。。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import logging`；`import torch`；`from trace_utils import save_profiling_data`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_save.py#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3fbb425f5b3b1cbae820bf249f20214080186ff997129d48fd071bcd8a4b8a97 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py`**

- 源码对模块职责的说明：Profiling 数据工具集：从 base.h 读取宏配置、核类型映射、profiling tensor 拆分保存。。
- 调用入口 `get_define_value_from_file(filepath, macro_name)`。
- 调用入口 `get_define_value_from_base(macro_name, base_h_path)`。
- 调用入口 `get_prof_size_per_core(base_h_path)`；声明返回 `int`。
- 调用入口 `get_enable_moe_profiling(base_h_path)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import os`；`import re`；`from typing import Callable, List, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_utils.py#L1-L149)。
<!-- /kb:file -->
