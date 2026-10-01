---
title: "ascend-moe-optimizer-trace-analyzer-analyzers 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ascend-moe-optimizer-trace-analyzer-analyzers 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/diagnosis.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f1f0503c83665e82ab002b2cfa7a7d4859b1e8798570d06a02a78df455c32d9 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/diagnosis.py`**

- `AutoDiagnosisInput` 定义类型边界。
- 调用入口 `build_auto_diagnosis(inp)`；声明返回 `dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Any, Dict, List, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/diagnosis.py#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f67961f1412601e7f3926e93c754209ad41fc3c7de04b1cf27836d56fc0bb8b -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py`**

- `LLMPromptInput` 定义类型边界。
- 调用入口 `build_llm_prompt(inp)`；声明返回 `str`。
- 调用入口 `run_llm_command(prompt, command, timeout_s)`；声明返回 `dict`。
- 调用入口 `generate_llm_analysis(prompt, enabled, command, timeout_s)`；声明返回 `dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import shlex`；`import subprocess`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/metrics.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a2c6c4ad89621b65972b9fa6372722dd1de54d5b6ce008da9a5169924818b55 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/metrics.py`**

- 调用入口 `normalize_event_name(name)`；声明返回 `str`。
- 调用入口 `build_phase_instances(events, mapper)`；声明返回 `Table`。
- 调用入口 `build_phase_summary(instances)`；声明返回 `Table`。
- 调用入口 `build_category_summary(instances)`；声明返回 `Table`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from collections import Counter, defaultdict`；`from typing import Any, Dict, Iterable, List, Optional, Tuple`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/metrics.py#L1-L595)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/parser.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c828e9eeff5190ef24560ab177555c2ea0ee1f5f37fc0066a8fe7ae87357d43e -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/parser.py`**

- `Event` 定义类型边界。
- 调用入口 `parse_trace_json(trace_path)`；声明返回 `List[Event]`。
- 调用入口 `events_to_dicts(events)`；声明返回 `List[Dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from dataclasses import dataclass, asdict`；`from typing import Any, Dict, List, Optional, Tuple`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/parser.py#L1-L173)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/phase_mapper.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be5fb5ee5f39cd6cae7df5435dd3caec0392fa28d1444bdc1ef84436f3bb19ea -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/phase_mapper.py`**

- `PhaseMapper` 定义类型边界；方法入口：`__init__`, `map_event_name`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from typing import Dict, List, Optional, Tuple`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/phase_mapper.py#L1-L110)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/plots.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=609dc1769ef7ee922b93edd12e41b54ba06b03c671f2c82b41374e706835b8a8 -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/plots.py`**

- 调用入口 `plot_analysis_charts(output_path, phase_summary, category_summary, core_group_summary, top_n)`；声明返回 `str`。
- 调用入口 `generate_summary_plots(output_dir, phase_summary, category_summary, core_group_summary, top_n)`；声明返回 `List[str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import getpass`；`import os`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/plots.py#L1-L219)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/reporter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f557209f8abb8221cc7fbcb5c375132d08d01e3428cbbfc13a906f96e9dd06eb -->
**`jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/reporter.py`**

- `StatisticalSummaryInput` 定义类型边界。
- `MarkdownReportInput` 定义类型边界。
- 调用入口 `ensure_dir(path)`；声明返回 `None`。
- 调用入口 `save_table(rows, path, fieldnames)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import csv`；`import json`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/reporter.py#L1-L490)。
<!-- /kb:file -->
